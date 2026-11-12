"""Real contact schedules/damage/parries; explicit fixtures are not GUI play."""
from collections import deque
from dataclasses import replace
import unittest
from unittest.mock import Mock

import main
from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_attack import EnemyAttackEvent
from enemy_attack_renderer import EnemyAttackRenderer
from enemy_behaviors import EnemyEncounter
from game import GameState, StageGame
from parry import Parry
from player import Player, DIRECTIONS


def pawn(name='pawn', col=4, row=4, delay=0):
    return Enemy(name, col, row, (0, -1), delay, max_hp=3)


def session(target=(5, 4), *, enemies=None, boss=False, hp=3):
    player, combat, parry = Player(*target, max_hp=hp), Combat(), Parry()
    enemies = (pawn(),) if enemies is None else enemies
    encounter = EnemyEncounter(enemies, combat_session_id=combat.combat_session_id,
                               stage_instance_id=combat.stage_instance_id, boss=boss)
    resolver = CombatResolver(player, combat, encounter, parry=parry)
    return StageGame(player, combat, encounter, parry, resolver,
                     stage_number=5 if boss else 1, boss=boss)


def start(**kwargs):
    game = session(**kwargs)
    game.resolve_current_tick()
    return game, game.encounter.enemies[0].current_attack


def parry_at(game, tick):
    game.advance(tick - game.combat.tick)
    attempt = game.parry.request(game.combat.tick)
    game.resolver.register_parry(attempt)
    return attempt


class PawnContactRangeTests(unittest.TestCase):
    def test_four_cardinal_cells_are_one_fixed_contact_each(self):
        for target in ((4, 5), (4, 3), (3, 4), (5, 4)):
            with self.subTest(target=target):
                g, event = start(target=target)
                self.assertEqual((event.attack_kind, event.target_cells), ('pawn_contact', (target,)))
                self.assertEqual((event.start_tick, event.telegraph_start_tick, event.hit_tick), (0, 0, 39))
                self.assertEqual(g.encounter.enemies[0].position, (4, 4))
                self.assertEqual(g.encounter.ledger.pending, (event,))

    def test_downward_diagonal_remains_basic_and_has_priority(self):
        for target in ((3, 3), (5, 3)):
            g, event = start(target=target)
            self.assertEqual((event.attack_kind, event.target_cells), ('basic', (target,)))
            self.assertEqual(len(g.encounter.ledger.pending), 1)
            g.advance(39)
            self.assertEqual(g.encounter.ledger.outcome(event), 'hit')

    def test_distant_and_upward_diagonal_targets_still_move_without_contact(self):
        for target in ((4, 6), (6, 4), (2, 4), (4, 2), (5, 5), (3, 5)):
            g, event = start(target=target)
            self.assertIsNone(event)
            self.assertEqual(g.encounter.ledger.pending, ())
            self.assertEqual(g.encounter.enemies[0].next_action_tick, 132)

    def test_all_corner_cardinal_targets_stay_in_bounds(self):
        for origin in ((0, 0), (9, 0), (0, 9), (9, 9)):
            for dx, dy in DIRECTIONS.values():
                target = origin[0] + dx, origin[1] + dy
                if not all(0 <= v < 10 for v in target):
                    continue
                g, event = start(target=target, enemies=(pawn(col=origin[0], row=origin[1]),))
                self.assertEqual(event.target_cells, (target,))
                self.assertEqual(g.encounter.enemies[0].position, origin)

    def test_player_overlap_and_invalid_target_cells_are_rejected(self):
        for target in ((4, 4), (-1, 4), (10, 4), (True, 4)):
            g = session()
            with self.assertRaises(ValueError):
                g.encounter.advance_to(0, target)

    def test_initial_delay_stun_and_death_gate_contact(self):
        g = session(enemies=(pawn(delay=.8),))
        g.advance(47)
        self.assertFalse(g.encounter.ledger.pending)
        g.advance()
        event = g.encounter.enemies[0].current_attack
        self.assertEqual((event.start_tick, event.hit_tick), (48, 87))
        g.encounter.stun(g.encounter.enemies[0].entity_instance_id, 48)
        self.assertEqual(g.encounter.ledger.state(event), 'cancelled')
        g.advance(59)
        self.assertFalse(g.encounter.ledger.pending)
        g.advance()
        self.assertEqual(g.encounter.enemies[0].current_attack.start_tick, 108)
        e = g.encounter.enemies[0]
        e.health.apply_damage(e.health.current_hp, tick=108)
        g.encounter.deactivate(e.entity_instance_id, tick=108)
        self.assertFalse(g.encounter.ledger.pending)

    def test_exact_39_tick_warning_and_54_tick_recovery(self):
        g, event = start()
        g.advance(38)
        self.assertEqual(g.player.health.current_hp, 3)
        self.assertEqual(g.encounter.ledger.telegraphs, (event,))
        g.advance()
        e = g.encounter.enemies[0]
        self.assertEqual((g.player.health.current_hp, e.state, e.next_action_tick), (2, 'recovering', 93))
        self.assertEqual(g.encounter.ledger.telegraphs, ())
        g.advance(53)
        self.assertEqual((g.combat.tick, e.current_attack), (92, None))
        g.advance()
        self.assertEqual((e.current_attack.start_tick, e.current_attack.hit_tick), (93, 132))
        self.assertNotEqual(e.current_attack.key, event.key)
        self.assertEqual(e.position, (4, 4))

    def test_contact_does_not_move_push_or_overlap_other_pawns(self):
        g, event = start(enemies=(pawn(), pawn('neighbor', 4, 5, delay=10)))
        self.assertFalse(g.player.move('left', occupied=g.encounter.occupied_cells))
        self.assertEqual(g.player.position, (5, 4))
        g.advance(39)
        self.assertEqual([e.position for e in g.encounter.enemies], [(4, 4), (4, 5)])
        self.assertEqual(len(g.encounter.occupied_cells), 2)
        self.assertNotIn(g.player.position, g.encounter.occupied_cells)


class PawnContactResolutionTests(unittest.TestCase):
    def test_hit_damage_result_and_repeated_delivery_are_single_use(self):
        g, event = start()
        results = g.advance(39)
        self.assertEqual(len(results), 1)
        hit = results[0]
        self.assertEqual((hit.amount, hit.hp_before, hit.hp_after, hit.tick), (1, 3, 2, 39))
        self.assertEqual(hit.attack_key, event.key)
        for _ in range(4):
            self.assertIsNone(g.resolver.resolve_enemy_attack(event))
            self.assertEqual(g.resolve_current_tick(), ())
        self.assertEqual((g.player.health.current_hp, g.resolver.player_invulnerable_until_tick), (2, 87))

    def test_evade_fixed_warning_then_old_event_cannot_hit_return(self):
        g, event = start()
        self.assertTrue(g.player.move('up', occupied=g.encounter.occupied_cells))
        g.advance(39)
        self.assertEqual(event.target_cells, ((5, 4),))
        self.assertEqual(g.encounter.ledger.outcome(event), 'miss')
        self.assertTrue(g.player.move('down', occupied=g.encounter.occupied_cells))
        self.assertIsNone(g.resolver.resolve_enemy_attack(event))
        self.assertEqual(g.player.health.current_hp, 3)

    def test_return_to_fixed_cell_before_hit_can_be_damaged(self):
        g, event = start()
        g.player.move('up')
        g.advance(38)
        g.player.move('down')
        g.advance()
        self.assertEqual(g.encounter.ledger.outcome(event), 'hit')
        self.assertEqual(g.player.health.current_hp, 2)

    def test_two_pawns_json_order_and_exact_invulnerability_end(self):
        g, first = start(enemies=(pawn('first'), pawn('second', 6, 4), pawn('later', 5, 5, .8)))
        second = g.encounter.enemies[1].current_attack
        self.assertLess(first.attack_id, second.attack_id)
        g.advance(39)
        self.assertEqual([g.encounter.ledger.outcome(e) for e in (first, second)], ['hit', 'invulnerable'])
        self.assertEqual(g.player.health.current_hp, 2)
        g.advance(47)
        self.assertEqual(g.player.health.current_hp, 2)
        later = g.encounter.enemies[2].current_attack
        g.advance()
        self.assertEqual((g.combat.tick, g.encounter.ledger.outcome(later), g.player.health.current_hp), (87, 'hit', 1))

    def test_normal_parry_all_existing_delta_boundaries(self):
        for delta in (8, 18):
            g, event = start()
            attempt = parry_at(g, 39 - delta)
            g.advance(delta)
            self.assertEqual(g.resolver.parry_result(attempt).status, 'normal')
            self.assertEqual(g.encounter.ledger.outcome(event), 'parried_normal')
            self.assertEqual((g.player.health.current_hp, g.combat.pending_attack_bonus), (3, 0))
            self.assertEqual(g.encounter.enemies[0].state, 'recovering')

    def test_perfect_parry_stuns60_grants2_without_pulse_reflection(self):
        for delta in (1, 7):
            g, event = start()
            parry_at(g, 39 - delta)
            g.advance(delta)
            e = g.encounter.enemies[0]
            self.assertEqual(g.encounter.ledger.outcome(event), 'parried_perfect')
            self.assertEqual((g.player.health.current_hp, e.health.current_hp), (3, 3))
            self.assertEqual((e.state, e.stun_until_tick, g.combat.pending_attack_bonus), ('stunned', 99, 2))
            g.advance(59)
            self.assertIsNone(e.current_attack)
            g.advance()
            self.assertEqual(e.current_attack.start_tick, 99)

    def test_perfect_bonus_real_hit_once_miss_consumption_and_nonstacking(self):
        for hit in (True, False):
            g, event = start()
            parry_at(g, 32)
            g.advance(7)
            g.combat.grant_perfect_counter()
            self.assertEqual(g.combat.pending_attack_bonus, 2)
            g.player.move('left' if hit else 'right', occupied=g.encounter.occupied_cells)
            attack = g.combat.request_attack(g.player)
            result = g.resolver.resolve_player_attack(attack)
            self.assertEqual(result.amount if result else None, 3 if hit else None)
            self.assertEqual(g.combat.pending_attack_bonus, 0)
            self.assertIsNone(g.resolver.resolve_player_attack(attack))

    def test_too_early_and_hit_tick_parries_do_not_block(self):
        for tick in (0, 20, 39):
            g, event = start()
            # Input at the fresh hit tick precedes adjudication, but delta0 is too late.
            g.advance(tick - 1 if tick else 0)
            if tick:
                g.combat.advance()
            attempt = g.parry.request(g.combat.tick)
            g.resolver.register_parry(attempt)
            g.resolve_current_tick()
            g.advance(39 - tick)
            self.assertEqual(g.resolver.parry_result(attempt).status, 'unbound')
            self.assertEqual(g.encounter.ledger.outcome(event), 'hit')

    def test_parry_before_attack_publication_never_relinks(self):
        g = session()
        self.assertEqual(g.encounter.ledger.telegraphs, ())
        attempt = g.parry.request(0)
        g.resolver.register_parry(attempt)
        self.assertIsNone(g.resolver.parry_binding(attempt).linked_enemy_event_key)
        g.advance(39)
        self.assertEqual(g.player.health.current_hp, 2)
        self.assertEqual(g.resolver.parry_result(attempt).status, 'unbound')

    def test_overlapping_parry_links_once_by_hit_tick_then_attack_id(self):
        g, event = start(enemies=(pawn('first'), pawn('second', 6, 4)))
        attempt = parry_at(g, 32)
        binding = g.resolver.parry_binding(attempt)
        self.assertEqual(binding.linked_enemy_event_key, event.key)
        self.assertIs(g.resolver.register_parry(attempt), binding)
        g.advance(7)
        outcomes = [g.encounter.ledger.outcome(r.event) for r in g.encounter.ledger._records.values()]
        self.assertEqual(outcomes, ['parried_perfect', 'hit'])
        self.assertEqual((g.player.health.current_hp, g.combat.pending_attack_bonus), (2, 2))

    def test_invulnerable_or_evaded_bound_parry_gives_no_reward(self):
        for reason in ('invulnerable', 'evaded'):
            g, event = start()
            attempt = parry_at(g, 32)
            if reason == 'invulnerable':
                g.resolver.player_invulnerable_until_tick = 40
            else:
                g.player.move('up')
            g.advance(7)
            self.assertEqual(g.resolver.parry_result(attempt).reason, reason)
            self.assertEqual((g.player.health.current_hp, g.combat.pending_attack_bonus), (3, 0))

    def test_cancelled_bound_contact_closes_link_without_reward(self):
        g, event = start()
        attempt = parry_at(g, 32)
        g.encounter.cancel_attacks(g.encounter.enemies[0].entity_instance_id, tick=32)
        g.advance(7)
        self.assertEqual(g.resolver.parry_result(attempt).status, 'failed')
        self.assertEqual(g.encounter.ledger.state(event), 'cancelled')
        self.assertEqual((g.player.health.current_hp, g.combat.pending_attack_bonus), (3, 0))


class PawnContactOwnershipTests(unittest.TestCase):
    def test_unknown_kinds_and_modified_snapshots_are_rejected(self):
        g, event = start()
        with self.assertRaises(ValueError):
            replace(event, attack_kind='collision')
        g.advance(39)
        for changes in ({'attack_kind': 'basic'}, {'target_cells': ((5, 5),)},
                        {'attack_id': 99}, {'hit_tick': 40}, {'source_entity_instance_id': 'unknown'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                g.resolver.resolve_enemy_attack(replace(event, **changes))
        self.assertEqual(g.player.health.current_hp, 2)

    def test_registered_contact_without_ai_plan_cannot_damage(self):
        g = session(target=(9, 9))
        g.advance(38)
        source = g.encounter.enemies[0]
        event = g.encounter.ledger.create(source.entity_instance_id, 0, 39, ((9, 9),), attack_kind='pawn_contact')
        g.combat.advance()
        g.encounter.advance_to(39, g.player.position)
        g.encounter.ledger.mark_due(event, 39)
        with self.assertRaises(ValueError):
            g.resolver.resolve_enemy_attack(event)
        self.assertEqual(g.player.health.current_hp, 3)
        self.assertEqual(g.encounter.ledger.state(event), 'due')

    def test_other_enemy_kinds_cannot_issue_pawn_contact(self):
        for kind in ('rook', 'knight', 'bishop', 'king'):
            e = Enemy(kind, 4, 4, None, 10, kind=kind, boss_hp=22 if kind == 'king' else None)
            g = session(enemies=(e,))
            g.advance(38)
            event = g.encounter.ledger.create(e.entity_instance_id, 0, 39, (g.player.position,), attack_kind='pawn_contact')
            g.combat.advance()
            g.encounter.advance_to(39, g.player.position)
            g.encounter.ledger.mark_due(event, 39)
            with self.assertRaises(ValueError):
                g.resolver.resolve_enemy_attack(event)
            self.assertEqual(g.player.health.current_hp, 3)

    def test_unregistered_foreign_session_stage_and_parry_are_rejected(self):
        old, event = start()
        fresh, _ = start()
        for changes in ({}, {'combat_session_id': fresh.encounter.ledger.combat_session_id},
                        {'stage_instance_id': fresh.encounter.ledger.stage_instance_id}):
            with self.assertRaises(ValueError):
                fresh.resolver.resolve_enemy_attack(replace(event, **changes))
        attempt = old.parry.request(0)
        with self.assertRaises(ValueError):
            fresh.resolver.register_parry(attempt)
        self.assertEqual(fresh.player.health.current_hp, 3)

    def test_source_killed_by_real_player_attack_on_due_tick_cancels_contact(self):
        g, event = start()
        g.advance(38)
        g.combat.advance()
        g.combat.grant_perfect_counter()
        g.player.move('left', occupied=g.encounter.occupied_cells)
        result = g.resolver.resolve_player_attack(g.combat.request_attack(g.player))
        self.assertEqual(result.amount, 3)
        g.resolve_current_tick()
        self.assertEqual((g.state, g.player.health.current_hp), (GameState.UPGRADE, 3))
        self.assertEqual(g.encounter.ledger.state(event), 'cancelled')
        g.advance(500)
        self.assertEqual((g.combat.tick, g.player.health.current_hp, g.transition_count), (39, 3, 1))

    def test_game_over_cancels_other_pending_contacts_and_stays_stopped(self):
        g, event = start(hp=1, enemies=(pawn(), pawn('later', 6, 4, .1)))
        g.advance(39)
        later = list(g.encounter.ledger._records.values())[1].event
        self.assertEqual((g.state, g.player.health.current_hp), (GameState.GAME_OVER, 0))
        self.assertEqual(g.encounter.ledger.state(later), 'cancelled')
        g.advance(400)
        self.assertEqual((g.combat.tick, g.transition_count), (39, 1))
        self.assertIsNone(g.resolver.resolve_enemy_attack(later))

    def test_simultaneous_all_dead_retains_game_over_priority(self):
        g, event = start(hp=1)
        g.player.health.apply_damage(1, tick=0)
        e = g.encounter.enemies[0]
        e.health.apply_damage(3, tick=0)
        g.update_state()
        self.assertEqual(g.state, GameState.GAME_OVER)
        self.assertEqual(g.encounter.ledger.state(event), 'cancelled')

    def test_stop_cancels_telegraph_and_prevents_further_damage(self):
        g, event = start()
        self.assertTrue(g.resolver.stop())
        self.assertFalse(g.resolver.stop())
        self.assertEqual(g.encounter.ledger.state(event), 'cancelled')
        self.assertIsNone(g.resolver.resolve_enemy_attack(event))
        self.assertEqual(g.encounter.ledger.telegraphs, ())
        self.assertEqual(g.player.health.current_hp, 3)

    def test_renderer_draws_exact_single_target_read_only_and_removes_it(self):
        from board import tile_bounds
        g, event = start()
        canvas = Mock()
        before = tuple(g.encounter.ledger._records)
        for _ in range(3):
            EnemyAttackRenderer().draw(canvas, g.encounter.ledger)
        left, bottom, right, top = tile_bounds(5, 4)
        self.assertEqual(canvas.draw_rectangle.call_args_list[0].args[:4], (left, bottom, right-1, top-1))
        self.assertEqual(canvas.draw_rectangle.call_count, 6)
        self.assertEqual(tuple(g.encounter.ledger._records), before)
        self.assertEqual(g.encounter.ledger.state(event), 'telegraph')
        g.advance(39)
        canvas.reset_mock()
        EnemyAttackRenderer().draw(canvas, g.encounter.ledger)
        canvas.draw_rectangle.assert_not_called()


def pulse_fixture():
    king = Enemy('king', 8, 8, None, 0, kind='king', boss_hp=22)
    g, event = start(enemies=(pawn(), king), boss=True)
    pulse = g.encounter.pulse
    # Deterministic scheduling fixture; all attack/parry/drain logic remains real.
    pulse.next_use_tick = 1
    king.next_action_tick = 1
    return g, event, pulse


class PawnContactPulseTests(unittest.TestCase):
    def test_contact_hit_miss_and_parries_drain_before_pulse(self):
        for outcome in ('hit', 'miss', 'parried_normal', 'parried_perfect'):
            with self.subTest(outcome=outcome):
                g, event, pulse = pulse_fixture()
                g.advance()
                self.assertEqual(pulse.state, 'DRAINING')
                if outcome == 'miss':
                    g.player.move('up')
                elif outcome.startswith('parried'):
                    parry_at(g, 21 if outcome.endswith('normal') else 32)
                g.advance(39 - g.combat.tick)
                self.assertEqual(g.encounter.ledger.outcome(event), outcome)
                self.assertIsNone(pulse.event)
                self.assertNotIn(event.key, g.encounter._attack_moves)
                g.advance()
                self.assertEqual((pulse.state, pulse.event.start_tick), ('PULSE_TELEGRAPH', 40))
                self.assertEqual(len(pulse.event.target_cells), 100)

    def test_dead_pawn_contact_cancellation_does_not_deadlock_draining(self):
        g, event, pulse = pulse_fixture()
        g.advance(10)
        e = g.encounter.enemies[0]
        e.health.apply_damage(3, tick=10)
        g.encounter.deactivate(e.entity_instance_id, tick=10)
        g.advance()
        self.assertEqual(g.encounter.ledger.state(event), 'cancelled')
        g.advance()
        self.assertIsNotNone(pulse.event)
        self.assertEqual(pulse.event.start_tick, 12)

    def test_freeze_cleanup_restore_remaining_contact_recovery(self):
        g, event, pulse = pulse_fixture()
        g.advance(40)
        e = g.encounter.enemies[0]
        saved = e.position, e.state, e.next_action_tick
        g.advance(113)
        self.assertEqual((e.position, e.state, e.next_action_tick), saved)
        parry_at(g, 153)
        g.advance(7)
        self.assertEqual(pulse.state, 'CLEANUP')
        self.assertEqual(pulse.king.health.current_hp, 20)
        g.advance(29)
        self.assertEqual((e.position, e.state, e.next_action_tick), saved)
        g.advance()
        self.assertEqual((pulse.state, e.next_action_tick), ('NORMAL', 243))
        g.advance(53)
        self.assertEqual(e.current_attack.attack_kind, 'pawn_contact')

    def test_king_death_during_pulse_releases_contact_timer_next_tick(self):
        g, event, pulse = pulse_fixture()
        g.advance(50)
        pulse.king.health.apply_damage(22, tick=50)
        g.encounter.deactivate(pulse.king.entity_instance_id, tick=50)
        g.advance()
        e = g.encounter.enemies[0]
        self.assertTrue(g.playing)
        self.assertIsNone(pulse.freeze_tick)
        self.assertEqual(e.next_action_tick, 104)
        g.advance(53)
        self.assertEqual(e.current_attack.attack_kind, 'pawn_contact')


class PawnContactRuntimeTests(unittest.TestCase):
    def test_original_stage1_2_5_6_10_pawns_issue_contact_with_original_delay(self):
        # Position the player via legal moves before tick0, leaving all enemy data intact.
        for stage in (1, 2, 5, 6, 10):
            with self.subTest(stage=stage):
                g = main._new_stage_game(stage)
                e = next(e for e in g.encounter.enemies if e.kind == 'pawn')
                target = e.col, e.row - 1
                queue = deque([(g.player.position, [])])
                seen = {g.player.position}
                while queue:
                    cell, path = queue.popleft()
                    if cell == target:
                        break
                    for name, (dx, dy) in DIRECTIONS.items():
                        nxt = cell[0]+dx, cell[1]+dy
                        if all(0 <= v < 10 for v in nxt) and nxt not in seen and nxt not in g.encounter.occupied_cells:
                            seen.add(nxt)
                            queue.append((nxt, path+[name]))
                self.assertEqual(cell, target)
                for direction in path:
                    self.assertTrue(g.player.move(direction, occupied=g.encounter.occupied_cells))
                g.advance(e.initial_delay_ticks)
                event = e.current_attack
                self.assertEqual((event.attack_kind, event.start_tick, event.target_cells),
                                 ('pawn_contact', e.initial_delay_ticks, (target,)))
                if stage == 10:
                    # Original Knight lands first (111); parry it so contact127
                    # tests actual damage rather than the existing shared invulnerability.
                    attempt = parry_at(g, 104)
                    g.advance(event.hit_tick - g.combat.tick)
                    self.assertEqual(g.resolver.parry_result(attempt).status, 'perfect')
                else:
                    g.advance(39)
                self.assertEqual(g.encounter.ledger.outcome(event), 'hit')
                self.assertEqual(g.player.health.current_hp, 2)

    def test_contact_mixed_battle_one_and_eight_tick_steps_match(self):
        def trace(stride):
            g, _ = start(enemies=(pawn(), pawn('second', 6, 4)))
            for _ in range(160 // stride):
                g.advance(stride)
            return (g.combat.tick, g.state, g.player.health.current_hp,
                    [(e.position, e.state, e.next_action_tick) for e in g.encounter.enemies],
                    [(r.event.attack_id, r.event.attack_kind, r.event.start_tick, r.event.hit_tick,
                      r.event.target_cells, r.state, r.outcome) for r in g.encounter.ledger._records.values()])
        self.assertEqual(trace(1), trace(8))


if __name__ == '__main__':
    unittest.main()
