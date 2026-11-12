"""Stage 3 factories, flow and actual main combat with integer fake time."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main
from config import FIXED_TIME_STEP
from game import GameState
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from stage_manager import StageCatalog
from tests.test_stage_transition import (N, R, UP, LEFT, SPACE, SHIFT, F11, ESC,
                                         MENU, key, finish, run_loop)


RIGHT, DOWN = 1073741903, 1073741905


def play_to(end, *, inputs=None, samples=(), observe=None, factory=None):
    """Run real main at chosen ticks; each frame advances at most eight ticks."""
    inputs = inputs or {}
    ticks = sorted(set(range(0, end + 1, 8)) | {end} | set(inputs) | set(samples))
    assert ticks[0] == 0 and ticks[-1] == end
    batches = [inputs.get(tick, []) for tick in ticks]
    lengths = [(b - a) * FIXED_TIME_STEP for a, b in zip(ticks, ticks[1:])]
    lengths.append(FIXED_TIME_STEP)
    return run_loop(batches, initial_stage=3, initial='playing', lengths=lengths,
                    initial_factory=factory,
                    after_render=(lambda game, frame: observe(game, ticks[frame])) if observe else None)


class StageThreeSessionTests(unittest.TestCase):
    def test_all_three_factories_preserve_catalog_spawns_and_scopes(self):
        catalog = StageCatalog.load()
        for number in (1, 2, 3):
            game = main._new_stage_game(number)
            definition = catalog.get_stage(number)
            self.assertEqual((game.stage_number, game.chapter, game.player.position,
                              game.player.facing, game.player.health.current_hp, game.combat.tick),
                             (number, 1, definition.player_spawn, 'up', 3, 0))
            self.assertEqual([(e.data_id, e.kind, e.position, e.initial_delay) for e in game.encounter.enemies],
                             [(e.data_id, e.kind, e.position, e.initial_delay) for e in definition.enemies])
            self.assertEqual(game.encounter.ledger.stage_instance_id, game.combat.stage_instance_id)
        self.assertEqual([e.health.current_hp for e in game.encounter.enemies], [3, 2, 2])
        self.assertEqual([e.initial_delay_ticks for e in game.encounter.enemies], [48, 62, 75])
        self.assertEqual([e.position for e in game.encounter.enemies], [(3, 6), (1, 6), (8, 6)])

    def test_future_stages_are_rejected_before_catalog_or_entity_creation(self):
        with patch.object(main.StageCatalog, 'load') as load:
            for number in range(10, 26):
                with self.assertRaises(ValueError):
                    main._new_stage_game(number)
            load.assert_not_called()

    def test_third_stage_requires_all_three_deaths_and_game_over_wins_tie(self):
        for tie in (False, True):
            game = main._new_stage_game(3)
            for enemy in game.encounter.enemies[:2]:
                enemy.health.apply_damage(enemy.health.max_hp, tick=0)
                game.encounter.deactivate(enemy.entity_instance_id)
            self.assertFalse(game.update_state())
            last = game.encounter.enemies[-1]
            last.health.apply_damage(last.health.max_hp, tick=0)
            if tie:
                game.player.health.apply_damage(3, tick=0)
            self.assertTrue(game.update_state())
            self.assertEqual(game.state, GameState.GAME_OVER if tie else GameState.UPGRADE)
            self.assertFalse(game.update_state())
            self.assertEqual(game.transition_count, 1)
            self.assertEqual(game.next_stage_number, None)

    def test_every_transition_builds_fresh_objects_and_rejects_previous_events(self):
        for before, after in ((1, 2), (2, 3), (3, 3), (3, 1)):
            old = main._new_stage_game(before)
            old.advance(48 if before != 2 else 120)
            attack = old.combat.request_attack(old.player)
            attempt = old.parry.request(old.combat.tick)
            old.resolver.register_parry(attempt)
            event = old.encounter.enemies[0].current_attack
            old.combat.grant_perfect_counter()
            old.resolver.player_invulnerable_until_tick = old.combat.tick + 48
            old.encounter.stun(old.encounter.enemies[0].entity_instance_id, old.combat.tick)
            old.resolver.stop()
            fresh = main._new_stage_game(after)
            for attr in ('player', 'combat', 'parry', 'encounter', 'resolver'):
                self.assertIsNot(getattr(old, attr), getattr(fresh, attr))
            self.assertNotEqual(old.player.entity_instance_id, fresh.player.entity_instance_id)
            self.assertNotEqual(old.combat.stage_instance_id, fresh.combat.stage_instance_id)
            self.assertNotEqual(old.combat.combat_session_id, fresh.combat.combat_session_id)
            self.assertTrue({e.entity_instance_id for e in old.encounter.enemies}.isdisjoint(
                e.entity_instance_id for e in fresh.encounter.enemies))
            self.assertEqual((fresh.combat.tick, fresh.combat.next_attack_tick, fresh.parry.next_parry_tick,
                              fresh.combat.pending_attack_bonus, fresh.resolver.player_invulnerable_until_tick),
                             (0, 0, 0, 0, 0))
            self.assertEqual(fresh.player.position, (5, 1))
            self.assertEqual(fresh.player.health.current_hp, 3)
            self.assertIsNone(fresh.player.health.last_damage_tick)
            self.assertIsNone(fresh.parry.last_attempt)
            self.assertIsNone(fresh.resolver.last_parry_result)
            self.assertEqual(fresh.encounter.ledger.telegraphs, ())
            self.assertTrue(all(e.current_attack is None and e.stun_until_tick == 0
                                for e in fresh.encounter.enemies))
            with self.assertRaises(ValueError):
                fresh.resolver.resolve_player_attack(attack)
            with self.assertRaises(ValueError):
                fresh.resolver.register_parry(attempt)
            if event is not None:
                with self.assertRaises(ValueError):
                    fresh.resolver.resolve_enemy_attack(event)

    def test_end_states_freeze_tick_ai_damage_reward_and_pending_landing(self):
        for state in ('clear', 'dead'):
            game = main._new_stage_game(3)
            game.advance(48)
            event = game.encounter.enemies[0].current_attack
            finish(game, state)
            before = (game.combat.tick, game.player.health.current_hp,
                      tuple(e.position for e in game.encounter.enemies), game.combat.pending_attack_bonus)
            for _ in range(3):
                self.assertEqual(game.advance(1000), ())
                self.assertIsNone(game.resolver.resolve_enemy_attack(event))
                self.assertFalse(game.encounter.complete_attack(event, game.player.position))
            self.assertEqual(game.encounter.ledger.state(event), 'cancelled')
            self.assertEqual(before, (game.combat.tick, game.player.health.current_hp,
                                     tuple(e.position for e in game.encounter.enemies), game.combat.pending_attack_bonus))


class StageThreeFlowTests(unittest.TestCase):
    def test_one_through_four_progress_reuses_window_and_rejects_stage_five(self):
        def clear_each(game, frame):
            if game.playing:
                finish(game, 'clear')
        created, snapshots, _, _, _, clock = run_loop(
            [batch for k in (49,49,50,50) for batch in ([key(k),key(k,False)], [])], after_render=clear_each)
        self.assertEqual([g.stage_number for g in created], [1, 2, 3, 4, 5])
        self.assertEqual([s['stage'] for s in snapshots], [2,2,3,3,4,4,5,5])
        self.assertTrue(all(s['tick'] == 0 for s in snapshots))
        self.assertEqual(clock.accumulator, 0)

    def test_third_stage_clear_replays_three_and_game_over_retries_one(self):
        for state in ('clear','dead'):
            created,snapshots,_,_,_,_=run_loop([[key(R)],[]],initial_stage=3,initial=state)
            self.assertEqual([g.stage_number for g in created],[3] if state=='clear' else [3,1])
            self.assertEqual(snapshots[0]['tick'],0)
            if state=='clear':
                self.assertEqual(created[0].state,GameState.UPGRADE)
                self.assertIsNone(created[0].next_stage_number)
                self.assertIsNone(created[0].restart_stage_number)
            else:
                self.assertEqual(created[-1].player.health.current_hp,3)
                self.assertTrue(created[-1].playing)

    def test_stage_three_keys_follow_playing_and_terminal_policy(self):
        for state in ('playing', 'dead', 'clear'):
            events = [key(N), key(R)] if state == 'playing' else [key(N)]
            created, _, _, _, _, _ = run_loop([events], initial_stage=3, initial=state)
            self.assertEqual([g.stage_number for g in created], [3])

    def test_stage_two_clear_held_n_requires_release_before_third_stage(self):
        def clear_two(game, frame):
            if frame == 0:
                finish(game, 'clear')
        created, snapshots, _, _, _, _ = run_loop(
            [[key(49)], [key(49)], [key(49, repeat=True)], [key(49, False)], [key(49)]],
            after_render=clear_two)
        self.assertEqual([s['count'] for s in snapshots], [2, 2, 2, 2, 3])
        self.assertEqual([g.stage_number for g in created], [1, 2, 3])

    def test_transition_to_three_blocks_same_batch_and_held_combat_keys(self):
        created, snapshots, _, _, _, _ = run_loop([
            [key(49), key(UP), key(SPACE), key(SHIFT), key(R), key(49)],
            [key(UP), key(SPACE), key(SHIFT), key(R)],
            [key(UP, False), key(SPACE, False), key(SHIFT, False), key(R, False), key(49, False)],
            [key(UP), key(SPACE), key(SHIFT)]], initial_stage=2)
        self.assertEqual([g.stage_number for g in created], [2, 3])
        self.assertTrue(all(s['position'] == (5, 1) and s['attack'] == s['parry'] == 0 for s in snapshots[:3]))
        self.assertEqual(created[-1].player.position, (5, 2))
        self.assertEqual((created[-1].combat.active_attack.start_tick,
                          created[-1].parry.last_attempt.start_tick), (3, 3))

    def test_pending_old_stage_queue_is_discarded_on_two_to_three(self):
        def clear_after_queue(game, frame):
            if frame == 1:
                finish(game, 'clear')
        created, snapshots, _, _, _, _ = run_loop(
            [[], [key(SPACE)], [], [key(49)], [key(SPACE)], [key(SPACE, False)], [key(SPACE)]],
            initial_stage=2, initial='playing',
            lengths=[0, 0, 0, FIXED_TIME_STEP, FIXED_TIME_STEP, FIXED_TIME_STEP, FIXED_TIME_STEP],
            after_render=clear_after_queue)
        self.assertEqual([g.stage_number for g in created], [2, 3])
        self.assertIsNone(created[0].combat.active_attack)
        self.assertTrue(all(s['attack'] == 0 for s in snapshots[:5]))
        self.assertEqual(created[-1].combat.active_attack.attack_id, 1)

    def test_settings_focus_and_f11_block_transition_until_new_press(self):
        for batches, focus in (
                ([[MENU, key(49)], [key(ESC), key(49)], [key(49, False)], [key(49)]], None),
                ([[key(F11), key(49)], [key(49)], [key(49, False)], [key(49)]], None),
                ([[], [key(49)], [key(49)], [key(49, False)], [key(49)]], [512, 0, 512, 512, 512])):
            created, snapshots, _, _, _, _ = run_loop(batches, initial_stage=2, focus=focus)
            self.assertEqual([g.stage_number for g in created], [2, 3])
            self.assertTrue(all(s['stage'] == 2 for s in snapshots[:-1]))

    def test_stage_three_restart_is_blocked_by_settings_and_focus(self):
        for batches,focus in (([[MENU,key(R)],[key(ESC),key(R)],[key(R,False)],[key(R)]],None),
                              ([[],[key(R)],[key(R)],[key(R,False)],[key(R)]],[512,0,512,512,512])):
            created,snapshots,_,_,_,_=run_loop(batches,initial_stage=3,focus=focus)
            self.assertEqual([g.stage_number for g in created],[3])
            self.assertTrue(all(s['tick']==0 and s['state'] is GameState.UPGRADE for s in snapshots))

    def test_only_one_session_change_per_frame_in_both_key_orders(self):
        for keys, expected in (([49, R, 49], 3), ([R, 49, R], 3)):
            created, _, _, _, _, _ = run_loop([[key(k) for k in keys]], initial_stage=2)
            self.assertEqual([g.stage_number for g in created], [2, expected])

    def test_repeated_third_stage_restart_discards_clock_debt_and_landing(self):
        created,snapshots,_,_,_,clock=run_loop([[key(R),key(R,False)] for _ in range(6)],initial_stage=3,lengths=[20]*6)
        self.assertEqual(len(created),1)
        self.assertTrue(all(s['tick']==0 and s['state'] is GameState.UPGRADE for s in snapshots))
        self.assertEqual(created[0].transition_count,1)
        self.assertEqual(clock.accumulator,0)
        self.assertIsNone(created[0].restart_stage_number)

    def test_terminal_settings_f11_escape_and_window_close_remain_live(self):
        for state in ('dead', 'clear'):
            created, snapshots, _, menu, display, _ = run_loop(
                [[MENU], [key(ESC)], [key(F11)], [key(ESC)]], initial_stage=3, initial=state)
            self.assertEqual(len(snapshots), 3)
            self.assertTrue(all(s['tick'] == 0 for s in snapshots))
            display.return_value.toggle.assert_called_once_with()
            self.assertFalse(menu.is_open)
            self.assertEqual(len(created), 1)
        created, snapshots, _, _, _, _ = run_loop(
            [[key(R), SimpleNamespace(type=256)]], initial_stage=3)
        self.assertEqual(len(created), 1)
        self.assertEqual(snapshots, [])


class StageThreeMainCombatTests(unittest.TestCase):
    def test_original_ai_warning_and_exact_hit_tick_run_in_main(self):
        observed = {}
        def record(game, tick):
            k = game.encounter.enemies[0]
            cells = [game.player.position] + [e.position for e in game.encounter.enemies if e.active]
            self.assertEqual(len(cells), len(set(cells)))
            observed[tick] = (k.position, game.player.health.current_hp, k.current_attack)
        created, _, _, _, _, _ = play_to(300, samples=(48, 83, 84, 192, 264, 299), observe=record)
        self.assertEqual(observed[48][2].target_cells, ((5, 5),))
        self.assertEqual(observed[48][2].hit_tick - observed[48][2].start_tick, 36)
        self.assertEqual(observed[83][0], (3, 6))
        self.assertEqual(observed[84][0], (5, 5))
        self.assertEqual(observed[192][0], (6, 3))
        self.assertEqual(observed[264][2].target_cells, ((5, 1),))
        self.assertEqual(observed[299][:2], ((6, 3), 3))
        self.assertEqual(observed[300][:2], ((6, 3), 2))
        self.assertEqual(created[-1].player.health.last_damage_tick, 300)

    def test_evade_in_main_keeps_hp_and_lands_at_frozen_target(self):
        created, _, _, _, _, _ = play_to(300, inputs={299: [key(UP)]})
        game = created[-1]
        self.assertEqual((game.player.position, game.player.health.current_hp), ((5, 2), 3))
        self.assertEqual(game.encounter.enemies[0].position, (5, 1))
        self.assertEqual(game.combat.pending_attack_bonus, 0)

    def test_player_entry_into_warned_landing_does_not_cancel(self):
        created, _, _, _, _, _ = play_to(300, inputs={250: [key(UP), key(UP, False)], 299: [key(DOWN)]})
        game = created[-1]
        self.assertEqual((game.player.position, game.player.health.current_hp), ((5, 1), 2))
        self.assertEqual(game.encounter.enemies[0].position, (6, 3))

    def test_main_normal_parry_has_no_perfect_reward(self):
        created, _, _, _, _, _ = play_to(300, inputs={282: [key(SHIFT)]})
        game = created[-1]
        self.assertEqual(game.resolver.last_parry_result.status, 'normal')
        self.assertEqual((game.player.health.current_hp, game.combat.pending_attack_bonus), (3, 0))
        self.assertEqual((game.encounter.enemies[0].position, game.encounter.enemies[0].state),
                         ((6, 3), 'recovering'))

    def test_main_perfect_stun_ends_at_360_and_resets_attack_cooldown(self):
        seen = {}
        def record(game, tick):
            if tick in (300, 359, 360):
                seen[tick] = (game.encounter.enemies[0].state, game.encounter.enemies[0].position,
                              game.encounter.enemies[0].current_attack)
        created, _, _, _, _, _ = play_to(360, inputs={280: [key(SPACE)], 293: [key(SHIFT)]},
                                        samples=(300, 359), observe=record)
        game = created[-1]
        self.assertEqual(game.resolver.last_parry_result.status, 'perfect')
        self.assertEqual((game.player.health.current_hp, game.combat.pending_attack_bonus), (3, 2))
        self.assertEqual(game.combat.next_attack_tick, 300)
        self.assertEqual(seen[300][:2], ('stunned', (6, 3)))
        self.assertEqual(seen[359][0], 'stunned')
        self.assertEqual(seen[360][2].start_tick, 360)
        self.assertTrue(all(e.state != 'stunned' for e in game.encounter.enemies[1:]))

    def test_main_perfect_next_space_deals_three_and_cancels_knight_once(self):
        created, _, _, _, _, _ = play_to(325, inputs={293: [key(SHIFT)],
            301: [key(UP), key(UP, False)], 313: [key(RIGHT), key(RIGHT, False)],
            325: [key(UP), key(SPACE)]})
        game = created[-1]
        self.assertEqual(game.encounter.enemies[0].health.current_hp, 0)
        self.assertFalse(game.encounter.enemies[0].active)
        self.assertEqual(game.combat.active_attack.damage_bonus, 2)
        self.assertEqual(game.combat.pending_attack_bonus, 0)

    def test_space_kill_on_hit_tick_cancels_before_knight_damage(self):
        events = []
        def weaken(game, tick):
            if tick == 264:
                events.append(game.encounter.enemies[0].current_attack)
                game.encounter.enemies[0].health.apply_damage(2, tick=tick)
        created, _, _, _, _, _ = play_to(300, inputs={265: [key(UP), key(UP, False)],
            277: [key(RIGHT), key(RIGHT, False)], 300: [key(UP), key(SPACE)]},
            samples=(264,), observe=weaken)
        game = created[-1]
        self.assertFalse(game.encounter.enemies[0].active)
        self.assertEqual(game.encounter.ledger.state(events[0]), 'cancelled')
        self.assertEqual(game.player.health.current_hp, 3)

    def test_other_enemy_entry_cancels_at_265_and_recovers_until_337(self):
        seen, events = {}, []
        def obstruct(game, tick):
            knight = game.encounter.enemies[0]
            if tick == 264:
                events.append(knight.current_attack)
                game.encounter.enemies[1].col, game.encounter.enemies[1].row = 5, 1
            if tick in (265, 336, 337):
                seen[tick] = (knight.state, knight.next_action_tick, knight.current_attack)
        created, _, _, _, _, _ = play_to(337, inputs={250: [key(UP)]},
                                        samples=(264, 265, 336), observe=obstruct)
        game = created[-1]
        self.assertEqual(game.encounter.ledger.state(events[0]), 'cancelled')
        self.assertEqual(seen[265][:2], ('recovering', 337))
        self.assertEqual(seen[336][0], 'recovering')
        self.assertEqual(seen[337][2].start_tick, 337)
        self.assertEqual(game.player.health.current_hp, 3)

    def test_actual_death_freezes_main_and_r_retries_chapter_start(self):
        created, snapshots, _, _, _, _ = play_to(540, inputs={532: [key(R)]}, samples=(516, 524))
        dead, fresh = created
        self.assertEqual((dead.state, dead.combat.tick, dead.player.health.current_hp),
                         (GameState.GAME_OVER, 516, 0))
        self.assertEqual(fresh.stage_number, 1)
        self.assertEqual(next(s['tick'] for s in snapshots if s['stage'] == 1), 0)

    def test_final_space_kill_in_main_clears_then_r_replays_three(self):
        factory = main._new_stage_game
        def almost_clear():
            game = factory(3)
            for e in game.encounter.enemies[1:]:
                e.health.apply_damage(2, tick=0)
                game.encounter.deactivate(e.entity_instance_id)
            knight = game.encounter.enemies[0]
            knight.col, knight.row = 5, 2
            knight.health.apply_damage(2, tick=0)
            return game
        created, snapshots, _, _, _, _ = run_loop(
            [[key(SPACE), key(49)], [], [key(R)]], initial='playing',
            initial_factory=almost_clear)
        self.assertEqual(snapshots[0]['state'], GameState.UPGRADE)
        self.assertEqual([g.stage_number for g in created], [3])
        self.assertEqual(created[-1].encounter.enemies[0].health.current_hp, 0)

    def test_same_tick_knight_and_pawn_use_shared_invulnerability_and_ledger(self):
        factory = main._new_stage_game
        def simultaneous():
            game = factory(3)
            k, p, idle = game.encounter.enemies
            k.col, k.row, k.next_action_tick = 4, 3, 12
            p.col, p.row, p.next_action_tick = 4, 2, 9
            idle.col, idle.row, idle.next_action_tick = 9, 9, 600
            return game
        events = []
        def record(game, tick):
            if tick == 41:
                events.extend(e.current_attack for e in game.encounter.enemies[:2])
        created, _, _, _, _, _ = play_to(48, inputs={41: [key(SHIFT)]},
                                        observe=record, factory=simultaneous)
        game = created[-1]
        self.assertEqual([game.encounter.ledger.outcome(e) for e in events], ['hit', 'invulnerable'])
        self.assertEqual((game.player.health.current_hp, game.combat.pending_attack_bonus), (2, 0))
        self.assertEqual(game.resolver.last_parry_result.reason, 'invulnerable')
        for e in events:
            self.assertIsNone(game.resolver.resolve_enemy_attack(e))
        self.assertEqual(game.player.health.current_hp, 2)

    def test_menu_and_focus_pause_stage_three_warning_and_parry_clock(self):
        factory = main._new_stage_game
        def warned():
            game = factory(3)
            game.advance(48)
            game.resolver.register_parry(game.parry.request(game.combat.tick))
            return game
        for batches, focus in (([[MENU], [], [], [key(ESC)], []], None),
                               ([[], [], [], [], []], [512, 0, 0, 512, 512])):
            created, snapshots, _, _, _, _ = run_loop(
                batches, initial='playing', initial_factory=warned, focus=focus,
                lengths=[8 * FIXED_TIME_STEP] * len(batches))
            self.assertTrue(all(s['tick'] == 48 for s in snapshots[:4]))
            self.assertEqual(snapshots[-1]['tick'], 56)
            game = created[-1]
            self.assertEqual(game.parry.last_attempt.start_tick, 48)
            self.assertEqual(game.encounter.enemies[0].current_attack.hit_tick, 84)
            self.assertEqual(game.player.health.current_hp, 3)


class StageThreeRendererTests(unittest.TestCase):
    def test_stage_two_and_three_terminal_prompts_are_truthful(self):
        for number in (2, 3):
            for state in ('clear', 'dead'):
                game = main._new_stage_game(number)
                finish(game, state)
                with patch.object(HealthRenderer, '_text') as text:
                    GameFlowRenderer().draw(Mock(), game)
                labels = [call.args[1] for call in text.call_args_list]
                self.assertIn(f'STAGE {number}', labels)
                self.assertNotIn('N TO CONTINUE', labels)
                self.assertIn('UPGRADE' if state == 'clear' else 'R TO STAGE 1', labels)
                self.assertFalse(any('CHAPTER CLEAR' in s or 'STAGE 4' in s or 'ENDING' in s for s in labels))

    def test_actual_stage_three_hp_and_single_cell_warning_render_without_mutation(self):
        game = main._new_stage_game(3)
        game.advance(48)
        event = game.encounter.enemies[0].current_attack
        with patch.object(HealthRenderer, '_text') as text:
            HealthRenderer().draw(Mock(), game.player, game.encounter.enemies, game.combat.tick)
            GameFlowRenderer().draw_stage_label(Mock(), game)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertIn('STAGE 3', labels)
        self.assertEqual(labels.count('3/3'), 2)
        self.assertEqual(labels.count('2/2'), 2)
        before = (game.combat.tick, game.player.health.current_hp,
                  tuple(e.position for e in game.encounter.enemies), game.combat.pending_attack_bonus)
        for _ in range(3):
            canvas = Mock()
            main.EnemyAttackRenderer().draw(canvas, game.encounter.ledger)
            self.assertEqual(canvas.draw_rectangle.call_count, 2)
            main.EnemyRenderer().draw(canvas, game.encounter.enemies)
        self.assertEqual(game.encounter.ledger.state(event), 'telegraph')
        self.assertEqual(event.target_cells, ((5, 5),))
        self.assertEqual(before, (game.combat.tick, game.player.health.current_hp,
                                 tuple(e.position for e in game.encounter.enemies), game.combat.pending_attack_bonus))


if __name__ == '__main__':
    unittest.main()
