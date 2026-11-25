"""Hidden full-campaign receipts, timed VFX captures and matched Stage25 draw samples."""
import argparse
from contextlib import nullcontext
import ctypes
import hashlib
import json
import os
from pathlib import Path
import pickle
from statistics import median
import sys
from time import perf_counter_ns
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from actor_animation import ActorAnimation
from arena_art_common import ArenaArtError
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX, MAX_EFFECTS, MAX_PARTICLES
from game import StageGame
from game_renderer import GameFlowRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from tests.test_hp_carryover import fight
from tools.chapter_art_play import advance_campaign, session
from tools.stage5_art_preview import capture_png, open_preview


def run(driver,output,*,renewed=False,layered=False,telegraph=False):
    import sdl2 as s
    from pico2d import pico2d as c

    if output:
        output.mkdir(parents=True,exist_ok=False)
    renewed = renewed or layered
    motion = RenderMotion(improved=renewed)
    animation = ActorAnimation(improved=renewed)
    vfx = CombatVFX(renewed=renewed,layered=layered)
    from attack_telegraph import TelegraphRenderer
    warning = TelegraphRenderer() if telegraph else None
    path = LiveArenaArtPath(c,motion=motion,animation=animation,vfx=vfx,
                           default_enabled=True,enlarged=renewed,telegraph=warning)
    hud = GameFlowRenderer()
    scenes, campaign, coverage, peaks = {}, [], set(), [0,0]
    resources = dict(loads=0,releases=0,peak=0)
    timings = {}
    live = set()
    def sync(g,elapsed=1/60):
        feed = g.encounter.ledger.presentation
        frozen = {g.player.entity_instance_id} if g.combat.active_attack or g.parry.active_at(g.combat.tick) else set()
        if g.encounter.pulse:
            frozen.update(e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse.frozen(e))
        motion.update((g.player,*g.encounter.enemies),elapsed,session=g.combat.combat_session_id,frozen=frozen)
        batch = feed.drain()
        animation.update(g,elapsed,batch,motion=motion)
        vfx.update(g,elapsed,batch,motion=motion)
        active = {fx.name for fx in vfx.effects}
        coverage.update(active)
        peaks[0] = max(peaks[0],len(vfx.effects))
        peaks[1] = max(peaks[1],sum(fx.particles for fx in vfx.effects))
        assert peaks[0]<=MAX_EFFECTS and peaks[1]<=MAX_PARTICLES
        assert set(vfx.charges)=={e.key for e in g.encounter.ledger.telegraphs}
        return active

    def frame(g):
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        assert path.draw(g,motion.positions)
        assert not vfx.failed and not path.path.renderer.animation_failed
        if warning is not None:
            assert not warning.failed
            expected = {cell for e in g.resolver.live_telegraphs(g.combat.tick) for cell in e.target_cells} if g.playing else set()
            assert set(path.path.renderer.warning_cells)==expected

    def capture(g,name):
        if name in scenes:
            return
        before = pickle.dumps((g,motion))
        frame(g)
        hud.draw_stage_label(c,g)
        hud.draw(c,g)
        assert pickle.dumps((g,motion))==before
        meta = dict(stage=g.stage_number,tick=g.combat.tick,visual_time=round(vfx.time,6),
                    active=[dict(cue=f.name,origin=f.origin,cell=f.cell,targets=len(f.cells),damage=f.amount)
                            for f in vfx.effects])
        if output:
            png = output/(name+'.png')
            capture_png(c,png)
            meta['sha256'] = hashlib.sha256(png.read_bytes()).hexdigest()
        scenes[name] = meta

    def benchmark(g,label):
        frame(g)
        art = path.path.renderer
        original = art.animation,art.vfx
        try:
            for mode,anim,effects in [('static',None,None),('animation',animation,None),('animation_vfx',*original)]:
                art.animation,art.vfx = anim,effects
                samples = []
                for i in range(140):
                    start = perf_counter_ns()
                    frame(g)
                    s.SDL_RenderPresent(c.renderer)
                    if i>=20:
                        samples.append((perf_counter_ns()-start)/1e6)
                samples.sort()
                timings[label+'_'+mode] = [round(x,3) for x in (median(samples),samples[113],samples[118])]
        finally:
            art.animation,art.vfx = original

    env = {key:value for key,value in os.environ.items()
           if not (key.startswith('CHECKMATE_') and key.endswith('_ART'))}
    env.update(SDL_VIDEODRIVER='windows' if driver=='direct3d11' else 'dummy',SDL_AUDIODRIVER='dummy')
    with patch.dict(os.environ,env,clear=True):
        create = c.SDL_CreateRenderer
        if driver=='direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
        override = patch.object(c,'SDL_CreateRenderer',lambda w,i,f:create(w,i,s.SDL_RENDERER_ACCELERATED))
        with override if driver=='direct3d11' else nullcontext():
            open_preview(c,capture=True)
        try:
            info = s.SDL_RendererInfo()
            assert s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info))==0 and info.name.decode()==driver
            load,destroy = c.load_image,c.SDL_DestroyTexture
            def acquire(file):
                img = load(file)
                handle = ctypes.cast(img.texture,ctypes.c_void_p).value
                assert handle and handle not in live
                live.add(handle)
                resources['loads']+=1
                resources['peak']=max(resources['peak'],len(live))
                return img
            def release(tex):
                if tex:
                    live.remove(ctypes.cast(tex,ctypes.c_void_p).value)
                    resources['releases']+=1
                return destroy(tex)
            with patch.object(c,'load_image',acquire),patch.object(c,'SDL_DestroyTexture',release):
                try:
                    g,flow = session(1)
                    flow.enable_presentation()
                    original_tick = StageGame.resolve_current_tick
                    samples = {1:'player_hit', 3:'knight_land', 16:'rook_strike',
                               24:'queen_fire', 25:'boss_death'}
                    def observe(current):
                        result = original_tick(current)
                        names = sync(current)
                        stage = current.stage_number
                        cue = samples.get(stage)
                        if cue in names:
                            fx = next(f for f in vfx.effects if f.name==cue)
                            if vfx.time-fx.start >= (.12 if cue in ('rook_impact','knight_land') else .033):
                                capture(current,f'stage{stage}_{cue}')
                        # Take the first realized example within the chapter when a
                        # particular stage's enemy dies before it gets a turn.
                        for chapter,desired in ((1,'pawn_thrust'),(3,'bishop_cast')):
                            if current.chapter==chapter and desired in names:
                                fx = next(f for f in vfx.effects if f.name==desired)
                                if vfx.time-fx.start >= (0 if desired=='pawn_thrust' else .035):
                                    capture(current,f'chapter{chapter}_{desired}')
                        if stage==24 and sum(kind=='queen' for _,_,kind in vfx.charges.values())==2:
                            capture(current,'stage24_two_charges')
                        return result
                    for stage in range(1,26):
                        g = flow.game
                        sync(g,0)
                        frame(g)
                        with patch.object(StageGame,'resolve_current_tick',observe):
                            result = fight(flow)
                        assert result[1]==('BOSS_CLEAR' if stage%5==0 else 'UPGRADE'),result
                        campaign.append(result)
                        if stage!=25:
                            advance_campaign(flow,result)
                    # A stationary player gives the forest Rook time to finish a
                    # real dash. The fast campaign can kill this enemy beforehand.
                    g = _new_stage_game(6)
                    g.encounter.ledger.presentation = PresentationEvents()
                    sync(g,0)
                    while g.playing and g.combat.tick<900:
                        g.advance()
                        sync(g)
                        if any(f.name=='rook_impact' and vfx.time-f.start>=.12 for f in vfx.effects):
                            capture(g,'stage6_rook_impact')
                            break
                    for delta in (18,7):
                        g = _new_stage_game(25)
                        g.encounter.ledger.presentation = PresentationEvents()
                        sync(g,0)
                        if delta==7:
                            benchmark(g,'idle')
                        while g.combat.tick < 385-delta:
                            g.advance()
                            sync(g)
                        pulse = g.encounter.pulse.event
                        assert pulse.hit_tick-g.combat.tick==delta
                        g.resolver.register_parry(g.parry.request(g.combat.tick))
                        g.advance(delta)
                        sync(g,delta/60)
                        grade = 'normal' if delta==18 else 'perfect'
                        assert g.resolver.last_parry_result.status==grade
                        capture(g,'pulse_'+grade)
                        if delta==7:
                            # Isolate the world shake and VFX draw from Pico2D HUD
                            # primitives, which legitimately set their own draw color.
                            def state():
                                viewport = s.SDL_Rect()
                                blend = ctypes.c_int()
                                rgba = [ctypes.c_uint8() for _ in range(4)]
                                s.SDL_RenderGetViewport(c.renderer,ctypes.byref(viewport))
                                assert s.SDL_GetRenderDrawBlendMode(c.renderer,ctypes.byref(blend))==0
                                assert s.SDL_GetRenderDrawColor(c.renderer,*(ctypes.byref(x) for x in rgba))==0
                                return (viewport.x,viewport.y,viewport.w,viewport.h), blend.value, tuple(ch.value for ch in rgba)
                            effects = path.path.renderer.vfx
                            before = state()
                            with effects.world(c):
                                assert state()[0]!=before[0]
                                effects.draw('front',c,g)
                            assert before==state()
                            assert any(f.name=='player_hit' and f.amount==2 for f in vfx.effects)
                            for i in range(12):
                                g.advance()
                                sync(g)
                                if i in (3,11):
                                    capture(g,'pulse_perfect_plus_'+str(i+1))
                                if i==3:
                                    benchmark(g,'pulse')
                    required = {'parry_perfect','parry_normal','player_hurt','player_hit','king_pulse',
                                'player_swing','pawn_thrust','rook_strike','rook_impact','knight_strike',
                                'knight_land','bishop_cast','queen_fire','king_strike','enemy_death','boss_death'}
                    assert required<=coverage,required-coverage
                    expected = {'stage24_two_charges','stage24_queen_fire','chapter1_pawn_thrust',
                                'stage6_rook_impact','chapter3_bishop_cast','stage25_boss_death'}
                    assert expected <= scenes.keys(),expected-scenes.keys()
                    # Renderer failure must leave the active animated renderer usable.
                    renderer = path.path.renderer
                    if layered:
                        atlas = renderer.vfx.atlas
                        assert atlas.image is not None
                        with patch.object(atlas,'flush',side_effect=ArenaArtError('QA atlas')) as fail:
                            frame(g)
                            frame(g)
                            assert atlas.failed and atlas.image is None and fail.call_count==1
                    with patch.object(renderer.vfx.mesh,'flush',side_effect=ArenaArtError('QA')) as fail:
                        assert path.draw(g,motion.positions) and vfx.failed
                        assert path.draw(g,motion.positions) and not renderer.animation_failed
                        assert fail.call_count==1
                finally:
                    path.close()
            assert not live and resources['loads']==resources['releases']
        finally:
            c.close_canvas()
            c.renderer=c.window=None
    report = dict(driver=driver,campaign=campaign,resources=resources,captures=scenes,coverage=sorted(coverage),
                  peak_effects=peaks[0],peak_particles=peaks[1])
    if output:
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return dict(captures=len(scenes),campaign=len(campaign),resources=resources,peaks=peaks,
                median_p95_p99_ms=timings)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer',choices=('software','direct3d11'),default='direct3d11')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--vfx-renewal',action='store_true')
    parser.add_argument('--vfx-layered',action='store_true')
    parser.add_argument('--telegraph',action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.renderer,args.output,renewed=args.vfx_renewal,
                         layered=args.vfx_layered,telegraph=args.telegraph),indent=2))
