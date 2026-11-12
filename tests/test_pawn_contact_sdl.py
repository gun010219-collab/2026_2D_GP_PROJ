"""Real main + native SDL dummy; controlled spawn, real contact/HP/parry/input."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class PawnContactSDLTests(unittest.TestCase):
    def native_contact(self, mode):
        script = textwrap.dedent('''
            import ctypes
            import sys
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from config import FIXED_TIME_STEP
            from game import GameState
            from tests.test_pawn_contact import session

            mode = sys.argv[1]
            games, closed, events_seen = [], [], []
            now, frame, started = [0.0], [0], [False]
            flags, done, restarted = [s.SDL_WINDOW_INPUT_FOCUS], [False], [False]
            pauses = {}
            factory_real = main._new_game
            poll_real, present_real = canvas.get_events, canvas.update_canvas

            def create(**kwargs):
                # Explicit adjacent spawn fixture. No pre-resolved damage or attacks.
                g = session() if not games else factory_real(**kwargs)
                games.append(g)
                return g

            def open_window(w, h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO) == 0
                assert canvas.TTF_Init() == 0
                canvas.window = s.SDL_CreateWindow(b'CHECKMATE contact test', 0, 0, w, h, s.SDL_WINDOW_HIDDEN)
                canvas.renderer = s.SDL_CreateRenderer(canvas.window, -1, s.SDL_RENDERER_SOFTWARE)
                assert canvas.window and canvas.renderer
                canvas.canvas_width, canvas.canvas_height = w, h

            def close_window():
                s.SDL_DestroyRenderer(canvas.renderer)
                s.SDL_DestroyWindow(canvas.window)
                canvas.TTF_Quit()
                s.SDL_Quit()
                closed.append(True)

            def push(kind, key=None, x=0, y=0):
                e = s.SDL_Event()
                e.type = kind
                if key is not None:
                    e.key.keysym.sym = key
                if kind in (s.SDL_MOUSEBUTTONDOWN, s.SDL_MOUSEBUTTONUP):
                    e.button.button = s.SDL_BUTTON_LEFT
                    e.button.x, e.button.y = x, y
                assert s.SDL_PushEvent(ctypes.byref(e)) == 1

            def tap(key):
                push(s.SDL_KEYDOWN, key)
                push(s.SDL_KEYUP, key)

            def poll():
                started[0] = True
                s.SDL_FlushEvents(s.SDL_FIRSTEVENT, s.SDL_LASTEVENT)
                f, g = frame[0], games[-1]
                flags[0] = 0 if f in (7, 8) else s.SDL_WINDOW_INPUT_FOCUS
                if done[0]:
                    if mode in ('normal', 'evade'):
                        tap(s.SDLK_ESCAPE)
                    else:
                        push(s.SDL_QUIT)
                elif f == 2:
                    push(s.SDL_MOUSEBUTTONDOWN, x=1295, y=41)
                    push(s.SDL_MOUSEBUTTONUP, x=1295, y=41)
                elif f == 5:
                    tap(s.SDLK_ESCAPE)
                elif f == 6:
                    tap(s.SDLK_F11)
                elif mode == 'hit' and g.state is GameState.GAME_OVER and not restarted[0]:
                    tap(s.SDLK_r)
                    restarted[0] = True
                elif mode == 'evade' and g.combat.tick == 19:
                    tap(s.SDLK_UP)
                elif mode == 'normal' and g.combat.tick == 20:
                    tap(s.SDLK_LSHIFT)
                elif mode == 'perfect' and g.combat.tick == 31:
                    tap(s.SDLK_LSHIFT)
                elif mode == 'perfect' and g.combat.tick == 39:
                    tap(s.SDLK_LEFT)  # Occupied move turns without overlap.
                    tap(s.SDLK_SPACE)
                return poll_real()

            def present():
                if not started[0]:
                    present_real()
                    return
                f, g = frame[0], games[-1]
                if len(games) == 1:
                    if f == 0:
                        event, = g.encounter.ledger.telegraphs
                        events_seen.append(event)
                        assert event.attack_kind == 'pawn_contact'
                        assert (event.start_tick, event.hit_tick, event.target_cells) == (0, 39, ((5, 4),))
                    if f in (2, 3, 4, 5, 6, 7, 8, 9):
                        pauses[f] = g.combat.tick
                    if g.combat.tick == 39:
                        expected = {'hit': 'hit', 'evade': 'miss', 'normal': 'parried_normal', 'perfect': 'parried_perfect'}[mode]
                        assert g.encounter.ledger.outcome(events_seen[0]) == expected
                        assert g.player.health.current_hp == (2 if mode == 'hit' else 3)
                        assert g.encounter.enemies[0].position == (4, 4)
                        if mode in ('normal', 'perfect'):
                            assert g.resolver.last_parry_result.status == mode
                        if mode == 'perfect':
                            assert g.combat.pending_attack_bonus == 2
                            assert g.encounter.enemies[0].stun_until_tick == 99
                        elif mode != 'hit':
                            done[0] = True
                    if mode == 'perfect' and g.combat.tick == 40:
                        assert g.state is GameState.UPGRADE
                        assert not g.encounter.enemies[0].alive
                        assert g.combat.pending_attack_bonus == 0
                        assert g.player.position == (5, 4)
                        done[0] = True
                    if g.state is GameState.GAME_OVER:
                        assert mode == 'hit' and g.combat.tick == 225
                        assert g.player.health.current_hp == 0
                        assert not g.encounter.ledger.pending
                else:
                    assert mode == 'hit' and restarted[0] and len(games) == 2
                    old = games[0]
                    assert g.stage_number == 1 and g.combat.tick == 0
                    assert g.player.health.current_hp == 3
                    assert g.combat.stage_instance_id != old.combat.stage_instance_id
                    assert g.encounter.ledger.state(events_seen[0]) == 'unknown'
                    try:
                        g.resolver.resolve_enemy_attack(events_seen[0])
                    except ValueError:
                        pass
                    else:
                        raise AssertionError('Old contact crossed the restart')
                    assert g.parry.last_attempt is None and not g.encounter.ledger.pending
                    done[0] = True
                present_real()
                frame[0] += 1
                now[0] += FIXED_TIME_STEP
                assert frame[0] < 300

            with patch.object(canvas, 'open_canvas', side_effect=open_window), \\
                 patch.object(canvas, 'close_canvas', side_effect=close_window), \\
                 patch.object(canvas, 'get_events', side_effect=poll), \\
                 patch.object(canvas, 'update_canvas', side_effect=present), \\
                 patch.object(canvas, 'SDL_GetWindowFlags', side_effect=lambda w: flags[0]), \\
                 patch.object(main, '_new_game', side_effect=create), \\
                 patch.object(main, 'perf_counter', side_effect=lambda: now[0]), \\
                 patch.object(main, 'sleep'):
                main.main()
            assert done[0] and closed == [True]
            assert pauses[2] == pauses[3] == pauses[4] == pauses[5]
            assert pauses[6] == pauses[7] == pauses[8] == pauses[9]
            print('PASS native contact', mode, 'real main, warning, settings/F11/focus, ESC/SDL_QUIT')
        ''')
        result = subprocess.run([sys.executable, '-c', script, mode],
                                cwd=Path(__file__).resolve().parents[1],
                                env={**os.environ, 'SDL_VIDEODRIVER': 'dummy'},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_contact_hit_game_over_and_fresh_restart(self):
        self.native_contact('hit')

    def test_native_contact_warning_and_direction_key_evade(self):
        self.native_contact('evade')

    def test_native_contact_shift_normal_parry(self):
        self.native_contact('normal')

    def test_native_contact_perfect_bonus_real_space_kill_upgrade(self):
        self.native_contact('perfect')

    def test_main_contact_parry_schedule_matches_one_and_eight_tick_frames(self):
        from config import FIXED_TIME_STEP
        from tests.test_pawn_contact import session
        from tests.test_stage_transition import run_loop, key, SHIFT
        traces = []
        for stride in (1, 8):
            ticks = sorted(set(range(0, 41, stride)) | {32, 39, 40})
            lengths = [(b-a)*FIXED_TIME_STEP for a, b in zip(ticks, ticks[1:])] + [FIXED_TIME_STEP]
            games, *_ = run_loop([[key(SHIFT), key(SHIFT, False)] if t == 32 else [] for t in ticks],
                                 initial='playing', initial_factory=session, lengths=lengths)
            g = games[-1]
            traces.append((g.combat.tick, g.player.position, g.player.health.current_hp,
                           g.combat.pending_attack_bonus, g.resolver.last_parry_result.status,
                           [(r.event.start_tick, r.event.hit_tick, r.event.target_cells, r.state, r.outcome)
                            for r in g.encounter.ledger._records.values()]))
        self.assertEqual(traces[0], traces[1])
        self.assertEqual(traces[0][:5], (40, (5, 4), 3, 2, 'perfect'))


if __name__ == '__main__':
    unittest.main()
