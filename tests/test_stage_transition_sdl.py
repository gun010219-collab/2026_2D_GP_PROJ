"""Actual SDL dummy window/event/drawing path; never a Windows GUI playtest."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class StageTransitionSDLTests(unittest.TestCase):
    def test_real_sdl_n_transition_mixed_combat_and_stage_two_overlay_draws(self):
        script = textwrap.dedent('''
            import ctypes
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from chapter_run import ChapterRun
            run=ChapterRun()
            for number in range(1,1):
                run.select(run.offer_after_clear(number,f"prior-{number}"),("move","move","attack")[number-1])
            from config import FIXED_TIME_STEP
            from game_renderer import GameFlowRenderer

            now, opened, closed, frames = [0.0], [], [], [0]
            loop_started = [False]
            stages, warnings = [], []
            one_factory, stage_factory = main._new_game, main._new_stage_game
            real_poll, real_present = canvas.get_events, canvas.update_canvas
            warning_draw = main.EnemyAttackRenderer.draw

            def open_window(width, height):
                assert s.SDL_Init(s.SDL_INIT_VIDEO) == 0
                assert canvas.TTF_Init() == 0
                canvas.window = s.SDL_CreateWindow(b'CHECKMATE test', 0, 0, width, height,
                                                  s.SDL_WINDOW_HIDDEN)
                canvas.renderer = s.SDL_CreateRenderer(canvas.window, -1, s.SDL_RENDERER_SOFTWARE)
                assert canvas.window and canvas.renderer
                canvas.canvas_width, canvas.canvas_height = width, height
                opened.append((width, height))

            def close_window():
                s.SDL_DestroyRenderer(canvas.renderer)
                s.SDL_DestroyWindow(canvas.window)
                canvas.TTF_Quit()
                s.SDL_Quit()
                closed.append(True)

            def cleared_one():
                game = one_factory()
                for enemy in game.encounter.enemies:
                    enemy.health.apply_damage(enemy.health.max_hp, tick=0)
                    game.encounter.deactivate(enemy.entity_instance_id)
                game.update_state()
                return game

            def create(number, **kwargs):
                game = stage_factory(number, **kwargs)
                stages.append(game)
                return game

            def push(kind, key=None):
                event = s.SDL_Event()
                event.type = kind
                if key is not None:
                    event.key.windowID = s.SDL_GetWindowID(canvas.window)
                    event.key.keysym.sym = key
                    event.key.repeat = 0
                assert s.SDL_PushEvent(ctypes.byref(event)) == 1

            def poll():
                loop_started[0] = True
                s.SDL_FlushEvents(s.SDL_FIRSTEVENT, s.SDL_LASTEVENT)
                if frames[0] == 0:
                    push(s.SDL_KEYDOWN, s.SDLK_1)
                    push(s.SDL_KEYUP, s.SDLK_1)
                elif frames[0] == 23:
                    push(s.SDL_QUIT)
                return real_poll()

            def present():
                # Pico2D hide_lattice() presents once during bootstrap, before
                # the loop's initial perf_counter. It is not a gameplay frame.
                if not loop_started[0]:
                    real_present()
                    return
                if frames[0] == 22:
                    # Also exercise the new stage-specific terminal glyphs with
                    # the installed Pico2D renderer, within the same SDL window.
                    for cleared in (False, True):
                        game = stage_factory(2)
                        if cleared:
                            for enemy in game.encounter.enemies:
                                enemy.health.apply_damage(enemy.health.max_hp, tick=0)
                        else:
                            game.player.health.apply_damage(3, tick=0)
                        game.update_state()
                        GameFlowRenderer().draw(canvas, game)
                real_present()
                frames[0] += 1
                now[0] += 8 * FIXED_TIME_STEP

            def draw_warning(renderer, target_canvas, ledger):
                warnings.extend(event.target_cells for event in ledger.telegraphs)
                warning_draw(renderer, target_canvas, ledger)

            with patch.object(canvas, 'open_canvas', side_effect=open_window), \
                 patch.object(canvas, 'close_canvas', side_effect=close_window), \
                 patch.object(canvas, 'get_events', side_effect=poll), \
                 patch.object(canvas, 'update_canvas', side_effect=present), \
                 patch.object(canvas, 'SDL_GetWindowFlags', return_value=s.SDL_WINDOW_INPUT_FOCUS), \
                 patch.object(main, '_new_game', side_effect=cleared_one), \
                 patch.object(main, '_new_stage_game', side_effect=create), \
                 patch.object(main.EnemyAttackRenderer, 'draw', draw_warning), \
                 patch.object(main, 'perf_counter', side_effect=lambda: now[0]), \
                 patch.object(main, 'sleep'):
                main.main(run=run)
            assert opened == [(1440,900)] and len(closed) == 1
            assert len(stages) == 1 and stages[0].stage_number == 2, (len(stages), frames)
            game = stages[0]
            assert [e.kind for e in game.encounter.enemies] == ['rook','pawn','pawn']
            assert [e.health.current_hp for e in game.encounter.enemies] == [4,2,2]
            assert ((3,1),(4,1),(5,1)) in warnings
            assert game.player.health.current_hp == 2
            assert game.player.health.last_damage_tick == 168
            assert game.encounter.enemies[0].position == (4,1)
            print('PASS: native SDL events, N transition, mixed combat, warning and stage overlays')
        ''')
        result = subprocess.run([sys.executable, '-c', script],
                                cwd=Path(__file__).resolve().parents[1],
                                env={**os.environ, 'SDL_VIDEODRIVER': 'dummy'},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
