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
