"""Main-loop outcomes/restart with fake SDL/time; no desktop or real sleeps."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import main
import test_main
import test_game as game_tests
from config import FIXED_TIME_STEP
from enemy import Enemy
from game import GameState
from simulation_clock import SimulationClock


def key(value, down=True):
    return SimpleNamespace(type=768 if down else 769, key=value)


R = ord('r')
UP, SPACE, SHIFT, F11, ESC = 1073741906, 32, 1073742049, 1073741892, 27
MENU = SimpleNamespace(type=1025, button=1, x=1295, y=41)


class GameFlowIntegrationTests(unittest.TestCase):
    def run_loop(self, batches, *, initial='dead', lengths=None, focus=None, after_render=None,
                 initial_factory=None, render_order=None):
        canvas = test_main.WindowLoopTests().make_canvas()
        canvas.SDLK_r, canvas.SDL_SCANCODE_R = R, 21
        scans = {UP: 82, 1073741905: 81, 1073741904: 80, 1073741903: 79,
                 SPACE: 44, SHIFT: 225, 1073742053: 229, R: 21}
        batches = batches + [[SimpleNamespace(type=256)]]
        flags = (focus + [focus[-1]]) if focus is not None else [512] * len(batches)
        queued = iter(zip(batches, flags))

        def poll():
            events, flag = next(queued)
            canvas.SDL_GetWindowFlags.return_value = flag
            # SDL's physical state represents the complete polled event batch.
            for event in events:
                if event.type in (768, 769) and event.key in scans:
                    canvas.SDL_GetKeyboardState.return_value[scans[event.key]] = int(event.type == 768)
            return events

        canvas.get_events.side_effect = poll
        now = [0.0]
        elapsed = iter(lengths or [FIXED_TIME_STEP] * (len(batches) - 1))
        created, snapshots = [], []
        original_factory = main._new_game

        def create():
            game = initial_factory() if not created and initial_factory is not None else original_factory()
            if not created:
                if initial == 'dead':
                    game.player.health.apply_damage(3, tick=0)
                elif initial == 'clear':
                    game_tests.kill_enemies(game)
                game.update_state()
            created.append(game)
            return game

        def rendered():
            game = created[-1]
            snapshots.append((game.state, game.combat.tick, game.player.position,
                              game.player.health.current_hp, game.combat.next_attack_tick,
                              game.parry.next_parry_tick, len(created)))
            if after_render is not None:
                after_render(game, len(snapshots) - 1)
            now[0] += next(elapsed)

        canvas.update_canvas.side_effect = rendered
        menu = main.SettingsMenu()
        clock = SimulationClock()
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, '_new_game', side_effect=create), \
                patch.object(main, 'DisplaySettings') as display, \
                patch.object(main, 'SettingsRenderer') as settings, \
                patch.object(main, 'BoardRenderer') as board, \
                patch.object(main, 'SettingsMenu', return_value=menu), \
                patch.object(main, 'SimulationClock', return_value=clock), \
                patch.object(main, 'perf_counter', side_effect=lambda: now[0]), \
                patch.object(main, 'sleep'):
            if render_order is not None:
                settings.return_value.draw.side_effect = lambda *a: render_order.append('settings')
            main.main()
        canvas.open_canvas.assert_called_once_with(1440, 900)
        canvas.close_canvas.assert_called_once_with()
        display.assert_called_once_with(canvas)
        settings.assert_called_once_with(canvas)
        settings.return_value.close.assert_called_once_with()
        board.assert_called_once_with(chapter=1)
        return created, snapshots, canvas, menu, display, clock

    def test_game_over_freezes_time_ai_and_blocks_gameplay(self):
        created, snapshots, _, _, _, clock = self.run_loop(
            [[key(UP), key(SPACE), key(SHIFT)], [], []], lengths=[20, 20, 20])
        game = created[0]
        self.assertTrue(all(s[:4] == (GameState.GAME_OVER, 0, (5, 1), 0) for s in snapshots))
        self.assertEqual([e.position for e in game.encounter.enemies], [(1, 6), (8, 6)])
        self.assertIsNone(game.combat.active_attack)
        self.assertIsNone(game.parry.last_attempt)
        self.assertEqual((game.transition_count, clock.accumulator), (1, 0))

    def test_stage_clear_freezes_time_and_blocks_gameplay(self):
        created, snapshots, _, _, _, clock = self.run_loop(
            [[key(UP), key(SPACE), key(SHIFT)], [], []], initial='clear', lengths=[20, 20, 20])
        game = created[0]
        self.assertTrue(all(s[:4] == (GameState.STAGE_CLEAR, 0, (5, 1), 3) for s in snapshots))
        self.assertIsNone(game.combat.active_attack)
        self.assertIsNone(game.parry.last_attempt)
        self.assertEqual((game.transition_count, clock.accumulator), (1, 0))

    def test_both_outcomes_restart_into_fresh_original_stage_without_reopening_window(self):
        for state in ('dead', 'clear'):
            with self.subTest(state=state):
                created, snapshots, _, _, _, clock = self.run_loop([[key(R)], []], initial=state)
                old, new = created
                self.assertTrue(old.resolver.stopped)
                self.assertTrue(new.playing)
                self.assertEqual((snapshots[0][1], new.player.health.current_hp), (0, 3))
                self.assertEqual(new.player.position, (5, 1))
                self.assertEqual([e.health.current_hp for e in new.encounter.enemies], [2, 2])
                self.assertNotEqual(old.player.entity_instance_id, new.player.entity_instance_id)
                self.assertNotEqual(old.combat.stage_instance_id, new.combat.stage_instance_id)
                self.assertEqual(clock.accumulator, 0)

    def test_restart_ignores_tail_actions_and_quarantines_held_keys_until_release(self):
        created, snapshots, _, _, _, _ = self.run_loop([
            [key(R), key(UP), key(SPACE), key(SHIFT)],
            [key(UP), key(SPACE), key(SHIFT)],
            [key(UP, False), key(SPACE, False), key(SHIFT, False)],
            [key(UP), key(SPACE), key(SHIFT)],
        ])
        new = created[-1]
        self.assertTrue(all(s[2] == (5, 1) and s[4:6] == (0, 0) for s in snapshots[:3]))
        self.assertEqual(new.player.position, (5, 2))
        self.assertEqual((new.combat.active_attack.attack_id, new.parry.last_attempt.parry_id), (1, 1))
        self.assertEqual((new.combat.active_attack.start_tick, new.parry.last_attempt.start_tick), (3, 3))

    def test_r_is_not_a_mid_fight_reset_or_buffered_for_future_death(self):
        def die_after_first_frame(game, frame):
            if frame == 0:
                game.player.health.apply_damage(3, tick=0)
        created, snapshots, _, _, _, _ = self.run_loop(
            [[key(R)], [key(R)], [key(R, False)], [key(R)]],
            initial='playing', after_render=die_after_first_frame)
        self.assertEqual([s[-1] for s in snapshots], [1, 1, 1, 2])
        self.assertEqual(created[0].state, GameState.GAME_OVER)
        self.assertTrue(created[1].playing)

    def test_repeated_r_down_cannot_restart_again_without_release(self):
        def die_after_restart(game, frame):
            if frame == 0:
                game.player.health.apply_damage(3, tick=0)
        created, snapshots, _, _, _, _ = self.run_loop(
            [[key(R), key(R)], [key(R)], [key(R, False)], [key(R)]],
            after_render=die_after_restart)
        self.assertEqual([s[-1] for s in snapshots], [2, 2, 2, 3])
        self.assertEqual(len(created), 3)

    def test_restart_then_f11_in_one_batch_preserves_both(self):
        created, _, _, _, display, _ = self.run_loop([[key(R), key(F11)], []])
        self.assertEqual(len(created), 2)
        display.return_value.toggle.assert_called_once_with()

    def test_f11_then_restart_requires_release_and_new_press(self):
        created, snapshots, _, _, display, _ = self.run_loop(
            [[key(F11), key(R)], [key(R, False)], [key(R)]])
        self.assertEqual([s[-1] for s in snapshots], [1, 1, 2])
        display.return_value.toggle.assert_called_once_with()
        self.assertTrue(created[-1].playing)

    def test_menu_blocks_restart_but_escape_closes_it_and_fresh_r_restarts(self):
        created, snapshots, _, menu, _, _ = self.run_loop(
            [[MENU, key(R)], [key(ESC), key(R, False)], [key(R)]])
        self.assertEqual([s[-1] for s in snapshots], [1, 1, 2])
        self.assertFalse(menu.is_open)
        self.assertTrue(created[-1].playing)

    def test_restart_then_settings_opens_menu_on_the_same_window(self):
        created, snapshots, _, menu, _, _ = self.run_loop([[key(R), MENU], [], [key(ESC)]])
        self.assertEqual(len(created), 2)
        self.assertEqual([s[1] for s in snapshots], [0, 0, 0])
        self.assertFalse(menu.is_open)

    def test_terminal_settings_f11_and_escape_exit_work_in_both_outcomes(self):
        for state in ('dead', 'clear'):
            with self.subTest(state=state):
                created, snapshots, _, menu, display, _ = self.run_loop(
                    [[MENU], [key(ESC)], [key(F11)], [key(ESC)]], initial=state)
                self.assertEqual(len(snapshots), 3)
                self.assertEqual(len(created), 1)
                self.assertFalse(menu.is_open)
                display.return_value.toggle.assert_called_once_with()

    def test_restart_is_not_triggered_by_unfocused_or_regained_held_r(self):
        created, snapshots, _, _, _, _ = self.run_loop(
            [[], [key(R)], [], [key(R)], [key(R, False)], [key(R)]],
            focus=[512, 0, 0, 512, 512, 512])
        self.assertEqual([s[-1] for s in snapshots], [1, 1, 1, 1, 1, 2])
        self.assertTrue(created[-1].playing)

    def test_consecutive_restarts_have_no_catchup_debt_and_unique_instances(self):
        count = 8
        def finish_again(game, frame):
            if frame < count - 1:
                game.player.health.apply_damage(3, tick=0)
        created, snapshots, _, _, _, clock = self.run_loop(
            [[key(R), key(R, False)] for _ in range(count)],
            lengths=[20] * count, after_render=finish_again)
        self.assertEqual(len(created), count + 1)
        self.assertEqual(len({g.combat.stage_instance_id for g in created}), count + 1)
        self.assertTrue(all(s[1] == 0 for s in snapshots))
        self.assertEqual(clock.accumulator, 0)
        self.assertEqual(created[-1].player.health.current_hp, 3)

    def test_historical_fatal_hit_then_r_in_same_frame_starts_at_zero(self):
        def danger():
            game = game_tests.fixture((Enemy('source', 4, 2, (0, -1), 0),
                                       Enemy('other', 8, 6, (0, -1), 10)))
            game.player.health.apply_damage(2, tick=0)
            return game
        created, snapshots, _, _, _, _ = self.run_loop(
            [[], [], [], [], [], [key(R)]], initial='playing', initial_factory=danger,
            lengths=[FIXED_TIME_STEP * 8] * 6)
        old, new = created
        self.assertEqual((old.combat.tick, old.state), (39, GameState.GAME_OVER))
        self.assertEqual((new.combat.tick, new.player.health.current_hp, snapshots[-1][-1]), (0, 3, 2))

    def test_last_kill_and_r_same_input_tick_wait_for_clear_transition(self):
        def almost_clear():
            first, second = Enemy('last', 5, 2, (0, -1), 10), Enemy('dead', 8, 6, (0, -1), 10)
            first.health.apply_damage(1, tick=0)
            second.health.apply_damage(2, tick=0)
            return game_tests.fixture((first, second))
        created, snapshots, _, _, _, _ = self.run_loop(
            [[key(SPACE), key(R)], [key(R, False), key(R)]],
            initial='playing', initial_factory=almost_clear)
        self.assertEqual((snapshots[0][0], snapshots[0][-1]), (GameState.STAGE_CLEAR, 1))
        self.assertEqual((snapshots[1][0], snapshots[1][-1]), (GameState.PLAYING, 2))
        self.assertEqual(created[0].end_tick, 0)

    def test_overlay_draws_after_game_and_before_settings(self):
        order = []
        with patch.object(main.GameFlowRenderer, 'draw', side_effect=lambda c, g: order.append('outcome')), \
                patch.object(main.HealthRenderer, 'draw', side_effect=lambda *a, **k: order.append('health')):
            created, _, _, _, _, _ = self.run_loop([[]], render_order=order)
        self.assertEqual(order, ['health', 'outcome', 'settings'])
        self.assertFalse(created[0].playing)
