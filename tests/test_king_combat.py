"""King melee in the shared resolver; no Pulse or playable Stage 5."""
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest
from unittest.mock import Mock

import main
from board import tile_bounds
from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from enemy_factory import create_stage_enemies
from enemy_renderer import EnemyRenderer
from enemy_attack_renderer import EnemyAttackRenderer
from game import GameState, StageGame
from health_renderer import HealthRenderer
from parry import Parry
from player import Player
from stage_manager import StageCatalog
from tests.test_king import king


def battle(enemies=None, player=None):
    p = player if player is not None else Player(5, 1)
    c, q = Combat(), Parry()
    e = EnemyEncounter((king(),) if enemies is None else enemies,
                       combat_session_id=c.combat_session_id, stage_instance_id=c.stage_instance_id)
    r = CombatResolver(p, c, e, parry=q)
    r.resolve_current_tick()
    return p, c, q, e, r


def parry_at(parts, tick):
    p, c, q, e, r = parts
    r.advance(tick - c.tick)
    attempt = q.request(c.tick)
    r.register_parry(attempt)
    return attempt


class KingCombatTests(unittest.TestCase):
    def test_exact_48_tick_hit_one_damage_and_90_tick_recovery_boundary(self):
        p, c, q, e, r = battle()
        source, event = e.enemies[0], e.enemies[0].current_attack
        r.advance(47)
        self.assertEqual(p.health.current_hp, 3)
        self.assertIsNone(r.resolve_enemy_attack(event))
        result = r.advance(1)[0]
        self.assertEqual((result.tick, result.amount, p.health.current_hp), (48, 1, 2))
        self.assertEqual((source.position, source.state, source.next_action_tick), ((5, 2), 'recovering', 138))
        for _ in range(5):
            self.assertIsNone(r.resolve_enemy_attack(event))
        self.assertEqual(p.health.current_hp, 2)
        r.advance(89)
        self.assertEqual(source.state, 'recovering')
        r.advance(1)
        self.assertEqual(source.current_attack.start_tick, 138)
        self.assertNotEqual(source.current_attack.key, event.key)

    def test_evade_keeps_original_target_and_does_not_move_king_or_hit_new_cell(self):
        p, c, q, e, r = battle()
        event = e.enemies[0].current_attack
        p.move('left', e.occupied_cells)
        r.advance(48)
        self.assertEqual((p.position, p.health.current_hp, e.enemies[0].position), ((4, 1), 3, (5, 2)))
        self.assertEqual(event.target_cells, ((5, 1),))
        self.assertEqual(e.ledger.outcome(event), 'miss')
        p.move('right', e.occupied_cells)
        self.assertIsNone(r.resolve_enemy_attack(event))
        self.assertEqual(p.health.current_hp, 3)

    def test_active_enemy_entering_empty_target_does_not_shrink_or_cancel_melee(self):
        pawn = Enemy('p', 5, 0, (0, -1), .5)
        p, c, q, e, r = battle((king(), pawn))
        event = e.enemies[0].current_attack
        p.move('left', e.occupied_cells)
        r.advance(48)
        self.assertEqual(pawn.position, (5, 1))
        self.assertEqual(event.target_cells, ((5, 1),))
        self.assertEqual(e.ledger.outcome(event), 'miss')
        self.assertEqual(e.enemies[0].position, (5, 2))

    def test_actual_normal_perfect_time_boundaries_do_not_reflect_two_damage(self):
        for delta, grade in ((0, 'unbound'), (1, 'perfect'), (7, 'perfect'),
                             (8, 'normal'), (18, 'normal'), (19, 'unbound')):
            parts = battle()
            p, c, q, e, r = parts
            attempt = parry_at(parts, 48 - delta)
            r.advance(delta)
            self.assertEqual(r.parry_result(attempt).status, grade)
            self.assertEqual(p.health.current_hp, 2 if grade == 'unbound' else 3)
            self.assertEqual(e.enemies[0].health.current_hp, 8)  # No Pulse reflection.
            self.assertEqual(c.pending_attack_bonus, 2 if grade == 'perfect' else 0)

    def test_normal_has_no_counter_cooldown_reset_stun_or_invulnerability(self):
        parts = battle()
        p, c, q, e, r = parts
        r.advance(30)
        r.resolve_player_attack(c.request_attack(p))
        attempt = q.request(c.tick)
        r.register_parry(attempt)
        r.advance(18)
        self.assertEqual((r.parry_result(attempt).status, p.health.current_hp, c.next_attack_tick,
                          c.pending_attack_bonus, r.player_invulnerable_until_tick), ('normal', 3, 66, 0, 0))
        self.assertEqual((e.enemies[0].state, e.enemies[0].next_action_tick), ('recovering', 138))

    def test_perfect_only_stuns_actual_king_60_ticks_and_resumes_with_new_melee(self):
        parts = battle((king(), Enemy('p', 9, 9, (0, -1), 10)))
        p, c, q, e, r = parts
        attempt = parry_at(parts, 41)
        event = e.enemies[0].current_attack
        r.advance(7)
        self.assertEqual((r.parry_result(attempt).status, e.enemies[0].state,
                          e.enemies[0].stun_until_tick), ('perfect', 'stunned', 108))
        self.assertNotEqual(e.enemies[1].state, 'stunned')
        r.advance(59)
        self.assertEqual(e.enemies[0].state, 'stunned')
        r.advance(1)
        self.assertEqual(e.enemies[0].current_attack.start_tick, 108)
        self.assertNotEqual(e.enemies[0].current_attack.key, event.key)
        self.assertEqual(e.ledger.outcome(event), 'parried_perfect')

    def test_perfect_counter_resets_cooldown_and_next_space_deals_three_once(self):
        parts = battle()
        p, c, q, e, r = parts
        r.advance(41)
        p.move('left', e.occupied_cells)
        r.resolve_player_attack(c.request_attack(p))  # Miss on a valid empty cell.
        p.move('right', e.occupied_cells)
        p.move('up', e.occupied_cells)  # Blocked by King; face up without overlap.
        attempt = q.request(c.tick)
        r.register_parry(attempt)
        event = e.enemies[0].current_attack
        r.advance(7)
        self.assertEqual((c.next_attack_tick, c.pending_attack_bonus), (48, 2))
        attack = c.request_attack(p)
        result = r.resolve_player_attack(attack)
        self.assertEqual((attack.damage_bonus, result.amount, e.enemies[0].health.current_hp), (2, 3, 5))
        self.assertEqual(c.pending_attack_bonus, 0)
        for _ in range(5):
            self.assertIsNone(r.resolve_player_attack(attack))
            self.assertIsNone(r.resolve_enemy_attack(event))
            r.register_parry(attempt)
        self.assertEqual((c.pending_attack_bonus, e.enemies[0].health.current_hp), (0, 5))

    def test_perfect_bonus_miss_is_consumed_without_harming_king(self):
        parts = battle()
        p, c, q, e, r = parts
        parry_at(parts, 41)
        r.advance(7)
        p.move('left', e.occupied_cells)
        attack = c.request_attack(p)
        self.assertEqual(attack.damage_bonus, 2)
        self.assertIsNone(r.resolve_player_attack(attack))
        self.assertEqual((c.pending_attack_bonus, e.enemies[0].health.current_hp), (0, 8))

    def test_existing_invulnerability_closes_attack_without_counter_or_late_rehit(self):
        parts = battle()
        p, c, q, e, r = parts
        attempt = parry_at(parts, 41)
        event = e.enemies[0].current_attack
        r.player_invulnerable_until_tick = 49
        r.advance(7)
        self.assertEqual((e.ledger.outcome(event), r.parry_result(attempt).reason), ('invulnerable', 'invulnerable'))
        self.assertEqual((p.health.current_hp, c.pending_attack_bonus), (3, 0))
        r.advance(1)
        self.assertIsNone(r.resolve_enemy_attack(event))

    def test_actual_king_damage_obeys_48_tick_invulnerability_end(self):
        for start, outcome in ((47, 'invulnerable'), (48, 'hit')):
            p, c, q, e, r = battle((king('a'), king('b', 4, 1, start / 60)))
            r.advance(start)
            event = e.enemies[1].current_attack
            r.advance(48)
            self.assertEqual(e.ledger.outcome(event), outcome)
            self.assertEqual(p.health.current_hp, 2 if outcome == 'invulnerable' else 1)

    def test_fatal_player_attack_on_hit_tick_cancels_king_and_releases_occupancy(self):
        p, c, q, e, r = battle((king(hp=1),))
        event = e.enemies[0].current_attack
        r.advance(47)
        c.advance()
        result = r.resolve_player_attack(c.request_attack(p))
        r.resolve_current_tick()
        self.assertEqual((result.amount, e.enemies[0].health.current_hp, p.health.current_hp), (1, 0, 3))
        self.assertNotIn((5, 2), e.occupied_cells)
        self.assertEqual(e.ledger.state(event), 'cancelled')
        self.assertIsNone(r.resolve_player_attack(c.active_attack))

    def test_stun_death_and_stop_cancel_all_unresolved_melee_without_rewards(self):
        for cause in ('stun', 'death', 'stop'):
            parts = battle()
            p, c, q, e, r = parts
            event = e.enemies[0].current_attack
            attempt = parry_at(parts, 41)
            if cause == 'stun':
                e.stun(e.enemies[0].entity_instance_id, c.tick)
            elif cause == 'death':
                e.enemies[0].health.apply_damage(8, tick=c.tick)
                e.deactivate(e.enemies[0].entity_instance_id)
            else:
                r.stop()
            r.advance(7)
            self.assertEqual(e.ledger.state(event), 'cancelled')
            self.assertEqual((p.health.current_hp, c.pending_attack_bonus), (3, 0))
            self.assertIsNone(r.resolve_enemy_attack(event))
            self.assertEqual(e._attack_moves, {})

    def test_foreign_modified_and_ledger_only_melee_cannot_affect_this_session(self):
        old = battle()
        old_event = old[-2].enemies[0].current_attack
        attempt = parry_at(old, 41)
        p, c, q, e, r = battle()
        with self.assertRaises(ValueError):
            r.resolve_enemy_attack(old_event)
        with self.assertRaises(ValueError):
            r.register_parry(attempt)
        event = e.enemies[0].current_attack
        for bad in (replace(event, hit_tick=49), replace(event, target_cells=((4, 1),))):
            with self.assertRaises(ValueError):
                r.resolve_enemy_attack(bad)
        fake = e.ledger.create(e.enemies[0].entity_instance_id, 0, 1, ((5, 1),))
        c.advance()
        e.advance_to(1, p.position)
        e.ledger.mark_due(fake, 1)
        with self.assertRaisesRegex(ValueError, 'melee plan'):
            r.resolve_enemy_attack(fake)
        self.assertEqual(p.health.current_hp, 3)

    def test_late_melee_expires_without_damage_or_movement(self):
        p, c, q, e, r = battle()
        event = e.enemies[0].current_attack
        c.advance(49)
        e.advance_to(49, p.position)
        self.assertIsNone(r.resolve_enemy_attack(event))
        self.assertEqual(e.ledger.outcome(event), 'expired')
        self.assertEqual((p.health.current_hp, e.enemies[0].position), (3, (5, 2)))

    def test_invalid_king_damage_is_rejected_before_resolution(self):
        for amount in (0, -1, True, 1.5, '1'):
            p, c, q, e, r = battle()
            with self.assertRaises((TypeError, ValueError)):
                CombatResolver(p, c, e, parry=q, king_damage=amount)


class KingMixedTests(unittest.TestCase):
    def test_stage_five_real_instances_advance_on_one_ledger_without_pulse_at_240(self):
        stage = StageCatalog.load().get_stage(5)
        p, c, q, e, r = battle(create_stage_enemies(stage))
        for _ in range(240):
            cells = [p.position] + [x.position for x in e.enemies if x.active]
            self.assertEqual(len(cells), len(set(cells)))
            r.advance(1)
        self.assertEqual((c.tick, e.enemies[0].position, e.enemies[0].state), (240, (5, 6), 'waiting'))
        self.assertTrue(all(len(event.target_cells) < 100 for event in e.ledger.telegraphs))
        self.assertEqual(e.enemies[0].health.current_hp, 8)
        self.assertEqual(p.health.current_hp, 2)  # Rook still acts; no DRAINING/freeze.
        self.assertEqual([x.kind for x in e.enemies], ['king', 'rook', 'pawn', 'pawn'])

    def test_five_kinds_same_tick_keep_json_order_parry_link_and_single_consumption(self):
        for order in ('krnpb', 'bkrnp'):
            enemies = {'k': king(delay=1), 'r': Enemy('r', 2, 1, None, 1, kind='rook'),
                       'n': Enemy('n', 4, 3, None, 1.2, kind='knight'),
                       'p': Enemy('p', 4, 2, (0, -1), 1.15),
                       'b': Enemy('b', 2, 8, None, 0, kind='bishop')}
            parts = battle(tuple(enemies[k] for k in order))
            p, c, q, e, r = parts
            attempt = parry_at(parts, 101)  # Bishop was published first in either order.
            events = [x.current_attack for x in e.enemies]
            self.assertTrue(all(event.hit_tick == 108 for event in events))
            r.advance(7)
            self.assertEqual(p.health.current_hp, 2)
            self.assertEqual(c.pending_attack_bonus, 2 if order[0] == 'b' else 0)
            self.assertEqual(r.parry_result(attempt).status, 'perfect' if order[0] == 'b' else 'failed')
            self.assertEqual(enemies['k'].health.current_hp, 8)
            for event in events:
                self.assertEqual(e.ledger.state(event), 'resolved')
                self.assertIsNone(r.resolve_enemy_attack(event))

    def test_king_first_death_keeps_other_enemy_ai_and_generic_outcome_adapter_playing(self):
        p, c, q, e, r = battle((king(hp=1), Enemy('p', 9, 9, (0, -1), 0)))
        # Exercise the existing generic outcome predicate, not a playable Stage 5/BOSS_CLEAR.
        game = StageGame(p, c, e, q, r)
        r.resolve_player_attack(c.request_attack(p))
        self.assertFalse(game.update_state())
        self.assertTrue(game.playing)
        before = e.enemies[1].position
        game.advance(132)
        self.assertNotEqual(e.enemies[1].position, before)
        e.enemies[1].health.apply_damage(2, tick=c.tick)
        game.update_state()
        self.assertEqual(game.state, GameState.STAGE_CLEAR)
        self.assertTrue(r.stopped)
        tick = c.tick
        game.advance(100)
        self.assertEqual(c.tick, tick)

    def test_mixed_runs_are_deterministic_and_no_dead_or_stopped_king_moves(self):
        traces = []
        for _ in range(2):
            stage = StageCatalog.load().get_stage(5)
            p, c, q, e, r = battle(create_stage_enemies(stage))
            rows = []
            for _ in range(601):
                cells = [p.position] + [x.position for x in e.enemies if x.active]
                self.assertEqual(len(cells), len(set(cells)))
                rows.append((c.tick, p.health.current_hp,
                             [(x.kind, x.position, x.state, x.health.current_hp) for x in e.enemies]))
                r.advance(1)
            traces.append(rows)
        self.assertEqual(traces[0], traces[1])
        self.assertEqual(traces[0][-1], traces[0][-2])

    def test_stage_five_main_stage_game_and_stage_four_continuation_stay_disabled(self):
        # Task 1-Q opens Stage 5; retain metadata rejection and Stage 6 boundary.
        self.assertTrue(main._new_stage_game(5).boss)
        with self.assertRaises(ValueError):
            main._new_stage_game(6)
        g = main._new_stage_game(4)
        with self.assertRaises(ValueError):
            StageGame(g.player, g.combat, g.encounter, g.parry, g.resolver, stage_number=5)
        for x in g.encounter.enemies:
            x.health.apply_damage(x.health.current_hp, tick=0)
        g.update_state()
        self.assertEqual(g.next_stage_number, 5)
        self.assertEqual(g.restart_stage_number, 4)


class KingRenderTests(unittest.TestCase):
    def test_crown_is_distinct_fits_all_cells_and_disappears_on_death(self):
        for col in range(10):
            for row in range(10):
                source = king(col=col, row=row)
                canvas = Mock()
                EnemyRenderer().draw(canvas, (source,))
                canvas.draw_circle.assert_not_called()
                left, bottom, right, top = tile_bounds(col, row)
                for call in canvas.draw_rectangle.call_args_list:
                    x1, y1, x2, y2 = call.args[:4]
                    self.assertTrue(left < x1 <= x2 < right - 1 and bottom < y1 <= y2 < top - 1)
                    self.assertLessEqual(y2, (bottom + top) / 2 + 27)
        other = Mock()
        EnemyRenderer().draw(other, (Enemy('r', 9, 9, None, 0, kind='rook'),))
        self.assertNotEqual(canvas.mock_calls, other.mock_calls)
        source.health.apply_damage(8, tick=0)
        dead = Mock()
        EnemyRenderer().draw(dead, (source,))
        self.assertEqual(dead.mock_calls, [])

    def test_warning_single_cell_and_actual_hp_feedback_are_read_only(self):
        p, c, q, e, r = battle()
        event = e.enemies[0].current_attack
        r.resolve_player_attack(c.request_attack(p))
        self.assertEqual(e.enemies[0].health.current_hp, 7)
        before = (p.health.current_hp, c.tick, e.enemies[0].position, e.enemies[0].health.current_hp,
                  c.pending_attack_bonus, len(e.ledger._consumed))
        for _ in range(5):
            canvas = Mock()
            EnemyAttackRenderer().draw(canvas, e.ledger)
            self.assertEqual(canvas.draw_rectangle.call_count, 2)
            self.assertEqual(event.target_cells, ((5, 1),))
            EnemyRenderer().draw(canvas, e.enemies)
            HealthRenderer().draw(canvas, p, e.enemies, c.tick)
        self.assertEqual(before, (p.health.current_hp, c.tick, e.enemies[0].position,
                                 e.enemies[0].health.current_hp, c.pending_attack_bonus, len(e.ledger._consumed)))

    def test_native_sdl_renders_real_king_melee_perfect_without_pulse_reflection(self):
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
            window = s.SDL_CreateWindow(b'King melee test',0,0,1440,900,s.SDL_WINDOW_HIDDEN)
            renderer = s.SDL_CreateRenderer(window,-1,s.SDL_RENDERER_SOFTWARE)
            assert window and renderer
            try:
                canvas.window,canvas.renderer = window,renderer
                canvas.canvas_width,canvas.canvas_height = 1440,900
                stage = StageCatalog.load().get_stage(5)
                p,c,q = Player(*stage.player_spawn),Combat(),Parry()
                enemies = create_stage_enemies(stage)
                for _ in range(7):
                    assert p.move('up',frozenset(e.position for e in enemies))
                e = EnemyEncounter(enemies,combat_session_id=c.combat_session_id,stage_instance_id=c.stage_instance_id)
                r = CombatResolver(p,c,e,parry=q)
                r.advance(48)
                assert e.enemies[0].current_attack.target_cells == ((5,8),)
                assert e.enemies[0].current_attack.hit_tick == 96
                EnemyAttackRenderer().draw(canvas,e.ledger)
                EnemyRenderer().draw(canvas,enemies)
                HealthRenderer().draw(canvas,p,enemies,c.tick)
                r.advance(41)
                r.register_parry(q.request(c.tick))
                r.advance(7)
                assert r.last_parry_result.status == 'perfect'
                assert p.health.current_hp == 3 and enemies[0].health.current_hp == 8
                assert c.pending_attack_bonus == 2 and enemies[0].stun_until_tick == 156
                ParryResultRenderer().draw(canvas,r.last_parry_result,c.tick)
                EnemyRenderer().draw(canvas,enemies)
                HealthRenderer().draw(canvas,p,enemies,c.tick,attack_bonus=c.pending_attack_bonus)
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
