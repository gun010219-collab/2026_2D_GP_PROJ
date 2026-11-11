"""Perfect reward state and exact stun boundaries without clocks or SDL."""
from dataclasses import FrozenInstanceError, replace
import unittest

from combat import Combat
from combat_resolution import CombatResolver
from config import PERFECT_COUNTER_BONUS, PERFECT_PARRY_STUN_SECONDS
from enemy import Enemy
from enemy_behaviors import PawnEncounter
from health import Health
from parry import Parry
from player import Player


def source(name='source', col=4, row=4):
    return Enemy(name, col, row, (0, -1), 0)


class PerfectCounterTests(unittest.TestCase):
    def test_pdf_reward_values(self):
        self.assertEqual(PERFECT_COUNTER_BONUS, 2)
        self.assertEqual(PERFECT_PARRY_STUN_SECONDS, 1.0)

    def test_cooldown_reset_does_not_create_or_replay_old_attack(self):
        player, combat = Player(5, 1), Combat()
        original = combat.request_attack(player)
        combat.advance(5)
        self.assertEqual(combat.next_attack_tick, 36)
        combat.grant_perfect_counter()
        self.assertEqual(combat.next_attack_tick, 5)
        self.assertIs(combat.active_attack, original)
        self.assertEqual(combat.attack_damage_bonus(original), 0)
        fresh = combat.request_attack(player)
        self.assertEqual((fresh.attack_id, fresh.start_tick, fresh.damage_bonus), (2, 5, 2))
        self.assertEqual(combat.next_attack_tick, 41)

    def test_counter_is_one_nonstacking_pending_reward(self):
        player, combat = Player(5, 1), Combat()
        self.assertFalse(combat.counter_ready)
        for _ in range(3):
            combat.grant_perfect_counter()
            self.assertEqual((combat.pending_attack_bonus, combat.counter_ready), (2, True))
        event = combat.request_attack(player)
        self.assertEqual(event.damage_bonus, 2)
        self.assertEqual((combat.pending_attack_bonus, combat.counter_ready), (0, False))
        combat.advance(36)
        self.assertEqual(combat.request_attack(player).damage_bonus, 0)

    def test_counter_has_no_invented_expiration(self):
        combat = Combat()
        combat.grant_perfect_counter()
        combat.advance(18000)
        self.assertTrue(combat.counter_ready)
        self.assertEqual(combat.request_attack(Player(5, 1)).damage_bonus, 2)

    def test_accepted_empty_cell_attempt_spends_bonus_without_hit_dependency(self):
        combat, player = Combat(), Player(5, 1)
        combat.grant_perfect_counter()
        event = combat.request_attack(player)
        self.assertEqual((event.target_cell, event.damage_bonus), ((5, 2), 2))
        # The producer does not query occupancy: even a miss has spent the reward.
        self.assertFalse(combat.counter_ready)
        combat.finish_attack(event)
        combat.advance(36)
        self.assertEqual(combat.request_attack(player).damage_bonus, 0)

    def test_out_of_board_attempt_keeps_bonus_and_does_not_spend_id(self):
        combat = Combat()
        combat.grant_perfect_counter()
        self.assertIsNone(combat.request_attack(Player(0, 5, 'left')))
        self.assertTrue(combat.counter_ready)
        event = combat.request_attack(Player(0, 5, 'right'))
        self.assertEqual((event.attack_id, event.damage_bonus), (1, 2))

    def test_dead_player_attempt_does_not_emit_or_spend_reward(self):
        combat, player = Combat(), Player(5, 1)
        player.health.apply_damage(3, tick=0)
        combat.grant_perfect_counter()
        self.assertIsNone(combat.request_attack(player))
        self.assertEqual(combat.pending_attack_bonus, 2)
        self.assertIsNone(combat.active_attack)

    def test_counter_snapshot_remains_immutable_after_new_reward(self):
        combat, player = Combat(), Player(5, 1)
        combat.grant_perfect_counter()
        event = combat.request_attack(player)
        self.assertFalse(combat.counter_ready)
        combat.grant_perfect_counter()
        self.assertEqual(combat.attack_damage_bonus(event), 2)
        with self.assertRaises(FrozenInstanceError):
            event.damage_bonus = 4
        for _ in range(20):
            self.assertEqual(combat.attack_damage_bonus(event), 2)
        self.assertTrue(combat.counter_ready)

    def test_forged_bonus_is_rejected_before_any_receipt(self):
        combat, player = Combat(), Player(5, 1)
        combat.grant_perfect_counter()
        event = combat.request_attack(player)
        with self.assertRaises(ValueError):
            combat.attack_damage_bonus(replace(event, damage_bonus=99))
        self.assertEqual(combat.attack_state(event), 'pending')
        self.assertTrue(combat.consume_attack(event, 'target'))
        self.assertFalse(combat.consume_attack(event, 'target'))

    def test_stage_change_clears_pending_counter_and_rejects_old_snapshot(self):
        combat, player = Combat(), Player(5, 1)
        combat.grant_perfect_counter()
        old = combat.request_attack(player)
        combat.grant_perfect_counter()
        combat.bind_stage('new-stage')
        self.assertFalse(combat.counter_ready)
        self.assertEqual(combat.pending_attack_bonus, 0)
        with self.assertRaises(ValueError):
            combat.attack_damage_bonus(old)
        combat.advance(36)
        self.assertEqual(combat.request_attack(player).damage_bonus, 0)

    def test_invalid_snapshot_bonus_is_rejected(self):
        event = Combat().request_attack(Player(5, 1))
        for value in (True, 2.0, '2', None):
            with self.subTest(value=value), self.assertRaises(TypeError):
                replace(event, damage_bonus=value)
        with self.assertRaises(ValueError):
            replace(event, damage_bonus=-1)

    def test_earned_counter_applies_three_actual_damage_once_then_next_attack_is_base_one(self):
        player, combat, parry = Player(5, 1), Combat(), Parry()
        enemy = source(col=4, row=2)
        self.assertEqual(enemy.health.current_hp, 2)  # Real Pawn baseline remains unchanged.
        # This isolated fixture survives three damage so overkill cannot hide
        # a missing or duplicated +2 in the actual resolver's HP reduction.
        enemy.health = Health(5)
        encounter = PawnEncounter((enemy,))
        resolver = CombatResolver(player, combat, encounter, parry=parry)
        resolver.resolve_current_tick()
        original = encounter.ledger.telegraphs[0]
        resolver.advance(32)
        attempt = parry.request(combat.tick)
        resolver.register_parry(attempt)
        resolver.advance(7)
        perfect_result = resolver.parry_result(attempt)
        self.assertEqual((perfect_result.status, combat.pending_attack_bonus), ('perfect', 2))

        resolver.advance()  # Use a fresh tick after the reward was earned.
        self.assertTrue(player.move('left', occupied=encounter.occupied_cells))
        self.assertFalse(player.move('up', occupied=encounter.occupied_cells))
        counter = combat.request_attack(player)
        hit = resolver.resolve_player_attack(counter)
        self.assertEqual((hit.amount, hit.hp_before, hit.hp_after, counter.damage_bonus), (3, 5, 2, 2))
        self.assertFalse(combat.counter_ready)
        self.assertIsNone(resolver.resolve_player_attack(counter))
        self.assertEqual(enemy.health.current_hp, 2)

        resolver.advance(36)
        ordinary = combat.request_attack(player)
        followup = resolver.resolve_player_attack(ordinary)
        self.assertEqual((ordinary.damage_bonus, followup.amount, enemy.health.current_hp), (0, 1, 1))
        self.assertIs(resolver.parry_result(attempt), perfect_result)
        self.assertEqual((encounter.ledger.state(original), encounter.ledger.outcome(original)),
                         ('resolved', 'parried_perfect'))


class PerfectStunTests(unittest.TestCase):
    def perfect_due(self, enemies=None):
        encounter = PawnEncounter((source(),) if enemies is None else enemies)
        encounter.advance_to(0, (3, 3))
        event = encounter.enemies[0].current_attack
        encounter.advance_to(39, (3, 3))
        self.assertTrue(encounter.ledger.consume(event, 'player'))
        self.assertTrue(encounter.ledger.finish(event, 'parried_perfect'))
        return encounter, event

    def test_source_stops_for_exactly_60_ticks_and_resumes_fresh_ai(self):
        encounter, event = self.perfect_due()
        enemy = encounter.enemies[0]
        before = enemy.position
        self.assertTrue(encounter.stun(enemy.entity_instance_id, 39))
        self.assertEqual((enemy.state, enemy.stun_until_tick), ('stunned', 99))
        self.assertIn(before, encounter.occupied_cells)
        self.assertEqual(encounter.advance_to(98, (3, 3)), ())
        self.assertEqual((enemy.position, enemy.state, enemy.current_attack), (before, 'stunned', None))
        encounter.advance_to(99, (3, 3))
        fresh = enemy.current_attack
        self.assertEqual((enemy.state, fresh.start_tick, fresh.hit_tick), ('telegraph', 99, 138))
        self.assertNotEqual(fresh.key, event.key)
        self.assertEqual((encounter.ledger.state(event), encounter.ledger.outcome(event)),
                         ('resolved', 'parried_perfect'))

    def test_stun_cancels_unresolved_source_attacks_without_rewriting_success(self):
        encounter, event = self.perfect_due()
        enemy = encounter.enemies[0]
        extra = encounter.ledger.create(enemy.entity_instance_id, 39, 78, ((3, 3),))
        encounter.stun(enemy.entity_instance_id, 39)
        self.assertEqual(encounter.ledger.state(extra), 'cancelled')
        self.assertEqual((encounter.ledger.state(event), encounter.ledger.outcome(event)),
                         ('resolved', 'parried_perfect'))
        self.assertFalse(encounter.ledger.consume(extra, 'player'))
        self.assertFalse(encounter.ledger.consume(event, 'another-target'))

    def test_stun_keeps_other_pawn_behavior_and_occupancy(self):
        encounter, event = self.perfect_due((source(), source('other', 6, 4)))
        first, other = encounter.enemies
        other_before = other.position
        encounter.stun(first.entity_instance_id, 39)
        encounter.advance_to(132, (3, 3))
        self.assertNotEqual(other.position, other_before)
        self.assertTrue(other.active)
        self.assertEqual(len(encounter.occupied_cells), 2)

    def test_stun_refresh_is_not_additive(self):
        encounter, event = self.perfect_due()
        enemy = encounter.enemies[0]
        encounter.stun(enemy.entity_instance_id, 39)
        encounter.stun(enemy.entity_instance_id, 39)
        self.assertEqual(enemy.stun_until_tick, 99)
        encounter.advance_to(49, (3, 3))
        encounter.stun(enemy.entity_instance_id, 49)
        self.assertEqual(enemy.stun_until_tick, 109)

    def test_death_during_stun_releases_cell_and_cannot_resurrect(self):
        encounter, event = self.perfect_due()
        enemy = encounter.enemies[0]
        encounter.stun(enemy.entity_instance_id, 39)
        enemy.health.apply_damage(2, tick=39)
        encounter.deactivate(enemy.entity_instance_id)
        self.assertEqual((enemy.state, enemy.stun_until_tick), ('inactive', 0))
        self.assertFalse(encounter.stun(enemy.entity_instance_id, 39))
        self.assertEqual(encounter.advance_to(200, (3, 3)), ())
        self.assertEqual(encounter.occupied_cells, frozenset())

    def test_invalid_stun_arguments_leave_source_and_records_unchanged(self):
        encounter, event = self.perfect_due()
        enemy = encounter.enemies[0]
        for tick, duration in ((38, 60), (40, 60), (39, 0), (39, -1)):
            with self.subTest(tick=tick, duration=duration), self.assertRaises(ValueError):
                encounter.stun(enemy.entity_instance_id, tick, duration)
        for duration in (True, 1.5, '60'):
            with self.subTest(duration=duration), self.assertRaises(TypeError):
                encounter.stun(enemy.entity_instance_id, 39, duration)
        with self.assertRaises(ValueError):
            encounter.stun('unknown-source', 39)
        self.assertEqual((enemy.state, enemy.stun_until_tick), ('recovering', 0))
        self.assertEqual(encounter.ledger.outcome(event), 'parried_perfect')

    def test_paused_or_repeated_queries_do_not_reduce_stun_duration(self):
        encounter, event = self.perfect_due()
        enemy = encounter.enemies[0]
        encounter.stun(enemy.entity_instance_id, 39)
        for _ in range(100):
            self.assertEqual(encounter.advance_to(39, (3, 3)), ())
            self.assertEqual((enemy.state, enemy.stun_until_tick), ('stunned', 99))


if __name__ == '__main__':
    unittest.main()
