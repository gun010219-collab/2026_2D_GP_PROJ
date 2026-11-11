"""Real Rook/Pawn resolution: integer time, immutable paths and one ledger."""
from dataclasses import replace
import hashlib
import json
import unittest
from unittest.mock import Mock

from board import tile_bounds
from combat import Combat
from combat_resolution import CombatResolver
from config import TILE_SIZE
from enemy import Enemy, load_stage1_enemies
from enemy_attack_renderer import EnemyAttackRenderer
from enemy_behaviors import EnemyEncounter, PawnEncounter
from enemy_factory import create_stage_enemies
from enemy_renderer import EnemyRenderer
from parry import Parry
from player import Player
from stage_manager import StageCatalog


def rook(name='r', col=1, row=1, delay=0):
    return Enemy(name, col, row, None, delay, kind='rook')


def fixture(enemies=None, player=None):
    player = player if player is not None else Player(7, 1)
    combat, parry = Combat(), Parry()
    encounter = EnemyEncounter((rook(),) if enemies is None else enemies,
                               combat_session_id=combat.combat_session_id,
                               stage_instance_id=combat.stage_instance_id)
    resolver = CombatResolver(player, combat, encounter, parry=parry)
    resolver.resolve_current_tick()
    return player, combat, parry, encounter, resolver


def parry_at(parts, tick):
    player, combat, parry, encounter, resolver = parts
    resolver.advance(tick - combat.tick)
    attempt = parry.request(combat.tick)
    resolver.register_parry(attempt)
    return attempt


class RookCombatTests(unittest.TestCase):
    def test_actual_rook_parry_boundaries_zero_one_seven_eight_eighteen_nineteen(self):
        for delta, expected in ((0, 'unbound'), (1, 'perfect'), (7, 'perfect'),
                                (8, 'normal'), (18, 'normal'), (19, 'unbound')):
            with self.subTest(delta=delta):
                parts = fixture()
                player, combat, parry, encounter, resolver = parts
                attempt = parry_at(parts, 48 - delta)
                resolver.advance(delta)
                self.assertEqual(resolver.parry_result(attempt).status, expected)
                self.assertEqual(player.health.current_hp, 2 if expected == 'unbound' else 3)
                self.assertEqual(combat.counter_ready, expected == 'perfect')

    def test_parry_outside_path_cannot_bind_later_when_player_returns(self):
        player, combat, parry, encounter, resolver = fixture()
        resolver.advance(41)
        player.move('up', encounter.occupied_cells)
        attempt = parry.request(combat.tick)
        resolver.register_parry(attempt)
        player.move('down', encounter.occupied_cells)
        resolver.advance(7)
        self.assertEqual((resolver.parry_result(attempt).status, player.health.current_hp), ('unbound', 2))
        self.assertFalse(combat.counter_ready)

    def test_exact_48_tick_hit_once_stops_before_player_and_recovers_90(self):
        player, combat, parry, encounter, resolver = fixture()
        source = encounter.enemies[0]
        event = source.current_attack
        resolver.advance(47)
        self.assertEqual((player.health.current_hp, source.position), (3, (1, 1)))
        results = resolver.advance(1)
        self.assertEqual(len(results), 1)
        self.assertEqual((results[0].amount, results[0].tick), (1, 48))
        self.assertEqual((player.health.current_hp, source.position, source.next_action_tick),
                         (2, (6, 1), 138))
        self.assertEqual(encounter.ledger.outcome(event), 'hit')
        for _ in range(10):
            self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual((player.health.current_hp, source.position), (2, (6, 1)))
        resolver.advance(89)
        self.assertEqual((combat.tick, source.state), (137, 'recovering'))
        resolver.advance(1)
        self.assertEqual((source.state, source.current_attack.start_tick), ('telegraph', 138))
        self.assertNotEqual(source.current_attack.key, event.key)

    def test_evade_dash_moves_to_original_booked_destination_not_new_player_cell(self):
        player, combat, parry, encounter, resolver = fixture()
        event = encounter.enemies[0].current_attack
        player.move('up', encounter.occupied_cells)
        resolver.advance(48)
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (7, 1)))
        self.assertEqual(encounter.ledger.outcome(event), 'miss')
        player.move('left', encounter.occupied_cells)
        player.move('down', encounter.occupied_cells)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(player.health.current_hp, 3)

    def test_player_entering_intermediate_warned_cell_is_hit_and_not_overlapped(self):
        player, combat, parry, encounter, resolver = fixture()
        for _ in range(3):
            player.move('left', encounter.occupied_cells)
        resolver.advance(48)
        self.assertEqual((player.position, player.health.current_hp, encounter.enemies[0].position),
                         ((4, 1), 2, (3, 1)))

    def test_player_next_to_origin_stops_dash_at_origin(self):
        player, combat, parry, encounter, resolver = fixture(player=Player(2, 1))
        resolver.advance(48)
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (2, (1, 1)))

    def test_all_four_dash_directions_finish_inside_board_before_player(self):
        for origin, target, stop in [((4, 1), (4, 7), (4, 6)), ((4, 7), (4, 1), (4, 2)),
                                     ((1, 4), (7, 4), (6, 4)), ((7, 4), (1, 4), (2, 4))]:
            with self.subTest(origin=origin):
                parts = fixture((rook(col=origin[0], row=origin[1]),), Player(*target))
                parts[-1].advance(48)
                self.assertEqual(parts[-2].enemies[0].position, stop)

    def test_normal_parry_no_damage_no_rewards_and_dash_stops_before_player(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        attempt = parry_at(parts, 30)  # delta 18
        resolver.advance(18)
        self.assertEqual(resolver.parry_result(attempt).status, 'normal')
        self.assertEqual(encounter.ledger.outcome(event), 'parried_normal')
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (6, 1)))
        self.assertFalse(combat.counter_ready)
        self.assertEqual(resolver.player_invulnerable_until_tick, 0)
        self.assertEqual(encounter.enemies[0].state, 'recovering')

    def test_perfect_stuns_only_source_at_origin_resets_cooldown_rewards_once(self):
        other = Enemy('p', 9, 9, (0, -1), 10)
        parts = fixture((rook(), other))
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        resolver.advance(41)
        old = combat.request_attack(player)
        resolver.resolve_player_attack(old)  # miss, cooldown to 77
        self.assertEqual(combat.next_attack_tick, 77)
        attempt = parry.request(combat.tick)
        resolver.register_parry(attempt)  # delta 7
        resolver.advance(7)
        self.assertEqual((resolver.parry_result(attempt).status, player.health.current_hp), ('perfect', 3))
        source = encounter.enemies[0]
        self.assertEqual((source.position, source.state, source.stun_until_tick), ((1, 1), 'stunned', 108))
        self.assertNotEqual(other.state, 'stunned')
        self.assertEqual((combat.next_attack_tick, combat.pending_attack_bonus), (48, 2))
        fresh = combat.request_attack(player)
        resolver.resolve_player_attack(fresh)
        self.assertEqual((fresh.damage_bonus, combat.pending_attack_bonus), (2, 0))
        for _ in range(10):
            self.assertIsNone(resolver.resolve_enemy_attack(event))
            resolver.register_parry(attempt)
        self.assertEqual((combat.pending_attack_bonus, source.stun_until_tick), (0, 108))
        self.assertEqual(encounter.ledger.outcome(event), 'parried_perfect')
        resolver.advance(59)
        self.assertEqual((combat.tick, source.state, source.position), (107, 'stunned', (1, 1)))
        resolver.advance(1)
        self.assertEqual((source.state, source.current_attack.start_tick), ('telegraph', 108))

    def test_perfect_next_attack_three_damage_to_rook_then_base_one_kills(self):
        parts = fixture(player=Player(2, 1, 'left'))
        player, combat, parry, encounter, resolver = parts
        parry_at(parts, 41)
        resolver.advance(7)
        source = encounter.enemies[0]
        event = combat.request_attack(player)
        result = resolver.resolve_player_attack(event)
        self.assertEqual((result.amount, source.health.current_hp, combat.pending_attack_bonus), (3, 1, 0))
        self.assertIsNone(resolver.resolve_player_attack(event))
        resolver.advance(36)
        event2 = combat.request_attack(player)
        self.assertEqual(event2.damage_bonus, 0)
        self.assertEqual(resolver.resolve_player_attack(event2).amount, 1)
        self.assertFalse(source.active)

    def test_invalid_late_parry_does_not_retroactively_block(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        resolver.advance(48)
        attempt = parry.request(combat.tick)
        binding = resolver.register_parry(attempt)
        self.assertIsNone(binding.linked_enemy_event_key)
        self.assertEqual(resolver.parry_result(attempt).status, 'unbound')
        self.assertEqual(player.health.current_hp, 2)

    def test_evading_linked_attack_does_not_earn_reward(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        attempt = parry_at(parts, 41)
        player.move('up', encounter.occupied_cells)
        resolver.advance(7)
        self.assertEqual((player.health.current_hp, resolver.parry_result(attempt).reason), (3, 'evaded'))
        self.assertFalse(combat.counter_ready)

    def test_hit_tick_input_movement_precedes_damage(self):
        player, combat, parry, encounter, resolver = fixture()
        resolver.advance(47)
        combat.advance()  # main's tick-boundary input before AI/damage
        player.move('up', encounter.occupied_cells)
        resolver.resolve_current_tick()
        self.assertEqual(player.health.current_hp, 3)
        self.assertEqual(encounter.enemies[0].position, (7, 1))

    def test_fatal_player_attack_on_due_tick_cancels_rook_first(self):
        parts = fixture(player=Player(2, 1, 'left'))
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        encounter.enemies[0].health.apply_damage(3, tick=0)
        resolver.advance(47)
        combat.advance()
        resolver.resolve_player_attack(combat.request_attack(player))
        resolver.resolve_current_tick()
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (1, 1)))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')

    def test_dead_rook_link_fails_without_reward_or_movement(self):
        parts = fixture(player=Player(2, 1, 'left'))
        player, combat, parry, encounter, resolver = parts
        source = encounter.enemies[0]
        source.health.apply_damage(3, tick=0)
        attempt = parry_at(parts, 41)
        resolver.resolve_player_attack(combat.request_attack(player))
        resolver.advance(7)
        self.assertEqual(resolver.parry_result(attempt).status, 'failed')
        self.assertFalse(combat.counter_ready)
        self.assertEqual((player.health.current_hp, source.position), (3, (1, 1)))

    def test_cancelled_attack_has_no_damage_movement_or_delayed_replay(self):
        player, combat, parry, encounter, resolver = fixture()
        event = encounter.enemies[0].current_attack
        encounter.ledger.cancel(event)
        resolver.advance(48)
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (1, 1)))
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')

    def test_stale_or_forged_event_rejected_without_movement_or_consumption(self):
        player, combat, parry, encounter, resolver = fixture()
        event = encounter.enemies[0].current_attack
        for fake in (replace(event, hit_tick=49), replace(event, target_cells=((7, 1),))):
            with self.assertRaises(ValueError):
                resolver.resolve_enemy_attack(fake)
        other = fixture()
        with self.assertRaises(ValueError):
            other[-1].resolve_enemy_attack(event)
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (1, 1)))
        self.assertEqual(encounter.ledger.state(event), 'telegraph')

    def test_rook_ledger_event_without_ai_plan_is_rejected(self):
        player, combat, parry, encounter, resolver = fixture()
        fake = encounter.ledger.create(encounter.enemies[0].entity_instance_id, 0, 1, ((7, 1),))
        combat.advance()
        encounter.advance_to(1, player.position)
        encounter.ledger.mark_due(fake, 1)
        with self.assertRaisesRegex(ValueError, 'dash plan'):
            resolver.resolve_enemy_attack(fake)
        self.assertEqual(player.health.current_hp, 3)

    def test_late_due_event_expires_without_dash(self):
        player, combat, parry, encounter, resolver = fixture()
        event = encounter.enemies[0].current_attack
        combat.advance(49)
        encounter.advance_to(49, player.position)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(encounter.ledger.outcome(event), 'expired')
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (1, 1)))

    def test_stop_retires_attacks_plans_parry_and_prevents_further_state_changes(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        attempt = parry_at(parts, 41)
        resolver.stop()
        before = (combat.tick, player.health.current_hp, encounter.enemies[0].position, combat.pending_attack_bonus)
        self.assertEqual(resolver.advance(500), ())
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertIsNone(resolver.register_parry(attempt))
        self.assertEqual(before, (combat.tick, player.health.current_hp, encounter.enemies[0].position,
                                  combat.pending_attack_bonus))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertFalse(encounter.complete_attack(event, player.position))


class MixedEncounterTests(unittest.TestCase):
    def test_approved_cancellation_recovery_boundary_is_start_inclusive_end_exclusive(self):
        blocker = Enemy('p', 4, 2, (0, -1), 31 / 60)
        player, combat, parry, encounter, resolver = fixture((rook(), blocker))
        source = encounter.enemies[0]
        event = source.current_attack
        resolver.advance(31)
        self.assertEqual((source.state, source.next_action_tick), ('recovering', 121))
        resolver.advance(89)
        self.assertEqual((combat.tick, source.position, source.state), (120, (1, 1), 'recovering'))
        resolver.advance(1)
        self.assertEqual((source.position, source.next_action_tick), ((3, 1), 193))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertIsNone(resolver.resolve_enemy_attack(event))

    def test_rook_respects_existing_48_tick_invulnerability_end_boundary(self):
        for start, expected in ((38, 'invulnerable'), (39, 'hit')):
            with self.subTest(start=start):
                pawn = Enemy('p', 6, 2, (0, -1), 0)  # first hit39, invulnerable [39,87)
                player, combat, parry, encounter, resolver = fixture((pawn, rook(delay=start / 60)))
                resolver.advance(start)
                event = encounter.enemies[1].current_attack
                resolver.advance(48)
                self.assertEqual(encounter.ledger.outcome(event), expected)
                self.assertEqual(player.health.current_hp, 2 if expected == 'invulnerable' else 1)

    def test_perfect_stuns_one_rook_but_other_simultaneous_rook_can_hit(self):
        parts = fixture((rook(), rook('b', 7, 8)))
        player, combat, parry, encounter, resolver = parts
        attempt = parry_at(parts, 41)
        events = [e.current_attack for e in encounter.enemies]
        resolver.advance(7)
        self.assertEqual(resolver.parry_result(attempt).status, 'perfect')
        self.assertEqual([e.state for e in encounter.enemies], ['stunned', 'recovering'])
        self.assertEqual([encounter.ledger.outcome(e) for e in events], ['parried_perfect', 'hit'])
        self.assertEqual(player.health.current_hp, 2)
        self.assertEqual(combat.pending_attack_bonus, 2)

    def test_pawn_enters_warning_path_cancel_whole_attack_and_recover_from_cancel_tick(self):
        blocker = Enemy('p', 4, 2, (0, -1), 31 / 60)
        parts = fixture((rook(), blocker))
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        attempt = parry_at(parts, 30)
        resolver.advance(1)
        self.assertEqual(blocker.position, (4, 1))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertEqual((encounter.enemies[0].state, encounter.enemies[0].next_action_tick), ('recovering', 121))
        self.assertEqual(event.target_cells, tuple((c, 1) for c in range(2, 8)))
        self.assertEqual(resolver.parry_result(attempt).status, 'failed')
        resolver.advance(17)
        self.assertEqual(player.health.current_hp, 3)
        self.assertFalse(combat.counter_ready)
        self.assertIsNone(resolver.resolve_enemy_attack(event))

    def test_later_json_pawn_moves_on_hit_tick_before_rook_damage(self):
        blocker = Enemy('p', 4, 2, (0, -1), .8)
        player, combat, parry, encounter, resolver = fixture((rook(), blocker))
        event = encounter.enemies[0].current_attack
        resolver.advance(48)
        self.assertEqual((blocker.position, player.health.current_hp), ((4, 1), 3))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertEqual(encounter.enemies[0].next_action_tick, 138)

    def test_blocker_that_dies_before_due_does_not_obstruct(self):
        blocker = Enemy('p', 4, 2, (0, -1), .8)
        player, combat, parry, encounter, resolver = fixture((rook(), blocker))
        blocker.health.apply_damage(2, tick=0)
        resolver.advance(48)
        self.assertEqual(player.health.current_hp, 2)
        self.assertFalse(blocker.active)

    def test_pawn_first_hit_uses_48_tick_invulnerability_and_no_rook_perfect_reward(self):
        pawn = Enemy('p', 6, 2, (0, -1), 9 / 60)  # hit 9+39=48
        parts = fixture((pawn, rook()))
        player, combat, parry, encounter, resolver = parts
        attempt = parry_at(parts, 41)  # tie links first JSON event (Rook ID1 before Pawn ID2)
        # Rook hit48 was published at0; Pawn hit48 published at9. The link is Rook,
        # while adjudication retains enemy JSON order, Pawn then Rook.
        self.assertEqual(resolver.parry_binding(attempt).linked_enemy_event_key,
                         encounter.enemies[1].current_attack.key)
        r_event = encounter.enemies[1].current_attack
        p_event = encounter.enemies[0].current_attack
        resolver.advance(7)
        self.assertEqual(player.health.current_hp, 2)
        self.assertEqual(resolver.player_invulnerable_until_tick, 96)
        self.assertEqual(encounter.ledger.outcome(p_event), 'hit')
        self.assertEqual(encounter.ledger.outcome(r_event), 'invulnerable')
        self.assertEqual(resolver.parry_result(attempt).reason, 'invulnerable')
        self.assertFalse(combat.counter_ready)
        resolver.advance(48)
        self.assertIsNone(resolver.resolve_enemy_attack(r_event))
        self.assertEqual(player.health.current_hp, 2)

    def test_rook_normal_parry_does_not_block_unlinked_simultaneous_pawn(self):
        pawn = Enemy('p', 6, 2, (0, -1), 9 / 60)
        parts = fixture((rook(), pawn))
        player, combat, parry, encounter, resolver = parts
        attempt = parry_at(parts, 30)
        r_event, p_event = [e.current_attack for e in encounter.enemies]
        resolver.advance(18)
        self.assertEqual((resolver.parry_result(attempt).status, player.health.current_hp), ('normal', 2))
        self.assertEqual(encounter.ledger.outcome(r_event), 'parried_normal')
        self.assertEqual(encounter.ledger.outcome(p_event), 'hit')

    def test_two_rooks_simultaneous_damage_is_once_and_positions_do_not_overlap(self):
        player, combat, parry, encounter, resolver = fixture((rook(), rook('b', 7, 8)))
        events = [e.current_attack for e in encounter.enemies]
        resolver.advance(48)
        self.assertEqual(player.health.current_hp, 2)
        self.assertEqual([encounter.ledger.outcome(e) for e in events], ['hit', 'invulnerable'])
        self.assertEqual([e.position for e in encounter.enemies], [(6, 1), (7, 2)])
        for event in events:
            self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(player.health.current_hp, 2)

    def test_earlier_dash_can_obstruct_later_due_attack_without_rewriting_range(self):
        player, combat, parry, encounter, resolver = fixture((rook(), rook('b', 7, 8)))
        events = [e.current_attack for e in encounter.enemies]
        original = events[1].target_cells
        player.move('up', encounter.occupied_cells)
        resolver.advance(48)
        self.assertEqual(player.health.current_hp, 3)
        self.assertEqual([e.position for e in encounter.enemies], [(7, 1), (7, 8)])
        self.assertEqual(encounter.ledger.outcome(events[0]), 'miss')
        self.assertEqual(encounter.ledger.state(events[1]), 'cancelled')
        self.assertEqual(events[1].target_cells, original)
        self.assertEqual(encounter.enemies[1].next_action_tick, 138)

    def test_stage_two_actual_mixed_simulation_is_deterministic_and_collision_free(self):
        stage = StageCatalog.load().get_stage(2)
        def trace():
            parts = fixture(create_stage_enemies(stage), Player(*stage.player_spawn))
            player, combat, parry, encounter, resolver = parts
            values = []
            for _ in range(601):
                cells = [player.position] + [e.position for e in encounter.enemies if e.active]
                self.assertEqual(len(cells), len(set(cells)))
                values.append((combat.tick, player.health.current_hp,
                               [(e.data_id, e.kind, e.position, e.state, e.next_action_tick,
                                 e.health.current_hp) for e in encounter.enemies]))
                resolver.advance(1)
            return values
        a, b = trace(), trace()
        self.assertEqual(a, b)
        self.assertTrue(any(row[2][0][3] == 'telegraph' for row in a))
        self.assertTrue(any(row[1] < 3 for row in a))
        self.assertEqual(a[-1][:2], (444, 0))
        self.assertTrue(all(snapshot == a[444] for snapshot in a[444:]))

    def test_fresh_mixed_instances_reject_previous_events_and_bonus(self):
        stage = StageCatalog.load().get_stage(2)
        first = fixture(create_stage_enemies(stage), Player(*stage.player_spawn))
        first[-1].advance(120)
        old_event = first[-2].enemies[0].current_attack
        self.assertIsNotNone(old_event)
        first[1].grant_perfect_counter()
        first[-1].stop()
        fresh = fixture(create_stage_enemies(stage), Player(*stage.player_spawn))
        with self.assertRaises(ValueError):
            fresh[-1].resolve_enemy_attack(old_event)
        self.assertEqual(fresh[1].pending_attack_bonus, 0)
        self.assertEqual([e.health.current_hp for e in fresh[-2].enemies], [4, 2, 2])
        self.assertNotEqual(first[1].combat_session_id, fresh[1].combat_session_id)
        self.assertNotEqual(first[-2].ledger.stage_instance_id, fresh[-2].ledger.stage_instance_id)

    def test_601_tick_pawn_trace_matches_pre_task_j_baseline(self):
        encounter = PawnEncounter(load_stage1_enemies())
        snapshots = []
        for tick in range(601):
            due = encounter.advance_to(tick, (5, 1))
            snapshots.append((tick, [(e.data_id, e.position, e.state, e.next_action_tick)
                                     for e in encounter.enemies],
                              [(e.attack_id, e.start_tick, e.hit_tick, e.target_cells) for e in due]))
        digest = hashlib.sha256(json.dumps(snapshots, separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(digest, '4caa3531585d5377bbe55cfd1bbf90acd771b794d70302b8df7b806ab4ce7353')


class RookRenderingTests(unittest.TestCase):
    def test_castle_silhouette_differs_from_pawn_and_fits_all_board_cells(self):
        for col in range(10):
            for row in range(10):
                canvas = Mock()
                EnemyRenderer().draw(canvas, (rook(col=col, row=row),))
                canvas.draw_circle.assert_not_called()
                self.assertGreaterEqual(canvas.draw_rectangle.call_count, 6)
                left, bottom, right, top = tile_bounds(col, row)
                for call in canvas.draw_rectangle.call_args_list + canvas.draw_line.call_args_list:
                    x1, y1, x2, y2 = call.args[:4]
                    self.assertTrue(left <= x1 <= x2 < right and bottom <= y1 <= y2 < top)

    def test_warning_cells_equal_actual_dash_path_and_render_is_read_only(self):
        player, combat, parry, encounter, resolver = fixture()
        event = encounter.enemies[0].current_attack
        before = (vars(encounter.enemies[0]).copy(), player.health.current_hp, combat.pending_attack_bonus)
        for _ in range(10):
            canvas = Mock()
            EnemyAttackRenderer().draw(canvas, encounter.ledger)
            boxes = [call.args[:4] for call in canvas.draw_rectangle.call_args_list
                     if call.args[2] - call.args[0] == TILE_SIZE - 1]
            expected = [(left, bottom, right - 1, top - 1)
                        for left, bottom, right, top in map(lambda c: tile_bounds(*c), event.target_cells)]
            self.assertEqual(boxes, expected)
            EnemyRenderer().draw(Mock(), encounter.enemies)
        self.assertEqual(encounter.ledger.state(event), 'telegraph')
        self.assertEqual(before, (vars(encounter.enemies[0]).copy(), player.health.current_hp,
                                  combat.pending_attack_bonus))
        resolver.advance(48)
        for _ in range(10):
            EnemyRenderer().draw(Mock(), encounter.enemies)
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (2, (6, 1)))

    def test_dead_rook_not_rendered(self):
        source = rook()
        source.health.apply_damage(4, tick=0)
        canvas = Mock()
        EnemyRenderer().draw(canvas, (source,))
        self.assertEqual(canvas.mock_calls, [])


if __name__ == '__main__':
    unittest.main()
