"""Hidden native real Stage12/13 resource/ledger audit, not human GUI or FPS."""
import argparse
from contextlib import ExitStack
import ctypes
import json
import os
from pathlib import Path
import pickle
import sys
from time import perf_counter
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from arena_art_common import ArenaArtError
from game import StageGame
from render_motion import RenderMotion
from stage13_art_renderer import LiveArenaArtPath,Stage13ArtRenderer
from tests.test_hp_carryover import fight
from tools.stage12_play import session as twelve
from tools.stage13_play import session as thirteen
from queen_behavior import queen_ray_targets
from tools.stage5_art_preview import open_preview


def run(driver):
    from pico2d import pico2d as c
    import sdl2 as s
    import main
    start=perf_counter();live=set();count=dict(loads=0,destroys=0,peak=0,frames=0)
    path=None;motion=RenderMotion();origins=set();kinds=set();texture_keys=[]
    env={f'CHECKMATE_STAGE{n}_ART':'1' for n in (11,12,13)}
    env.update(SDL_VIDEODRIVER='windows' if driver=='direct3d11' else 'dummy',SDL_AUDIODRIVER='dummy')
    with patch.dict(os.environ,env),ExitStack() as stack:
        try:
            if driver=='direct3d11':
                s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11');create=c.SDL_CreateRenderer
                with patch.object(c,'SDL_CreateRenderer',lambda w,i,flags:create(w,i,s.SDL_RENDERER_ACCELERATED)):
                    open_preview(c,capture=True)
            else:open_preview(c,capture=True)
            if not c.window or not c.renderer:raise RuntimeError('Hidden SDL renderer unavailable')
            info=s.SDL_RendererInfo();assert s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info))==0
            assert info.name.decode()==driver
            load,destroy=c.load_image,c.SDL_DestroyTexture
            def loading(p):
                image=load(p);key=ctypes.cast(image.texture,ctypes.c_void_p).value
                assert key and key not in live;live.add(key);count['loads']+=1;count['peak']=max(count['peak'],len(live));return image
            def destroying(texture):
                key=ctypes.cast(texture,ctypes.c_void_p).value
                if key:assert key in live;live.remove(key);count['destroys']+=1
                return destroy(texture)
            stack.enter_context(patch.object(c,'load_image',loading));stack.enter_context(patch.object(c,'SDL_DestroyTexture',destroying))
            path=LiveArenaArtPath(c,motion=motion)
            def draw(g,elapsed=1/60):
                nonlocal texture_keys
                frozen=(g.player.entity_instance_id,) if g.combat.active_attack or g.parry.active_at(g.combat.tick) else ()
                motion.update((g.player,*g.encounter.enemies),elapsed,session=g.combat.combat_session_id,frozen=frozen)
                before=pickle.dumps((g,motion));active=path.draw(g,motion.positions)
                assert pickle.dumps((g,motion))==before and active==(g.stage_number in (11,12,13))
                if active:
                    r=path.stage13.renderer if g.stage_number==13 else path.previous.stage12.renderer if g.stage_number==12 else path.previous.previous.stage11.renderer
                    assert r.warning_cells==([tuple(cell) for e in g.encounter.ledger.telegraphs for cell in e.target_cells] if g.playing else [])
                    assert len(live)==8
                    if g.stage_number==13:
                        texture_keys=sorted(r.images)
                        for event in g.encounter.ledger.telegraphs:
                            e=next(e for e in g.encounter.enemies if e.entity_instance_id==event.source_entity_instance_id)
                            kinds.add(e.kind)
                            if e.kind=='queen':
                                origins.add(e.position);assert event.target_cells==queen_ray_targets(e.position)
                else:
                    assert not live;main.BoardRenderer(chapter=g.chapter).draw(c)
                c.update_canvas();count['frames']+=1
            g,flow=twelve();draw(g,0);original=StageGame.resolve_current_tick
            def observe(game):
                result=original(game)
                if game is g:draw(game)
                return result
            with patch.object(StageGame,'resolve_current_tick',observe):
                result12=fight(flow);assert result12==(12,'UPGRADE',669,3,4)
                g,_=flow.choose(flow.sync_offer(),'attack',main._new_stage_game);draw(g,0)
                assert (count['loads'],count['destroys'])==(16,8)
                result13=fight(flow);assert result13==(13,'UPGRADE',543,3,4)
            assert kinds=={'queen','knight'} and len(origins)>1
            g,_=flow.choose(flow.sync_offer(),'hp',main._new_stage_game);draw(g,0)
            assert (g.stage_number,g.player.health.current_hp,g.player.health.max_hp,len(flow.run.receipts))==(14,4,5,3) and not live
            # Normal restart before any failure injection must also stay below nine textures.
            g,flow=thirteen();draw(g,0)
            while g.playing:g.advance();draw(g)
            assert (g.state.value,g.end_tick)==('GAME_OVER',374)
            g,_=flow.restart(main._new_stage_game);draw(g,0)
            assert g.stage_number==11 and count['peak']==8
            results=[]
            for delta,status in ((18,'normal'),(7,'perfect')):
                g,flow=thirteen();draw(g,0)
                while g.combat.tick<121-delta:g.advance();draw(g)
                event=g.encounter.enemies[0].current_attack;g.resolver.register_parry(g.parry.request(g.combat.tick))
                draw(g)
                while g.combat.tick<121:g.advance();draw(g)
                assert (g.resolver.last_parry_result.status,g.resolver.last_parry_result.enemy_event_key)==(status,event.key)
                assert g.player.health.current_hp==3;results.append(status)
            g,flow=thirteen();draw(g,0)
            while g.playing:g.advance();draw(g)
            assert (g.state.value,g.end_tick)==('GAME_OVER',374)
            before=pickle.dumps((g,flow.run))
            with patch.object(Stage13ArtRenderer,'draw',side_effect=ArenaArtError('intentional Stage13 QA fallback')):
                assert not path.draw(g,motion.positions)
            assert pickle.dumps((g,flow.run))==before and not live and path.stage13.failed
            main.BoardRenderer(chapter=3).draw(c);c.update_canvas()
            g,_=flow.restart(main._new_stage_game);draw(g,0)
            assert (g.stage_number,len(flow.run.receipts),g.player.health.current_hp)==(11,0,3)
            path.close();path.close();assert not live and count['loads']==count['destroys']==64 and count['peak']==8
            return dict(scope='Actual hidden native Stage12->13->14, Stage13 normal/perfect parry and death/restart; not human GUI/performance',
                        renderer=driver,vsync=bool(info.flags&s.SDL_RENDERER_PRESENTVSYNC),stage12=result12,stage13=result13,
                        stage14=dict(hp=4,max_hp=5,receipts=3,legacy_display=True),queen_real_origins=sorted(origins),parries=results,
                        stage13_texture_keys=texture_keys,resources=count,no_input_death_tick=374,restart_stage=11,
                        expected_failure_legacy_draw=True,elapsed_seconds=round(perf_counter()-start,3),
                        human_stage13_gui='pending',windows_fps_p95_p99='unmeasured',long_term_ram_vram='unmeasured')
        finally:
            if path is not None:path.close()
            if c.window:c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renderer',choices=('software','direct3d11'),default='software');p.add_argument('--output',type=Path)
    args=p.parse_args();result=run(args.renderer)
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
