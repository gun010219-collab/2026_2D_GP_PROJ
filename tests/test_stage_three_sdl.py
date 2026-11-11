"""Native SDL events and Pico2D drawing through main; not user GUI evidence."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class StageThreeSDLTests(unittest.TestCase):
    def test_native_sdl_one_two_three_knight_warning_perfect_and_terminal_overlays(self):
        script = textwrap.dedent('''
            import ctypes
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from config import FIXED_TIME_STEP
            from game_renderer import GameFlowRenderer

            now, frames, active = [0.0], [0], [False]
            stages, warnings, labels, kinds, opened, closed = [], [], [], [], [], []
            one_factory, stage_factory = main._new_game, main._new_stage_game
            real_poll, real_present = canvas.get_events, canvas.update_canvas
            warning_draw, enemy_draw = main.EnemyAttackRenderer.draw, main.EnemyRenderer.draw
            real_text = main.HealthRenderer._text

            def open_window(width, height):
                assert s.SDL_Init(s.SDL_INIT_VIDEO) == 0
                assert canvas.TTF_Init() == 0
                canvas.window = s.SDL_CreateWindow(b'CHECKMATE Stage 3 test',0,0,width,height,s.SDL_WINDOW_HIDDEN)
                canvas.renderer = s.SDL_CreateRenderer(canvas.window,-1,s.SDL_RENDERER_SOFTWARE)
                assert canvas.window and canvas.renderer
                canvas.canvas_width, canvas.canvas_height = width,height
                opened.append((width,height))

            def close_window():
                s.SDL_DestroyRenderer(canvas.renderer)
                s.SDL_DestroyWindow(canvas.window)
                canvas.TTF_Quit()
                s.SDL_Quit()
                closed.append(True)

            def clear(game):
                for enemy in game.encounter.enemies:
                    enemy.health.apply_damage(enemy.health.current_hp,tick=game.combat.tick)
                    game.encounter.deactivate(enemy.entity_instance_id)
                game.update_state()

            def create_one():
                game = one_factory()
                clear(game)
                stages.append(game)
                return game

            def create(number):
                game = stage_factory(number)
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
                active[0] = True
                s.SDL_FlushEvents(s.SDL_FIRSTEVENT,s.SDL_LASTEVENT)
                if frames[0] in (0,1):
                    push(s.SDL_KEYUP,s.SDLK_n)
                    push(s.SDL_KEYDOWN,s.SDLK_n)
                elif frames[0] == 38:
                    push(s.SDL_KEYDOWN,s.SDLK_LSHIFT)
                elif frames[0] == 40:
                    push(s.SDL_QUIT)
                return real_poll()

            def present():
                if not active[0]:
                    real_present()
                    return
                if frames[0] == 0:
                    assert stages[-1].stage_number == 2
                    clear(stages[-1])
                    GameFlowRenderer().draw(canvas,stages[-1])
                if frames[0] == 1:
                    game = stages[-1]
                    assert game.stage_number == 3 and game.combat.tick == 0
                    assert [e.kind for e in game.encounter.enemies] == ['knight','pawn','pawn']
                    assert [e.position for e in game.encounter.enemies] == [(3,6),(1,6),(8,6)]
                    assert [e.health.current_hp for e in game.encounter.enemies] == [3,2,2]
                if frames[0] == 39:
                    game = stages[-1]
                    assert game.combat.tick == 300
                    assert game.player.health.current_hp == 3
                    assert game.resolver.last_parry_result.status == 'perfect'
                    assert game.combat.pending_attack_bonus == 2
                    assert game.encounter.enemies[0].state == 'stunned'
                    assert game.encounter.enemies[0].position == (6,3)
                    for cleared in (False,True):
                        terminal = stage_factory(3)
                        if cleared:
                            clear(terminal)
                        else:
                            terminal.player.health.apply_damage(3,tick=0)
                            terminal.update_state()
                        GameFlowRenderer().draw(canvas,terminal)
                real_present()
                now[0] += (5 if frames[0] == 37 else 7 if frames[0] == 38 else 8) * FIXED_TIME_STEP
                frames[0] += 1

            def warning(renderer,target_canvas,ledger):
                if stages[-1].stage_number == 3:
                    warnings.extend(e.target_cells for e in ledger.telegraphs)
                warning_draw(renderer,target_canvas,ledger)

            def enemies(renderer,target_canvas,items):
                kinds.append(tuple(e.kind for e in items if e.active))
                enemy_draw(renderer,target_canvas,items)

            def text(target_canvas,value,*args,**kwargs):
                labels.append(value)
                real_text(target_canvas,value,*args,**kwargs)

            with patch.object(canvas,'open_canvas',side_effect=open_window), \
                 patch.object(canvas,'close_canvas',side_effect=close_window), \
                 patch.object(canvas,'get_events',side_effect=poll), \
                 patch.object(canvas,'update_canvas',side_effect=present), \
                 patch.object(canvas,'SDL_GetWindowFlags',return_value=s.SDL_WINDOW_INPUT_FOCUS), \
                 patch.object(main,'_new_game',side_effect=create_one), \
                 patch.object(main,'_new_stage_game',side_effect=create), \
                 patch.object(main.EnemyAttackRenderer,'draw',warning), \
                 patch.object(main.EnemyRenderer,'draw',enemies), \
                 patch.object(main.HealthRenderer,'_text',side_effect=text), \
                 patch.object(main,'perf_counter',side_effect=lambda:now[0]), \
                 patch.object(main,'sleep'):
                main.main()
            assert opened == [(1440,900)] and closed == [True]
            assert [g.stage_number for g in stages] == [1,2,3]
            assert ('knight','pawn','pawn') in kinds
            assert ((5,5),) in warnings and ((5,1),) in warnings
            assert all(len(cells) == 1 for cells in warnings)
            assert 'STAGE 3' in labels and '3/3' in labels and '2/2' in labels
            assert 'STAGE CLEAR' in labels and 'GAME OVER' in labels
            assert 'N TO CONTINUE' in labels and 'R TO STAGE 1' in labels
            print('PASS: native SDL N events, Stage 3 main combat/drawing and perfect parry')
        ''')
        result = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[1],
                                env={**os.environ, 'SDL_VIDEODRIVER': 'dummy'},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
