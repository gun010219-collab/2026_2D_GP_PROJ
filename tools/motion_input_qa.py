"""Compare R6 and R7-A1 from identical combat, capture real stages and time SDL."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import pickle
from statistics import median
import sys
from time import perf_counter_ns
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from actor_animation import ActorAnimation
from arena_art_common import PIECE_INCREASE
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from game_audio import AudioManager,AudioSettings
from game_renderer import GameFlowRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from sdl_input import GameplayInput
from tests.test_game_audio import FakeMixer
from tools.stage5_art_preview import capture_png,open_preview


def run(output,driver):
    import sdl2 as s
    from pico2d import pico2d as c

    if output:
        output.mkdir(parents=True,exist_ok=False)
    counts = dict(loads=0,frees=0,peak=0)
    live,frames,measure = set(),{},{}
    motion=[RenderMotion(improved=i) for i in (False,True)]
    anim=[ActorAnimation(improved=i) for i in (False,True)]
    vfx=[CombatVFX(),CombatVFX()]
    art=[LiveArenaArtPath(c,default_enabled=True,motion=m,animation=a,vfx=v,enlarged=bool(i))
         for i,(m,a,v) in enumerate(zip(motion,anim,vfx))]
    backend=FakeMixer()
    audio=AudioManager(backend,AudioSettings())
    hud=GameFlowRenderer(official=True)

    def sync(g,dt):
        batch=g.encounter.ledger.presentation.drain()
        frozen = {g.player.entity_instance_id} if g.combat.active_attack or g.parry.active_at(g.combat.tick) else set()
        if g.encounter.pulse:
            frozen.update(e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse.frozen(e))
        for m,a,v in zip(motion,anim,vfx):
            m.update((g.player,*g.encounter.enemies),dt,session=g.combat.combat_session_id,frozen=frozen)
            a.update(g,dt,batch,motion=m)
            v.update(g,dt,batch,motion=m)
        backend.live.clear()
        audio.update(g,dt,batch,motion=motion[1])

    def draw(g,mode,*,label=False):
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        assert art[mode].draw(g,motion[mode].positions)
        renderer=art[mode].path.renderer
        assert not renderer.animation_failed and not vfx[mode].failed
        if label:
            hud.draw_stage_label(c,g)
        return renderer

    def snap(g,name):
        before=pickle.dumps(g)
        for mode,label in enumerate(('r6','r7a1')):
            draw(g,mode,label=True)
            if output:
                path=output/(f'{name}_{label}.png')
                capture_png(c,path)
                frames[path.name]=dict(stage=g.stage_number,tick=g.combat.tick,
                                       sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        assert pickle.dumps(g)==before

    def benchmark(g,mode,include_pose=False):
        samples=[]
        draw(g,mode)
        for i in range(140):
            start=perf_counter_ns()
            if include_pose:
                anim[mode].update(g,0,(),motion=motion[mode])
            draw(g,mode)
            s.SDL_RenderPresent(c.renderer)
            if i>=20:
                samples.append((perf_counter_ns()-start)/1e6)
        samples.sort()
        return [round(x,3) for x in (median(samples),samples[113],samples[118])]

    def stage(number):
        g=_new_stage_game(number)
        g.encounter.ledger.presentation=PresentationEvents()
        sync(g,0)
        return g

    env={k:v for k,v in os.environ.items() if not (k.startswith('CHECKMATE_') and k.endswith('_ART'))}
    env.update(SDL_VIDEODRIVER='windows' if driver=='direct3d11' else 'dummy',SDL_AUDIODRIVER='dummy')
    with patch.dict(os.environ,env,clear=True):
        if driver=='direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
            make=c.SDL_CreateRenderer
            with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:make(w,i,s.SDL_RENDERER_ACCELERATED)):
                open_preview(c,capture=True)
        else:
            open_preview(c,capture=True)
        info=s.SDL_RendererInfo()
        assert s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info))==0 and info.name.decode()==driver
        load,destroy=c.load_image,c.SDL_DestroyTexture
        def acquire(path):
            image=load(path)
            key=ctypes.cast(image.texture,ctypes.c_void_p).value
            assert key and key not in live
            live.add(key)
            counts['loads']+=1
            counts['peak']=max(counts['peak'],len(live))
            return image
        def release(texture):
            if texture:
                live.remove(ctypes.cast(texture,ctypes.c_void_p).value)
                counts['frees']+=1
            return destroy(texture)
        try:
            with patch.object(c,'load_image',acquire),patch.object(c,'SDL_DestroyTexture',release):
                try:
                    for n in range(1,26):
                        g=stage(n)
                        old,new=draw(g,0),draw(g,1)
                        assert old.warning_cells==new.warning_cells
                        assert old.order==new.order
                        for actor in (g.player,*g.encounter.enemies):
                            key=actor.entity_instance_id
                            a,b=old.actor_layouts[key],new.actor_layouts[key]
                            assert abs(b['height']/a['height']-PIECE_INCREASE.get(getattr(actor,'kind','player'),1.))<1e-9
                            assert a['foot']==b['foot'] and b['hp_y']<880
                    g=stage(1)
                    controls=GameplayInput(c)
                    def press(code):
                        controls.handle_key(SimpleNamespace(type=c.SDL_KEYDOWN,key=code),
                                            g.player,g.combat,parry=g.parry,
                                            occupied=g.encounter.occupied_cells,
                                            on_attack=g.resolver.resolve_player_attack,
                                            on_parry=g.resolver.register_parry)
                    press(c.SDLK_UP)
                    sync(g,0)
                    snap(g,'stage1_move_0')
                    for i in (1,2):
                        sync(g,1/60)
                        snap(g,f'stage1_move_{i}')
                    press(c.SDLK_LCTRL)
                    press(c.SDLK_LALT)
                    sync(g,0)
                    assert g.combat.active_attack and g.parry.last_attempt
                    snap(g,'stage1_ctrl_alt')
                    g=stage(3)
                    knight=next(e for e in g.encounter.enemies if e.kind=='knight')
                    peak=False
                    since=len(backend.cues)
                    for _ in range(104):
                        g.advance()
                        sync(g,1/60)
                        if not peak and motion[1].ground_pose(knight)[1]>17.9:
                            peak=True
                            snap(g,'stage3_knight_apex')
                        if 'knight_land' in backend.cues[since:]:
                            assert any(f.name=='knight_land' and f.landed is not None for f in vfx[1].effects)
                            snap(g,'stage3_knight_land')
                            break
                    assert peak and 'knight_land' in backend.cues[since:]
                    for n,cue in ((6,'rook_impact'),(12,'bishop_cast'),(24,'queen_fire')):
                        g=stage(n)
                        while g.playing and g.combat.tick<600:
                            g.advance()
                            sync(g,1/60)
                            active=[f for f in vfx[1].effects if f.name==cue]
                            if active and vfx[1].time-active[0].start>=.11:
                                snap(g,f'stage{n}_{cue}')
                                break
                        else:
                            raise AssertionError((n,cue))
                    g=stage(25)
                    for _ in range(378):
                        g.advance()
                        sync(g,1/60)
                    g.resolver.register_parry(g.parry.request(g.combat.tick))
                    for _ in range(11):
                        g.advance()
                        sync(g,1/60)
                    assert g.combat.tick==389 and g.resolver.last_parry_result.status=='perfect'
                    snap(g,'stage25_perfect_pulse')
                    for mode,label in enumerate(('R6','R7-A1')):
                        measure[label]=benchmark(g,mode)
                        measure[label+' with pose']=benchmark(g,mode,include_pose=True)
                finally:
                    for path in art:path.close()
        finally:
            c.close_canvas()
            c.window=c.renderer=None
    assert not live and counts['loads']==counts['frees']
    result=dict(driver=driver,captures=frames,texture_resources=counts)
    if output:
        (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return {**result,'performance_ms':measure}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--renderer',choices=('direct3d11','software'),default='direct3d11')
    args=parser.parse_args()
    print(json.dumps(run(args.output,args.renderer),indent=2))
