from dataclasses import FrozenInstanceError
import unittest

from combat import Combat
from parry import Parry
from player import Player


class ParryTests(unittest.TestCase):
    def test_initial_state_is_inactive(self):
        parry = Parry()
        self.assertIsNone(parry.last_attempt)
        self.assertEqual(parry.state_at(0), 'inactive')
        self.assertFalse(parry.active_at(0))
        self.assertFalse(parry.perfect_at(0))
        self.assertFalse(parry.normal_at(0))

    def test_attempt_records_shared_combat_tick_and_boundaries(self):
        combat = Combat()
        combat.advance(25)
        parry = Parry()
        attempt = parry.request(combat.tick)
        self.assertEqual((attempt.parry_id, attempt.start_tick,
                          attempt.perfect_end_tick, attempt.end_tick), (1, 25, 33, 43))
        self.assertEqual((parry.window_ticks, parry.perfect_ticks, parry.cooldown_ticks), (18, 8, 60))
        self.assertIs(parry.last_attempt, attempt)

    def test_start_and_perfect_window_end_are_exact(self):
        parry = Parry()
        parry.request(10)
        self.assertEqual(parry.state_at(9), 'inactive')
        self.assertEqual(parry.state_at(10), 'perfect_window')
        self.assertTrue(parry.perfect_at(17))
        self.assertFalse(parry.normal_at(17))
        self.assertFalse(parry.perfect_at(18))
        self.assertEqual(parry.state_at(18), 'normal_window')

    def test_normal_window_end_and_active_expiry_are_exact(self):
        parry = Parry()
        parry.request(10)
        self.assertTrue(parry.normal_at(27))
        self.assertTrue(parry.active_at(27))
        self.assertEqual(parry.state_at(28), 'inactive')
        self.assertFalse(parry.active_at(28))
        self.assertFalse(parry.perfect_at(28))
        self.assertFalse(parry.normal_at(28))

    def test_same_tick_queries_are_deterministic_and_do_not_mutate(self):
        parry = Parry()
        attempt = parry.request(0)
        for tick in (0, 7, 8, 17, 18, 100):
            with self.subTest(tick=tick):
                first = parry.state_at(tick)
                for _ in range(5):
                    self.assertEqual(parry.state_at(tick), first)
                    self.assertIs(parry.last_attempt, attempt)
        self.assertEqual(parry.next_parry_tick, 60)

    def test_active_and_cooldown_requests_do_not_renew_attempt(self):
        parry = Parry()
        first = parry.request(0)
        for tick in (0, 7, 8, 17, 18, 59):
            self.assertIsNone(parry.request(tick))
            self.assertIs(parry.last_attempt, first)
            self.assertEqual(parry.next_parry_tick, 60)
        second = parry.request(60)
        self.assertEqual((second.parry_id, second.start_tick), (2, 60))

    def test_active_window_is_not_overwritten_by_shorter_custom_cooldown(self):
        parry = Parry(cooldown_seconds=0.1)
        first = parry.request(0)
        self.assertIsNone(parry.request(6))
        self.assertIs(parry.last_attempt, first)
        self.assertEqual(parry.request(18).parry_id, 2)

    def test_attempt_snapshot_is_frozen(self):
        attempt = Parry().request(0)
        with self.assertRaises(FrozenInstanceError):
            attempt.end_tick = 100

    def test_attack_movement_and_parry_do_not_block_or_modify_each_other(self):
        combat, parry, player = Combat(), Parry(), Player(5, 1)
        attack = combat.request_attack(player)
        attempt = parry.request(combat.tick)
        player.move('right')
        self.assertEqual(player.position, (6, 1))
        self.assertEqual(player.facing, 'right')
        self.assertEqual(attack.target_cell, (5, 2))
        self.assertEqual(combat.next_attack_tick, 36)
        self.assertEqual(combat.effect_ticks, 9)
        self.assertEqual(attempt.start_tick, 0)
        self.assertEqual(parry.state_at(combat.tick), 'perfect_window')

    def test_invalid_ticks_are_rejected_without_mutation(self):
        parry = Parry()
        for tick in (True, 1.5, None, '0'):
            for method in (parry.request, parry.state_at):
                with self.subTest(tick=tick, method=method), self.assertRaises(TypeError):
                    method(tick)
        for method in (parry.request, parry.state_at):
            with self.assertRaises(ValueError):
                method(-1)
        self.assertIsNone(parry.last_attempt)
        self.assertEqual(parry.next_parry_tick, 0)

    def test_duration_rounding_reuses_attack_policy(self):
        parry = Parry(window_seconds=0.30001, perfect_seconds=0.12001, cooldown_seconds=1.00001)
        self.assertEqual((parry.window_ticks, parry.perfect_ticks, parry.cooldown_ticks), (19, 8, 61))
        with self.assertRaises(ValueError):
            Parry(perfect_seconds=0.31)
        with self.assertRaises(ValueError):
            Parry(window_seconds=0)

    def test_parry_model_contains_no_success_or_damage_state(self):
        parry = Parry()
        attempt = parry.request(0)
        self.assertFalse(any(hasattr(value, field) for value in (parry, attempt)
                             for field in ('success', 'failed', 'damage', 'stun')))
