from dataclasses import replace
import unittest

from combat import AttackEvent, Combat
from combat_resolution import CombatResolver
from config import FIXED_TIME_STEP, PAWN_ATTACK_DAMAGE, PLAYER_ATTACK_DAMAGE
from enemy import Enemy
from enemy_behaviors import PawnEncounter
from health import Health
from parry import Parry
from player import Player
from simulation_clock import SimulationClock


def pawn(name='pawn', col=5, row=2, delay=10):
    return Enemy(name, col, row, (0, -1), delay)


def setup(enemies=None, player=None, combat=None):
    player = player if player is not None else Player(5, 1)
    combat = combat if combat is not None else Combat()
    encounter = PawnEncounter((pawn(),) if enemies is None else enemies,
                              start_tick=combat.tick)
    resolver = CombatResolver(player, combat, encounter)
    return player, combat, encounter, resolver


def attack_setup(two=False):
    enemies = [pawn('left', 4, 2, 0)]
    if two:
        enemies.append(pawn('right', 6, 2, 0))
    fixture = setup(tuple(enemies))
    fixture[3].resolve_current_tick()
    return fixture


class PlayerDamageTests(unittest.TestCase):
    def test_pdf_baseline_damage_and_space_hit(self):
        player, combat, encounter, resolver = setup()
        self.assertEqual((PLAYER_ATTACK_DAMAGE, PAWN_ATTACK_DAMAGE), (1, 1))
        event = combat.request_attack(player)
        result = resolver.resolve_player_attack(event)
        self.assertEqual(encounter.enemies[0].health.current_hp, 1)
        self.assertEqual((result.amount, result.hp_before, result.hp_after, result.tick), (1, 2, 1, 0))
        self.assertEqual(result.attack_key, event.key)
        self.assertEqual(combat.attack_state(event), 'resolved')

    def test_empty_target_is_finished_and_never_hits_later_arrival(self):
        player, combat, encounter, resolver = setup((pawn(col=6),))
        event = combat.request_attack(player)
        self.assertIsNone(resolver.resolve_player_attack(event))
        encounter.enemies[0].col = 5
        self.assertIsNone(resolver.resolve_player_attack(event))
        self.assertEqual(encounter.enemies[0].health.current_hp, 2)

    def test_player_movement_does_not_change_fixed_attack_target(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        player.move('right')
        self.assertEqual(event.target_cell, (5, 2))
        self.assertIsNotNone(resolver.resolve_player_attack(event))
        self.assertEqual(encounter.enemies[0].health.current_hp, 1)

    def test_repeated_event_during_all_nine_effect_ticks_damages_once(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        self.assertIsNotNone(resolver.resolve_player_attack(event))
        for _ in range(9):
            self.assertIsNone(resolver.resolve_player_attack(event))
            resolver.advance()
        self.assertEqual(encounter.enemies[0].health.current_hp, 1)
        self.assertIsNone(combat.active_attack)

    def test_late_first_delivery_is_closed_without_retroactive_hit(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        resolver.advance()
        self.assertIsNone(resolver.resolve_player_attack(event))
        self.assertEqual((encounter.enemies[0].health.current_hp, combat.attack_state(event)), (2, 'resolved'))

    def test_distinct_attack_ids_can_kill_at_exact_cooldown(self):
        player, combat, encounter, resolver = setup()
        first = combat.request_attack(player)
        resolver.resolve_player_attack(first)
        resolver.advance(36)
        second = combat.request_attack(player)
        self.assertNotEqual(first.key, second.key)
        self.assertIsNotNone(resolver.resolve_player_attack(second))
        enemy = encounter.enemies[0]
        self.assertEqual((enemy.health.current_hp, enemy.state, enemy.active), (0, 'inactive', False))
        self.assertNotIn(enemy.position, encounter.occupied_cells)

    def test_inactive_pawn_cannot_be_damaged(self):
        player, combat, encounter, resolver = setup()
        encounter.deactivate(encounter.enemies[0].entity_instance_id)
        event = combat.request_attack(player)
        self.assertIsNone(resolver.resolve_player_attack(event))
        self.assertEqual(encounter.enemies[0].health.current_hp, 2)

    def test_two_pawns_have_independent_hp_and_receipts(self):
        player, combat, encounter, resolver = setup((pawn('up'), pawn('right', 6, 1)))
        event = combat.request_attack(player)
        resolver.resolve_player_attack(event)
        self.assertEqual([e.health.current_hp for e in encounter.enemies], [1, 2])
        resolver.advance(36)
        player.move('right', occupied=encounter.occupied_cells)
        resolver.resolve_player_attack(combat.request_attack(player))
        self.assertEqual([e.health.current_hp for e in encounter.enemies], [1, 1])

    def test_forged_payload_and_numeric_id_only_event_are_rejected(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        for candidate in (replace(event, target_cell=(6, 1), facing='right'), replace(event, attack_id=99),
                          AttackEvent(event.attack_id, event.origin_cell, event.facing,
                                      event.target_cell, event.start_tick), None, object()):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                resolver.resolve_player_attack(candidate)
        self.assertEqual((encounter.enemies[0].health.current_hp, combat.attack_state(event)), (2, 'pending'))
        self.assertIsNotNone(resolver.resolve_player_attack(event))

    def test_numeric_ids_are_scoped_to_combat_and_stage_instances(self):
        p1, c1, e1, r1 = setup()
        old = c1.request_attack(p1)
        r1.resolve_player_attack(old)
        p2, c2, e2, r2 = setup()
        new = c2.request_attack(p2)
        self.assertEqual((old.attack_id, new.attack_id), (1, 1))
        self.assertNotEqual(old.key, new.key)
        with self.assertRaises(ValueError):
            r2.resolve_player_attack(old)
        self.assertIsNotNone(r2.resolve_player_attack(new))

    def test_restart_same_combat_rejects_previous_stage_event(self):
        player, combat, encounter, resolver = setup()
        old = combat.request_attack(player)
        restarted = PawnEncounter((pawn('new'),), start_tick=combat.tick)
        new_resolver = CombatResolver(player, combat, restarted)
        with self.assertRaises(ValueError):
            new_resolver.resolve_player_attack(old)
        self.assertEqual(restarted.enemies[0].health.current_hp, 2)

    def test_attack_from_different_player_instance_is_rejected_without_receipt(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(Player(5, 1))
        with self.assertRaises(ValueError):
            resolver.resolve_player_attack(event)
        self.assertEqual(combat.attack_state(event), 'pending')

    def test_invalid_damage_configuration_fails_before_consuming(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        resolver.player_damage = -1
        with self.assertRaises(ValueError):
            resolver.resolve_player_attack(event)
        self.assertEqual((encounter.enemies[0].health.current_hp, combat.attack_state(event)), (2, 'pending'))
        resolver.player_damage = 1
        self.assertIsNotNone(resolver.resolve_player_attack(event))

    def test_invalid_enemy_reference_fails_before_consuming(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        original = encounter.enemies
        encounter.enemies = (pawn('foreign'),)
        with self.assertRaises(ValueError):
            resolver.resolve_player_attack(event)
        self.assertEqual(combat.attack_state(event), 'pending')
        encounter.enemies = original
        self.assertIsNotNone(resolver.resolve_player_attack(event))

    def test_player_ledger_claims_same_event_per_target_once(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        self.assertTrue(combat.consume_attack(event, 'target-a'))
        self.assertFalse(combat.consume_attack(event, 'target-a'))
        self.assertTrue(combat.consume_attack(event, 'target-b'))
        self.assertTrue(combat.finish_attack(event))
        self.assertFalse(combat.consume_attack(event, 'target-c'))

    def test_attack_event_strict_identity_and_snapshot_validation(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        for changes in ({'attack_id': True}, {'attack_id': 0}, {'attack_id': 1.0},
                        {'origin_cell': (True, 1)}, {'target_cell': (5, 3)},
                        {'facing': 'unknown'}, {'source_entity_instance_id': ''},
                        {'start_tick': -1}, {'target_cell': (5, 10)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(event, **changes)
        with self.assertRaises(TypeError):
            replace(event, start_tick=True)
        self.assertEqual(combat.attack_state(event), 'pending')

    def test_invalid_entity_cell_rejected_before_receipt(self):
        player, combat, encounter, resolver = setup()
        event = combat.request_attack(player)
        encounter.enemies[0].col = True
        with self.assertRaises(ValueError):
            resolver.resolve_player_attack(event)
        self.assertEqual(combat.attack_state(event), 'pending')
        encounter.enemies[0].col = 5
        self.assertIsNotNone(resolver.resolve_player_attack(event))


class EnemyDamageTests(unittest.TestCase):
    def test_no_damage_before_hit_and_exact_hit_damage(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        resolver.advance(38)
        self.assertEqual(player.health.current_hp, 3)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        results = resolver.advance()
        self.assertEqual((combat.tick, player.health.current_hp, len(results)), (39, 2, 1))
        self.assertEqual((encounter.ledger.state(event), encounter.ledger.outcome(event)), ('resolved', 'hit'))
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertFalse(encounter.ledger.consume(event, player.entity_instance_id))

    def test_warning_target_is_the_only_damage_cell_and_dodge_finishes_event(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        self.assertEqual(event.target_cells, ((5, 1),))
        resolver.advance(38)
        player.move('right', occupied=encounter.occupied_cells)
        self.assertEqual(resolver.advance(), ())
        self.assertEqual((player.health.current_hp, encounter.ledger.outcome(event)), (3, 'miss'))
        player.move('left')
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        resolver.advance()
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(player.health.current_hp, 3)

    def test_move_into_other_diagonal_does_not_expand_fixed_warning(self):
        player = Player(3, 3)
        player, combat, encounter, resolver = setup((pawn('source', 4, 4, 0),), player)
        resolver.resolve_current_tick()
        event = encounter.ledger.telegraphs[0]
        player.move('right')
        player.move('right')
        resolver.advance(39)
        self.assertEqual((event.target_cells, player.position, player.health.current_hp), (((3, 3),), (5, 3), 3))

    def test_cancelled_attack_cannot_damage(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        encounter.ledger.cancel(event)
        self.assertEqual(resolver.advance(39), ())
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(player.health.current_hp, 3)

    def test_lethal_player_hit_cancels_source_warning_and_stops_ai(self):
        player, combat, encounter, resolver = attack_setup()
        enemy = encounter.enemies[0]
        event = encounter.ledger.telegraphs[0]
        enemy.health.apply_damage(1, tick=0)
        player.move('left')
        player.move('up', occupied=encounter.occupied_cells)  # Face the occupied Pawn without entering it.
        attack = combat.request_attack(player)
        resolver.resolve_player_attack(attack)
        self.assertEqual((enemy.health.current_hp, enemy.state, enemy.active), (0, 'inactive', False))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        before = enemy.position
        resolver.advance(150)
        self.assertEqual((enemy.position, player.health.current_hp), (before, 3))
        self.assertEqual(encounter.occupied_cells, frozenset())

    def test_lethal_player_hit_at_due_tick_precedes_enemy_ai(self):
        player, combat, encounter, resolver = attack_setup()
        enemy = encounter.enemies[0]
        event = encounter.ledger.telegraphs[0]
        enemy.health.apply_damage(1, tick=0)
        resolver.advance(38)
        combat.advance()  # Open tick 39, then process current input before AI.
        player.move('left')
        player.move('up', occupied=encounter.occupied_cells)
        resolver.resolve_player_attack(combat.request_attack(player))
        resolver.resolve_current_tick()
        self.assertEqual((combat.tick, player.health.current_hp, enemy.alive), (39, 3, False))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')

    def test_dead_source_cancels_pending_due_event(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        resolver.advance(38)
        combat.advance()
        encounter.advance_to(39, player.position)
        encounter.enemies[0].health.apply_damage(2, tick=39)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual((encounter.ledger.state(event), player.health.current_hp), ('cancelled', 3))

    def test_same_tick_multiple_attacks_obey_player_invulnerability(self):
        player, combat, encounter, resolver = attack_setup(two=True)
        first, second = encounter.ledger.telegraphs
        results = resolver.advance(39)
        self.assertEqual((len(results), player.health.current_hp), (1, 2))
        self.assertEqual((encounter.ledger.outcome(first), encounter.ledger.outcome(second)), ('hit', 'invulnerable'))
        self.assertEqual((encounter.ledger.state(first), encounter.ledger.state(second)), ('resolved', 'resolved'))
        self.assertEqual(resolver.player_invulnerable_until_tick, 87)
        self.assertFalse(encounter.ledger.consume(second, player.entity_instance_id))
        self.assertIsNone(resolver.resolve_enemy_attack(second))
        self.assertEqual(player.health.last_damage_tick, 39)

    def test_invulnerability_is_end_exclusive_at_48_ticks(self):
        player, combat, encounter, resolver = attack_setup()
        source = encounter.enemies[0]
        resolver.advance(39)
        self.assertEqual(resolver.player_invulnerability_ticks, 48)
        resolver.advance(47)
        event = encounter.ledger.create(source.entity_instance_id, 85, 86, (player.position,))
        encounter.ledger.mark_due(event, 86)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual((player.health.current_hp, encounter.ledger.outcome(event)), (2, 'invulnerable'))
        self.assertEqual(encounter.ledger.state(event), 'resolved')
        resolver.advance()
        allowed = encounter.ledger.create(source.entity_instance_id, 86, 87, (player.position,))
        encounter.ledger.mark_due(allowed, 87)
        self.assertIsNotNone(resolver.resolve_enemy_attack(allowed))
        self.assertEqual((player.health.current_hp, player.health.last_damage_tick), (1, 87))
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual((player.health.current_hp, player.health.last_damage_tick), (1, 87))

    def test_paused_wall_time_preserves_active_invulnerability_until_ticks_resume(self):
        # Native Pawn schedules hit at39 and87, exactly 48 combat ticks apart.
        player, combat, encounter, resolver = setup((pawn('first', 4, 2, 0),
                                                    pawn('second', 6, 2, .8)))
        resolver.resolve_current_tick()
        resolver.advance(39)
        clock = SimulationClock()
        for _ in range(3):
            resolver.advance(clock.advance(60.0, paused=True))
        self.assertEqual((combat.tick, player.health.current_hp, player.health.last_damage_tick), (39, 2, 39))
        self.assertEqual(resolver.player_invulnerable_until_tick, 87)
        for _ in range(47):
            resolver.advance(clock.advance(FIXED_TIME_STEP))
        self.assertEqual((combat.tick, player.health.current_hp), (86, 2))
        results = resolver.advance(clock.advance(FIXED_TIME_STEP))
        self.assertEqual((combat.tick, player.health.current_hp, player.health.last_damage_tick), (87, 1, 87))
        self.assertEqual([result.amount for result in results], [1])

    def test_invulnerability_counts_simulation_ticks_instead_of_render_frames(self):
        player, combat, encounter, resolver = setup((pawn('first', 4, 2, 0),
                                                    pawn('second', 6, 2, .8)))
        resolver.resolve_current_tick()
        resolver.advance(39)
        clock = SimulationClock()
        # At120 render frames/s, 95 frames advance only47 complete combat ticks.
        # The second Pawn must still wait until tick87 rather than frame48.
        for _ in range(95):
            resolver.advance(clock.advance(FIXED_TIME_STEP / 2))
        self.assertEqual((combat.tick, player.health.current_hp, player.health.last_damage_tick), (86, 2, 39))
        results = resolver.advance(clock.advance(FIXED_TIME_STEP / 2))
        self.assertEqual((combat.tick, player.health.current_hp, player.health.last_damage_tick), (87, 1, 87))
        self.assertEqual(len(results), 1)

    def test_delayed_first_due_delivery_expires_instead_of_hitting(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        combat.advance(40)
        encounter.advance_to(40, player.position)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual((player.health.current_hp, encounter.ledger.outcome(event)), (3, 'expired'))

    def test_foreign_stage_and_changed_payload_are_rejected(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        other = attack_setup()[2].ledger.telegraphs[0]
        for candidate in (other, replace(event, target_cells=((6, 1),)), object(), None):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                resolver.resolve_enemy_attack(candidate)
        self.assertEqual(encounter.ledger.state(event), 'telegraph')
        self.assertEqual(player.health.current_hp, 3)

    def test_invalid_source_is_not_consumed_or_finished(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.create('foreign-source', 0, 1, (player.position,))
        encounter.ledger.mark_due(event, 1)
        combat.advance()
        with self.assertRaises(ValueError):
            resolver.resolve_enemy_attack(event)
        self.assertEqual((encounter.ledger.state(event), player.health.current_hp), ('due', 3))

    def test_no_parry_window_grants_implicit_damage_immunity(self):
        player, combat, encounter, resolver = attack_setup()
        parry = Parry()
        resolver.advance(38)
        parry.request(combat.tick)
        resolver.advance()
        self.assertTrue(parry.active_at(combat.tick))
        self.assertEqual(player.health.current_hp, 2)

    def test_death_clamps_hp_and_freezes_future_combat_ticks(self):
        player, combat, encounter, resolver = attack_setup()
        resolver.advance(225)  # Hits at 39,132,225; each is outside 48-tick immunity.
        self.assertEqual((player.health.current_hp, player.alive, combat.tick), (0, False, 225))
        before = combat.tick, encounter.tick, encounter.enemies[0].position
        self.assertEqual(resolver.advance(100), ())
        self.assertEqual((combat.tick, encounter.tick, encounter.enemies[0].position), before)
        self.assertIsNone(combat.request_attack(player))
        self.assertFalse(player.move('up'))

    def test_sequential_and_eight_tick_batches_have_identical_results(self):
        def trace(chunks):
            player, combat, encounter, resolver = attack_setup(two=True)
            results = []
            for count in chunks:
                results.extend(resolver.advance(count))
            return [(result.tick, result.amount, result.hp_after) for result in results], \
                player.health.current_hp, combat.tick, [e.state for e in encounter.enemies]
        self.assertEqual(trace([1] * 160), trace([8] * 20))

    def test_repeated_current_tick_resolution_is_read_only(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        for _ in range(100):
            self.assertEqual(resolver.resolve_current_tick(), ())
        self.assertEqual((player.health.current_hp, encounter.ledger.state(event)), (3, 'telegraph'))

    def test_missing_tick_is_rejected_instead_of_using_current_position_for_history(self):
        player, combat, encounter, resolver = attack_setup()
        combat.advance(2)
        with self.assertRaises(ValueError):
            resolver.resolve_current_tick()
        self.assertEqual(player.health.current_hp, 3)

    def test_invalid_step_counts_do_not_advance(self):
        player, combat, encounter, resolver = attack_setup()
        for value in (True, 1.5, '1', None):
            with self.subTest(value=value), self.assertRaises(TypeError):
                resolver.advance(value)
        with self.assertRaises(ValueError):
            resolver.advance(-1)
        self.assertEqual((combat.tick, encounter.tick), (0, 0))

    def test_zero_advance_settles_pending_initial_tick_before_first_catchup(self):
        player, combat, encounter, resolver = setup((pawn('source', 4, 2, 0),))
        self.assertEqual((combat.tick, encounter.tick), (0, -1))
        self.assertEqual(resolver.advance(0), ())
        self.assertEqual((combat.tick, encounter.tick), (0, 0))
        combat.advance()
        self.assertEqual(resolver.resolve_current_tick(), ())
        self.assertEqual((combat.tick, encounter.tick), (1, 1))

    def test_source_death_preserves_already_resolved_outcomes_and_receipts(self):
        player, combat, encounter, resolver = attack_setup()
        event = encounter.ledger.telegraphs[0]
        resolver.advance(39)
        encounter.deactivate(encounter.enemies[0].entity_instance_id)
        self.assertEqual((encounter.ledger.state(event), encounter.ledger.outcome(event)), ('resolved', 'hit'))
        self.assertFalse(encounter.ledger.consume(event, 'new-target'))


if __name__ == '__main__':
    unittest.main()
