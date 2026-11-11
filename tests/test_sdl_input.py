from types import SimpleNamespace
from unittest.mock import Mock
import unittest

from combat import Combat
from player import Player
from sdl_input import GameplayInput
from parry import Parry


class SDLInputTests(unittest.TestCase):
    def setUp(self):
        self.c = SimpleNamespace(SDL_KEYDOWN=768, SDL_KEYUP=769, SDLK_UP=1, SDLK_DOWN=2,
                                 SDLK_LEFT=3, SDLK_RIGHT=4, SDLK_SPACE=32,
                                 SDLK_LSHIFT=6, SDLK_RSHIFT=7,
                                 SDL_SCANCODE_UP=1, SDL_SCANCODE_DOWN=2,
                                 SDL_SCANCODE_LEFT=3, SDL_SCANCODE_RIGHT=4,
                                 SDL_SCANCODE_SPACE=5, SDL_WINDOW_INPUT_FOCUS=512,
                                 SDL_SCANCODE_LSHIFT=6, SDL_SCANCODE_RSHIFT=7,
                                 window=object(), SDL_GetWindowFlags=Mock(return_value=512),
                                 SDL_GetKeyboardState=Mock(return_value=[0] * 8))
        self.controls, self.player, self.combat = GameplayInput(self.c), Player(5, 1), Combat()
        self.parry = Parry()

    def key(self, key, down=True, blocked=False):
        return self.controls.handle_key(SimpleNamespace(type=768 if down else 769, key=key),
                                        self.player, self.combat, blocked, parry=self.parry)

    def test_movement_attack_order_is_deterministic(self):
        self.key(4)
        self.key(32)
        self.assertEqual(self.combat.active_attack.origin_cell, (6, 1))
        self.assertEqual(self.combat.active_attack.target_cell, (7, 1))
        self.setUp()
        self.key(32)
        self.key(4)
        self.assertEqual(self.combat.active_attack.origin_cell, (5, 1))
        self.assertEqual(self.combat.active_attack.target_cell, (5, 2))

    def test_space_does_not_join_direction_chord(self):
        self.key(32)
        self.key(1)
        self.key(4)
        self.assertEqual(self.player.position, (5, 2))
        self.assertEqual(self.combat.active_attack.origin_cell, (5, 1))

    def test_menu_and_display_tails_track_release_without_attack(self):
        self.key(32, blocked=True)
        self.assertIsNone(self.combat.active_attack)
        self.key(32)
        self.assertIsNone(self.combat.active_attack)
        self.key(32, down=False, blocked=True)
        self.key(32)
        self.assertIsNotNone(self.combat.active_attack)

    def test_focus_loss_and_regain_do_not_create_attack(self):
        self.key(32)
        self.combat.advance(self.combat.cooldown_ticks)
        self.controls.release_on_focus_loss()
        self.c.SDL_GetWindowFlags.return_value = 0
        self.assertFalse(self.controls.focused)
        self.c.SDL_GetWindowFlags.return_value = 512
        self.c.SDL_GetKeyboardState.return_value = [0, 1, 0, 0, 0, 1, 0, 0]
        self.controls.reconcile_physical_keys()
        self.assertTrue(self.controls.focused)
        self.key(32)
        self.key(1)
        self.assertEqual(self.player.position, (5, 1))
        self.assertIsNone(self.combat.active_attack)
        self.key(32, down=False)
        self.key(32)
        self.assertEqual(self.combat.active_attack.attack_id, 2)

    def test_reconcile_missing_release_allows_next_press(self):
        self.key(32)
        self.combat.advance(self.combat.cooldown_ticks)
        self.controls.reconcile_physical_keys()
        self.key(32)
        self.assertEqual(self.combat.active_attack.attack_id, 2)

    def test_each_shift_uses_current_combat_tick(self):
        for key in (6, 7):
            self.setUp()
            self.combat.advance(12)
            self.key(key)
            self.assertEqual(self.parry.last_attempt.start_tick, 12)
            self.assertEqual(self.parry.state_at(12), 'perfect_window')

    def test_both_shifts_share_one_latch_and_release(self):
        self.key(6)
        self.key(7)
        self.assertEqual(self.parry.last_attempt.parry_id, 1)
        self.combat.advance(60)
        self.key(6, down=False)
        self.key(7)
        self.assertEqual(self.parry.last_attempt.parry_id, 1)
        self.key(7, down=False)
        self.key(7)
        self.assertEqual(self.parry.last_attempt.parry_id, 2)

    def test_menu_blocks_shift_until_release_and_fresh_input(self):
        self.key(6, blocked=True)
        self.key(6)
        self.assertIsNone(self.parry.last_attempt)
        self.key(6, down=False, blocked=True)
        self.key(6)
        self.assertEqual(self.parry.last_attempt.parry_id, 1)

    def test_focus_and_display_reconcile_shift_without_ghost_parry(self):
        self.key(6)
        self.combat.advance(60)
        self.controls.release_on_focus_loss()
        self.c.SDL_GetKeyboardState.return_value = [0, 0, 0, 0, 0, 0, 0, 1]
        self.controls.reconcile_physical_keys()
        self.key(7)
        self.assertEqual(self.parry.last_attempt.parry_id, 1)
        self.key(7, down=False)
        self.key(7)
        self.assertEqual(self.parry.last_attempt.parry_id, 2)
        self.c.SDL_GetKeyboardState.return_value = [0] * 8
        self.controls.reconcile_physical_keys()  # recover a missing release
        self.combat.advance(60)
        self.key(7)
        self.assertEqual(self.parry.last_attempt.parry_id, 3)

    def test_parry_does_not_change_facing_or_block_attack_and_movement(self):
        self.key(4)
        before = self.player.position, self.player.facing
        self.key(6)
        self.assertEqual((self.player.position, self.player.facing), before)
        self.key(32)
        self.assertEqual(self.combat.active_attack.target_cell, (7, 1))
        self.assertEqual(self.combat.next_attack_tick, 36)
        self.key(4, down=False)
        self.key(1)
        self.assertEqual(self.player.position, (6, 2))

    def test_space_and_shift_same_tick_are_independent_in_both_orders(self):
        for keys in ((32, 6), (6, 32)):
            self.setUp()
            for key in keys:
                self.key(key)
            self.assertEqual(self.parry.last_attempt.start_tick, self.combat.active_attack.start_tick)
            self.assertEqual(self.combat.active_attack.target_cell, (5, 2))
            self.assertEqual(self.parry.next_parry_tick, 60)

    def test_new_attack_callback_preserves_bool_consumption_and_exact_delivery(self):
        delivered = []
        down = SimpleNamespace(type=768, key=32)
        up = SimpleNamespace(type=769, key=32)
        for event in (down, down, up, down):
            self.assertIs(self.controls.handle_key(event, self.player, self.combat,
                                                   on_attack=delivered.append), True)
        self.assertEqual(delivered, [self.combat.active_attack])
        self.combat.advance(36)
        self.controls.handle_key(up, self.player, self.combat, on_attack=delivered.append)
        self.controls.handle_key(down, self.player, self.combat, on_attack=delivered.append)
        self.assertEqual([event.attack_id for event in delivered], [1, 2])

    def test_callback_runs_before_later_movement_and_never_on_effect_reads(self):
        observed = []
        self.controls.handle_key(SimpleNamespace(type=768, key=32), self.player, self.combat,
                                 on_attack=lambda event: observed.append((event, self.player.position)))
        self.key(4)
        for _ in range(9):
            self.assertIs(self.combat.active_attack, observed[0][0])
        self.assertEqual(observed[0][1], (5, 1))
        self.assertEqual(observed[0][0].target_cell, (5, 2))
        self.assertEqual(len(observed), 1)

    def test_blocked_or_invalid_target_does_not_deliver_attack(self):
        delivered = Mock()
        self.controls.handle_key(SimpleNamespace(type=768, key=32), self.player, self.combat,
                                 blocked=True, on_attack=delivered)
        self.controls.handle_key(SimpleNamespace(type=769, key=32), self.player, self.combat)
        edge = Player(5, 9)
        self.controls.handle_key(SimpleNamespace(type=768, key=32), edge, self.combat,
                                 on_attack=delivered)
        delivered.assert_not_called()

    def test_dead_player_blocks_gameplay_but_releases_and_menu_keys_survive(self):
        self.key(32)
        self.key(1)
        before = self.player.position, self.player.facing
        self.player.health.apply_damage(3, tick=0)
        self.combat.advance(60)
        for key in (32, 1, 6):
            self.key(key, down=False)
            self.key(key)
            self.key(key, down=False)
        self.assertEqual((self.player.position, self.player.facing), before)
        self.assertIsNone(self.parry.last_attempt)
        self.assertEqual(self.combat.next_attack_tick, 36)
        self.assertFalse(self.controls.attack.held)
        self.assertFalse(self.key(27))

    def test_new_parry_callback_delivers_only_accepted_attempt_once(self):
        delivered = []
        def send(value, down=True, blocked=False):
            return self.controls.handle_key(SimpleNamespace(type=768 if down else 769, key=value),
                                            self.player, self.combat, blocked=blocked,
                                            parry=self.parry, on_parry=delivered.append)
        for value in (6, 6, 7):
            self.assertIs(send(value), True)
        self.assertEqual(delivered, [self.parry.last_attempt])
        send(6, down=False)
        send(7, down=False)
        send(6)  # Cooldown request creates no attempt/callback.
        self.combat.advance(60)
        send(6)
        self.assertEqual(len(delivered), 1)
        send(6, down=False)
        send(7)
        self.assertEqual([attempt.parry_id for attempt in delivered], [1, 2])

    def test_blocked_and_reconciled_shifts_never_deliver_a_parry(self):
        delivered = Mock()
        event = SimpleNamespace(type=768, key=6)
        self.controls.handle_key(event, self.player, self.combat, blocked=True,
                                 parry=self.parry, on_parry=delivered)
        self.c.SDL_GetKeyboardState.return_value[6] = 1
        self.controls.reconcile_physical_keys()
        self.controls.handle_key(event, self.player, self.combat,
                                 parry=self.parry, on_parry=delivered)
        self.controls.handle_key(SimpleNamespace(type=769, key=6), self.player, self.combat,
                                 blocked=True, parry=self.parry, on_parry=delivered)
        delivered.assert_not_called()
