from dataclasses import FrozenInstanceError
import unittest

from combat import Combat
from player import Player


class CombatTests(unittest.TestCase):
    def test_cardinal_targets_at_stage1_spawn(self):
        for facing, expected in [('up', (5, 2)), ('down', (5, 0)),
                                 ('left', (4, 1)), ('right', (6, 1))]:
            with self.subTest(facing=facing):
                event = Combat().request_attack(Player(5, 1, facing))
                self.assertEqual(event.origin_cell, (5, 1))
                self.assertEqual(event.facing, facing)
                self.assertEqual(event.target_cell, expected)
                self.assertEqual(event.start_tick, 0)

    def test_outside_board_has_no_event_cooldown_or_id_cost(self):
        for col, row, facing, inward in [(0, 5, 'left', 'right'), (9, 5, 'right', 'left'),
                                         (5, 0, 'down', 'up'), (5, 9, 'up', 'down')]:
            with self.subTest(facing=facing):
                combat = Combat()
                self.assertIsNone(combat.request_attack(Player(col, row, facing)))
                self.assertEqual(combat.next_attack_tick, 0)
                self.assertIsNone(combat.active_attack)
                event = combat.request_attack(Player(col, row, inward))
                self.assertEqual(event.attack_id, 1)

    def test_one_request_creates_one_event_and_retries_create_none(self):
        combat, player = Combat(), Player(5, 1)
        event = combat.request_attack(player)
        self.assertEqual(event.attack_id, 1)
        for _ in range(10):
            self.assertIsNone(combat.request_attack(player))
            self.assertIs(combat.active_attack, event)

    def test_event_snapshot_survives_player_move_and_facing_change(self):
        combat, player = Combat(), Player(5, 1)
        event = combat.request_attack(player)
        player.move('right')
        player.move('down')
        self.assertEqual(event.origin_cell, (5, 1))
        self.assertEqual(event.facing, 'up')
        self.assertEqual(event.target_cell, (5, 2))
        with self.assertRaises(FrozenInstanceError):
            event.target_cell = (6, 2)

    def test_exact_cooldown_boundary(self):
        combat, player = Combat(), Player(5, 1)
        combat.request_attack(player)
        self.assertEqual(combat.cooldown_ticks, 36)
        self.assertEqual(combat.next_attack_tick, 36)
        combat.advance(35)
        self.assertIsNone(combat.request_attack(player))
        combat.advance()
        event = combat.request_attack(player)
        self.assertEqual((event.attack_id, event.start_tick), (2, 36))

    def test_effect_expiry_is_independent_of_cooldown(self):
        combat, player = Combat(), Player(5, 1)
        event = combat.request_attack(player)
        self.assertEqual(combat.effect_ticks, 9)
        combat.advance(8)
        self.assertIs(combat.active_attack, event)
        combat.advance()
        self.assertIsNone(combat.active_attack)
        self.assertIsNone(combat.request_attack(player))
        combat.advance(27)
        self.assertEqual(combat.request_attack(player).attack_id, 2)

    def test_event_start_uses_current_tick(self):
        combat = Combat()
        combat.advance(10)
        event = combat.request_attack(Player(5, 1))
        self.assertEqual(event.start_tick, 10)
        self.assertEqual(combat.next_attack_tick, 46)

    def test_ids_are_unique_and_monotonic(self):
        combat, player = Combat(), Player(5, 1)
        events = []
        for _ in range(20):
            events.append(combat.request_attack(player))
            combat.advance(combat.cooldown_ticks)
        self.assertEqual([event.attack_id for event in events], list(range(1, 21)))

    def test_non_integral_durations_round_up_to_ticks(self):
        combat = Combat(cooldown_seconds=0.60001, effect_seconds=0.15001)
        self.assertEqual((combat.cooldown_ticks, combat.effect_ticks), (37, 10))

    def test_invalid_durations_are_rejected(self):
        for value in (0, -0.1, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Combat(cooldown_seconds=value)
        for value in (True, None, '0.6'):
            with self.subTest(value=value), self.assertRaises(TypeError):
                Combat(effect_seconds=value)

    def test_invalid_advance_does_not_mutate_time(self):
        combat = Combat()
        for value in (True, 1.5, None, '1'):
            with self.subTest(value=value), self.assertRaises(TypeError):
                combat.advance(value)
        with self.assertRaises(ValueError):
            combat.advance(-1)
        combat.advance(0)
        self.assertEqual(combat.tick, 0)

    def test_attack_request_does_not_move_or_turn_player(self):
        player = Player(5, 1, 'right')
        Combat().request_attack(player)
        self.assertEqual((player.position, player.facing), ((5, 1), 'right'))
