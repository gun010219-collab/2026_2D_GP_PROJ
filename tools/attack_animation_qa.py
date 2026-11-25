"""Capture real enemy attacks and benchmark both animation modes on hidden SDL."""
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
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from actor_animation import ActorAnimation, State
from attack_telegraph import TelegraphRenderer
from board import is_light_tile
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from input_controller import InputController
from main import _new_stage_game
from presentation_events import PresentationEvents
from player_combat_guide import player_aim
from render_motion import RenderMotion
from tools.stage5_art_preview import capture_png, open_preview


CASES = (
    ('pawn',1,'pawn','pawn_contact','left',4),
    ('rook',6,'rook','basic',None,0),
    ('knight',3,'knight','basic',None,0),
    ('bishop',12,'bishop','basic',None,0),
    ('queen',24,'queen','queen_diagonal',None,0),
    ('king_melee',5,'king','basic','up',6),
    ('king_pulse',25,'king','king_pulse',None,0),
)


def run(output,driver,*,player_combat=False,articulation=False,clips=False):
    import sdl2 as s
    from pico2d import pico2d as c
    if output:
        output.mkdir(parents=True,exist_ok=False)
    prior,after = ('previous','articulated') if articulation else (('previous','player') if player_combat else ('a3f','a3d'))
    animations = {mode:ActorAnimation(improved=True,enemy_attacks=articulation or player_combat or mode==after,
                                     player_actions=articulation or (player_combat and mode==after),
                                     articulated=articulation and mode==after) for mode in (prior,after)}
    if clips and (not articulation or not output):
        raise ValueError('Clips require both --articulation and --output')
    motion = RenderMotion(improved=True)
    vfx = CombatVFX(layered=True)
    warning = TelegraphRenderer()
    art = LiveArenaArtPath(c,motion=motion,animation=animations[after],vfx=vfx,
                           enlarged=True,default_enabled=True,telegraph=warning,
                           player_combat_visual=articulation or player_combat)
    scenes,performance,clip_frames = {},{},{}

    def draw(game,mode):
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        if art.path and art.stage == game.stage_number and art.path.renderer:
            art.path.renderer.animation = animations[mode]
            art.path.renderer.player_combat_visual = articulation or (player_combat and mode==after)
        assert art.draw(game,motion.positions)
        assert not art.path.renderer.animation_failed and not warning.failed and not vfx.failed
        return art.path.renderer

    def record(game,name,actor):
        before = pickle.dumps(game)
        for mode in animations:
            renderer = draw(game,mode)
            layout = renderer.actor_layouts[actor.entity_instance_id]
            pose,effect = animations[mode].mesh_pose(game,actor,motion)
            key = name+'_'+mode
            record = dict(stage=game.stage_number,tick=game.combat.tick,pose=pose.state.value,
                          attack_motion=pose.attack_motion,phase=round(pose.phase,5),foot=layout['foot'],
                          hp_y=layout['hp_y'],lift=layout.get('elevation',0.),
                          warning_cells=len(renderer.warning_cells),
                          vfx=[f.name for f in vfx.effects])
            if player_combat:
                aim = player_aim(game)
                record.update(facing=aim.facing,preview=aim.target,
                              locked=aim.strike.target_cell if aim.strike else None,
                              locked_facing=aim.strike.facing if aim.strike else None,
                              preview_light=is_light_tile(*aim.target) if aim.target else None)
            if output:
                file = output/(key+'.png')
                capture_png(c,file)
                record['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            scenes[key] = record
        assert pickle.dumps(game)==before

    def clip_frame(game,name,actor):
        from sdl2.sdlimage import IMG_SavePNG
        if name not in clip_frames:
            (output/'clips'/name).mkdir(parents=True)
            clip_frames[name] = []
        index = len(clip_frames[name])
        clip_frames[name].append(game.combat.tick)
        width,height = 264,184
        surface = s.SDL_CreateRGBSurfaceWithFormat(0,width,height,32,s.SDL_PIXELFORMAT_RGBA32)
        if not surface:
            raise RuntimeError('Cannot allocate clip crop')
        try:
            for mode in animations:
                renderer = draw(game,mode)
                x,y = renderer.actor_layouts[actor.entity_instance_id]['foot']
                rect = s.SDL_Rect(max(0,min(1440-width,round(x-width/2))),
                                  max(0,min(900-height,round(899-y-141))),width,height)
                file = output/'clips'/name/f'{index:03}_{mode}.png'
                if s.SDL_RenderReadPixels(c.renderer,ctypes.byref(rect),s.SDL_PIXELFORMAT_RGBA32,
                                          surface.contents.pixels,surface.contents.pitch):
                    raise RuntimeError('Cannot read clip crop')
                if IMG_SavePNG(surface,str(file).encode('utf-8')):
                    raise RuntimeError('Cannot write clip crop')
        finally:
            s.SDL_FreeSurface(surface)

    def benchmark(game,label):
        values = {mode:[] for mode in animations}
        draw(game,after)
        for block in range(12):
            for mode in ((prior,after) if block%2==0 else (after,prior)):
                for _ in range(12):
                    start = perf_counter_ns()
                    animations[mode].update(game,0,(),motion=motion)
                    draw(game,mode)
                    s.SDL_RenderPresent(c.renderer)
                    if block>=2:
                        values[mode].append((perf_counter_ns()-start)/1e6)
        for mode,values_ms in values.items():
            values_ms.sort()
            values[mode] = [round(x,3) for x in (median(values_ms),values_ms[113],values_ms[118])]
        performance[label] = values

    def sync(g):
        frozen = {g.player.entity_instance_id} if g.combat.active_attack or g.parry.active_at(g.combat.tick) else set()
        if g.encounter.pulse:
            frozen.update(e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse.frozen(e))
        motion.update((g.player,*g.encounter.enemies),1/60,session=g.combat.combat_session_id,frozen=frozen)
        batch = g.encounter.ledger.presentation.drain()
        for animation in animations.values():
            animation.update(g,1/60,batch,motion=motion)
        vfx.update(g,1/60,batch,motion=motion)

    def player_cases():
        def stage(number):
            g = _new_stage_game(number)
            g.encounter.ledger.presentation = PresentationEvents()
            g.advance(0)
            sync(g)
            draw(g,after)
            return g

        for facing in ('up','down','left','right'):
            g = stage(1)
            controls = InputController(move_interval_ticks=18)
            def step(direction):
                assert controls.key_down(direction,g.player,occupied=g.encounter.occupied_cells,tick=g.combat.tick)
                controls.key_up(direction)
            if facing=='down':
                step('up')
                for _ in range(18):
                    g.advance()
                    sync(g)
            step(facing)
            sync(g)
            record(g,facing+'_ready',g.player)
            for n in range(18):
                g.advance()
                sync(g)
                if clips and n in (10,12,14,16):
                    clip_frame(g,'player_'+facing,g.player)
            g.combat.advance(1)
            attack = g.combat.request_attack(g.player)
            assert attack.facing==facing
            g.resolver.resolve_player_attack(attack)
            g.resolve_current_tick()
            sync(g)
            record(g,facing+'_start',g.player)
            if clips:
                clip_frame(g,'player_'+facing,g.player)
            for offset in range(1,33 if clips else 14):
                if offset==3:
                    step('right' if facing!='right' else 'up')
                g.advance()
                sync(g)
                tag = {3:'release_turned',7:'follow',11:'recovery'}.get(offset)
                if tag:
                    record(g,facing+'_'+tag,g.player)
                if facing=='up' and offset==3:
                    benchmark(g,'player_swing')
                if clips and offset%2==0:
                    clip_frame(g,'player_'+facing,g.player)
            assert g.player.facing!=attack.facing

        for number in (1,6,11,16,21):
            g = stage(number)
            light = is_light_tile(*player_aim(g).target)
            record(g,f'chapter_{g.chapter}_'+('light' if light else 'dark'),g.player)
            assert InputController().key_down('up',g.player,occupied=g.encounter.occupied_cells,tick=g.combat.tick)
            for _ in range(7):
                g.advance()
                sync(g)
            assert is_light_tile(*player_aim(g).target)!=light
            record(g,f'chapter_{g.chapter}_'+('dark' if light else 'light'),g.player)

        g = stage(24)
        while g.combat.tick<135:
            g.advance()
            sync(g)
        record(g,'stage24_overlap',g.player)
        benchmark(g,'stage24_crossing')

        for grade,issued in (('normal',369),('perfect',379),('unbound',1)):
            g = stage(25 if grade!='unbound' else 1)
            while g.combat.tick<issued-1:
                g.advance()
                sync(g)
            if grade=='perfect':
                record(g,'stage25_ready_ring',g.player)
                benchmark(g,'stage25_pulse_windup')
            g.combat.advance(1)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.resolve_current_tick()
            sync(g)
            while grade!='unbound' and g.combat.tick<385:
                g.advance()
                sync(g)
            assert g.resolver.last_parry_result.status==grade
            record(g,'parry_'+grade,g.player)
            if grade=='perfect':
                benchmark(g,'stage25_pulse_perfect')

    def scenario(name,stage,kind,attack_kind,direction,steps):
        g = _new_stage_game(stage)
        g.encounter.ledger.presentation = PresentationEvents()
        controls = InputController()
        targets = {e.entity_instance_id:e for e in g.encounter.enemies if e.kind==kind}
        actor = None
        clip_actor = None
        hit_tick = None
        seen = set()
        extra = {'travel','contact'} if kind in ('rook','knight') else set()
        expected = {'anticipation','release','follow','recovery'} | extra
        for _ in range(900):
            tick = g.combat.tick
            if direction and tick%18==0 and tick<18*steps:
                controls.key_down(direction,g.player,occupied=g.encounter.occupied_cells,tick=tick)
                controls.key_up(direction)
            if attack_kind=='king_pulse' and tick==368:
                # A genuine normal parry keeps this Pulse in release without stunning King.
                g.combat.advance(1)
                link = g.resolver.register_parry(g.parry.request(g.combat.tick))
                assert link.adjudication_grade=='normal'
                g.resolve_current_tick()
            else:
                g.advance()
            sync(g)
            if actor is None:
                event = next((e for e in g.resolver.live_telegraphs(g.combat.tick)
                              if e.source_entity_instance_id in targets and e.attack_kind==attack_kind
                              and e.hit_tick-g.combat.tick==5),None)
                if event is not None:
                    actor = targets[event.source_entity_instance_id]
                    record(g,name+'_anticipation',actor)
                    seen.add('anticipation')
            elif actor.active:
                pose = animations[after].pose(g,actor,motion)
                tag = None
                if pose.state is State.ATTACK:
                    if 'release' not in seen:
                        tag = 'release'
                    elif pose.attack_motion=='travel' and .4 <= pose.phase <= .7:
                        tag = 'travel'
                    elif pose.attack_motion=='arrival' and pose.phase < .16:
                        tag = 'contact'
                    elif pose.attack_motion!='travel' and .50 <= pose.phase < .70:
                        tag = 'follow'
                    elif pose.attack_motion!='travel' and .78 <= pose.phase < .96:
                        tag = 'recovery'
                if tag and tag not in seen:
                    record(g,name+'_'+tag,actor)
                    seen.add(tag)
            if clips:
                if clip_actor is None:
                    event = next((e for e in g.resolver.live_telegraphs(g.combat.tick)
                                  if e.source_entity_instance_id in targets and e.attack_kind==attack_kind
                                  and e.hit_tick-g.combat.tick==18),None)
                    if event:
                        clip_actor = targets[event.source_entity_instance_id]
                        hit_tick = event.hit_tick
                if clip_actor and g.combat.tick<=hit_tick+44 and (g.combat.tick-hit_tick)%2==0:
                    clip_frame(g,name,clip_actor)
            if stage==24 and g.combat.tick==135:
                assert len({f.key[2] for f in vfx.effects if f.name=='queen_fire'})==2
                benchmark(g,'stage24_crossing')
            if stage==25 and g.combat.tick==389:
                assert g.resolver.last_parry_result.status=='normal'
                benchmark(g,'stage25_pulse')
            if seen==expected and (not clips or (hit_tick is not None and g.combat.tick>=hit_tick+44)):
                break
        assert seen==expected,(name,seen,g.combat.tick)
        if clips:
            assert len(clip_frames[name])==32,name

    env = {k:v for k,v in os.environ.items() if not (k.startswith('CHECKMATE_') and k.endswith('_ART'))}
    env.update(SDL_VIDEODRIVER='windows' if driver=='direct3d11' else 'dummy',SDL_AUDIODRIVER='dummy')
    with patch.dict(os.environ,env,clear=True):
        if driver=='direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
            make = c.SDL_CreateRenderer
            with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:make(w,i,s.SDL_RENDERER_ACCELERATED)):
                open_preview(c,capture=True)
        else:
            open_preview(c,capture=True)
        try:
            info = s.SDL_RendererInfo()
            assert s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info))==0 and info.name.decode()==driver
            if player_combat:
                player_cases()
            else:
                for case in CASES:
                    scenario(*case)
        finally:
            art.close()
            c.close_canvas()
            c.renderer=c.window=None
    if output:
        result = dict(driver=driver,frames=scenes,performance_ms=performance,clip_ticks=clip_frames)
        (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return dict(frames=len(scenes),performance_ms=performance)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--renderer',choices=('direct3d11','software'),default='direct3d11')
    parser.add_argument('--player-combat',action='store_true')
    parser.add_argument('--articulation',action='store_true')
    parser.add_argument('--clips',action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.output,args.renderer,player_combat=args.player_combat,
                         articulation=args.articulation,clips=args.clips),indent=2))
