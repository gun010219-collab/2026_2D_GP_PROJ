"""Hidden native Stage11 audit; technical rendering, not human GUI or FPS."""
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

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from arena_art_common import ArenaArtError
from game import StageGame
from render_motion import RenderMotion
from stage11_art_renderer import LiveArenaArtPath, Stage11ArtRenderer
from tests.test_hp_carryover import fight
from tools.stage11_play import session
from tools.stage5_art_preview import open_preview


def run(driver):
    from pico2d import pico2d as c
    import sdl2 as s
    import main
    started = perf_counter(); live = set(); count = dict(loads=0,destroys=0,peak=0,frames=0)
    motion = RenderMotion(); path = None; warning_kinds = set(); peak_lift = 0
    env = {'CHECKMATE_STAGE11_ART':'1','SDL_AUDIODRIVER':'dummy',
           'SDL_VIDEODRIVER':'windows' if driver == 'direct3d11' else 'dummy'}
    with patch.dict(os.environ,env), ExitStack() as stack:
        try:
            if driver == 'direct3d11':
                s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
                create = c.SDL_CreateRenderer
                with patch.object(c,'SDL_CreateRenderer',lambda w,i,flags:create(w,i,s.SDL_RENDERER_ACCELERATED)):
                    open_preview(c,capture=True)
            else: open_preview(c,capture=True)
            if not c.window or not c.renderer: raise RuntimeError('Native hidden window/renderer unavailable')
            info = s.SDL_RendererInfo()
            assert s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info)) == 0
            assert info.name.decode() == driver
            load,destroy = c.load_image,c.SDL_DestroyTexture
            def loading(name):
                image = load(name); key = ctypes.cast(image.texture,ctypes.c_void_p).value
                assert key and key not in live
                live.add(key); count['loads'] += 1; count['peak'] = max(count['peak'],len(live))
                return image
            def destroying(texture):
                key = ctypes.cast(texture,ctypes.c_void_p).value
                if key:
                    assert key in live; live.remove(key); count['destroys'] += 1
                return destroy(texture)
            stack.enter_context(patch.object(c,'load_image',loading))
            stack.enter_context(patch.object(c,'SDL_DestroyTexture',destroying))
            path = LiveArenaArtPath(c,motion=motion)

            def draw(g,elapsed=1/60):
                nonlocal peak_lift
                frozen = (g.player.entity_instance_id,) if g.combat.active_attack or g.parry.active_at(g.combat.tick) else ()
                motion.update((g.player,*g.encounter.enemies),elapsed,session=g.combat.combat_session_id,frozen=frozen)
                before = pickle.dumps((g,motion)); active = path.draw(g,motion.positions)
                assert pickle.dumps((g,motion)) == before
                assert active == (g.stage_number == 11)
                if active:
                    r = path.stage11.renderer
                    expected = [tuple(cell) for e in g.encounter.ledger.telegraphs for cell in e.target_cells] if g.playing else []
                    assert r.warning_cells == expected
                    for e in g.encounter.ledger.telegraphs:
                        warning_kinds.add(next(a.kind for a in g.encounter.enemies if a.entity_instance_id == e.source_entity_instance_id))
                    peak_lift = max(peak_lift,*(motion.ground_pose(e)[1] for e in g.encounter.enemies))
                else:
                    assert not live
                    main.BoardRenderer(chapter=g.chapter).draw(c)
                c.update_canvas(); count['frames'] += 1

            g,flow = session(); draw(g,0); resolve = StageGame.resolve_current_tick
            def observe(game):
                result = resolve(game)
                if game is g: draw(game)
                return result
            with patch.object(StageGame,'resolve_current_tick',observe): result = fight(flow)
            assert result == (11,'UPGRADE',669,2,3)
            assert warning_kinds == {'rook','knight','pawn'}
            g,_ = flow.choose(flow.sync_offer(),'hp',main._new_stage_game); draw(g,0)
            assert (g.stage_number,g.player.health.current_hp,len(flow.run.receipts)) == (12,3,1)
            assert count['loads'] == count['destroys'] == 8
            g,flow = session(); draw(g,0)
            while g.playing:
                g.advance(); draw(g)
            assert (g.state.value,g.combat.tick) == ('GAME_OVER',435)
            g,_ = flow.restart(main._new_stage_game); draw(g,0)
            assert (count['loads'],count['destroys'],len(live)) == (24,16,8)
            # Deliberate expected SDL failure: verify native legacy BoardRenderer actually draws.
            before = pickle.dumps(g)
            with patch.object(Stage11ArtRenderer,'draw',side_effect=ArenaArtError('intentional QA fallback')):
                assert not path.draw(g,motion.positions)
            assert pickle.dumps(g) == before and not live
            main.BoardRenderer(chapter=g.chapter).draw(c); c.update_canvas()
            assert path.stage11.failed
            path.close(); path.close()
            assert not live and count['loads'] == count['destroys'] == 24
            return dict(scope='Hidden native real Stage11, not human GUI or realtime performance',
                        renderer=driver,vsync=bool(info.flags&s.SDL_RENDERER_PRESENTVSYNC),
                        result=result,warning_kinds=sorted(warning_kinds),max_knight_lift=peak_lift,
                        resources=count,stage12=dict(hp=3,max_hp=4,receipt=1,legacy_draw=True),
                        no_input_game_over_tick=435,restart_stage=11,expected_draw_failure_legacy=True,
                        elapsed_seconds=round(perf_counter()-started,3),
                        human_gui='pending',windows_fps_p95_p99='unmeasured',long_term_ram_vram='unmeasured')
        finally:
            if path is not None: path.close()
            if c.window: c.close_canvas(); c.window = c.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer',choices=('software','direct3d11'),default='software')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args(); report = run(args.renderer)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
