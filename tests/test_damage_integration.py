"""Real main-loop damage integration using fake time/SDL, never real sleeps."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import main
import test_main
from combat import Combat
from config import FIXED_TIME_STEP
from enemy import Enemy
from enemy_behaviors import PawnEncounter
from player import Player


def key(value, down=True):
    return SimpleNamespace(type=768 if down else 769, key=value)


class DamageIntegrationTests(unittest.TestCase):
    def run_frames(self, batches, *, player=None, enemies=None, lengths=None, focus=None,
                   initial_elapsed=0, observe=None):
        player = player if player is not None else Player(5, 1)
        enemies = enemies if enemies is not None else (Enemy('adjacent', 5, 2, (0, -1), 10),)
        combat = Combat()
        encounter = PawnEncounter(enemies)
        canvas = test_main.WindowLoopTests().make_canvas()
        all_batches = batches + [[SimpleNamespace(type=256)]]
        if focus is None:
            canvas.get_events.side_effect = all_batches
        else:
            queued = iter(zip(all_batches, focus + [focus[-1]]))

            def poll():
                events, flags = next(queued)
                canvas.SDL_GetWindowFlags.return_value = flags
                return events

            canvas.get_events.side_effect = poll
        now = [0.0]
        time_reads = [0]

        def time_now():
            if time_reads[0] == 1:
                now[0] += initial_elapsed
            time_reads[0] += 1
            return now[0]

        frame_lengths = iter(lengths or [FIXED_TIME_STEP] * len(batches))
        snapshots = []

        def rendered():
            snapshots.append((combat.tick, player.health.current_hp,
                              tuple(e.health.current_hp for e in enemies), player.position))
            if observe is not None:
                observe()
            now[0] += next(frame_lengths)

        canvas.update_canvas.side_effect = rendered
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings') as display, \
                patch.object(main, 'SettingsRenderer'), \
                patch.object(main, 'load_stage1_player', return_value=player), \
                patch.object(main, 'Combat', return_value=combat), \
                patch.object(main, 'PawnEncounter', return_value=encounter), \
                patch.object(main, 'perf_counter', side_effect=time_now), \
                patch.object(main, 'sleep'):
            main.main()
        self.assertEqual(canvas.close_canvas.call_count, 1)
        return player, encounter, combat, snapshots, display

    def test_space_hits_once_during_nine_effect_ticks_and_repeated_keydown(self):
        _, encounter, combat, snapshots, _ = self.run_frames(
            [[key(32), key(32)]] + [[] for _ in range(9)])
        self.assertTrue(all(snapshot[2] == (1,) for snapshot in snapshots))
        self.assertEqual(encounter.enemies[0].health.last_damage_tick, 0)
        self.assertIsNone(combat.active_attack)

    def test_second_attack_kills_and_same_batch_movement_uses_released_cell(self):
        player, encounter, _, _, _ = self.run_frames(
            [[key(32)]] + [[] for _ in range(35)] + [[key(32, False), key(32), key(1073741906)]])
        self.assertEqual(encounter.enemies[0].health.current_hp, 0)
        self.assertFalse(encounter.enemies[0].active)
        self.assertEqual(encounter.occupied_cells, frozenset())
        self.assertEqual(player.position, (5, 2))

    def test_same_tick_movement_cannot_retarget_previous_player_attack(self):
        _, encounter, combat, _, _ = self.run_frames([[key(32), key(1073741903)]])
        self.assertEqual(encounter.enemies[0].health.current_hp, 1)
        self.assertEqual(combat.active_attack.target_cell, (5, 2))

    def test_empty_attack_never_hits_an_enemy_that_arrives_in_the_effect_cell(self):
        enemy = Enemy('moving', 5, 3, (0, -1), 0)
        _, encounter, _, _, _ = self.run_frames([[key(32)]] + [[] for _ in range(8)], enemies=(enemy,))
        self.assertEqual(enemy.position, (5, 2))
        self.assertEqual(enemy.health.current_hp, 2)
        self.assertTrue(enemy.active)

    def test_exact_hit_tick_perfect_parry_prevents_damage(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        player, encounter, _, snapshots, _ = self.run_frames(
            [[] for _ in range(38)] + [[key(1073742049)], []], enemies=(enemy,))
        self.assertTrue(all(snapshot[1] == 3 for snapshot in snapshots[:-1]))
        self.assertEqual((snapshots[-1][0], player.health.current_hp), (39, 3))
        self.assertIsNone(player.health.last_damage_tick)
        self.assertEqual(enemy.state, 'stunned')
        event = enemy.current_attack
        self.assertIsNone(event)
        self.assertEqual(encounter.ledger.telegraphs, ())

    def test_move_on_exact_hit_tick_avoids_damage_and_no_later_rehit(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        player, encounter, _, _, _ = self.run_frames(
            [[] for _ in range(39)] + [[key(1073741903)]] + [[] for _ in range(17)] + [
                                     [key(1073741903, False), key(1073741904)]], enemies=(enemy,))
        self.assertEqual(player.position, (5, 1))
        self.assertEqual(player.health.current_hp, 3)
        self.assertIsNone(player.health.last_damage_tick)
        self.assertEqual(encounter.ledger.telegraphs, ())

    def test_current_tick_player_kill_cancels_due_before_enemy_damage(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        enemy.health.apply_damage(1, tick=0)
        player, encounter, _, _, _ = self.run_frames(
            [[] for _ in range(21)] + [[key(1073741904), key(1073741904, False)]] +
            [[] for _ in range(17)] + [[key(1073741906), key(32)]], enemies=(enemy,))
        # Left moves to (4,1); after release, the blocked up press faces the
        # Pawn without entering its cell, so SPACE kills it before due.
        self.assertEqual(player.health.current_hp, 3)
        self.assertEqual(enemy.health.current_hp, 0)
        self.assertEqual(enemy.state, 'inactive')
        self.assertEqual(encounter.ledger.telegraphs, ())

    def test_historical_hit_is_not_undone_by_new_input_in_an_eight_tick_frame(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        # 0,8,16,24,32,40: hit_tick39 is settled before input stamped40.
        player, _, combat, _, _ = self.run_frames(
            [[], [], [], [], [], [key(1073741903)]], enemies=(enemy,),
            lengths=[FIXED_TIME_STEP * 8] * 6)
        self.assertEqual((combat.tick, player.health.last_damage_tick), (40, 39))
        self.assertEqual(player.health.current_hp, 2)
        self.assertEqual(player.position, (6, 1))

    def test_menu_freezes_hp_and_due_until_resume(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        batches = [[] for _ in range(38)]
        batches += [[SimpleNamespace(type=1025, button=1, x=1295, y=41)], [], [key(27)], []]
        lengths = [FIXED_TIME_STEP] * 38 + [10, 10, FIXED_TIME_STEP, FIXED_TIME_STEP]
        _, _, _, snapshots, _ = self.run_frames(batches, enemies=(enemy,), lengths=lengths)
        self.assertEqual([snapshot[:2] for snapshot in snapshots[-4:]],
                         [(38, 3), (38, 3), (38, 3), (39, 2)])

    def test_f11_on_hit_tick_preserves_damage_and_ui(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        player, _, combat, snapshots, display = self.run_frames(
            [[] for _ in range(39)] + [[key(1073741892)]], enemies=(enemy,))
        self.assertEqual((combat.tick, player.health.current_hp), (39, 2))
        self.assertEqual(snapshots[-1][1], 2)
        display.return_value.toggle.assert_called_once_with()

    def test_focus_loss_and_gain_do_not_turn_wall_time_into_damage(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        player, _, combat, _, _ = self.run_frames(
            [[], [], [], [], []], enemies=(enemy,),
            lengths=[10, 10, 10, FIXED_TIME_STEP, FIXED_TIME_STEP], focus=[512, 0, 0, 512, 512])
        self.assertEqual((combat.tick, player.health.current_hp), (1, 3))

    def test_dead_player_freezes_simulation_but_f11_and_close_work(self):
        player = Player(5, 1)
        player.health.apply_damage(3, tick=0)
        _, encounter, combat, snapshots, display = self.run_frames(
            [[key(1073741906), key(32), key(1073742049)], [key(1073741892)], []], player=player)
        self.assertEqual((combat.tick, encounter.tick), (0, -1))
        self.assertTrue(all(snapshot[1] == 0 for snapshot in snapshots))
        self.assertEqual(player.position, (5, 1))
        self.assertIsNone(combat.active_attack)
        display.return_value.toggle.assert_called_once_with()

    def test_fatal_historical_hit_blocks_fresh_inputs_and_stops_all_remaining_ticks(self):
        player = Player(5, 1)
        player.health.apply_damage(2, tick=0)
        parry = main.Parry()
        attacker = Enemy('fatal-attacker', 4, 2, (0, -1), 0)
        waiting = Enemy('later-mover', 8, 6, (0, -1), 1)
        # Tick 0 accepts SPACE/Shift. A queued zero-step release is flushed at
        # tick 39 before its fatal hit. Input polled by the next 8-tick frame
        # belongs to a later time and must never act after death at tick 39.
        batches = [[key(32), key(1073742049)]] + [[] for _ in range(38)]
        batches += [[key(32, False), key(1073742049, False)],
                    [key(1073741906), key(1073741905), key(1073741904),
                     key(1073741903), key(32), key(1073742049)],
                    [key(32), key(1073742049)],
                    [key(32, False), key(1073742049, False),
                     key(32), key(1073742053)], []]
        lengths = [FIXED_TIME_STEP] * 38 + [0, FIXED_TIME_STEP * 8, 10, 10, 10, 10]
        with patch.object(main, 'Parry', return_value=parry), \
                patch.object(player.health, 'apply_damage', wraps=player.health.apply_damage) as damage:
            _, encounter, combat, snapshots, _ = self.run_frames(
                batches, player=player, enemies=(attacker, waiting), lengths=lengths)
        self.assertEqual((player.health.current_hp, player.health.last_damage_tick), (0, 39))
        damage.assert_called_once_with(1, tick=39)
        self.assertEqual((combat.tick, encounter.tick), (39, 39))
        self.assertEqual((player.position, player.facing), ((5, 1), 'up'))
        self.assertEqual(combat.next_attack_tick, 36)  # Only the tick-0 attack.
        self.assertIsNone(combat.active_attack)
        self.assertEqual((parry.last_attempt.parry_id, parry.last_attempt.start_tick), (1, 0))
        self.assertEqual((waiting.position, waiting.state, waiting.next_action_tick),
                         ((8, 6), 'initial_wait', 60))
        self.assertEqual((attacker.state, attacker.next_action_tick), ('recovering', 93))
        self.assertTrue(all(snapshot[:2] == (39, 0) for snapshot in snapshots[-4:]))

    def test_dead_player_settings_open_close_and_escape_exit_remain_available(self):
        player = Player(5, 1)
        player.health.apply_damage(100, tick=0)
        parry = main.Parry()
        menu = main.SettingsMenu()
        with patch.object(main, 'Parry', return_value=parry), \
                patch.object(main, 'SettingsMenu', return_value=menu):
            _, encounter, combat, snapshots, display = self.run_frames(
                [[SimpleNamespace(type=1025, button=1, x=1295, y=41)],
                 [key(1073741906), key(32), key(1073742049), key(27)],
                 [key(1073741892), key(32, False), key(1073742049, False)],
                 [key(27)]], player=player, lengths=[10, 10, 10, 10])
        self.assertFalse(menu.is_open)
        self.assertEqual(len(snapshots), 3)  # Last ESC exits before rendering.
        self.assertEqual((combat.tick, encounter.tick, player.health.current_hp), (0, -1, 0))
        self.assertEqual(player.position, (5, 1))
        self.assertIsNone(combat.active_attack)
        self.assertIsNone(parry.last_attempt)
        display.return_value.toggle.assert_called_once_with()

    def test_live_post_hit_immunity_pauses_in_settings_then_ends_at_tick_87(self):
        enemies = (Enemy('first-hit', 4, 2, (0, -1), 0),
                   Enemy('next-hit', 6, 2, (0, -1), .80))
        batches = [[] for _ in range(40)]
        batches += [[SimpleNamespace(type=1025, button=1, x=1295, y=41)], [], [key(27)], []]
        batches += [[] for _ in range(46)]
        lengths = ([FIXED_TIME_STEP] * 40 + [20, 20, FIXED_TIME_STEP, FIXED_TIME_STEP]
                   + [FIXED_TIME_STEP] * 46)
        captured, windows = [], []
        resolver_type = main.CombatResolver

        def capture_resolver(*args, **kwargs):
            resolver = resolver_type(*args, **kwargs)
            captured.append(resolver)
            return resolver

        with patch.object(main, 'CombatResolver', side_effect=capture_resolver):
            player, _, combat, snapshots, _ = self.run_frames(
                batches, enemies=enemies, lengths=lengths,
                observe=lambda: windows.append(captured[0].player_invulnerable_until_tick))
        self.assertEqual(snapshots[39][:2], (39, 2))
        self.assertEqual([snapshot[:2] for snapshot in snapshots[40:44]],
                         [(40, 2), (40, 2), (40, 2), (41, 2)])
        self.assertTrue(all(until == 87 for until in windows[39:-1]))
        self.assertEqual(snapshots[-2][:2], (86, 2))
        self.assertEqual((combat.tick, player.health.current_hp, player.health.last_damage_tick),
                         (87, 1, 87))

    def test_live_post_hit_immunity_pauses_on_focus_loss_and_gain(self):
        enemies = (Enemy('first-hit', 4, 2, (0, -1), 0),
                   Enemy('next-hit', 6, 2, (0, -1), .80))
        batches = [[] for _ in range(44 + 47)]
        lengths = ([FIXED_TIME_STEP] * 39 + [20, 20, 20, FIXED_TIME_STEP]
                   + [FIXED_TIME_STEP] * (len(batches) - 43))
        focus = [512] * 40 + [0, 0, 512, 512] + [512] * 47
        captured, windows = [], []
        resolver_type = main.CombatResolver

        def capture_resolver(*args, **kwargs):
            resolver = resolver_type(*args, **kwargs)
            captured.append(resolver)
            return resolver

        with patch.object(main, 'CombatResolver', side_effect=capture_resolver):
            player, _, combat, snapshots, _ = self.run_frames(
                batches, enemies=enemies, lengths=lengths, focus=focus,
                observe=lambda: windows.append(captured[0].player_invulnerable_until_tick))
        self.assertEqual([snapshot[:2] for snapshot in snapshots[39:44]],
                         [(39, 2), (39, 2), (39, 2), (39, 2), (40, 2)])
        self.assertTrue(all(until == 87 for until in windows[39:-1]))
        self.assertEqual(snapshots[-2][:2], (86, 2))
        self.assertEqual((combat.tick, player.health.current_hp, player.health.last_damage_tick),
                         (87, 1, 87))

    def test_initial_one_tick_frame_settles_initial_ai_without_skipping_tick(self):
        _, encounter, combat, _, _ = self.run_frames([[key(32)]], initial_elapsed=FIXED_TIME_STEP)
        self.assertEqual((combat.tick, encounter.tick), (1, 1))
        self.assertEqual(encounter.enemies[0].health.current_hp, 1)
        self.assertEqual(encounter.enemies[0].health.last_damage_tick, 1)

    def test_zero_step_quick_tap_waits_for_next_tick_and_hits_once(self):
        _, encounter, combat, snapshots, _ = self.run_frames(
            [[], [key(32), key(32, False)], []], lengths=[0, FIXED_TIME_STEP, FIXED_TIME_STEP])
        self.assertEqual([snapshot[2] for snapshot in snapshots], [(2,), (2,), (1,)])
        self.assertEqual((combat.active_attack.start_tick, encounter.enemies[0].health.last_damage_tick), (1, 1))

    def test_zero_step_input_after_hit_is_stamped_next_tick_without_rollback(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        enemy.health.apply_damage(1, tick=0)
        batches = [[] for _ in range(40)]
        batches += [[key(1073741904), key(1073741904, False), key(1073741906), key(32)], []]
        lengths = [FIXED_TIME_STEP] * 39 + [0, FIXED_TIME_STEP, FIXED_TIME_STEP]
        player, _, combat, snapshots, _ = self.run_frames(batches, enemies=(enemy,), lengths=lengths)
        self.assertEqual(snapshots[40][:3], (39, 2, (1,)))
        # The quick turn is discarded by the approved 18-tick move gate;
        # SPACE still executes at tick40 without undoing tick39 damage.
        self.assertEqual(snapshots[41][:3], (40, 2, (1,)))
        self.assertEqual(combat.active_attack.target_cell, (3, 1))
        self.assertEqual((player.health.last_damage_tick, combat.active_attack.start_tick), (39, 40))

    def test_modal_transition_discards_pending_quick_tap_without_attack(self):
        _, encounter, combat, _, _ = self.run_frames(
            [[], [key(32), key(32, False), SimpleNamespace(type=1025, button=1, x=1295, y=41)],
             [key(27)], []], lengths=[0, FIXED_TIME_STEP, FIXED_TIME_STEP, FIXED_TIME_STEP])
        self.assertEqual(encounter.enemies[0].health.current_hp, 2)
        self.assertIsNone(combat.active_attack)

    def test_f11_discards_pending_press_and_keeps_tail_release(self):
        _, encounter, combat, _, _ = self.run_frames(
            [[], [key(32), key(1073741892), key(32, False)], [key(32)]],
            lengths=[0, FIXED_TIME_STEP, FIXED_TIME_STEP])
        self.assertEqual(encounter.enemies[0].health.current_hp, 1)
        self.assertEqual(combat.active_attack.attack_id, 1)

    def test_focus_loss_discards_pending_attack_until_a_fresh_press(self):
        _, encounter, combat, _, _ = self.run_frames(
            [[], [key(32)], [], [], [], [key(32)]],
            lengths=[0, FIXED_TIME_STEP, FIXED_TIME_STEP, FIXED_TIME_STEP,
                     FIXED_TIME_STEP, FIXED_TIME_STEP], focus=[512, 512, 0, 512, 512, 512])
        self.assertEqual(encounter.enemies[0].health.current_hp, 1)
        self.assertEqual(combat.active_attack.attack_id, 1)

    def test_queued_dodge_precedes_first_hit_tick_in_eight_tick_catchup(self):
        enemy = Enemy('attacker', 4, 2, (0, -1), 0)
        # Render tick38 twice: the second frame queues a dodge. It belongs to
        # tick39, before damage, even when the following frame reaches tick46.
        batches = [[] for _ in range(39)] + [[key(1073741903)], []]
        lengths = [FIXED_TIME_STEP] * 38 + [0, FIXED_TIME_STEP * 8, FIXED_TIME_STEP]
        player, _, combat, snapshots, _ = self.run_frames(batches, enemies=(enemy,), lengths=lengths)
        self.assertEqual(snapshots[-2][:2], (38, 3))
        self.assertEqual((combat.tick, player.health.current_hp, player.position), (46, 3, (6, 1)))
        self.assertIsNone(player.health.last_damage_tick)
