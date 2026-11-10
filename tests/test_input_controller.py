import unittest

from input_controller import InputController
from player import Player


class InputTests(unittest.TestCase):
    def setUp(self):
        self.player = Player(5, 1)
        self.controller = InputController()

    def test_hold_does_not_repeat(self):
        for _ in range(20):
            self.controller.key_down('up', self.player)
        self.assertEqual(self.player.position, (5, 2))

    def test_release_allows_new_press(self):
        self.controller.key_down('up', self.player)
        self.controller.key_up('up')
        self.controller.key_down('up', self.player)
        self.assertEqual(self.player.position, (5, 3))

    def test_chord_first_key_wins_no_diagonal_or_release_motion(self):
        self.controller.key_down('up', self.player)
        self.controller.key_down('right', self.player)
        self.assertEqual(self.player.position, (5, 2))
        self.controller.key_up('up')
        self.controller.key_down('right', self.player)
        self.assertEqual(self.player.position, (5, 2))
        self.controller.key_up('right')
        self.controller.key_down('right', self.player)
        self.assertEqual(self.player.position, (6, 2))

    def test_menu_press_stays_blocked_until_release(self):
        self.controller.key_down('up', self.player, blocked=True)
        self.controller.key_down('up', self.player, blocked=False)
        self.assertEqual(self.player.position, (5, 1))
        self.controller.key_up('up')
        self.controller.key_down('up', self.player)
        self.assertEqual(self.player.position, (5, 2))

    def test_release_in_menu_and_repress_after_menu(self):
        self.controller.key_down('up', self.player)
        self.controller.key_up('up')  # release processed even while menu is open
        self.controller.key_down('right', self.player, blocked=True)
        self.controller.key_up('right')
        self.controller.key_down('right', self.player)
        self.assertEqual(self.player.position, (6, 2))

    def test_pre_menu_hold_does_not_create_ghost_input(self):
        self.controller.key_down('up', self.player)
        self.controller.key_down('up', self.player, blocked=True)
        self.controller.key_down('up', self.player)
        self.assertEqual(self.player.position, (5, 2))

    def test_fast_sequence_and_unknown_keys(self):
        for direction in ['up', 'right', 'down', 'left'] * 20:
            self.controller.key_down(direction, self.player)
            self.controller.key_up(direction)
        self.assertEqual(self.player.position, (5, 1))
        self.assertFalse(self.controller.key_down('space', self.player))
        self.controller.key_up(None)
