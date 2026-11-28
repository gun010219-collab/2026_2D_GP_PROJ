"""Play and capture time-separated poses with real combat on a hidden SDL canvas."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import pickle
import sys
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from actor_animation import ActorAnimation, State
from arena_art_common import ArenaArtError
from chapter_art_renderer import LiveArenaArtPath
from game import StageGame
from game_renderer import GameFlowRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from tests.test_hp_carryover import fight
from tools.chapter_art_play import session
from tools.stage5_art_preview import capture_png, open_preview


def run(driver, output=None):
    import sdl2 as s
    from pico2d import pico2d as c

    options = {k:v for k,v in os.environ.items() if not (k.startswith('CHECKMATE_') and k.endswith('_ART'))}
    options.update(SDL_VIDEODRIVER='windows' if driver == 'direct3d11' else 'dummy', SDL_AUDIODRIVER='dummy')
    clock, motion = ActorAnimation(), RenderMotion()
    art = LiveArenaArtPath(c, motion=motion, default_enabled=True, animation=clock)
    hud = GameFlowRenderer()
    frames, states, live, measured = [], set(), set(), []
    counts = dict(loads=0, frees=0, peak=0, frames=0)
    if output:
        output.mkdir(parents=True)

    def sync(g, queue, elapsed=1/60, *, paused=False):
        freeze = {g.player.entity_instance_id} if g.combat.active_attack or g.parry.active_at(g.combat.tick) else set()
        if g.encounter.pulse:
            freeze.update(e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse.frozen(e))
        motion.update((g.player,*g.encounter.enemies), elapsed, session=g.combat.combat_session_id, frozen=freeze)
        clock.update(g, elapsed, queue.drain(), paused=paused)

    def draw(g, name=None, *, expect_animation=True):
        before = pickle.dumps((g,motion))
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        start = perf_counter()
        assert art.draw(g,motion.positions)
        measured.append(perf_counter()-start)
        renderer = art.path.renderer
        assert renderer.animation_failed != expect_animation
        armor_mesh = art.player_armor.appearance is not None
        assert len(live) == len(renderer.images) + armor_mesh
        assert before == pickle.dumps((g,motion))
        assert renderer.warning_cells == ([cell for event in g.encounter.ledger.telegraphs
                                           for cell in event.target_cells] if g.playing else [])
        ids = {e.entity_instance_id:e.data_id for e in g.encounter.enemies}
        ids[g.player.entity_instance_id] = 'player'
        poses = {ids[key]:p['animation'] for key,p in renderer.actor_layouts.items() if 'animation' in p}
        corpse_ids = {sprite.entity_instance_id for sprite in clock.deaths}
        assert not corpse_ids.intersection(renderer.order)
        assert bool(poses) or not expect_animation
        states.update(poses.values())
        hud.draw_stage_label(c,g)
        hud.draw(c,g)
        if output and name:
            path = output/(name+'.png')
            capture_png(c,path)
            frames.append(dict(file=path.name, stage=g.stage_number, tick=g.combat.tick,
                               visual_time=round(clock.time,6), poses=poses,
                               sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        counts['frames'] += 1
        return renderer

    def texture_state(texture):
        red, green, blue, alpha = (ctypes.c_uint8() for _ in range(4))
        blend = ctypes.c_int()
        assert s.SDL_GetTextureColorMod(texture, ctypes.byref(red), ctypes.byref(green), ctypes.byref(blue)) == 0
        assert s.SDL_GetTextureAlphaMod(texture, ctypes.byref(alpha)) == 0
        assert s.SDL_GetTextureBlendMode(texture, ctypes.byref(blend)) == 0
        return tuple(v.value for v in (red,green,blue,alpha,blend))

    with patch.dict(os.environ,options,clear=True):
        try:
            if driver == 'direct3d11':
                s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
                create=c.SDL_CreateRenderer
                with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:create(w,i,s.SDL_RENDERER_ACCELERATED)):
                    open_preview(c,capture=True)
            else:
                open_preview(c,capture=True)
            info=s.SDL_RendererInfo()
            assert c.renderer and s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info)) == 0
            assert info.name.decode() == driver
            load, destroy = c.load_image, c.SDL_DestroyTexture

            def loading(path):
                image=load(path)
                handle=ctypes.cast(image.texture,ctypes.c_void_p).value
                assert handle and handle not in live
                live.add(handle)
                counts['loads']+=1
                counts['peak']=max(counts['peak'],len(live))
                return image

            def releasing(texture):
                if texture:
                    live.remove(ctypes.cast(texture,ctypes.c_void_p).value)
                    counts['frees']+=1
                return destroy(texture)

            with patch.object(c,'load_image',loading),patch.object(c,'SDL_DestroyTexture',releasing):
                try:
                    # The same actor IDs and textures live through multiple idle samples.
                    for stage in range(1,26):
                        g=_new_stage_game(stage)
                        q=g.encounter.ledger.presentation=PresentationEvents()
                        sync(g,q,0)
                        renderer = draw(g, 'idle_25_a' if stage==25 else None)
                        if stage==25:
                            texture=renderer.images['king'].texture
                            texture_before=texture_state(texture)
                            loads_before=counts['loads']
                            start=clock.time
                            sync(g,q,.10,paused=True)
                            assert clock.time == start
                            for step in range(1,3):
                                for _ in range(36):
                                    sync(g,q,1/180)
                                draw(g,f'idle_25_{step}')
                            assert texture_state(texture)==texture_before and counts['loads']==loads_before
                    g,flow=session(3)
                    q=flow.enable_presentation()
                    sync(g,q,0)
                    found=False
                    knight=g.encounter.enemies[0]
                    for _ in range(106):
                        g.advance()
                        sync(g,q)
                        if not found and motion.ground_pose(knight)[1] > 17.9:
                            r=draw(g,'knight_peak')
                            assert r.actor_layouts[knight.entity_instance_id]['animation'] in ('move','attack')
                            assert abs(r.actor_layouts[knight.entity_instance_id]['elevation']-18)<.1
                            found=True
                    assert found
                    g,flow=session(1)
                    q=flow.enable_presentation()
                    sync(g,q,0)
                    assert g.player.move('up',occupied=g.encounter.occupied_cells)
                    sync(g,q,1/60)
                    draw(g,'player_move')

                    for delta,label in ((18,'normal'),(7,'perfect')):
                        g=_new_stage_game(25)
                        q=g.encounter.ledger.presentation=PresentationEvents()
                        sync(g,q,0)
                        attempt=g.parry.request(0)
                        g.resolver.register_parry(attempt)
                        sync(g,q)
                        draw(g,'parry_failed' if delta==18 else None)
                        for _ in range(385-delta):
                            g.advance()
                            sync(g,q)
                            if g.combat.tick==340 and delta==7:
                                draw(g,'king_pulse_windup')
                        pulse=g.encounter.pulse.event
                        g.resolver.register_parry(g.parry.request(g.combat.tick))
                        sync(g,q,0)
                        assert clock.pose(g,g.player,motion).state is State.PARRY_READY
                        if delta==7:
                            draw(g,'parry_ready')
                        g.advance(delta)
                        sync(g,q,0)
                        assert g.resolver.last_parry_result.status==label
                        assert g.resolver.last_parry_result.enemy_event_key==pulse.key
                        draw(g,'parry_'+label)

                    g,flow=session(25)
                    q=flow.enable_presentation()
                    sync(g,q,0)
                    original=StageGame.resolve_current_tick
                    caught=set()
                    king_death_tick=None

                    def observe(active):
                        nonlocal king_death_tick
                        result=original(active)
                        sync(active,q)
                        for entity in (active.player,*active.encounter.enemies):
                            pose=clock.pose(active,entity,motion)
                            if pose.state in (State.ATTACK,State.HIT,State.STUN) and pose.state not in caught:
                                caught.add(pose.state)
                                draw(active,pose.state.value)
                        if clock.deaths and State.DEATH not in caught:
                            caught.add(State.DEATH)
                            draw(active,'first_death')
                        if any(actor.kind=='king' for actor in clock.deaths):
                            if king_death_tick is None:
                                king_death_tick=active.combat.tick
                                draw(active,'king_death')
                            elif active.combat.tick==king_death_tick+28:
                                caught.add('king_fall')
                                draw(active,'king_death_b')
                        return result

                    with patch.object(StageGame,'resolve_current_tick',observe):
                        result=fight(flow)
                    assert result[1]=='BOSS_CLEAR'
                    assert clock.deaths
                    draw(g,'terminal_death_a')
                    for _ in range(9):
                        sync(g,q,1/60)
                    draw(g,'terminal_death_b')
                    assert 'king_fall' in caught
                    g,_=flow.restart(_new_stage_game)
                    sync(g,q,0)
                    assert not clock.deaths and clock.time==0
                    with patch('actor_mesh.draw_actor',side_effect=ArenaArtError('intentional mesh failure')) as failed:
                        draw(g,expect_animation=False)
                        draw(g,expect_animation=False)
                        assert failed.call_count==1
                finally:
                    art.close()
            assert not live and counts['loads']==counts['frees']
        finally:
            if c.window:
                c.close_canvas()
                c.window=c.renderer=None
    assert states=={state.value for state in State}, states
    manifest=dict(driver=driver,counts=counts,states=sorted(states),captures=frames)
    if output:
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return {**manifest,'hidden_art_mean_ms':round(sum(measured)*1000/len(measured),3)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer',choices=('software','direct3d11'),default='software')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.renderer,args.output),indent=2))
