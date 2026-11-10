import unittest

from attack_input import AttackInput
from combat import Combat
from input_controller import InputController
from player import Player


class AttackInputTests(unittest.TestCase):
    def setUp(self):
        self.input = AttackInput()
        self.combat = Combat()
        self.player = Player(5, 1)

    def test_first_press_emits_one_attack(self):
        event = self.input.key_down(self.player, self.combat)
        self.assertEqual(event.attack_id, 1)
        self.assertEqual(event.target_cell, (5, 2))
        self.assertTrue(self.input.held)

    def test_hold_never_repeats_even_after_cooldown(self):
        self.input.key_down(self.player, self.combat)
        for _ in range(self.combat.cooldown_ticks * 2):
            self.combat.advance()
            self.assertIsNone(self.input.key_down(self.player, self.combat))
        self.assertEqual(self.combat.next_attack_tick, 36)
        self.input.key_up()
        self.assertEqual(self.input.key_down(self.player, self.combat).attack_id, 2)

    def test_release_and_new_press_obey_cooldown_boundary(self):
        self.input.key_down(self.player, self.combat)
        self.input.key_up()
        self.combat.advance(35)
        self.assertIsNone(self.input.key_down(self.player, self.combat))
        self.combat.advance()
        self.assertIsNone(self.input.key_down(self.player, self.combat))
        self.input.key_up()
        event = self.input.key_down(self.player, self.combat)
        self.assertEqual((event.attack_id, event.start_tick), (2, 36))

    def test_menu_press_is_consumed_without_attack_or_cooldown(self):
        self.assertIsNone(self.input.key_down(self.player, self.combat, blocked=True))
        self.assertIsNone(self.combat.active_attack)
        self.assertEqual(self.combat.next_attack_tick, 0)
        self.assertIsNone(self.input.key_down(self.player, self.combat, blocked=False))
        self.input.key_up()
        self.assertEqual(self.input.key_down(self.player, self.combat).attack_id, 1)

    def test_release_in_menu_rearms_for_fresh_press_after_close(self):
        self.input.key_down(self.player, self.combat)
        self.input.key_up()
        self.input.key_down(self.player, self.combat, blocked=True)
        self.input.key_up()
        self.combat.advance(self.combat.cooldown_ticks)
        self.assertEqual(self.input.key_down(self.player, self.combat).attack_id, 2)

    def test_pre_menu_hold_does_not_become_ghost_attack(self):
        self.input.key_down(self.player, self.combat)
        self.combat.advance(self.combat.cooldown_ticks)
        self.assertIsNone(self.input.key_down(self.player, self.combat, blocked=True))
        self.assertIsNone(self.input.key_down(self.player, self.combat, blocked=False))
        self.input.key_up()
        self.assertEqual(self.input.key_down(self.player, self.combat).attack_id, 2)

    def test_reconcile_lost_release_does_not_synthesize_attack(self):
        self.input.key_down(self.player, self.combat, blocked=True)
        self.input.reconcile(False)
        self.assertFalse(self.input.held)
        self.assertIsNone(self.combat.active_attack)
        self.assertEqual(self.combat.next_attack_tick, 0)
        self.assertEqual(self.input.key_down(self.player, self.combat).attack_id, 1)

    def test_reconcile_held_key_after_focus_or_f11_requires_release(self):
        self.input.reconcile(True)
        self.assertTrue(self.input.held)
        self.assertIsNone(self.combat.active_attack)
        self.assertIsNone(self.input.key_down(self.player, self.combat))
        self.input.key_up()
        self.assertEqual(self.input.key_down(self.player, self.combat).attack_id, 1)

    def test_attack_and_direction_latches_are_independent(self):
        movement = InputController()
        movement.key_down('right', self.player)
        event = self.input.key_down(self.player, self.combat)
        self.assertEqual(event.origin_cell, (6, 1))
        self.assertEqual(event.target_cell, (7, 1))
        self.input.key_up()
        movement.key_down('up', self.player)
        self.assertEqual(self.player.position, (6, 1))
