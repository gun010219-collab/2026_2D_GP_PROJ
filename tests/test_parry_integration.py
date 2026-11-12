"""Actual main-loop parry input, catch-up, pauses and rewards with fake time."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import main
import test_damage_integration as damage_helpers
from combat_resolution import CombatResolver
from config import FIXED_TIME_STEP
from enemy import Enemy
from parry import Parry

key = damage_helpers.key


class ParryIntegrationTests(unittest.TestCase):
    def run_loop(self, batches, **kwargs):
        captured, results = [], []
        parry = Parry()

        def capture(*args, **options):
            resolver = CombatResolver(*args, **options)
            captured.append(resolver)
            return resolver

        kwargs.setdefault('enemies', (Enemy('attacker', 4, 2, (0, -1), 0),))
        with patch.object(main, 'CombatResolver', side_effect=capture), \
                patch.object(main, 'Parry', return_value=parry):
            state = damage_helpers.DamageIntegrationTests().run_frames(
                batches, observe=lambda: results.append(captured[0].last_parry_result), **kwargs)
        return (*state, parry, captured[0], results)

    def test_real_input_and_hit_tick_obey_all_six_grade_boundaries(self):
        for delta, expected in ((0, None), (1, 'perfect'), (7, 'perfect'),
                                (8, 'normal'), (18, 'normal'), (19, None)):
            with self.subTest(delta=delta):
                batches = [[] for _ in range(40)]
                batches[39 - delta] = [key(1073742049)]
                player, _, combat, _, _, parry, resolver, results = self.run_loop(batches)
                result = resolver.last_parry_result
                self.assertEqual(parry.last_attempt.start_tick, 39 - delta)
                self.assertEqual(result.status, expected or 'unbound')
                self.assertEqual(player.health.current_hp, 3 if expected else 2)
                if expected:
                    self.assertTrue(all(item is None for item in results[:-1]))
                    self.assertEqual((result.tick, combat.tick), (39, 39))

    def test_shift_before_initial_ai_cannot_bind_a_future_telegraph(self):
        player, _, _, _, _, parry, resolver, _ = self.run_loop(
            [[key(1073742049)]] + [[] for _ in range(39)])
        self.assertEqual(player.health.current_hp, 2)
        self.assertEqual(resolver.parry_result(parry.last_attempt).status, 'unbound')
        self.assertIsNone(resolver.parry_binding(parry.last_attempt).linked_enemy_event_key)

    def test_zero_step_shift_is_applied_at_first_catchup_tick(self):
        batches = [[] for _ in range(32)] + [[key(1073742049)], []]
        lengths = [FIXED_TIME_STEP] * 31 + [0, FIXED_TIME_STEP * 8, FIXED_TIME_STEP]
        player, _, combat, _, _, parry, resolver, _ = self.run_loop(batches, lengths=lengths)
        self.assertEqual((parry.last_attempt.start_tick, combat.tick), (32, 39))
        self.assertEqual((resolver.last_parry_result.status, player.health.current_hp), ('perfect', 3))

    def test_newly_polled_shift_cannot_retroactively_parry_historical_hit(self):
        player, _, combat, _, _, parry, resolver, _ = self.run_loop(
            [[], [], [], [], [], [key(1073742049)]], lengths=[FIXED_TIME_STEP * 8] * 6)
        self.assertEqual((combat.tick, parry.last_attempt.start_tick), (40, 40))
        self.assertEqual((player.health.current_hp, player.health.last_damage_tick), (2, 39))
        self.assertEqual(resolver.last_parry_result.status, 'unbound')
        self.assertEqual(combat.pending_attack_bonus, 0)

    def test_linked_parry_survives_settings_pause_without_wall_time_advancement(self):
        menu = SimpleNamespace(type=1025, button=1, x=1295, y=41)
        batches = [[] for _ in range(32)] + [[key(1073742049)], [menu], [], [key(27)]]
        batches += [[] for _ in range(6)]
        lengths = [FIXED_TIME_STEP] * 33 + [20, 20, FIXED_TIME_STEP] + [FIXED_TIME_STEP] * 6
        player, _, combat, snapshots, _, parry, resolver, _ = self.run_loop(batches, lengths=lengths)
        self.assertEqual([s[0] for s in snapshots[33:36]], [33, 33, 33])
        self.assertEqual((combat.tick, parry.last_attempt.start_tick), (39, 32))
        self.assertEqual((player.health.current_hp, resolver.last_parry_result.status), (3, 'perfect'))

    def test_linked_parry_survives_focus_loss_and_gain(self):
        batches = [[] for _ in range(43)]
        batches[32] = [key(1073742049)]
        focus = [512] * 33 + [0, 0, 512] + [512] * 7
        lengths = [FIXED_TIME_STEP] * 32 + [20, 20, 20] + [FIXED_TIME_STEP] * 8
        player, _, combat, snapshots, _, parry, resolver, _ = self.run_loop(
            batches, lengths=lengths, focus=focus)
        self.assertEqual([s[0] for s in snapshots[32:36]], [32, 32, 32, 32])
        self.assertEqual((combat.tick, parry.last_attempt.start_tick), (39, 32))
        self.assertEqual((player.health.current_hp, resolver.last_parry_result.status), (3, 'perfect'))

    def test_f11_and_shift_release_do_not_change_link_or_create_another_attempt(self):
        batches = [[] for _ in range(40)]
        batches[32] = [key(1073742049), key(1073742053)]
        batches[33] = [key(1073741892), key(1073742049, False), key(1073742053, False)]
        player, _, _, _, display, parry, resolver, _ = self.run_loop(batches)
        self.assertEqual((parry.last_attempt.parry_id, parry.last_attempt.start_tick), (1, 32))
        self.assertEqual((resolver.last_parry_result.status, player.health.current_hp), ('perfect', 3))
        display.return_value.toggle.assert_called_once_with()

    def test_move_out_after_binding_gives_miss_without_a_success_reward(self):
        batches = [[] for _ in range(40)]
        batches[32] = [key(1073742049)]
        batches[33] = [key(1073741904)]
        player, encounter, combat, _, _, _, resolver, _ = self.run_loop(batches)
        self.assertEqual((player.health.current_hp, resolver.last_parry_result.status), (3, 'failed'))
        self.assertEqual(resolver.last_parry_result.reason, 'evaded')
        self.assertEqual(combat.pending_attack_bonus, 0)
        self.assertEqual(encounter.enemies[0].state, 'recovering')

    def test_player_kill_cancels_link_and_no_success_appears_later(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        enemy.health.apply_damage(1, tick=0)
        batches = [[] for _ in range(40)]
        batches[21] = [key(1073742049), key(1073741904), key(1073741904, False)]
        batches[39] = [key(1073741906), key(32)]
        player, _, combat, _, _, _, resolver, _ = self.run_loop(batches, enemies=(enemy,))
        self.assertEqual((enemy.health.current_hp, player.health.current_hp), (0, 3))
        self.assertEqual((resolver.last_parry_result.status, resolver.last_parry_result.tick), ('failed', 39))
        self.assertEqual(combat.pending_attack_bonus, 0)

    def test_perfect_resets_cooldown_and_spends_bonus_on_next_real_space_event(self):
        batches = [[] for _ in range(41)]
        batches[30] = [key(32)]
        batches[38] = [key(1073742049)]
        batches[40] = [key(32, False), key(32)]
        player, _, combat, _, _, _, resolver, _ = self.run_loop(batches)
        attack = combat.active_attack
        self.assertEqual((attack.attack_id, attack.start_tick, attack.damage_bonus), (2, 40, 2))
        self.assertEqual((combat.pending_attack_bonus, combat.next_attack_tick), (0, 76))
        self.assertEqual((player.health.current_hp, resolver.last_parry_result.status), (3, 'perfect'))

    def test_normal_does_not_reset_cooldown_grant_bonus_or_stun(self):
        batches = [[] for _ in range(41)]
        batches[30] = [key(32)]
        batches[31] = [key(1073742049)]
        batches[40] = [key(32, False), key(32)]
        player, encounter, combat, _, _, _, resolver, _ = self.run_loop(batches)
        self.assertEqual((combat.next_attack_tick, combat.pending_attack_bonus), (66, 0))
        self.assertEqual((resolver.last_parry_result.status, player.health.current_hp), ('normal', 3))
        self.assertEqual(encounter.enemies[0].state, 'recovering')

    def test_perfect_counter_space_kills_full_health_pawn_in_one_hit(self):
        batches = [[] for _ in range(59)]
        batches[32] = [key(1073742049)]
        batches[40] = [key(1073741904), key(1073741904, False)]
        batches[58] = [key(1073741906), key(32)]
        player, encounter, combat, _, _, _, resolver, _ = self.run_loop(batches)
        source = encounter.enemies[0]
        self.assertEqual((source.health.max_hp, source.health.current_hp), (2, 0))
        self.assertEqual((source.state, player.health.current_hp), ('inactive', 3))
        self.assertEqual(combat.active_attack.damage_bonus, 2)
        self.assertEqual(combat.pending_attack_bonus, 0)
        self.assertEqual(encounter.occupied_cells, frozenset())
        self.assertEqual(resolver.last_parry_result.status, 'perfect')

    def test_one_attempt_blocks_one_of_two_simultaneous_pawns_without_granting_immunity(self):
        batches = [[] for _ in range(40)]
        batches[32] = [key(1073742049), key(1073742053)]
        enemies = (Enemy('first', 4, 2, (0, -1), 0), Enemy('second', 6, 2, (0, -1), 0))
        player, encounter, combat, _, _, parry, resolver, _ = self.run_loop(batches, enemies=enemies)
        self.assertEqual((parry.last_attempt.parry_id, resolver.last_parry_result.status), (1, 'perfect'))
        self.assertEqual((player.health.current_hp, player.health.last_damage_tick), (2, 39))
        self.assertEqual((enemies[0].state, enemies[1].state), ('stunned', 'recovering'))
        self.assertEqual(combat.pending_attack_bonus, 2)
        self.assertEqual(resolver.last_parry_result.enemy_event_key[2], enemies[0].entity_instance_id)
