"""Knight hit/landing/parry lifecycle and three-kind combat on integer ticks."""
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest
from unittest.mock import Mock

from board import tile_bounds
from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_attack_renderer import EnemyAttackRenderer
from enemy_behaviors import EnemyEncounter
from enemy_factory import create_stage_enemies
from enemy_renderer import EnemyRenderer
from health_renderer import HealthRenderer
from parry import Parry
from player import Player
from stage_manager import StageCatalog
from tests.test_knight import knight


def fixture(enemies=None, player=None):
    player = player if player is not None else Player(5, 1)
    combat, parry = Combat(), Parry()
    encounter = EnemyEncounter((knight(),) if enemies is None else enemies,
                               combat_session_id=combat.combat_session_id,
                               stage_instance_id=combat.stage_instance_id)
    resolver = CombatResolver(player, combat, encounter, parry=parry)
    resolver.resolve_current_tick()
    return player, combat, parry, encounter, resolver


def press_parry(parts, tick):
    player, combat, parry, encounter, resolver = parts
    resolver.advance(tick - combat.tick)
    attempt = parry.request(combat.tick)
    resolver.register_parry(attempt)
    return attempt


class KnightCombatTests(unittest.TestCase):
    def test_hit_at_36_once_stays_at_origin_and_recovers_until_108(self):
        player, combat, parry, encounter, resolver = fixture()
        source = encounter.enemies[0]
        event = source.current_attack
        resolver.advance(35)
        self.assertEqual((player.health.current_hp, source.position), (3, (4, 3)))
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        result = resolver.advance(1)[0]
        self.assertEqual((result.tick, result.amount, player.health.current_hp), (36, 1, 2))
        self.assertEqual((source.position, source.state, source.next_action_tick), ((4, 3), 'recovering', 108))
        for _ in range(10):
            self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(player.health.current_hp, 2)
        resolver.advance(71)
        self.assertEqual((combat.tick, source.state), (107, 'recovering'))
        resolver.advance(1)
        self.assertEqual((source.state, source.current_attack.start_tick), ('telegraph', 108))
        self.assertNotEqual(source.current_attack.key, event.key)

    def test_all_eight_attack_directions_hit_only_the_selected_landing(self):
        for dx, dy in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
            with self.subTest(offset=(dx, dy)):
                player, combat, parry, encounter, resolver = fixture((knight(col=4, row=4),),
                                                                    Player(4 + dx, 4 + dy))
                event = encounter.enemies[0].current_attack
                self.assertEqual(event.target_cells, (player.position,))
                resolver.advance(36)
                self.assertEqual(player.health.current_hp, 2)
                self.assertEqual(encounter.enemies[0].position, (4, 4))

    def test_evading_player_leaves_knight_at_original_booked_cell_not_new_player_cell(self):
        player, combat, parry, encounter, resolver = fixture()
        event = encounter.enemies[0].current_attack
        player.move('up', encounter.occupied_cells)
        resolver.advance(36)
        self.assertEqual((player.health.current_hp, player.position, encounter.enemies[0].position),
                         (3, (5, 2), (5, 1)))
        self.assertEqual(encounter.ledger.outcome(event), 'miss')
        self.assertFalse(encounter.complete_attack(event, player.position))

    def test_player_entering_previously_empty_landing_is_hit_without_cancelling(self):
        player, combat, parry, encounter, resolver = fixture((knight(col=4, row=4),), Player(9, 9))
        event = encounter.enemies[0].current_attack
        self.assertEqual(event.target_cells, ((5, 6),))
        for _ in range(4):
            player.move('left', encounter.occupied_cells)
        for _ in range(3):
            player.move('down', encounter.occupied_cells)
        resolver.advance(36)
        self.assertEqual((player.position, player.health.current_hp, encounter.enemies[0].position),
                         ((5, 6), 2, (4, 4)))
        self.assertEqual(encounter.ledger.outcome(event), 'hit')

    def test_intermediate_live_pieces_are_jumped_over_without_occupancy_collision(self):
        blockers = (Enemy('a', 4, 2, (0, -1), 10), Enemy('b', 5, 2, (0, -1), 10))
        player, combat, parry, encounter, resolver = fixture((knight(), *blockers))
        player.move('right', encounter.occupied_cells)
        resolver.advance(36)
        self.assertEqual(encounter.enemies[0].position, (5, 1))
        self.assertEqual([e.position for e in blockers], [(4, 2), (5, 2)])
        self.assertEqual(player.health.current_hp, 3)

    def test_actual_normal_perfect_time_boundaries_against_knight(self):
        for delta, expected in ((0, 'unbound'), (1, 'perfect'), (7, 'perfect'),
                                (8, 'normal'), (18, 'normal'), (19, 'unbound')):
            with self.subTest(delta=delta):
                parts = fixture()
                player, combat, parry, encounter, resolver = parts
                attempt = press_parry(parts, 36 - delta)
                resolver.advance(delta)
                self.assertEqual(resolver.parry_result(attempt).status, expected)
                self.assertEqual(player.health.current_hp, 2 if expected == 'unbound' else 3)
                self.assertEqual(combat.pending_attack_bonus, 2 if expected == 'perfect' else 0)

    def test_normal_parry_only_blocks_damage_and_knight_does_not_land_on_player(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        attempt = press_parry(parts, 18)
        resolver.advance(18)
        self.assertEqual((player.health.current_hp, resolver.parry_result(attempt).status), (3, 'normal'))
        self.assertEqual(encounter.ledger.outcome(event), 'parried_normal')
        self.assertEqual((encounter.enemies[0].position, encounter.enemies[0].state), ((4, 3), 'recovering'))
        self.assertEqual((combat.pending_attack_bonus, resolver.player_invulnerable_until_tick), (0, 0))

    def test_perfect_stuns_only_source_60_ticks_and_resumes_with_new_event(self):
        other = Enemy('p', 9, 9, (0, -1), 10)
        parts = fixture((knight(), other))
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        attempt = press_parry(parts, 29)
        resolver.advance(7)
        source = encounter.enemies[0]
        self.assertEqual((source.position, source.state, source.stun_until_tick), ((4, 3), 'stunned', 96))
        self.assertEqual(resolver.parry_result(attempt).status, 'perfect')
        self.assertNotEqual(other.state, 'stunned')
        resolver.advance(59)
        self.assertEqual((combat.tick, source.state), (95, 'stunned'))
        resolver.advance(1)
        self.assertEqual((source.current_attack.start_tick, source.current_attack.hit_tick), (96, 132))
        self.assertNotEqual(source.current_attack.key, event.key)
        self.assertEqual(encounter.ledger.outcome(event), 'parried_perfect')

    def test_perfect_counter_resets_attack_cooldown_and_three_damage_consumes_reward_once(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        resolver.advance(29)
        resolver.resolve_player_attack(combat.request_attack(player))
        self.assertEqual(combat.next_attack_tick, 65)
        attempt = parry.request(combat.tick)
        resolver.register_parry(attempt)
        enemy_event = encounter.enemies[0].current_attack
        resolver.advance(7)
        self.assertEqual((combat.next_attack_tick, combat.pending_attack_bonus), (36, 2))
        player.move('up', encounter.occupied_cells)
        player.move('left', encounter.occupied_cells)
        player.move('up', encounter.occupied_cells)  # blocked Knight cell still sets facing
        attack = combat.request_attack(player)
        result = resolver.resolve_player_attack(attack)
        self.assertEqual((attack.damage_bonus, result.amount, encounter.enemies[0].health.current_hp), (2, 3, 0))
        self.assertFalse(encounter.enemies[0].active)
        for _ in range(10):
            self.assertIsNone(resolver.resolve_enemy_attack(enemy_event))
            self.assertIsNone(resolver.resolve_player_attack(attack))
            resolver.register_parry(attempt)
        self.assertEqual(combat.pending_attack_bonus, 0)
        self.assertEqual(encounter.ledger.outcome(enemy_event), 'parried_perfect')

    def test_outside_range_parry_cannot_bind_retroactively_after_player_enters(self):
        player, combat, parry, encounter, resolver = fixture((knight(col=4, row=4),), Player(9, 9))
        resolver.advance(29)
        attempt = parry.request(combat.tick)
        resolver.register_parry(attempt)
        for _ in range(4):
            player.move('left', encounter.occupied_cells)
        for _ in range(3):
            player.move('down', encounter.occupied_cells)
        resolver.advance(7)
        self.assertEqual((resolver.parry_result(attempt).status, player.health.current_hp), ('unbound', 2))

    def test_evading_a_linked_attempt_is_miss_not_success_or_reward(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        attempt = press_parry(parts, 29)
        player.move('up', encounter.occupied_cells)
        resolver.advance(7)
        self.assertEqual((resolver.parry_result(attempt).status, resolver.parry_result(attempt).reason),
                         ('failed', 'evaded'))
        self.assertEqual((player.health.current_hp, combat.pending_attack_bonus), (3, 0))

    def test_existing_invulnerability_finishes_attack_without_perfect_reward_or_late_hit(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        attempt = press_parry(parts, 29)
        resolver.player_invulnerable_until_tick = 37
        resolver.advance(7)
        self.assertEqual(encounter.ledger.outcome(event), 'invulnerable')
        self.assertEqual(resolver.parry_result(attempt).reason, 'invulnerable')
        self.assertEqual((player.health.current_hp, combat.pending_attack_bonus), (3, 0))
        resolver.advance(1)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(encounter.enemies[0].position, (4, 3))

    def test_knight_hits_obey_exact_48_tick_invulnerability_end(self):
        for start, expected in ((47, 'invulnerable'), (48, 'hit')):
            with self.subTest(start=start):
                player, combat, parry, encounter, resolver = fixture((knight('a'), knight('b', 6, 3, start / 60)))
                resolver.advance(start)
                event = encounter.enemies[1].current_attack
                resolver.advance(36)
                self.assertEqual(encounter.ledger.outcome(event), expected)
                self.assertEqual(player.health.current_hp, 2 if expected == 'invulnerable' else 1)

    def test_fatal_space_on_hit_tick_cancels_knight_and_releases_occupancy(self):
        player, combat, parry, encounter, resolver = fixture()
        source = encounter.enemies[0]
        event = source.current_attack
        source.health.apply_damage(2, tick=0)
        resolver.advance(35)
        player.move('up', encounter.occupied_cells)
        player.move('left', encounter.occupied_cells)
        player.move('up', encounter.occupied_cells)
        combat.advance()
        resolver.resolve_player_attack(combat.request_attack(player))
        resolver.resolve_current_tick()
        self.assertEqual((player.health.current_hp, source.health.current_hp, source.position), (3, 0, (4, 3)))
        self.assertNotIn(source.position, encounter.occupied_cells)
        self.assertEqual(encounter.ledger.state(event), 'cancelled')

    def test_stun_or_death_cancels_a_pending_knight_without_moving_or_earning_reward(self):
        for cause in ('stun', 'death'):
            parts = fixture()
            player, combat, parry, encounter, resolver = parts
            source = encounter.enemies[0]
            event = source.current_attack
            attempt = press_parry(parts, 29)
            if cause == 'stun':
                encounter.stun(source.entity_instance_id, combat.tick)
            else:
                source.health.apply_damage(3, tick=combat.tick)
                encounter.deactivate(source.entity_instance_id)
            resolver.advance(7)
            self.assertEqual(encounter.ledger.state(event), 'cancelled')
            self.assertEqual(resolver.parry_result(attempt).status, 'failed')
            self.assertEqual((player.health.current_hp, source.position, combat.pending_attack_bonus), (3, (4, 3), 0))

    def test_foreign_or_forged_events_and_stale_attempts_cannot_affect_a_new_instance(self):
        old = fixture()
        event = old[-2].enemies[0].current_attack
        attempt = press_parry(old, 29)
        fresh = fixture()
        for fake in (event, replace(event, hit_tick=37), replace(event, target_cells=((6, 1),))):
            with self.assertRaises(ValueError):
                fresh[-1].resolve_enemy_attack(fake)
        with self.assertRaises(ValueError):
            old[-1].resolve_enemy_attack(replace(event, hit_tick=37))
        with self.assertRaises(ValueError):
            fresh[-1].register_parry(attempt)
        self.assertEqual((fresh[0].health.current_hp, fresh[-2].enemies[0].position, fresh[1].pending_attack_bonus),
                         (3, (4, 3), 0))

    def test_ledger_only_knight_event_without_jump_plan_is_rejected_before_consumption(self):
        player, combat, parry, encounter, resolver = fixture()
        fake = encounter.ledger.create(encounter.enemies[0].entity_instance_id, 0, 1, ((5, 1),))
        combat.advance()
        encounter.advance_to(1, player.position)
        encounter.ledger.mark_due(fake, 1)
        with self.assertRaisesRegex(ValueError, 'jump plan'):
            resolver.resolve_enemy_attack(fake)
        self.assertEqual(encounter.ledger.state(fake), 'due')
        self.assertEqual(player.health.current_hp, 3)

    def test_late_due_attack_expires_without_jump_or_damage(self):
        player, combat, parry, encounter, resolver = fixture()
        event = encounter.enemies[0].current_attack
        combat.advance(37)
        encounter.advance_to(37, player.position)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual(encounter.ledger.outcome(event), 'expired')
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (4, 3)))

    def test_stop_retires_pending_jump_and_blocks_damage_movement_and_rewards(self):
        parts = fixture()
        player, combat, parry, encounter, resolver = parts
        event = encounter.enemies[0].current_attack
        attempt = press_parry(parts, 29)
        resolver.stop()
        self.assertEqual(resolver.advance(1000), ())
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertFalse(encounter.complete_attack(event, player.position))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertEqual((combat.tick, player.health.current_hp, combat.pending_attack_bonus), (29, 3, 0))
        self.assertEqual(encounter.enemies[0].position, (4, 3))


class KnightMixedCombatTests(unittest.TestCase):
    def test_approved_landing_obstruction_cancels_whole_event_and_recovers_exactly_72(self):
        pawn = Enemy('p', 5, 0, (0, -1), .5)
        parts = fixture((knight(), pawn))
        player, combat, parry, encounter, resolver = parts
        source = encounter.enemies[0]
        event = source.current_attack
        attempt = press_parry(parts, 20)
        player.move('up', encounter.occupied_cells)
        resolver.advance(10)
        self.assertEqual(pawn.position, (5, 1))
        self.assertEqual((source.state, source.next_action_tick, source.position), ('recovering', 102, (4, 3)))
        self.assertEqual(event.target_cells, ((5, 1),))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertEqual(resolver.parry_result(attempt).reason, 'cancelled')
        resolver.advance(71)
        self.assertEqual((combat.tick, source.state), (101, 'recovering'))
        resolver.advance(1)
        self.assertEqual((source.state, source.current_attack.start_tick), ('telegraph', 102))
        self.assertNotEqual(source.current_attack.key, event.key)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual((player.health.current_hp, combat.pending_attack_bonus), (3, 0))

    def test_blocker_on_hit_tick_cancels_after_all_ai_before_damage(self):
        pawn = Enemy('p', 5, 0, (0, -1), .6)
        player, combat, parry, encounter, resolver = fixture((knight(), pawn))
        event = encounter.enemies[0].current_attack
        player.move('up', encounter.occupied_cells)
        resolver.advance(36)
        self.assertEqual((pawn.position, player.health.current_hp), ((5, 1), 3))
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertEqual(encounter.enemies[0].next_action_tick, 108)

    def test_cancelled_landing_never_reactivates_after_blocker_dies_and_player_returns(self):
        pawn = Enemy('p', 5, 0, (0, -1), .5)
        player, combat, parry, encounter, resolver = fixture((knight(), pawn))
        event = encounter.enemies[0].current_attack
        player.move('up', encounter.occupied_cells)
        resolver.advance(30)
        pawn.health.apply_damage(2, tick=30)
        encounter.deactivate(pawn.entity_instance_id)
        player.move('down', encounter.occupied_cells)
        resolver.advance(6)
        self.assertIsNone(resolver.resolve_enemy_attack(event))
        self.assertEqual((player.health.current_hp, encounter.enemies[0].position), (3, (4, 3)))

    def test_same_tick_two_knights_one_landing_uses_json_order_and_cancels_later_jump(self):
        player, combat, parry, encounter, resolver = fixture(
            (knight('a', 4, 4), knight('b', 6, 4)), Player(5, 6))
        events = [e.current_attack for e in encounter.enemies]
        player.move('up', encounter.occupied_cells)
        resolver.advance(36)
        self.assertEqual([e.position for e in encounter.enemies], [(5, 6), (6, 4)])
        self.assertEqual(encounter.ledger.outcome(events[0]), 'miss')
        self.assertEqual(encounter.ledger.state(events[1]), 'cancelled')
        self.assertEqual(encounter.enemies[1].next_action_tick, 108)

    def test_perfect_knight_only_stuns_linked_attacker_other_attack_still_hits(self):
        parts = fixture((knight('a'), knight('b', 6, 3)))
        player, combat, parry, encounter, resolver = parts
        attempt = press_parry(parts, 29)
        events = [e.current_attack for e in encounter.enemies]
        resolver.advance(7)
        self.assertEqual([encounter.ledger.outcome(e) for e in events], ['parried_perfect', 'hit'])
        self.assertEqual([e.state for e in encounter.enemies], ['stunned', 'recovering'])
        self.assertEqual((player.health.current_hp, combat.pending_attack_bonus), (2, 2))
        self.assertEqual(resolver.parry_result(attempt).status, 'perfect')

    def test_three_kinds_same_hit_tick_keep_json_order_invulnerability_and_single_consumption(self):
        for order in ('krp', 'rkp'):
            kinds = {'k': knight(delay=.2), 'r': Enemy('r', 1, 1, None, 0, kind='rook'),
                     'p': Enemy('p', 4, 2, (0, -1), .15)}
            parts = fixture(tuple(kinds[key] for key in order))
            player, combat, parry, encounter, resolver = parts
            attempt = press_parry(parts, 41)  # All hit48; Rook was published first.
            events = [e.current_attack for e in encounter.enemies]
            resolver.advance(7)
            self.assertEqual(player.health.current_hp, 2)
            self.assertEqual(combat.pending_attack_bonus, 2 if order == 'rkp' else 0)
            self.assertEqual(resolver.parry_result(attempt).status, 'perfect' if order == 'rkp' else 'failed')
            for event in events:
                self.assertEqual(encounter.ledger.state(event), 'resolved')
                self.assertIsNone(resolver.resolve_enemy_attack(event))
            self.assertEqual(player.health.current_hp, 2)
            cells = [player.position] + [e.position for e in encounter.enemies if e.active]
            self.assertEqual(len(cells), len(set(cells)))

    def test_knight_landing_in_rook_path_preserves_rook_full_cancel_and_90_tick_recovery(self):
        rook = Enemy('r', 1, 1, None, 0, kind='rook')
        pawn = Enemy('p', 6, 2, (0, -1), 0)  # Blocks Knight's equally near (6,2).
        player, combat, parry, encounter, resolver = fixture((rook, knight(), pawn), Player(7, 1))
        r_event, k_event = rook.current_attack, encounter.enemies[1].current_attack
        self.assertEqual(k_event.target_cells, ((5, 1),))
        resolver.advance(36)
        self.assertEqual(encounter.enemies[1].position, (5, 1))
        self.assertEqual(encounter.ledger.state(r_event), 'cancelled')
        self.assertEqual((rook.state, rook.next_action_tick, rook.position), ('recovering', 126, (1, 1)))
        self.assertEqual(player.health.current_hp, 3)

    def test_warning_overlap_alone_does_not_cancel_rook_when_knight_stays_at_origin(self):
        rook = Enemy('r', 1, 1, None, 0, kind='rook')
        player, combat, parry, encounter, resolver = fixture((rook, knight(col=5, row=2)), Player(7, 1))
        r_event = rook.current_attack
        resolver.advance(36)
        self.assertEqual(encounter.enemies[1].position, (5, 2))
        self.assertEqual(encounter.ledger.state(r_event), 'telegraph')
        resolver.advance(12)
        self.assertEqual(encounter.ledger.outcome(r_event), 'invulnerable')

    def test_stage_three_and_custom_three_kind_encounter_are_repeatable_and_collision_free(self):
        catalog = StageCatalog.load()
        for mixed in (False, True):
            def trace():
                enemies = create_stage_enemies(catalog.get_stage(3))
                if mixed:
                    enemies = (create_stage_enemies(catalog.get_stage(2))[0], *enemies)
                player, combat, parry, encounter, resolver = fixture(enemies)
                rows = []
                for _ in range(601):
                    cells = [player.position] + [e.position for e in enemies if e.active]
                    self.assertEqual(len(cells), len(set(cells)))
                    rows.append((combat.tick, player.health.current_hp,
                                 [(e.kind, e.position, e.state, e.next_action_tick, e.health.current_hp) for e in enemies]))
                    resolver.advance(1)
                return rows
            with self.subTest(mixed=mixed):
                first, second = trace(), trace()
                self.assertEqual(first, second)
                self.assertTrue(any(row[1] < 3 for row in first))
                self.assertEqual(first[-1][1], 0)
                self.assertEqual(first[-1], first[-2])  # terminal combat time/AI frozen


class KnightRendererTests(unittest.TestCase):
    def test_distinct_horse_silhouette_fits_every_tile_below_hp_and_inside_warning_border(self):
        for col in range(10):
            for row in range(10):
                canvas = Mock()
                EnemyRenderer().draw(canvas, (knight(col=col, row=row),))
                canvas.draw_circle.assert_not_called()
                self.assertGreater(canvas.draw_rectangle.call_count, 0)
                left, bottom, right, top = tile_bounds(col, row)
                for call in canvas.draw_rectangle.call_args_list:
                    x1, y1, x2, y2 = call.args[:4]
                    self.assertTrue(left < x1 <= x2 < right - 1 and bottom < y1 <= y2 < top - 1)
                    self.assertLessEqual(y2, (bottom + top) / 2 + 27)
        pawn_canvas, rook_canvas, knight_canvas = Mock(), Mock(), Mock()
        for canvas, enemy in ((pawn_canvas, Enemy('p', 4, 3, (0, -1), 0)),
                              (rook_canvas, Enemy('r', 4, 3, None, 0, kind='rook')),
                              (knight_canvas, knight())):
            EnemyRenderer().draw(canvas, (enemy,))
        self.assertNotEqual(knight_canvas.mock_calls, pawn_canvas.mock_calls)
        self.assertNotEqual(knight_canvas.mock_calls, rook_canvas.mock_calls)

    def test_warning_uses_single_actual_target_not_all_candidates_and_never_mutates_combat(self):
        player, combat, parry, encounter, resolver = fixture()
        source = encounter.enemies[0]
        event = source.current_attack
        before = (source.position, source.health.current_hp, player.health.current_hp, combat.tick,
                  combat.pending_attack_bonus, len(encounter.ledger._consumed))
        for _ in range(10):
            canvas = Mock()
            EnemyAttackRenderer().draw(canvas, encounter.ledger)
            self.assertEqual(canvas.draw_rectangle.call_args_list[0].args[:4], (720, 114, 803, 197))
            self.assertEqual(canvas.draw_rectangle.call_count, 2)
            EnemyRenderer().draw(canvas, encounter.enemies)
            HealthRenderer().draw(canvas, player, encounter.enemies, combat.tick)
        self.assertEqual(before, (source.position, source.health.current_hp, player.health.current_hp,
                                  combat.tick, combat.pending_attack_bonus, len(encounter.ledger._consumed)))
        self.assertEqual(encounter.ledger.state(event), 'telegraph')

    def test_dead_knight_is_not_drawn(self):
        source = knight()
        source.health.apply_damage(3, tick=0)
        canvas = Mock()
        EnemyRenderer().draw(canvas, (source,))
        self.assertEqual(canvas.mock_calls, [])


class KnightSDLTests(unittest.TestCase):
    def test_native_sdl_dummy_draws_knight_and_single_landing_without_stage_three_gui(self):
        script = textwrap.dedent('''
            import sdl2 as s
            from pico2d import pico2d as canvas
            from combat import Combat
            from combat_resolution import CombatResolver
            from enemy_behaviors import EnemyEncounter
            from enemy_factory import create_stage_enemies
            from enemy_renderer import EnemyRenderer
            from enemy_attack_renderer import EnemyAttackRenderer
            from health_renderer import HealthRenderer
            from parry import Parry
            from parry_renderer import ParryResultRenderer
            from player import Player
            from stage_manager import StageCatalog
            assert s.SDL_Init(s.SDL_INIT_VIDEO) == 0
            window = s.SDL_CreateWindow(b'Knight offscreen test',0,0,1440,900,s.SDL_WINDOW_HIDDEN)
            renderer = s.SDL_CreateRenderer(window,-1,s.SDL_RENDERER_SOFTWARE)
            assert window and renderer
            try:
                canvas.window, canvas.renderer = window, renderer
                canvas.canvas_width, canvas.canvas_height = 1440,900
                stage = StageCatalog.load().get_stage(3)
                p,c,q = Player(*stage.player_spawn),Combat(),Parry()
                e = EnemyEncounter(create_stage_enemies(stage),combat_session_id=c.combat_session_id,
                                   stage_instance_id=c.stage_instance_id)
                r = CombatResolver(p,c,e,parry=q)
                r.advance(48)
                assert e.enemies[0].current_attack.target_cells == ((5,5),)
                EnemyAttackRenderer().draw(canvas,e.ledger)
                EnemyRenderer().draw(canvas,e.enemies)
                HealthRenderer().draw(canvas,p,e.enemies,c.tick)
                r.advance(245)
                assert c.tick == 293 and p.health.current_hp == 3
                r.register_parry(q.request(c.tick))
                r.advance(7)
                assert r.last_parry_result.status == 'perfect'
                assert c.pending_attack_bonus == 2 and e.enemies[0].state == 'stunned'
                ParryResultRenderer().draw(canvas,r.last_parry_result,c.tick)
                EnemyRenderer().draw(canvas,e.enemies)
                HealthRenderer().draw(canvas,p,e.enemies,c.tick,attack_bonus=c.pending_attack_bonus)
                s.SDL_RenderPresent(renderer)
            finally:
                s.SDL_DestroyRenderer(renderer)
                s.SDL_DestroyWindow(window)
                s.SDL_Quit()
        ''')
        result = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[1],
                                env={**os.environ, 'SDL_VIDEODRIVER': 'dummy'},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
