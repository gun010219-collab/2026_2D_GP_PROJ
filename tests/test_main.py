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
        canvas.SDLK_LSHIFT, canvas.SDLK_RSHIFT = 1073742049, 1073742053
        canvas.SDL_WINDOW_INPUT_FOCUS = 512
        canvas.SDL_GetWindowFlags.return_value = 512
        canvas.SDL_SCANCODE_UP, canvas.SDL_SCANCODE_DOWN = 82, 81
        canvas.SDL_SCANCODE_LEFT, canvas.SDL_SCANCODE_RIGHT = 80, 79
        canvas.SDL_SCANCODE_SPACE = 44
        canvas.SDL_SCANCODE_LSHIFT, canvas.SDL_SCANCODE_RSHIFT = 225, 229
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
                patch.object(main, 'AttackRenderer') as attack, patch.object(main, 'ParryRenderer') as parry, \
                patch.object(main, 'EnemyRenderer') as enemies, \
                patch.object(main, 'EnemyAttackRenderer') as warning:
            order.attach_mock(board.return_value.draw, 'board')
            order.attach_mock(warning.return_value.draw, 'warning')
            order.attach_mock(attack.return_value.draw, 'attack')
            order.attach_mock(enemies.return_value.draw, 'enemies')
            order.attach_mock(parry.return_value.draw, 'parry')
            order.attach_mock(player.return_value.draw, 'player')
            order.attach_mock(ui.return_value.draw, 'settings')
            main.main()
        self.assertEqual([call[0] for call in order.mock_calls],
                         ['board', 'warning', 'attack', 'enemies', 'parry', 'player', 'settings'])

    def run_combat_frames(self, batches, frame_lengths=None, parry=None,
                          focus_flags=None, held_shift=False, encounter=None):
        from combat import Combat
        from config import FIXED_TIME_STEP
        canvas = self.make_canvas()
        canvas.get_events.side_effect = batches + [[SimpleNamespace(type=256)]]
        if focus_flags is not None:
            queued = iter(zip(batches + [[SimpleNamespace(type=256)]], focus_flags + [focus_flags[-1]]))
            def poll():
                events, flags = next(queued)
                canvas.SDL_GetWindowFlags.return_value = flags
                return events
            canvas.get_events.side_effect = poll
        if held_shift:
            canvas.SDL_GetKeyboardState.return_value[225] = 1
        now = [0.0]
        lengths = iter(frame_lengths or [FIXED_TIME_STEP] * len(batches))
        canvas.update_canvas.side_effect = lambda: now.__setitem__(0, now[0] + next(lengths))
        combat = Combat()
        parry_state = parry if parry is not None else main.Parry()
        pawns = encounter if encounter is not None else main.PawnEncounter(main.load_stage1_enemies())
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings'), patch.object(main, 'SettingsRenderer'), \
                patch.object(main, 'Combat', return_value=combat), \
                patch.object(main, 'Parry', return_value=parry_state), \
                patch.object(main, 'PawnEncounter', return_value=pawns), \
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

    def test_shift_uses_shared_tick_for_phase_and_expiry(self):
        from parry import Parry
        for ticks, expected in [(0, 'perfect_window'), (8, 'normal_window'), (18, 'inactive')]:
            parry = Parry()
            combat = self.run_combat_frames([[SimpleNamespace(type=768, key=1073742049)]]
                                            + [[] for _ in range(ticks)], parry=parry)
            self.assertEqual(combat.tick, ticks)
            self.assertEqual(parry.state_at(combat.tick), expected)
            self.assertEqual(parry.last_attempt.start_tick, 0)

    def test_long_menu_pause_freezes_parry_window(self):
        from config import FIXED_TIME_STEP
        from parry import Parry
        parry = Parry()
        combat = self.run_combat_frames([
            [SimpleNamespace(type=768, key=1073742049)],
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=769, key=1073742049)],
            [SimpleNamespace(type=768, key=27)], [],
        ], [FIXED_TIME_STEP, 10.0, 10.0, FIXED_TIME_STEP, FIXED_TIME_STEP], parry=parry)
        self.assertEqual(combat.tick, 2)
        self.assertEqual(parry.state_at(combat.tick), 'perfect_window')
        self.assertEqual(parry.next_parry_tick, 60)

    def test_shift_in_menu_is_consumed_and_fresh_press_after_close_starts(self):
        from parry import Parry
        parry = Parry()
        combat = self.run_combat_frames([
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=768, key=1073742049)],
            [SimpleNamespace(type=768, key=27)],
            [SimpleNamespace(type=769, key=1073742049), SimpleNamespace(type=768, key=1073742053)],
        ], parry=parry)
        self.assertEqual(parry.last_attempt.parry_id, 1)
        self.assertEqual(parry.last_attempt.start_tick, combat.tick)

    def test_f11_keeps_shift_release_and_new_press_after_cooldown(self):
        from parry import Parry
        parry = Parry()
        batches = [[SimpleNamespace(type=768, key=1073742049)],
                   [SimpleNamespace(type=768, key=1073741892), SimpleNamespace(type=769, key=1073742049)]]
        batches += [[] for _ in range(58)] + [[SimpleNamespace(type=768, key=1073742053)]]
        combat = self.run_combat_frames(batches, parry=parry)
        self.assertEqual(combat.tick, 60)
        self.assertEqual(parry.last_attempt.parry_id, 2)
        self.assertEqual(parry.last_attempt.start_tick, 60)

    def test_focus_regain_held_shift_does_not_create_phantom_attempt(self):
        from parry import Parry
        parry = Parry()
        combat = self.run_combat_frames([[], [],
            [SimpleNamespace(type=768, key=1073742049)],
            [SimpleNamespace(type=769, key=1073742049), SimpleNamespace(type=768, key=1073742049)],
        ], parry=parry, focus_flags=[512, 0, 512, 512], held_shift=True)
        self.assertEqual(parry.last_attempt.parry_id, 1)
        self.assertEqual(parry.last_attempt.start_tick, 1)
        self.assertEqual(combat.tick, 1)

    def test_space_shift_same_frame_preserve_attack_and_parry(self):
        from parry import Parry
        for keys in ([32, 1073742049], [1073742049, 32]):
            parry = Parry()
            combat = self.run_combat_frames([[SimpleNamespace(type=768, key=key) for key in keys]], parry=parry)
            self.assertEqual(combat.active_attack.start_tick, parry.last_attempt.start_tick)
            self.assertEqual(combat.next_attack_tick, 36)
            self.assertEqual(parry.next_parry_tick, 60)

    def attack_encounter(self):
        from enemy import Enemy
        from enemy_behaviors import PawnEncounter
        return PawnEncounter((Enemy('test-pawn', 4, 2, (0, -1), 0),))

    def test_enemy_time_and_warning_freeze_during_long_menu(self):
        from config import FIXED_TIME_STEP
        encounter = self.attack_encounter()
        combat = self.run_combat_frames([[],
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)], [],
            [SimpleNamespace(type=768, key=27)], [],
        ], [FIXED_TIME_STEP, 10, 10, FIXED_TIME_STEP, FIXED_TIME_STEP], encounter=encounter)
        self.assertEqual((combat.tick, encounter.tick), (2, 2))
        event = encounter.ledger.telegraphs[0]
        self.assertEqual((event.telegraph_start_tick, event.hit_tick), (0, 39))
        self.assertFalse(encounter.ledger.consume(event, 'player-instance'))

    def test_enemy_ai_freezes_through_focus_loss_and_gain(self):
        encounter = self.attack_encounter()
        combat = self.run_combat_frames([[], [], [], [], []],
                                        focus_flags=[512, 0, 0, 512, 512], encounter=encounter)
        self.assertEqual((combat.tick, encounter.tick), (1, 1))
        self.assertEqual(len(encounter.ledger.telegraphs), 1)

    def test_f11_does_not_recreate_enemy_event_or_auto_consume(self):
        encounter = self.attack_encounter()
        encounter.advance_to(0, (5, 1))
        event = encounter.ledger.telegraphs[0]
        combat = self.run_combat_frames([[], [SimpleNamespace(type=768, key=1073741892)]]
                                        + [[] for _ in range(38)], encounter=encounter)
        self.assertEqual((combat.tick, encounter.tick), (39, 39))
        self.assertEqual(encounter.ledger.telegraphs, ())
        self.assertEqual(encounter.enemies[0].state, 'recovering')
        # A due event is still available for the future damage consumer.
        self.assertEqual(encounter.ledger.state(event), 'due')
        self.assertTrue(encounter.ledger.consume(event, 'player-instance'))
        encounter.advance_to(93, (5, 1))
        self.assertEqual(encounter.enemies[0].current_attack.attack_id, 2)

    def test_player_cannot_enter_spawned_pawn_cell_but_facing_updates(self):
        from enemy import Enemy
        with patch.object(main, 'load_stage1_enemies',
                          return_value=(Enemy('blocker', 6, 1, (0, -1), 10),)):
            player = self.run_player_events([[SimpleNamespace(type=768, key=1073741903)]])
        self.assertEqual((player.position, player.facing), ((5, 1), 'right'))


if __name__ == '__main__':
    unittest.main()
