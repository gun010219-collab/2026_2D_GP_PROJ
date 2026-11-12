"""Stage 10 real data, fourth choice, boss ownership and mixed Pulse runtime."""
import unittest
from collections import deque
from input_controller import InputController
from player import DIRECTIONS
from unittest.mock import Mock, patch
from dataclasses import replace
import main
from game import GameState
from stage_manager import StageCatalog
from health_renderer import HealthRenderer
from game_renderer import GameFlowRenderer
from tests.test_chapter_two_stages import flow_at, state
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish, run_loop, key, R, N, SPACE, SHIFT, UP
from upgrades import ChapterBuild


def boss_flow():
    flow=flow_at(9)
    flow.choose(clear(flow),'hp',main._new_stage_game)
    return flow


def pulse_game(delta=7):
    g=main._new_stage_game(10)
    # Real JSON roster/timers; stand still until the first Pulse warning.
    for _ in range(700):
        g.advance()
        if g.encounter.pulse.event is not None:break
    event=g.encounter.pulse.event
    if event is None:raise AssertionError('Original Stage 10 never emitted Pulse')
    g.advance(event.hit_tick-delta-g.combat.tick)
    attempt=g.parry.request(g.combat.tick)
    g.resolver.register_parry(attempt)
    g.advance(delta)
    return g,event


class StageTenTests(unittest.TestCase):
    def test_exact_original_data_and_boss_hp_from_catalog(self):
        g=main._new_stage_game(10);d=StageCatalog.load().get_stage(10)
        self.assertEqual((g.chapter,g.boss,g.player.position),(2,True,(5,1)))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp)
                          for e in g.encounter.enemies],
            [('s10_king_1','king',(5,9),48,40),('s10_bishop_1','bishop',(2,8),62,7),
             ('s10_knight_1','knight',(3,6),75,7),('s10_pawn_1','pawn',(1,6),88,5),
             ('s10_pawn_2','pawn',(8,6),101,5)])
        self.assertEqual(g.encounter.pulse.king.health.current_hp,40)
        self.assertEqual(main._new_stage_game(5).encounter.pulse.king.health.max_hp,22)
        self.assertEqual(g.encounter.pulse.next_use_tick,240)

    def test_fourth_offer_selects_once_and_propagates_stats(self):
        f=flow_at(9);o=clear(f);self.assertIs(f.sync_offer(),o)
        self.assertEqual((o.stage,len(f.run.receipts)),(9,3))
        g,_=f.choose(o,'hp',main._new_stage_game)
        self.assertEqual((g.stage_number,len(f.run.receipts),g.player.health.current_hp,g.resolver.player_damage),(10,4,5,2))
        with self.assertRaises(ValueError):f.choose(o,'hp',main._new_stage_game)

    def test_fourth_choice_factory_input_and_candidate_failures_preserve_offer(self):
        for fault in ('factory','input','candidate'):
            f=flow_at(9);o=clear(f);before=state(f)
            def factory(n,*,stats):
                if fault=='factory':raise RuntimeError('factory')
                g=main._new_stage_game(n,stats=stats)
                if fault=='candidate':g.encounter.pulse.king.health.apply_damage(1,tick=0)
                return g
            def prepare(stats):
                if fault=='input':raise RuntimeError('input')
            with self.assertRaises((ValueError,RuntimeError)):f.choose(o,'hp',factory,prepare)
            self.assertEqual(state(f),before)
            f.choose(o,'hp',main._new_stage_game)
            self.assertEqual(len(f.run.receipts),4)

    def test_fourth_copied_offer_and_max_do_not_call_factory(self):
        f=flow_at(9,('move','move','hp'));o=clear(f);factory=Mock()
        for offer,kind in ((replace(o),'hp'),(o,'move')):
            with self.assertRaises(ValueError):f.choose(offer,kind,factory)
        factory.assert_not_called()

    def test_only_annihilation_clears_and_player_death_wins(self):
        for killed,dead,expected in (((0,),False,GameState.PLAYING),((1,2,3,4),False,GameState.PLAYING),
                                     (range(5),False,GameState.BOSS_CLEAR),(range(5),True,GameState.GAME_OVER)):
            g=main._new_stage_game(10)
            for i in killed:
                e=g.encounter.enemies[i];e.health.apply_damage(e.health.current_hp,tick=0)
                g.encounter.deactivate(e.entity_instance_id,tick=0)
            if dead:g.player.health.apply_damage(3,tick=0)
            g.update_state();self.assertEqual(g.state,expected)
            if expected is not GameState.PLAYING:
                g.advance(999);self.assertEqual((g.combat.tick,g.transition_count),(0,1))

    def test_boss_replay_retains_run_four_receipts_and_uses_new_everything(self):
        f=boss_flow();old=f.game;run=f.run;finish(old,'clear')
        before=state(f)
        with self.assertRaises(RuntimeError):f.restart(Mock(side_effect=RuntimeError('replay')))
        self.assertEqual(state(f),before)
        g,_=f.restart(main._new_stage_game)
        self.assertIs(f.run,run);self.assertEqual(len(run.receipts),4)
        self.assertEqual((g.stage_number,g.player.health.current_hp,g.encounter.pulse.king.health.current_hp),(10,5,40))
        for attr in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(g,attr),getattr(old,attr))
        self.assertNotEqual(g.combat.stage_instance_id,old.combat.stage_instance_id)

    def test_boss_clear_never_offers_or_enters_chapter_three(self):
        f=boss_flow();finish(f.game,'clear');factory=Mock()
        self.assertIsNone(f.sync_offer());self.assertIsNone(f.game.next_stage_number)
        with self.assertRaises(ValueError):f.enter_next_chapter(factory)
        factory.assert_not_called();self.assertEqual((f.run.chapter,len(f.run.receipts)),(2,4))

    def test_game_over_resets_chapter_two_after_failed_retry(self):
        f=boss_flow();old=f.run;finish(f.game,'dead');before=state(f)
        with self.assertRaises(RuntimeError):f.restart(main._new_stage_game,Mock(side_effect=RuntimeError('input')))
        self.assertEqual(state(f),before)
        g,_=f.restart(main._new_stage_game)
        self.assertTrue(old.retired)
        self.assertEqual((g.stage_number,f.run.build,f.run.receipts,g.player.health.current_hp),(6,ChapterBuild(),(),3))

    def test_original_pulse_perfect_reflects_two_and_normal_does_not(self):
        for delta,status,hp,bonus in ((7,'perfect',38,2),(18,'normal',40,0)):
            g,event=pulse_game(delta)
            self.assertEqual((len(event.target_cells),event.hit_tick-event.start_tick),(100,120))
            self.assertEqual((g.resolver.last_parry_result.status,g.encounter.pulse.king.health.current_hp,
                              g.combat.pending_attack_bonus),(status,hp,bonus))
            self.assertEqual(g.encounter.pulse.next_use_tick,event.hit_tick+480)
            self.assertIsNone(g.resolver.resolve_enemy_attack(event))

    def test_pulse_freezes_and_restores_real_bishop_knight_pawns(self):
        g=main._new_stage_game(10);p=g.encounter.pulse
        while p.event is None and g.playing:g.advance()
        event=p.event;self.assertIsNotNone(event)
        start=g.combat.tick;saved=p._remaining.copy()
        snapshot=tuple((e.position,e.state,e.next_action_tick) for e in g.encounter.enemies[1:])
        g.advance(100)
        self.assertEqual(snapshot,tuple((e.position,e.state,e.next_action_tick) for e in g.encounter.enemies[1:]))
        g.advance(event.hit_tick-g.combat.tick-7);g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(7)
        g.advance(29);self.assertEqual(p.state,'CLEANUP')
        g.advance();self.assertEqual(p.state,'NORMAL')
        for e in g.encounter.enemies[1:]:
            if saved[e.entity_instance_id][1]>0:
                self.assertEqual(e.next_action_tick,event.hit_tick+30+saved[e.entity_instance_id][1])

    def test_bishop_and_knight_original_pending_plans_drain_before_pulse(self):
        g=main._new_stage_game(10);g.advance(90);p=g.encounter.pulse
        bishop,knight=g.encounter.enemies[1:3]
        events=(bishop.current_attack,knight.current_attack)
        self.assertEqual([e.hit_tick for e in events],[170,111])
        # Scheduling fixture makes the boss ready during both live warnings.
        p.next_use_tick=91;p.king.next_action_tick=91
        g.advance();self.assertEqual(p.state,'DRAINING')
        self.assertIsNone(p.event)
        g.advance(79)
        self.assertTrue(all(g.encounter.ledger.state(e)=='resolved' for e in events))
        self.assertIsNone(p.event)
        g.advance();self.assertEqual(p.event.start_tick,171)
        self.assertFalse(any(e.current_attack for e in g.encounter.enemies[1:]))

    def test_king_death_cancels_pulse_and_resumes_survivors_next_tick(self):
        g=main._new_stage_game(10);p=g.encounter.pulse
        while p.event is None and g.playing:g.advance()
        event=p.event;k=p.king;k.health.apply_damage(k.health.max_hp,tick=g.combat.tick)
        g.encounter.deactivate(k.entity_instance_id,tick=g.combat.tick);g.update_state()
        self.assertTrue(g.playing);self.assertEqual(g.encounter.ledger.state(event),'cancelled')
        g.advance();self.assertIsNone(p.freeze_tick);self.assertTrue(any(e.alive for e in g.encounter.enemies[1:]))

    def test_original_mixed_fight_one_and_eight_ticks_are_identical(self):
        traces=[]
        for stride in (1,8):
            g=main._new_stage_game(10)
            for _ in range(800//stride):
                g.advance(stride)
                cells=[e.position for e in g.encounter.enemies if e.active]
                self.assertEqual(len(cells),len(set(cells)))
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,
                tuple((e.position,e.state,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies),
                tuple((r.event.start_tick,r.event.hit_tick,r.event.target_cells,r.state,r.outcome)
                      for r in g.encounter.ledger._records.values())))
        self.assertEqual(traces[0],traces[1])

    def test_main_fourth_choice_then_boss_n_blocked_replay_and_death_retry(self):
        for terminal,target in (('clear',10),('dead',6)):
            created,_,*_=run_loop([[key(N)],[key(R),key(N),key(SPACE),key(SHIFT),key(UP)]],initial_stage=10,initial=terminal)
            self.assertEqual([g.stage_number for g in created],[10,target])
            self.assertEqual(created[-1].combat.tick,0)

    def test_renderer_uses_real_hp_and_clear_has_no_next_or_unlock_prompt(self):
        g=main._new_stage_game(10)
        with patch.object(HealthRenderer,'_text') as text:
            GameFlowRenderer().draw_stage_label(Mock(),g)
            finish(g,'clear');GameFlowRenderer().draw(Mock(),g)
        labels=[c.args[1] for c in text.call_args_list]
        for label in ('KING HP 40/40','BOSS CLEAR','STAGE 10','R TO RESTART','ESC TO EXIT'):self.assertIn(label,labels)
        self.assertFalse(any(s.startswith('N TO') or 'UNLOCK' in s or 'SAVED' in s for s in labels))

    def test_original_stage_ten_can_be_cleared_by_real_attack_and_parry(self):
        for n in (10,):
            flow=boss_flow();g=flow.game
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
            self.assertEqual(g.state,GameState.BOSS_CLEAR,
                             (n,g.combat.tick,g.player.health.current_hp))
            self.assertEqual(damaged,{e.entity_instance_id for e in g.encounter.enemies})
            self.assertFalse(g.encounter.occupied_cells)
            self.assertTrue(all(not e.alive for e in g.encounter.enemies))
