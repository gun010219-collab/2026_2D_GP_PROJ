"""Stage 6 catalog fidelity, safe development boundary and session metadata."""
import unittest
from collections import deque
from unittest.mock import Mock, patch

import main
from chapter_run import ChapterRun
from combat import Combat
from combat_resolution import CombatResolver
from enemy_behaviors import EnemyEncounter
from enemy_factory import create_stage_enemies
from game import GameState, StageGame, StageOneGame, SUPPORTED_STAGES
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from input_controller import InputController
from parry import Parry
from player import DIRECTIONS, Player
from renderer import BoardRenderer
from stage_manager import StageCatalog
from stage_progression import StageProgression
from upgrades import ChapterBuild


def stage_six():
    definition = StageCatalog.load().get_stage(6)
    player = Player(*definition.player_spawn)
    combat, parry = Combat(), Parry()
    encounter = EnemyEncounter(create_stage_enemies(definition),
        combat_session_id=combat.combat_session_id, stage_instance_id=combat.stage_instance_id)
    resolver = CombatResolver(player, combat, encounter, parry=parry)
    return StageGame(player, combat, encounter, parry, resolver, stage_number=6, chapter=2)


def clear(game):
    for enemy in game.encounter.enemies:
        if enemy.alive:
            enemy.health.apply_damage(enemy.health.current_hp, tick=game.combat.tick)
        game.encounter.deactivate(enemy.entity_instance_id, tick=game.combat.tick)
    game.update_state()


def boundary_flow(game):
    run = ChapterRun(2)
    for n, kind in zip(range(6, 10), ('attack', 'hp', 'move', 'hp')):
        run.select(run.offer_after_clear(n, 'boundary-fixture-'+str(n)), kind)
    return StageProgression(game, run)


class StageSixTests(unittest.TestCase):
    def test_catalog_roster_hp_positions_delays_and_fresh_clock(self):
        g = main._new_stage_game(6)
        self.assertEqual((g.stage_number,g.chapter,g.boss,g.player.position,g.player.facing),
                         (6,2,False,(5,1),'up'))
        self.assertEqual((g.combat.tick,g.encounter.tick,g.player.health.current_hp,g.resolver.player_damage),
                         (0,-1,3,1))
        self.assertIsNone(g.encounter.pulse)
        self.assertEqual([(e.data_id,e.kind,e.position,e.health.max_hp,e.initial_delay_ticks)
                          for e in g.encounter.enemies],
                         [('s6_pawn_1','pawn',(1,6),5,48),('s6_pawn_2','pawn',(8,6),5,62),
                          ('s6_pawn_3','pawn',(3,8),5,75),('s6_rook_1','rook',(2,4),9,88)])
        self.assertEqual(g.encounter.ledger.stage_instance_id,g.combat.stage_instance_id)
        self.assertEqual(g.encounter.ledger.combat_session_id,g.combat.combat_session_id)

    def test_only_explicit_supported_stages_are_executable(self):
        self.assertEqual(SUPPORTED_STAGES,frozenset(range(1,18)))
        for n in (*range(18,26),0,26,-1):
            with self.subTest(stage=n),self.assertRaises(ValueError):
                main._new_stage_game(n)
        for n in (True,False,6.0,'6',None):
            with self.subTest(stage=n),self.assertRaises(TypeError):
                main._new_stage_game(n)

    def test_catalog_metadata_must_match_without_requiring_original_roster(self):
        g = stage_six()
        args = (g.player,g.combat,g.encounter,g.parry,g.resolver)
        for chapter,boss in ((1,False),(3,False),(True,False),(2,True),(2,1)):
            with self.subTest(chapter=chapter,boss=boss),self.assertRaises(ValueError):
                StageGame(*args,stage_number=6,chapter=chapter,boss=boss)
        for n in (11,13,25,True):
            with self.subTest(stage=n),self.assertRaises(ValueError):
                StageGame(*args,stage_number=n,chapter=2)
        old = main._new_game()
        self.assertIsInstance(old,StageOneGame)
        self.assertTrue(old.playing)

    def test_live_combat_has_no_flow_destination(self):
        g = stage_six()
        self.assertTrue(g.playing)
        self.assertIsNone(g.next_stage_number)
        self.assertIsNone(g.restart_stage_number)
        self.assertIsNone(StageProgression(g,ChapterRun(2)).sync_offer())

    def test_partial_clear_stays_playing_until_last_enemy(self):
        g = stage_six()
        for enemy in g.encounter.enemies[:-1]:
            enemy.health.apply_damage(enemy.health.current_hp,tick=0)
            g.encounter.deactivate(enemy.entity_instance_id,tick=0)
        self.assertFalse(g.update_state())
        self.assertTrue(g.playing)
        clear(g)
        self.assertEqual((g.state,g.transition_count,g.end_tick),(GameState.UPGRADE,1,0))

    def test_boundary_cancels_pending_attack_and_freezes_all_runtime(self):
        g = main._new_stage_game(10)
        g.advance(200)
        pending = g.encounter.ledger.pending
        self.assertTrue(pending)
        clear(g)
        before = (g.combat.tick,g.encounter.tick,g.player.health.current_hp,
                  len(g.encounter.ledger._records),tuple(e.position for e in g.encounter.enemies))
        self.assertEqual(g.state,GameState.BOSS_CLEAR)
        self.assertTrue(g.resolver.stopped)
        for _ in range(3):
            self.assertEqual(g.advance(1000),())
            self.assertFalse(g.update_state())
            self.assertEqual(g.resolve_current_tick(),())
            for event in pending:
                self.assertEqual(g.encounter.ledger.state(event),'cancelled')
                self.assertIsNone(g.resolver.resolve_enemy_attack(event))
        self.assertEqual(g.transition_count,1)
        self.assertEqual(before,(g.combat.tick,g.encounter.tick,g.player.health.current_hp,
                                len(g.encounter.ledger._records),tuple(e.position for e in g.encounter.enemies)))

    def test_boundary_has_no_upgrade_offer_n_or_r(self):
        g = main._new_stage_game(10)
        flow = boundary_flow(g)
        clear(g)
        self.assertEqual(g.next_stage_number,11)
        self.assertEqual(g.restart_stage_number,10)
        self.assertIsNone(flow.sync_offer())
        self.assertIsNone(flow.offer)
        self.assertEqual(len(flow.run.receipts),4)
        self.assertEqual(flow.run.build,ChapterBuild(1,2,1))
        with self.assertRaises(ValueError):
            flow.choose(None,'hp',main._new_stage_game)
        with self.assertRaises(RuntimeError):
            flow.restart(Mock(side_effect=RuntimeError('replay preparation failed')))

    def test_boundary_never_requests_or_consumes_upgrade_model_commands(self):
        g = main._new_stage_game(10)
        flow = boundary_flow(g)
        clear(g)
        with patch.object(flow.run, 'offer_after_clear') as offer, \
             patch.object(flow.run, 'select') as select:
            for _ in range(3):
                self.assertIsNone(flow.sync_offer())
                with self.assertRaises(ValueError):
                    flow.choose(None, 'hp', main._new_stage_game)
            offer.assert_not_called()
            select.assert_not_called()
        self.assertEqual(len(flow.run.receipts),4)

    def test_all_original_enemies_die_through_actual_attacks_and_parries(self):
        g = main._new_stage_game(6)
        flow = StageProgression(g, ChapterRun(2))
        movement = InputController(move_interval_ticks=flow.run.stats.move_interval_ticks)
        damaged_ids = set()
        # Deterministic test driver: walk to the nearest enemy, face it by
        # attempting an occupied move, attack, and parry imminent warnings.
        # All positions, HP, delays, cooldowns and damage use the real rules.
        for tick in range(2400):
            if not g.playing:
                break
            if tick:
                g.combat.advance()
            occupied = set(g.encounter.occupied_cells)
            queue, seen = deque([(g.player.position, None)]), {g.player.position}
            direction = None
            while queue and direction is None:
                (x, y), first = queue.popleft()
                for name, (dx, dy) in DIRECTIONS.items():
                    cell = (x + dx, y + dy)
                    if cell in occupied:
                        direction = first or name
                        break
                    if 0 <= cell[0] < 10 and 0 <= cell[1] < 10 and cell not in seen:
                        seen.add(cell)
                        queue.append((cell, first or name))
            if direction:
                movement.key_down(direction, g.player, occupied=occupied, tick=tick)
                movement.key_up(direction)
            if any(g.player.position in e.target_cells and 0 <= e.hit_tick - tick <= 7
                   for e in g.encounter.ledger.pending):
                attempt = g.parry.request(tick)
                if attempt is not None:
                    g.resolver.register_parry(attempt)
            attack = g.combat.request_attack(g.player)
            if attack is not None:
                result = g.resolver.resolve_player_attack(attack)
                if result is not None:
                    damaged_ids.add(result.target_entity_instance_id)
                    self.assertIsNone(g.resolver.resolve_player_attack(attack))
            g.resolve_current_tick()
        self.assertEqual((g.state, g.combat.tick, g.player.health.current_hp),
                         (GameState.UPGRADE, 630, 3))
        self.assertEqual(damaged_ids, {e.entity_instance_id for e in g.encounter.enemies})
        self.assertTrue(all(not e.alive and not e.active for e in g.encounter.enemies))
        self.assertFalse(g.encounter.occupied_cells)
        self.assertIsNotNone(flow.sync_offer())
        self.assertEqual(flow.run.receipts, ())

    def test_boundary_escape_and_window_close_exit_without_creating_a_stage(self):
        from types import SimpleNamespace
        from tests.test_stage_transition import ESC, N, R, key, run_loop
        for exit_event in (key(ESC), SimpleNamespace(type=256)):
            with self.subTest(event=exit_event):
                created, snapshots, canvas, *_ = run_loop(
                    [[key(N)], [exit_event]], initial_stage=10)
                self.assertEqual([g.stage_number for g in created], [10,11])
                self.assertEqual(snapshots[0]['state'], GameState.PLAYING)
                canvas.close_canvas.assert_called_once_with()

    def test_simultaneous_player_death_has_priority_and_restarts_current_chapter(self):
        g = stage_six()
        g.player.health.apply_damage(3,tick=0)
        clear(g)
        self.assertEqual((g.state,g.restart_stage_number,g.transition_count),(GameState.GAME_OVER,6,1))
        self.assertIsNone(g.next_stage_number)
        g.advance(999)
        self.assertEqual(g.combat.tick,0)

    def test_boundary_does_not_change_after_later_outside_damage(self):
        g = main._new_stage_game(10)
        clear(g)
        g.player.health.apply_damage(3,tick=0)
        self.assertFalse(g.update_state())
        self.assertEqual((g.state,g.transition_count),(GameState.BOSS_CLEAR,1))

    def test_stage_six_generation_does_not_reuse_health_ids_or_history(self):
        first,second = main._new_stage_game(6),main._new_stage_game(6)
        first.advance(200)
        first.player.health.apply_damage(1,tick=first.combat.tick)
        self.assertEqual(second.player.health.current_hp,3)
        self.assertEqual((second.combat.tick,second.encounter.tick),(0,-1))
        self.assertIsNot(first.player.health,second.player.health)
        self.assertNotEqual(first.combat.combat_session_id,second.combat.combat_session_id)
        self.assertNotEqual(first.combat.stage_instance_id,second.combat.stage_instance_id)
        self.assertTrue({e.entity_instance_id for e in first.encounter.enemies}.isdisjoint(
                        e.entity_instance_id for e in second.encounter.enemies))
        self.assertFalse(second.encounter.ledger.pending)
        for event in first.encounter.ledger.pending:
            with self.assertRaises(ValueError):
                second.resolver.resolve_enemy_attack(event)

    def test_boss_next_chapter_is_available_only_after_boss_clear(self):
        for number in range(1,7):
            g = main._new_stage_game(number)
            self.assertIsNone(g.next_stage_number)
            clear(g)
            self.assertEqual(g.next_stage_number,6 if number==5 else None)
            self.assertEqual(g.restart_stage_number,5 if number==5 else None)

    def test_forest_palette_is_supported_without_modifying_board_geometry(self):
        board = BoardRenderer(chapter=2)
        self.assertEqual(board.theme.chapter,2)
        self.assertNotEqual(board.theme,BoardRenderer(chapter=1).theme)
        commands = board._commands
        board.draw(Mock())
        self.assertIs(board._commands,commands)

    def test_chapter_entry_rejects_runtime_replacement_even_with_matching_combat_ids(self):
        from enemy_attack import EnemyAttackLedger
        from tests.test_upgrade_flow import flow_at_boss
        from tests.test_stage_transition import finish
        for component in ('combat','resolver','encounter','player','parry','ledger'):
            with self.subTest(component=component):
                flow = flow_at_boss()
                finish(flow.game,'clear')
                game,run = flow.game,flow.run
                before = (run.build,run.receipts,run.current_stage,run.active_offer)
                foreign = main._new_stage_game(5,stats=run.stats)
                finish(foreign,'clear')
                if component == 'combat':
                    replacement = Combat(combat_session_id=game.combat.combat_session_id,
                                         stage_instance_id=game.combat.stage_instance_id)
                    replacement.advance(game.combat.tick)
                    game.combat = replacement
                elif component == 'ledger':
                    game.encounter.ledger = EnemyAttackLedger(game.combat.combat_session_id,
                                                              game.combat.stage_instance_id)
                else:
                    setattr(game,component,getattr(foreign,component))
                factory = Mock(side_effect=main._new_stage_game)
                with self.assertRaises(ValueError):
                    flow.enter_next_chapter(factory)
                factory.assert_not_called()
                self.assertIs(flow.game,game)
                self.assertIs(flow.run,run)
                self.assertFalse(run.retired)
                self.assertEqual(before,(run.build,run.receipts,run.current_stage,run.active_offer))

    def test_original_stage_six_rook_perfect_parry_in_actual_main_at_208(self):
        from config import FIXED_TIME_STEP
        from tests.test_stage_transition import key,SHIFT,run_loop
        ticks = sorted(set(range(0,209,8))|{201,208})
        lengths = [(b-a)*FIXED_TIME_STEP for a,b in zip(ticks,ticks[1:])]+[FIXED_TIME_STEP]
        created,_,_,_,_,_ = run_loop([[key(SHIFT)] if t==201 else [] for t in ticks],
                                     initial_stage=6,initial='playing',lengths=lengths)
        g = created[-1]
        self.assertEqual((g.stage_number,g.chapter,g.combat.tick),(6,2,208))
        self.assertEqual((g.player.health.current_hp,g.combat.pending_attack_bonus),(3,2))
        self.assertEqual((g.resolver.last_parry_result.status,g.resolver.last_parry_result.tick),
                         ('perfect',208))
        rook = g.encounter.enemies[3]
        self.assertEqual((rook.state,rook.stun_until_tick),('stunned',268))
        events = [r.event for r in g.encounter.ledger._records.values()
                  if r.event.source_entity_instance_id==rook.entity_instance_id]
        self.assertEqual(len(events),1)
        self.assertEqual((events[0].start_tick,events[0].hit_tick,events[0].target_cells),
                         (160,208,((3,1),(4,1),(5,1))))
        self.assertEqual(g.encounter.ledger.outcome(events[0]),'parried_perfect')

    def test_stage_six_main_same_parry_schedule_matches_single_and_eight_tick_frames(self):
        from config import FIXED_TIME_STEP
        from tests.test_stage_transition import key,SHIFT,run_loop
        traces = []
        for stride in (1,8):
            ticks = sorted(set(range(0,209,stride))|{201,208})
            batches = [[key(SHIFT)] if tick==201 else [] for tick in ticks]
            lengths = [(b-a)*FIXED_TIME_STEP for a,b in zip(ticks,ticks[1:])]+[FIXED_TIME_STEP]
            created,_,_,_,_,_ = run_loop(batches,initial_stage=6,initial='playing',lengths=lengths)
            g = created[-1]
            event_trace = tuple((r.event.start_tick,r.event.hit_tick,r.event.target_cells,
                                 r.event.attack_kind,r.state,r.outcome)
                                for r in g.encounter.ledger._records.values())
            traces.append((g.combat.tick,g.player.position,g.player.health.current_hp,
                           g.combat.pending_attack_bonus,g.resolver.last_parry_result.status,
                           tuple((e.kind,e.position,e.health.current_hp,e.state,e.next_action_tick,
                                  e.stun_until_tick) for e in g.encounter.enemies),event_trace))
        self.assertEqual(traces[0],traces[1])
        self.assertEqual(traces[0][:5],(208,(5,1),3,2,'perfect'))


class StageSixRendererTests(unittest.TestCase):
    def test_development_boundary_labels_no_unsupported_progress_prompts_and_read_only(self):
        g = main._new_stage_game(10)
        clear(g)
        before = (g.state,g.combat.tick,g.transition_count,len(g.encounter.ledger._records))
        with patch.object(HealthRenderer,'_text') as text:
            for _ in range(3):GameFlowRenderer().draw(Mock(),g)
        labels = [call.args[1] for call in text.call_args_list]
        for expected in ('BOSS CLEAR','STAGE 10','R TO RESTART',
                         'ESC TO EXIT','SETTINGS / F11'):
            self.assertIn(expected,labels)
        self.assertIn('N TO CHAPTER 3',labels)
        self.assertFalse(any('CHAPTER CLEAR' in s or 'UNLOCKED' in s or 'SAVED' in s
                             for s in labels))
        self.assertEqual(before,(g.state,g.combat.tick,g.transition_count,len(g.encounter.ledger._records)))
        GameFlowRenderer().draw(Mock(),g)  # Installed glyph coverage, no text mock.

    def test_boss_clear_shows_both_replay_and_chapter_entry_and_retry_feedback(self):
        g = main._new_stage_game(5)
        clear(g)
        with patch.object(HealthRenderer,'_text') as text:
            GameFlowRenderer().draw(Mock(),g,error=True)
        labels = [call.args[1] for call in text.call_args_list]
        for expected in ('BOSS CLEAR','R TO RESTART','N TO CHAPTER 2',
                         'COULD NOT START STAGE  TRY AGAIN'):
            self.assertIn(expected,labels)
        GameFlowRenderer().draw(Mock(),g,error=True)

    def test_stage_six_game_over_prompt_returns_to_six(self):
        g = stage_six()
        g.player.health.apply_damage(3,tick=0)
        g.update_state()
        with patch.object(HealthRenderer,'_text') as text:
            GameFlowRenderer().draw(Mock(),g)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertIn('GAME OVER',labels)
        self.assertIn('R TO RESTART',labels)
        self.assertNotIn('R TO STAGE 1',labels)


if __name__=='__main__':unittest.main()
