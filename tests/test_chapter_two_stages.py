"""Chapter 2 executable data, upgrade transactions and mixed combat regression."""
from collections import Counter, deque
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main
from chapter_run import ChapterRun
from game import GameState
from stage_progression import StageProgression
from stage_manager import StageCatalog
from tests.test_stage_transition import finish, run_loop, key, MENU, ESC, F11, R, N
from tests.test_upgrade_flow import clear
from upgrades import ChapterBuild
from sdl_input import GameplayInput
from input_controller import InputController
from player import DIRECTIONS
from tests import test_main as canvas_tests


def flow_at(stage, choices=('attack', 'hp', 'move'), *, entry_attack_level=0):
    run=ChapterRun(2,entry_attack_level=entry_attack_level)
    flow = StageProgression(main._new_stage_game(6,stats=run.stats), run)
    for kind in choices[:stage-6]:
        flow.choose(clear(flow), kind, main._new_stage_game)
    return flow


def state(flow):
    return (flow.game, flow.run, flow.run.build, flow.run.receipts,
            flow.run.current_stage, flow.offer, flow.game.state, flow.run.retired)


class ChapterTwoStageTests(unittest.TestCase):
    def test_catalog_fidelity_and_fresh_instances(self):
        for n, counts in ((7, {'knight':2,'pawn':2}), (8, {'bishop':1,'rook':1,'knight':1,'pawn':2}),
                          (9, {'bishop':1,'rook':2,'knight':1,'pawn':1})):
            with self.subTest(stage=n):
                a, b = main._new_stage_game(n), main._new_stage_game(n)
                d = StageCatalog.load().get_stage(n)
                self.assertEqual(Counter(e.kind for e in a.encounter.enemies), counts)
                self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay) for e in a.encounter.enemies],
                                 [(e.data_id,e.kind,e.position,e.initial_delay) for e in d.enemies])
                self.assertEqual((a.chapter,a.boss,a.player.position,a.combat.tick,a.encounter.tick),
                                 (2,False,d.player_spawn,0,-1))
                self.assertIsNone(a.encounter.pulse)
                self.assertNotEqual(a.combat.stage_instance_id,b.combat.stage_instance_id)
                self.assertTrue({e.entity_instance_id for e in a.encounter.enemies}.isdisjoint(
                                e.entity_instance_id for e in b.encounter.enemies))

    def test_actual_three_choices_apply_stats_and_reset_runtime(self):
        flow = flow_at(6)
        for n, kind in zip(range(6,9), ('attack','hp','move')):
            old = flow.game
            offer = clear(flow)
            self.assertEqual(old.state,GameState.UPGRADE)
            self.assertIs(flow.sync_offer(),offer)
            g, controls = flow.choose(offer,kind,main._new_stage_game,
                lambda stats: GameplayInput(canvas_tests.WindowLoopTests().make_canvas(),move_interval_ticks=stats.move_interval_ticks))
            self.assertEqual((g.stage_number,len(flow.run.receipts)),(n+1,n-5))
            self.assertEqual((g.player.health.current_hp,g.player.health.max_hp,g.resolver.player_damage,
                              controls.movement.move_interval_ticks),
                             (flow.run.stats.max_hp,flow.run.stats.max_hp,flow.run.stats.attack_damage,
                              flow.run.stats.move_interval_ticks))
            self.assertNotEqual(g.combat.stage_instance_id,old.combat.stage_instance_id)
            self.assertIsNot(g.player.health,old.player.health)
            self.assertEqual((g.combat.tick,g.combat.pending_attack_bonus,controls.movement.next_move_tick),(0,0,0))
            self.assertIsNone(g.parry.last_attempt)

    def test_three_hp_choices_reach_max_and_heal(self):
        flow=flow_at(9,('hp','hp','hp'))
        self.assertEqual((flow.game.player.health.current_hp,flow.run.stats.max_hp),(6,6))

    def test_max_attack_and_move_reject_without_candidate_or_consumption(self):
        for kind,index in (('attack',0),('move',2)):
            flow=flow_at(8,(kind,kind),entry_attack_level=13 if kind=='attack' else 0)
            o=clear(flow); before=state(flow); factory=Mock()
            self.assertFalse(o.options[index].enabled)
            with self.assertRaises(ValueError):flow.choose(o,kind,factory)
            factory.assert_not_called()
            self.assertEqual(state(flow),before)
            flow.choose(o,'hp',main._new_stage_game)
            self.assertEqual((flow.game.stage_number,len(flow.run.receipts)),(9,3))

    def test_failures_preserve_same_offer_build_and_receipts_until_retry(self):
        for n in (6,7,8):
            for fault in ('factory','input','candidate'):
                with self.subTest(stage=n,fault=fault):
                    flow=flow_at(n);o=clear(flow);before=state(flow)
                    def factory(number,*,stats):
                        if fault=='factory':raise RuntimeError('factory')
                        g=main._new_stage_game(number,stats=stats)
                        if fault=='candidate':g.resolver.player_damage=99
                        return g
                    def prepare(stats):
                        if fault=='input':raise RuntimeError('input')
                    with self.assertRaises((ValueError,RuntimeError)):flow.choose(o,'hp',factory,prepare)
                    self.assertEqual(state(flow),before)
                    flow.choose(o,'hp',main._new_stage_game)
                    self.assertEqual(flow.game.stage_number,n+1)

    def test_copied_foreign_and_consumed_offer_rejected(self):
        flow=flow_at(6);o=clear(flow);factory=Mock()
        for fake in (replace(o),ChapterRun(2).offer_after_clear(6,'foreign'),None):
            with self.assertRaises(ValueError):flow.choose(fake,'hp',factory)
        factory.assert_not_called()
        flow.choose(o,'hp',main._new_stage_game)
        clear(flow)
        with self.assertRaises(ValueError):flow.choose(o,'hp',factory)
        self.assertEqual(len(flow.run.receipts),1)

    def test_boundary_preserves_three_receipts_and_never_builds_stage_ten(self):
        # Historical method identity: X replaces the W boundary with an offer.
        flow=flow_at(9);before=flow.run.receipts
        o=clear(flow)
        self.assertIs(flow.sync_offer(),o)
        self.assertEqual(flow.game.state,GameState.UPGRADE)
        self.assertEqual(flow.run.receipts,before)
        self.assertEqual(flow.run.current_stage,9)
        self.assertIsNone(flow.game.restart_stage_number)
        self.assertIsNone(flow.game.next_stage_number)
        with self.assertRaises(ValueError):flow.restart(main._new_stage_game)
        flow.choose(o,'hp',main._new_stage_game)
        self.assertEqual((flow.game.stage_number,len(flow.run.receipts)),(10,4))

    def test_game_over_all_chapter_two_stages_reset_to_six_atomically(self):
        for n in range(6,10):
            flow=flow_at(n);old=flow.run;g=flow.game
            finish(g,'dead');before=state(flow)
            with self.assertRaises(RuntimeError):flow.restart(Mock(side_effect=RuntimeError('retry')))
            self.assertEqual(state(flow),before)
            fresh,_=flow.restart(main._new_stage_game)
            self.assertEqual((fresh.stage_number,flow.run.build,flow.run.receipts),(6,ChapterBuild(),()))
            self.assertTrue(old.retired)
            self.assertNotEqual(fresh.combat.stage_instance_id,g.combat.stage_instance_id)

    def test_death_wins_simultaneous_clear_all_new_stages(self):
        for n in (7,8,9):
            g=main._new_stage_game(n);finish(g,'dead');finish(g,'clear')
            self.assertEqual((g.state,g.restart_stage_number,g.transition_count),(GameState.GAME_OVER,6,1))

    def test_original_mixed_ai_occupancy_ledger_and_batch_determinism(self):
        for n in (7,8,9):
            traces=[]
            for stride in (1,8):
                g=main._new_stage_game(n)
                for _ in range(1000//stride):
                    g.advance(stride)
                    cells=[e.position for e in g.encounter.enemies if e.active]
                    self.assertEqual(len(cells),len(set(cells)))
                    self.assertNotIn(g.player.position,cells)
                records=list(g.encounter.ledger._records.values())
                sources={r.event.source_entity_instance_id for r in records}
                for e in g.encounter.enemies:
                    if e.kind in ('knight','rook','bishop'):self.assertIn(e.entity_instance_id,sources)
                for record in records:
                    source=next(e for e in g.encounter.enemies if e.entity_instance_id==record.event.source_entity_instance_id)
                    if source.kind in ('knight','rook','bishop'):
                        self.assertEqual(record.event.hit_tick-record.event.start_tick,
                                         {'knight':36,'rook':48,'bishop':108}[source.kind])
                traces.append((g.state,g.combat.tick,g.player.health.current_hp,
                    tuple((e.position,e.state,e.health.current_hp) for e in g.encounter.enemies),
                    tuple((r.event.start_tick,r.event.hit_tick,r.event.target_cells,r.state,r.outcome) for r in records)))
            self.assertEqual(traces[0],traces[1])

    def test_stage_seven_original_knight_normal_and_perfect_parries(self):
        for delta, expected in ((18,'normal'),(7,'perfect')):
            g=main._new_stage_game(7)
            event=None
            for _ in range(600):
                g.advance()
                event=next((e for e in g.encounter.ledger.pending
                            if g.player.position in e.target_cells and e.hit_tick-g.combat.tick>=18),None)
                if event is not None:break
            self.assertIsNotNone(event)
            g.advance(event.hit_tick-delta-g.combat.tick)
            attempt=g.parry.request(g.combat.tick)
            g.resolver.register_parry(attempt)
            g.advance(delta)
            self.assertEqual(g.resolver.last_parry_result.status,expected)
            self.assertEqual(g.player.health.current_hp,3)
            self.assertEqual(g.combat.pending_attack_bonus,2 if expected=='perfect' else 0)

    def test_original_seven_eight_nine_can_be_cleared_by_real_attack_and_parry(self):
        for n in (7,8,9):
            flow=flow_at(n,('attack','attack','hp'));g=flow.game
            movement=InputController(move_interval_ticks=flow.run.stats.move_interval_ticks)
            damaged=set()
            for tick in range(1800):
                if not g.playing:break
                if tick:g.combat.advance()
                occupied=set(g.encounter.occupied_cells)
                queue=deque([(g.player.position,None)]);seen={g.player.position};direction=None
                while queue and direction is None:
                    (x,y),first=queue.popleft()
                    for name,(dx,dy) in DIRECTIONS.items():
                        cell=(x+dx,y+dy)
                        if cell in occupied:
                            direction=first or name
                            break
                        if 0<=cell[0]<10 and 0<=cell[1]<10 and cell not in seen:
                            seen.add(cell);queue.append((cell,first or name))
                if direction:
                    movement.key_down(direction,g.player,occupied=occupied,tick=tick)
                    movement.key_up(direction)
                if any(g.player.position in e.target_cells and 0<=e.hit_tick-tick<=7
                       for e in g.encounter.ledger.pending):
                    attempt=g.parry.request(tick)
                    if attempt:g.resolver.register_parry(attempt)
                attack=g.combat.request_attack(g.player)
                if attack:
                    result=g.resolver.resolve_player_attack(attack)
                    if result:damaged.add(result.target_entity_instance_id)
                    self.assertIsNone(g.resolver.resolve_player_attack(attack))
                g.resolve_current_tick()
            self.assertEqual(g.state,GameState.UPGRADE,
                             (n,g.combat.tick,g.player.health.current_hp))
            self.assertEqual(damaged,{e.entity_instance_id for e in g.encounter.enemies})
            self.assertFalse(g.encounter.occupied_cells)
            self.assertTrue(all(not e.alive for e in g.encounter.enemies))

    def test_main_max_numeric_and_mouse_blocked_then_enabled_choice_advances(self):
        def terminal(g,frame):
            if g.playing:finish(g,'clear')
        for number,x in ((49,450),(51,970)):
            click=SimpleNamespace(type=1025,button=1,x=x,y=500)
            release=SimpleNamespace(type=1026,button=1,x=x,y=500)
            created,snapshots,*_=run_loop([[key(number),key(number,False)],[],
                [key(number),key(number,False)],[],[key(number),key(number,False)],
                [click,release],[key(50)]],initial_stage=6,after_render=terminal,entry_attack_level=13 if number==49 else 0)
            self.assertEqual([g.stage_number for g in created],[6,7,8,9])
            self.assertEqual([s['stage'] for s in snapshots[-3:]],[8,8,9])

    def test_main_modal_and_display_frames_block_chapter_two_selection(self):
        for events in ([[MENU,key(49)],[key(ESC),key(49,False)],[key(49)]],
                       [[key(F11),key(49)],[key(49,False)],[key(49)]]):
            created,snapshots,*_=run_loop(events,initial_stage=6)
            self.assertEqual([g.stage_number for g in created],[6,7])
            self.assertTrue(all(s['stage']==6 for s in snapshots[:-1]))

    def test_main_game_over_seven_eight_nine_restarts_six(self):
        for n in (7,8,9):
            created,snapshots,*_=run_loop([[key(N)],[key(R)]],initial_stage=n,initial='dead')
            self.assertEqual([g.stage_number for g in created],[n,6])
            self.assertEqual((snapshots[-1]['tick'],snapshots[-1]['hp']),(0,3))

    def test_stage_ten_through_twenty_five_never_reach_catalog(self):
        with patch.object(main.StageCatalog,'load') as load:
            for n in range(15,26):
                with self.assertRaises(ValueError):main._new_stage_game(n)
            load.assert_not_called()
