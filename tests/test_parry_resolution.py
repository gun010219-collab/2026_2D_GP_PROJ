"""Hit-relative parry adjudication on explicit integer ticks, without SDL."""
from dataclasses import FrozenInstanceError, replace
import unittest

from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_behaviors import PawnEncounter
from parry import Parry, ParryAttempt
from parry_resolution import grade_for_delta
from player import Player


def encounter_fixture(two=False, *, ready=True, parry=None):
    player, combat = Player(5, 1), Combat()
    parry = parry if parry is not None else Parry()
    delay = 0 if ready else 10
    enemies = [Enemy('left', 4, 2, (0, -1), delay,
                     entity_instance_id='z-left-source')]
    if two:
        enemies.append(Enemy('right', 6, 2, (0, -1), delay,
                             entity_instance_id='a-right-source'))
    encounter = PawnEncounter(enemies, combat_session_id=combat.combat_session_id,
                              stage_instance_id=combat.stage_instance_id)
    resolver = CombatResolver(player, combat, encounter, parry=parry)
    return player, combat, encounter, parry, resolver


def started_fixture(two=False):
    fixture = encounter_fixture(two)
    fixture[-1].resolve_current_tick()
    return fixture


def attempt_at(fixture, tick):
    _, combat, _, parry, resolver = fixture
    resolver.advance(tick - combat.tick)
    attempt = parry.request(combat.tick)
    return attempt, resolver.register_parry(attempt)


class HitRelativeGradeTests(unittest.TestCase):
    def test_exact_pdf_integer_tick_boundaries(self):
        for delta, grade in ((0, None), (1, 'perfect'), (7, 'perfect'),
                             (8, 'normal'), (18, 'normal'), (19, None)):
            with self.subTest(delta=delta):
                self.assertEqual(grade_for_delta(delta), grade)

    def test_nonpositive_and_late_deltas_do_not_succeed(self):
        for delta in (-100, -1, 0, 19, 100):
            with self.subTest(delta=delta):
                self.assertIsNone(grade_for_delta(delta))

    def test_noninteger_delta_is_rejected(self):
        for delta in (True, False, 7.0, '7', None):
            with self.subTest(delta=delta), self.assertRaises(TypeError):
                grade_for_delta(delta)

    def test_real_enemy_hit_obeys_all_six_boundaries(self):
        for delta, grade in ((0, None), (1, 'perfect'), (7, 'perfect'),
                             (8, 'normal'), (18, 'normal'), (19, None)):
            with self.subTest(delta=delta):
                fixture = started_fixture()
                player, combat, encounter, parry, resolver = fixture
                event = encounter.ledger.telegraphs[0]
                input_tick = event.hit_tick - delta
                # Tick 39 must remain open so delta zero is tested before hit
                # resolution, rather than after an already received attack.
                resolver.advance(input_tick - 1)
                combat.advance()
                attempt = parry.request(combat.tick)
                binding = resolver.register_parry(attempt)
                if grade is None:
                    self.assertIsNone(binding.linked_enemy_event_key)
                    self.assertEqual(resolver.parry_result(attempt).status, 'unbound')
                else:
                    self.assertEqual(binding.linked_enemy_event_key, event.key)
                    self.assertEqual(binding.adjudication_grade, grade)
                    self.assertIsNone(resolver.parry_result(attempt))
                resolver.resolve_current_tick()
                resolver.advance(event.hit_tick - combat.tick)
                self.assertEqual(player.health.current_hp, 3 if grade else 2)
                self.assertEqual(encounter.ledger.outcome(event),
                                 'parried_' + grade if grade else 'hit')
                self.assertEqual(resolver.parry_result(attempt).status, grade or 'unbound')

    def test_preview_gold_does_not_turn_eight_tick_delta_into_perfect(self):
        fixture = started_fixture()
        player, combat, encounter, parry, resolver = fixture
        attempt, binding = attempt_at(fixture, 31)
        self.assertEqual(parry.state_at(31), 'perfect_window')
        self.assertEqual(binding.adjudication_grade, 'normal')
        resolver.advance(8)
        self.assertEqual((resolver.parry_result(attempt).status, player.health.current_hp),
                         ('normal', 3))
        self.assertFalse(combat.counter_ready)

    def test_eighteen_tick_normal_succeeds_when_preview_has_just_expired(self):
        fixture = started_fixture()
        _, _, _, parry, resolver = fixture
        attempt, _ = attempt_at(fixture, 21)
        self.assertEqual(parry.state_at(39), 'inactive')
        resolver.advance(18)
        self.assertEqual(resolver.parry_result(attempt).status, 'normal')


class ParryBindingTests(unittest.TestCase):
    def test_bound_attempt_has_no_success_result_before_actual_hit(self):
        fixture = started_fixture()
        player, combat, encounter, _, resolver = fixture
        attempt, binding = attempt_at(fixture, 21)
        event = encounter.ledger.telegraphs[0]
        self.assertEqual((binding.parry_id, binding.parry_start_tick,
                          binding.expected_hit_tick), (attempt.parry_id, 21, 39))
        self.assertEqual(binding.linked_enemy_event_key, event.key)
        for _ in range(20):
            self.assertIsNone(resolver.parry_result(attempt))
            self.assertIsNone(resolver.last_parry_result)
            self.assertIs(resolver.parry_binding(attempt), binding)
        resolver.advance(17)
        self.assertEqual((combat.tick, player.health.current_hp), (38, 3))
        self.assertIsNone(resolver.parry_result(attempt))
        resolver.advance()
        result = resolver.parry_result(attempt)
        self.assertEqual((result.status, result.tick, result.enemy_event_key),
                         ('normal', 39, event.key))

    def test_unbound_is_immediate_and_spends_existing_parry_cooldown(self):
        fixture = encounter_fixture(ready=False)
        _, _, _, parry, resolver = fixture
        attempt = parry.request(0)
        binding = resolver.register_parry(attempt)
        result = resolver.parry_result(attempt)
        self.assertIsNone(binding.linked_enemy_event_key)
        self.assertEqual((result.status, result.tick, result.successful), ('unbound', 0, False))
        self.assertEqual(parry.next_parry_tick, 60)
        self.assertIsNone(parry.request(59))

    def test_unbound_does_not_attach_to_attack_created_later_in_same_tick(self):
        fixture = encounter_fixture()
        player, _, encounter, parry, resolver = fixture
        attempt = parry.request(0)
        binding = resolver.register_parry(attempt)
        resolver.resolve_current_tick()  # AI now publishes the first warning.
        event = encounter.ledger.telegraphs[0]
        self.assertIsNone(binding.linked_enemy_event_key)
        self.assertEqual(resolver.parry_result(attempt).status, 'unbound')
        resolver.advance(39)
        self.assertEqual((player.health.current_hp, encounter.ledger.outcome(event)), (2, 'hit'))
        self.assertIsNone(resolver.parry_binding(attempt).linked_enemy_event_key)

    def test_input_cell_must_be_in_fixed_warning_target(self):
        fixture = started_fixture()
        player, _, encounter, _, resolver = fixture
        resolver.advance(21)
        player.move('right')
        attempt, binding = attempt_at(fixture, 21)
        self.assertIsNone(binding.linked_enemy_event_key)
        player.move('left')
        resolver.advance(18)
        self.assertEqual(player.health.current_hp, 2)
        self.assertEqual(resolver.parry_result(attempt).status, 'unbound')

    def test_earliest_hit_is_selected_before_lower_numeric_attack_id(self):
        fixture = encounter_fixture(two=True, ready=False)
        _, _, encounter, parry, resolver = fixture
        first, second = encounter.enemies
        later = encounter.ledger.create(first.entity_instance_id, 0, 18, ((5, 1),))
        earlier = encounter.ledger.create(second.entity_instance_id, 0, 12, ((5, 1),))
        self.assertLess(later.attack_id, earlier.attack_id)
        binding = resolver.register_parry(parry.request(0))
        self.assertEqual(binding.linked_enemy_event_key, earlier.key)

    def test_equal_hit_prefers_numeric_attack_id_before_source_lexical_order(self):
        fixture = encounter_fixture(two=True, ready=False)
        _, _, encounter, parry, resolver = fixture
        first, second = encounter.enemies
        low = encounter.ledger.create(first.entity_instance_id, 0, 12, ((5, 1),))
        high = encounter.ledger.create(second.entity_instance_id, 0, 12, ((5, 1),))
        self.assertGreater(low.source_entity_instance_id, high.source_entity_instance_id)
        self.assertEqual(resolver.register_parry(parry.request(0)).linked_enemy_event_key, low.key)

    def test_full_scoped_key_breaks_an_adversarial_cross_source_numeric_tie(self):
        fixture = encounter_fixture(two=True, ready=False)
        _, _, encounter, parry, resolver = fixture
        first, second = encounter.enemies
        high = encounter.ledger.create(first.entity_instance_id, 0, 12, ((5, 1),))
        # Ordinary publication is monotonic. Force a cross-source imported-ID
        # collision to exercise the documented final deterministic tie-break.
        encounter.ledger._next_attack_id = high.attack_id
        low = encounter.ledger.create(second.entity_instance_id, 0, 12, ((5, 1),))
        self.assertLess(low.key, high.key)
        self.assertEqual(resolver.register_parry(parry.request(0)).linked_enemy_event_key, low.key)

    def test_ineligible_sources_cancelled_and_future_warnings_are_not_bound(self):
        fixture = encounter_fixture(two=True, ready=False)
        _, _, encounter, parry, resolver = fixture
        first, second = encounter.enemies
        cancelled = encounter.ledger.create(first.entity_instance_id, 0, 10, ((5, 1),))
        encounter.ledger.cancel(cancelled)
        encounter.deactivate(second.entity_instance_id)
        encounter.ledger.create(second.entity_instance_id, 0, 11, ((5, 1),))
        encounter.ledger.create(first.entity_instance_id, 1, 12, ((5, 1),))
        encounter.ledger.create('unknown-source', 0, 13, ((5, 1),))
        binding = resolver.register_parry(parry.request(0))
        self.assertIsNone(binding.linked_enemy_event_key)

    def test_repeated_registration_returns_same_link_without_rescanning(self):
        fixture = started_fixture(two=True)
        _, _, encounter, _, resolver = fixture
        attempt, binding = attempt_at(fixture, 21)
        linked = encounter.ledger.telegraphs[0]
        encounter.ledger.cancel(linked)
        resolver.advance()
        for _ in range(20):
            self.assertIs(resolver.register_parry(attempt), binding)
        self.assertEqual(resolver.parry_result(attempt).status, 'failed')
        self.assertEqual(binding.linked_enemy_event_key, linked.key)

    def test_a_second_genuine_attempt_cannot_claim_an_already_linked_event(self):
        # Short preview/cooldown isolates reservation behavior. Production
        # balance remains the default 60-tick cooldown and 18-tick preview.
        short = Parry(window_seconds=1 / 60, perfect_seconds=1 / 60,
                      cooldown_seconds=1 / 60)
        fixture = encounter_fixture(ready=False, parry=short)
        _, _, encounter, parry, resolver = fixture
        event = encounter.ledger.create(encounter.enemies[0].entity_instance_id,
                                         0, 10, ((5, 1),))
        first = parry.request(0)
        self.assertEqual(resolver.register_parry(first).linked_enemy_event_key, event.key)
        resolver.advance()
        second = parry.request(1)
        self.assertIsNotNone(second)
        self.assertIsNone(resolver.register_parry(second).linked_enemy_event_key)
        self.assertEqual(resolver.parry_result(second).status, 'unbound')
        self.assertIsNone(resolver.parry_result(first))

    def test_different_attempts_can_reserve_different_enemy_events(self):
        short = Parry(window_seconds=1 / 60, perfect_seconds=1 / 60,
                      cooldown_seconds=1 / 60)
        fixture = encounter_fixture(two=True, ready=False, parry=short)
        _, _, encounter, parry, resolver = fixture
        first, second = (encounter.ledger.create(source.entity_instance_id,
                                                  0, 10 + index, ((5, 1),))
                         for index, source in enumerate(encounter.enemies))
        first_attempt = parry.request(0)
        self.assertEqual(resolver.register_parry(first_attempt).linked_enemy_event_key, first.key)
        resolver.advance()
        second_attempt = parry.request(1)
        self.assertEqual(resolver.register_parry(second_attempt).linked_enemy_event_key, second.key)
        self.assertNotEqual(first_attempt.key, second_attempt.key)

    def test_binding_and_completed_result_are_immutable(self):
        fixture = started_fixture()
        _, _, _, _, resolver = fixture
        attempt, binding = attempt_at(fixture, 21)
        with self.assertRaises(FrozenInstanceError):
            binding.expected_hit_tick = 40
        resolver.advance(18)
        with self.assertRaises(FrozenInstanceError):
            resolver.parry_result(attempt).status = 'perfect'


class ParryAdjudicationTests(unittest.TestCase):
    def test_normal_blocks_without_stun_counter_reset_or_hit_invulnerability(self):
        fixture = started_fixture()
        player, combat, encounter, parry, resolver = fixture
        resolver.advance(21)
        attack = combat.request_attack(player)  # Empty target; next attack at 57.
        resolver.resolve_player_attack(attack)
        attempt = parry.request(21)
        resolver.register_parry(attempt)
        resolver.advance(18)
        enemy = encounter.enemies[0]
        self.assertEqual((player.health.current_hp, enemy.health.current_hp), (3, 2))
        self.assertEqual((enemy.state, enemy.stun_until_tick), ('recovering', 0))
        self.assertEqual((combat.next_attack_tick, combat.counter_ready), (57, False))
        self.assertEqual(resolver.player_invulnerable_until_tick, 0)
        self.assertIsNone(player.health.last_damage_tick)
        self.assertEqual(resolver.parry_result(attempt).status, 'normal')

    def test_one_attempt_does_not_block_second_simultaneous_attack(self):
        fixture = started_fixture(two=True)
        player, _, encounter, _, resolver = fixture
        first, second = encounter.ledger.telegraphs
        attempt, binding = attempt_at(fixture, 21)
        self.assertEqual(binding.linked_enemy_event_key, first.key)
        results = resolver.advance(18)
        self.assertEqual((player.health.current_hp, len(results)), (2, 2))
        self.assertEqual((encounter.ledger.outcome(first), encounter.ledger.outcome(second)),
                         ('parried_normal', 'hit'))
        self.assertEqual(resolver.parry_result(attempt).status, 'normal')
        self.assertFalse(encounter.ledger.consume(first, player.entity_instance_id))
        self.assertFalse(encounter.ledger.consume(first, 'other-target'))

    def test_leaving_warning_before_hit_finishes_link_as_failed(self):
        fixture = started_fixture()
        player, _, encounter, _, resolver = fixture
        event = encounter.ledger.telegraphs[0]
        attempt, _ = attempt_at(fixture, 21)
        player.move('right')
        resolver.advance(18)
        result = resolver.parry_result(attempt)
        self.assertEqual((result.status, result.reason, result.tick), ('failed', 'evaded', 39))
        self.assertEqual((player.health.current_hp, encounter.ledger.outcome(event)), (3, 'miss'))
        player.move('left')
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        resolver.advance()
        self.assertIs(resolver.parry_result(attempt), result)
        self.assertEqual(player.health.current_hp, 3)

    def test_leaving_then_returning_before_hit_preserves_original_link(self):
        fixture = started_fixture()
        player, _, _, _, resolver = fixture
        attempt, binding = attempt_at(fixture, 21)
        player.move('right')
        resolver.advance(10)
        self.assertIsNone(resolver.parry_result(attempt))
        player.move('left')
        resolver.advance(8)
        self.assertEqual((player.health.current_hp, resolver.parry_result(attempt).status),
                         (3, 'normal'))
        self.assertIs(resolver.parry_binding(attempt), binding)

    def test_cancelled_link_fails_without_reattaching_or_rewards(self):
        fixture = started_fixture(two=True)
        player, combat, encounter, _, resolver = fixture
        first, second = encounter.ledger.telegraphs
        attempt, binding = attempt_at(fixture, 32)
        encounter.ledger.cancel(first)
        resolver.resolve_current_tick()
        self.assertEqual(resolver.parry_result(attempt).status, 'failed')
        resolver.advance(7)
        self.assertEqual((player.health.current_hp, encounter.ledger.outcome(second)), (2, 'hit'))
        self.assertEqual(binding.linked_enemy_event_key, first.key)
        self.assertFalse(combat.counter_ready)
        self.assertTrue(all(enemy.stun_until_tick == 0 for enemy in encounter.enemies))

    def test_source_killed_by_player_closes_link_and_cancels_attack(self):
        fixture = started_fixture()
        player, combat, encounter, _, resolver = fixture
        enemy = encounter.enemies[0]
        event = encounter.ledger.telegraphs[0]
        attempt, _ = attempt_at(fixture, 32)
        enemy.health.apply_damage(1, tick=32)
        player.move('left')
        self.assertFalse(player.move('up', occupied=encounter.occupied_cells))
        resolver.resolve_player_attack(combat.request_attack(player))
        self.assertFalse(enemy.alive)
        self.assertEqual(resolver.parry_result(attempt).status, 'failed')
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        resolver.advance(7)
        self.assertEqual(player.health.current_hp, 3)
        self.assertFalse(combat.counter_ready)

    def test_real_prior_hit_invulnerability_prevents_parry_and_rewards(self):
        fixture = started_fixture()
        player, combat, encounter, _, resolver = fixture
        source = encounter.enemies[0]
        original = encounter.ledger.telegraphs[0]
        attempt, _ = attempt_at(fixture, 32)
        prior = encounter.ledger.create(source.entity_instance_id, 32, 35, (player.position,))
        resolver.advance(3)
        encounter.ledger.mark_due(prior, 35)
        self.assertEqual(resolver.resolve_enemy_attack(prior).amount, 1)
        self.assertEqual(resolver.player_invulnerable_until_tick, 83)
        resolver.advance(4)
        self.assertEqual((player.health.current_hp, encounter.ledger.outcome(original)),
                         (2, 'invulnerable'))
        result = resolver.parry_result(attempt)
        self.assertEqual((result.status, result.reason), ('failed', 'invulnerable'))
        self.assertFalse(combat.counter_ready)
        self.assertEqual(source.stun_until_tick, 0)

    def test_success_is_recorded_once_despite_attempt_and_event_replays(self):
        fixture = started_fixture()
        player, combat, encounter, _, resolver = fixture
        event = encounter.ledger.telegraphs[0]
        attempt, binding = attempt_at(fixture, 32)
        resolver.advance(7)
        result = resolver.parry_result(attempt)
        self.assertEqual(result.status, 'perfect')
        self.assertEqual((player.health.current_hp, encounter.enemies[0].stun_until_tick,
                          combat.pending_attack_bonus), (3, 99, 2))
        for _ in range(20):
            self.assertIs(resolver.register_parry(attempt), binding)
            self.assertIsNone(resolver.resolve_enemy_attack(event))
            self.assertEqual(resolver.resolve_current_tick(), ())
            self.assertIs(resolver.parry_result(attempt), result)
            self.assertIs(resolver.last_parry_result, result)
        self.assertEqual((encounter.enemies[0].stun_until_tick, combat.pending_attack_bonus,
                          resolver.player_invulnerable_until_tick), (99, 2, 0))
        self.assertEqual(encounter.ledger.outcome(event), 'parried_perfect')

    def test_multiple_elapsed_ticks_match_sequential_adjudication(self):
        def trace(chunks):
            fixture = started_fixture()
            player, combat, encounter, _, resolver = fixture
            attempt, _ = attempt_at(fixture, 21)
            for count in chunks:
                resolver.advance(count)
            return (combat.tick, player.health.current_hp,
                    resolver.parry_result(attempt).status,
                    encounter.enemies[0].state, combat.counter_ready)
        self.assertEqual(trace([1] * 18), trace([8, 8, 2]))

    def test_later_success_does_not_overwrite_previous_attempt_result(self):
        fixture = started_fixture()
        _, _, encounter, _, resolver = fixture
        first_attempt, _ = attempt_at(fixture, 21)
        resolver.advance(18)
        first_result = resolver.parry_result(first_attempt)
        second_attempt, second_binding = attempt_at(fixture, 125)
        self.assertEqual(second_binding.expected_hit_tick, 132)
        resolver.advance(7)
        self.assertEqual(resolver.parry_result(second_attempt).status, 'perfect')
        self.assertIs(resolver.parry_result(first_attempt), first_result)
        self.assertEqual((first_result.status, first_result.tick), ('normal', 39))
        self.assertIs(resolver.last_parry_result, resolver.parry_result(second_attempt))
        self.assertEqual(encounter.enemies[0].stun_until_tick, 192)

    def test_unsynchronized_direct_perfect_cannot_partially_consume_success(self):
        fixture = started_fixture()
        _, combat, encounter, _, resolver = fixture
        event = encounter.ledger.telegraphs[0]
        attempt, _ = attempt_at(fixture, 32)
        resolver.advance(6)
        combat.advance()  # Caller has not run the encounter's tick 39.
        encounter.ledger.mark_due(event, 39)
        with self.assertRaises(ValueError):
            resolver.resolve_enemy_attack(event)
        self.assertEqual(encounter.ledger.state(event), 'due')
        self.assertIsNone(encounter.ledger.outcome(event))
        self.assertIsNone(resolver.parry_result(attempt))
        self.assertFalse(combat.counter_ready)
        self.assertEqual(encounter.enemies[0].stun_until_tick, 0)


class ParryAuthenticityTests(unittest.TestCase):
    def test_forged_unscoped_and_foreign_attempts_are_rejected_without_binding(self):
        fixture = started_fixture()
        _, _, _, parry, resolver = fixture
        resolver.advance(21)
        genuine = parry.request(21)
        forged = (replace(genuine, parry_id=99),
                  replace(genuine, perfect_end_tick=genuine.perfect_end_tick + 1),
                  ParryAttempt(1, 21, 29, 39), Parry().request(21), None, object())
        for attempt in forged:
            with self.subTest(attempt=attempt), self.assertRaises(ValueError):
                resolver.register_parry(attempt)
        self.assertIsNone(resolver.parry_binding(genuine))
        self.assertIsNone(resolver.last_parry_result)
        self.assertIsNotNone(resolver.register_parry(genuine).linked_enemy_event_key)

    def test_late_first_attempt_delivery_is_rejected_without_claiming_event(self):
        fixture = started_fixture()
        _, _, _, parry, resolver = fixture
        resolver.advance(21)
        attempt = parry.request(21)
        resolver.advance()
        with self.assertRaises(ValueError):
            resolver.register_parry(attempt)
        self.assertIsNone(resolver.parry_binding(attempt))
        self.assertIsNone(resolver.parry_result(attempt))

    def test_dead_player_attempt_is_rejected_before_any_event_reservation(self):
        fixture = started_fixture()
        player, _, _, parry, resolver = fixture
        resolver.advance(21)
        player.health.apply_damage(3, tick=21)
        attempt = parry.request(21)
        with self.assertRaises(ValueError):
            resolver.register_parry(attempt)
        self.assertIsNone(resolver.parry_binding(attempt))
        self.assertIsNone(resolver.parry_result(attempt))

    def test_previous_combat_attempt_id_one_is_not_new_attempt_id_one(self):
        old = started_fixture()
        attempt, _ = attempt_at(old, 21)
        new = started_fixture()
        _, _, _, parry, resolver = new
        resolver.advance(21)
        fresh = parry.request(21)
        self.assertEqual((attempt.parry_id, fresh.parry_id), (1, 1))
        self.assertNotEqual(attempt.key, fresh.key)
        with self.assertRaises(ValueError):
            resolver.register_parry(attempt)
        self.assertIsNotNone(resolver.register_parry(fresh).linked_enemy_event_key)

    def test_shared_parry_new_stage_rejects_old_attempt_at_same_input_tick(self):
        fixture = started_fixture()
        player, combat, _, parry, resolver = fixture
        resolver.advance(21)
        old = parry.request(21)
        new_encounter = PawnEncounter((Enemy('new', 4, 2, (0, -1), 0),),
                                      start_tick=21,
                                      combat_session_id=combat.combat_session_id)
        new_resolver = CombatResolver(player, combat, new_encounter, parry=parry)
        self.assertFalse(parry.owns(old))
        self.assertIsNone(parry.last_attempt)
        with self.assertRaises(ValueError):
            new_resolver.register_parry(old)
        self.assertIsNone(new_resolver.parry_binding(old))
        self.assertIsNone(new_resolver.last_parry_result)

    def test_rebinding_parry_stage_after_link_fails_and_allows_regular_damage(self):
        fixture = started_fixture()
        player, combat, encounter, parry, resolver = fixture
        event = encounter.ledger.telegraphs[0]
        attempt, _ = attempt_at(fixture, 32)
        parry.bind_stage('replacement-stage')
        resolver.advance(7)
        self.assertEqual((resolver.parry_result(attempt).status, player.health.current_hp),
                         ('failed', 2))
        self.assertEqual(encounter.ledger.outcome(event), 'hit')
        self.assertFalse(combat.counter_ready)
        self.assertEqual(encounter.enemies[0].stun_until_tick, 0)

    def test_replacing_parry_model_after_link_fails_and_allows_regular_damage(self):
        fixture = started_fixture()
        player, combat, encounter, _, resolver = fixture
        event = encounter.ledger.telegraphs[0]
        attempt, _ = attempt_at(fixture, 32)
        resolver.parry = Parry()
        resolver.advance(7)
        self.assertEqual((resolver.parry_result(attempt).status, player.health.current_hp),
                         ('failed', 2))
        self.assertEqual(encounter.ledger.outcome(event), 'hit')
        self.assertFalse(combat.counter_ready)


if __name__ == '__main__':
    unittest.main()
