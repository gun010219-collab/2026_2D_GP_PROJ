from types import SimpleNamespace
from unittest.mock import Mock
import unittest

from combat import Combat
from player import Player
from sdl_input import GameplayInput


class SDLInputTests(unittest.TestCase):
    def setUp(self):
        self.c = SimpleNamespace(SDL_KEYDOWN=768, SDL_KEYUP=769, SDLK_UP=1, SDLK_DOWN=2,
                                 SDLK_LEFT=3, SDLK_RIGHT=4, SDLK_SPACE=32,
                                 SDL_SCANCODE_UP=1, SDL_SCANCODE_DOWN=2,
                                 SDL_SCANCODE_LEFT=3, SDL_SCANCODE_RIGHT=4,
                                 SDL_SCANCODE_SPACE=5, SDL_WINDOW_INPUT_FOCUS=512,
                                 window=object(), SDL_GetWindowFlags=Mock(return_value=512),
                                 SDL_GetKeyboardState=Mock(return_value=[0] * 6))
        self.controls, self.player, self.combat = GameplayInput(self.c), Player(5, 1), Combat()

    def key(self, key, down=True, blocked=False):
        return self.controls.handle_key(SimpleNamespace(type=768 if down else 769, key=key),
                                        self.player, self.combat, blocked)

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
        self.c.SDL_GetKeyboardState.return_value = [0, 1, 0, 0, 0, 1]
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
