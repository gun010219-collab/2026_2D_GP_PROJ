"""Loop control tests with a fake canvas; these do not verify Windows GUI."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main


class WindowLoopTests(unittest.TestCase):
    def make_canvas(self):
        canvas = Mock()
        canvas.SDL_QUIT = 256
        canvas.SDL_KEYDOWN = 768
        canvas.SDL_KEYUP = 769
        canvas.SDLK_UP, canvas.SDLK_DOWN = 1073741906, 1073741905
        canvas.SDLK_LEFT, canvas.SDLK_RIGHT = 1073741904, 1073741903
        canvas.SDLK_ESCAPE = 27
        canvas.SDLK_F11 = 1073741892
        canvas.SDL_MOUSEBUTTONDOWN = 1025
        canvas.SDL_BUTTON_LEFT = 1
        canvas.SDLK_SPACE = 32
        canvas.SDL_WINDOW_INPUT_FOCUS = 512
        canvas.SDL_GetWindowFlags.return_value = 512
        canvas.SDL_SCANCODE_UP, canvas.SDL_SCANCODE_DOWN = 82, 81
        canvas.SDL_SCANCODE_LEFT, canvas.SDL_SCANCODE_RIGHT = 80, 79
        canvas.SDL_SCANCODE_SPACE = 44
        canvas.SDL_GetKeyboardState.return_value = [0] * 512
        return canvas

    def run_with_canvas(self, canvas):
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings'), patch.object(main, 'SettingsRenderer'):
            main.main()

    def test_escape_and_close_release_resources_on_repeated_runs(self):
        for kind, key in [(768, 27), (256, None), (768, 27)]:
            with self.subTest(kind=kind):
                canvas = self.make_canvas()
                canvas.get_events.return_value = [SimpleNamespace(type=kind, key=key)]
                self.run_with_canvas(canvas)
                canvas.open_canvas.assert_called_once_with(1440, 900)
                canvas.close_canvas.assert_called_once_with()
                canvas.draw_rectangle.assert_not_called()

    def test_render_frame_is_paced_and_title_restored(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [[], [SimpleNamespace(type=256)]]
        with patch.object(main, 'sleep') as sleeper:
            self.run_with_canvas(canvas)
        self.assertGreaterEqual(canvas.draw_rectangle.call_count, 100)
        canvas.update_canvas.assert_called_once_with()
        sleeper.assert_called_once()
        self.assertGreaterEqual(sleeper.call_args.args[0], 0)
        canvas.SDL_SetWindowTitle.assert_called_with(canvas.window, b'CHECKMATE')
        canvas.close_canvas.assert_called_once_with()

    def test_render_failure_still_releases_resources(self):
        canvas = self.make_canvas()
        canvas.get_events.return_value = []
        canvas.SDL_RenderClear.side_effect = RuntimeError('render failure')
        with self.assertRaisesRegex(RuntimeError, 'render failure'):
            self.run_with_canvas(canvas)
        canvas.close_canvas.assert_called_once_with()

    def test_menu_escape_is_consumed_before_normal_escape_exit(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=768, key=27)],
            [SimpleNamespace(type=768, key=27)],
        ]
        self.run_with_canvas(canvas)
        self.assertEqual(canvas.update_canvas.call_count, 2)
        canvas.close_canvas.assert_called_once_with()

    def test_f11_and_menu_click_use_same_display_toggle(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [
            [SimpleNamespace(type=768, key=1073741892)],
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=1025, button=1, x=720, y=427)],
            [SimpleNamespace(type=256)],
        ]
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings') as display, \
                patch.object(main, 'SettingsRenderer'):
            main.main()
        self.assertEqual(display.return_value.toggle.call_count, 2)
        canvas.open_canvas.assert_called_once_with(1440, 900)

    def test_x_exits_while_menu_is_open(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=256)],
        ]
        self.run_with_canvas(canvas)
        canvas.close_canvas.assert_called_once_with()

    def test_x_is_not_lost_in_same_batch_as_f11(self):
        canvas = self.make_canvas()
        canvas.get_events.return_value = [SimpleNamespace(type=768, key=1073741892),
                                         SimpleNamespace(type=256)]
        self.run_with_canvas(canvas)
        canvas.update_canvas.assert_not_called()
        canvas.close_canvas.assert_called_once_with()

    def run_player_events(self, batches):
        from player import Player
        p = Player(5, 1)
        canvas = self.make_canvas()
        canvas.get_events.side_effect = batches + [[SimpleNamespace(type=256)]]
        with patch.object(main, 'load_stage1_player', return_value=p):
            self.run_with_canvas(canvas)
        return p

    def test_arrow_down_up_repress_moves_one_cell_each(self):
        down = SimpleNamespace(type=768, key=1073741906)
        up = SimpleNamespace(type=769, key=1073741906)
        p = self.run_player_events([[down, down], [up, down]])
        self.assertEqual(p.position, (5, 3))

    def test_menu_blocks_moves_and_key_release_is_not_lost(self):
        down = SimpleNamespace(type=768, key=1073741906)
        up = SimpleNamespace(type=769, key=1073741906)
        p = self.run_player_events([
            [down], [SimpleNamespace(type=1025, button=1, x=1295, y=41), up, down],
            [SimpleNamespace(type=768, key=27), down], [up, down],
        ])
        self.assertEqual(p.position, (5, 3))

    def test_f11_tail_release_does_not_latch_arrow(self):
        down = SimpleNamespace(type=768, key=1073741906)
        up = SimpleNamespace(type=769, key=1073741906)
        p = self.run_player_events([[down], [SimpleNamespace(type=768, key=1073741892), up], [down]])
        self.assertEqual(p.position, (5, 3))

    def test_board_player_menu_render_in_that_order(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [[], [SimpleNamespace(type=256)]]
        order = Mock()
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings'), patch.object(main, 'SettingsRenderer') as ui, \
                patch.object(main, 'BoardRenderer') as board, patch.object(main, 'PlayerRenderer') as player, \
                patch.object(main, 'AttackRenderer') as attack:
            order.attach_mock(board.return_value.draw, 'board')
            order.attach_mock(attack.return_value.draw, 'attack')
            order.attach_mock(player.return_value.draw, 'player')
            order.attach_mock(ui.return_value.draw, 'settings')
            main.main()
        self.assertEqual([call[0] for call in order.mock_calls], ['board', 'attack', 'player', 'settings'])

    def run_combat_frames(self, batches, frame_lengths=None):
        from combat import Combat
        from config import FIXED_TIME_STEP
        canvas = self.make_canvas()
        canvas.get_events.side_effect = batches + [[SimpleNamespace(type=256)]]
        now = [0.0]
        lengths = iter(frame_lengths or [FIXED_TIME_STEP] * len(batches))
        canvas.update_canvas.side_effect = lambda: now.__setitem__(0, now[0] + next(lengths))
        combat = Combat()
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings'), patch.object(main, 'SettingsRenderer'), \
                patch.object(main, 'Combat', return_value=combat), \
                patch.object(main, 'perf_counter', side_effect=lambda: now[0]), patch.object(main, 'sleep'):
            main.main()
        return combat

    def test_space_requests_obey_exact_cooldown_in_main(self):
        down, up = SimpleNamespace(type=768, key=32), SimpleNamespace(type=769, key=32)
        batches = [[down], [up, down], [up]] + [[] for _ in range(33)] + [[down]]
        combat = self.run_combat_frames(batches)
        self.assertEqual(combat.tick, 36)
        self.assertEqual(combat.active_attack.attack_id, 2)
        self.assertEqual(combat.active_attack.start_tick, 36)

    def test_long_menu_pause_does_not_advance_combat_or_expire_effect(self):
        from config import FIXED_TIME_STEP
        combat = self.run_combat_frames([
            [SimpleNamespace(type=768, key=32)],
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=769, key=32)],
            [SimpleNamespace(type=768, key=27)],
            [SimpleNamespace(type=768, key=32)],
        ], [FIXED_TIME_STEP, 10.0, 10.0, FIXED_TIME_STEP, FIXED_TIME_STEP])
        self.assertEqual(combat.tick, 2)
        self.assertEqual(combat.active_attack.attack_id, 1)

    def test_f11_retains_space_release_and_does_not_duplicate_attack(self):
        down = SimpleNamespace(type=768, key=32)
        batches = [[down], [SimpleNamespace(type=768, key=1073741892),
                            SimpleNamespace(type=769, key=32)]]
        batches += [[] for _ in range(34)] + [[down]]
        combat = self.run_combat_frames(batches)
        self.assertEqual(combat.active_attack.attack_id, 2)
        self.assertEqual(combat.active_attack.start_tick, 36)

    def test_move_then_attack_and_attack_then_move_in_main(self):
        for keys, origin, target in [([1073741903, 32], (6, 1), (7, 1)),
                                     ([32, 1073741903], (5, 1), (5, 2))]:
            combat = self.run_combat_frames([[SimpleNamespace(type=768, key=key) for key in keys]])
            self.assertEqual(combat.active_attack.origin_cell, origin)
            self.assertEqual(combat.active_attack.target_cell, target)


if __name__ == '__main__':
    unittest.main()
