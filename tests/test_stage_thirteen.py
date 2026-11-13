"""Stage13 original mixed roster and atomic second choice; no Stage14 execution."""
from dataclasses import replace
import unittest
from unittest.mock import Mock,patch,PropertyMock
import main
from chapter_run import ChapterRun
from stage_progression import StageProgression
from upgrades import ChapterBuild
from game import GameState
from tests.test_chapter_three_entry import entered_three,state
from tests.test_stage_transition import finish,run_loop,key,R
from tests.test_upgrade_flow import clear
from tests.balance_driver import measure,STYLES


def at12():
    f=entered_three();f.choose(clear(f),'attack',main._new_stage_game);return f

def at13():
    f=at12();f.choose(clear(f),'attack',main._new_stage_game);return f

class StageThirteenTests(unittest.TestCase):
    def test_exact_original_roster_and_initial_runtime(self):
        g=main._new_stage_game(13)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(3,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp,e.forward) for e in g.encounter.enemies],
            [('s13_queen_1','queen',(4,7),48,14,None),('s13_knight_1','knight',(3,6),62,10,None),
             ('s13_pawn_1','pawn',(1,6),75,7,(0,-1)),('s13_pawn_2','pawn',(8,6),88,7,(0,-1)),('s13_pawn_3','pawn',(3,8),101,7,(0,-1))])
        self.assertEqual(g.encounter.queen_steps[g.encounter.enemies[0].entity_instance_id],'reposition')
        self.assertTrue(all(e.state=='initial_wait' and e.health.current_hp==e.health.max_hp for e in g.encounter.enemies))

    def test_all_three_choices_propagate_stats_and_keep_run(self):
        for kind in ('attack','hp','move'):
            f=at12();old=f.game;run=f.run;o=clear(f)
            self.assertTrue(old.upgrade_selection_enabled)
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(f.run,run)
            self.assertEqual((run.current_stage,len(run.receipts)),(13,2))
            self.assertEqual((g.resolver.player_damage,g.player.health.current_hp),(run.stats.attack_damage,run.stats.max_hp))
            for name in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(g,name),getattr(old,name))
            self.assertIsNot(g.encounter.ledger,old.encounter.ledger)
            self.assertNotEqual(g.combat.stage_instance_id,old.combat.stage_instance_id)
            self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
            self.assertFalse(g.encounter.ledger.pending)
            self.assertIsNone(g.parry.last_attempt)
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())

    def test_every_candidate_fault_preserves_offer_and_retry(self):
        for mode in ('factory','input','stage','chapter','boss','queen_hp','knight_hp','pawn_hp','roster','position','delay','player_hp','session','stage_id','ledger'):
            with self.subTest(mode=mode):
                f=at12();o=clear(f);before=state(f)
                def factory(n,*,stats):
                    if mode=='factory':raise RuntimeError(mode)
                    g=main._new_stage_game(n,stats=stats);e=g.encounter.enemies[0]
                    if mode=='stage':g._stage_number=12
                    if mode=='chapter':g._chapter=2
                    if mode=='boss':g._boss=True
                    if mode.endswith('_hp') and mode!='player_hp':g.encounter.enemies[{'queen_hp':0,'knight_hp':1,'pawn_hp':2}[mode]].health.apply_damage(1,tick=0)
                    if mode=='roster':e.data_id='forged'
                    if mode=='position':e.col=0
                    if mode=='delay':e.initial_delay=.9
                    if mode=='player_hp':g.player.health.apply_damage(1,tick=0)
                    if mode=='session':g.combat._combat_session_id=f.game.combat.combat_session_id
                    if mode=='stage_id':g.combat._stage_instance_id=f.game.combat.stage_instance_id
                    if mode=='ledger':g.encounter.ledger=f.game.encounter.ledger
                    return g
                prepare=Mock(side_effect=RuntimeError('input')) if mode=='input' else lambda stats:None
                with self.assertRaises((ValueError,RuntimeError)):f.choose(o,'hp',factory,prepare)
                self.assertEqual(state(f),before)
                f.choose(o,'hp',main._new_stage_game)
                self.assertEqual(len(f.run.receipts),2)

    def test_foreign_copied_and_previous_receipts_cannot_authorize_choice(self):
        f=at12();o=clear(f);foreign=at12();foreign=clear(foreign);factory=Mock()
        for invalid in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(invalid,'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=(replace(f.run.receipts[0]),)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        factory.assert_not_called();self.assertIs(f.offer,o)

    def test_max_does_not_consume_other_card_works(self):
        r=ChapterRun(3,entry_attack_level=15);f=StageProgression(main._new_stage_game(11,stats=r.stats),r)
        f.choose(clear(f),'hp',main._new_stage_game);o=clear(f);before=state(f);factory=Mock()
        with self.assertRaises(ValueError):f.choose(o,'attack',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)
        f.choose(o,'move',main._new_stage_game);self.assertEqual(f.run.stats.attack_damage,16)

    def test_stage13_queen_actual_delay_warning_and_parries(self):
        for grade,delta in (('hit',None),('normal',18),('perfect',7),('miss',None)):
            g=main._new_stage_game(13)
            # Isolate the original Queen scheduling; complete mixed combat is measured below.
            for e in g.encounter.enemies[1:]:e.next_action_tick=1000
            g.advance(47);q=g.encounter.enemies[0];self.assertEqual(q.position,(4,7))
            self.assertIsNone(q.current_attack);g.advance();self.assertIsNone(q.current_attack)
            g.advance();event=q.current_attack;self.assertEqual((event.start_tick,event.hit_tick),(49,121))
            g.advance();g.player.move('right',occupied=g.encounter.occupied_cells)
            g.advance(18);g.player.move('up',occupied=g.encounter.occupied_cells)
            self.assertIn(g.player.position,event.target_cells)
            if delta:
                g.advance(121-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
            if grade=='miss':
                g.advance(18);g.player.move('right',occupied=g.encounter.occupied_cells)
            g.advance(121-g.combat.tick)
            self.assertEqual(g.encounter.ledger.outcome(event),'parried_'+grade if delta else grade)
            self.assertEqual(g.player.health.current_hp,2 if grade=='hit' else 3)
            if grade=='perfect':self.assertEqual((q.stun_until_tick,g.combat.pending_attack_bonus),(181,2))
            self.assertIsNone(g.resolver.resolve_enemy_attack(event))

    def test_queen_death_cancels_warning_without_clearing_other_four(self):
        g=main._new_stage_game(13);g.advance(49);q=g.encounter.enemies[0];event=q.current_attack
        q.health.apply_damage(14,tick=g.combat.tick);g.encounter.deactivate(q.entity_instance_id,tick=g.combat.tick)
        g.update_state();self.assertTrue(g.playing)
        self.assertEqual(sum(e.alive for e in g.encounter.enemies),4)
        self.assertEqual(g.encounter.ledger.state(event),'cancelled');self.assertNotIn(event.key,g.encounter._attack_moves)

    def test_clear_third_offer_stops_combat_and_never_requests14(self):
        f=at13();f.choose(clear(f),'hp',main._new_stage_game);g=f.game;g.advance(80);pending=g.encounter.ledger.pending;o=clear(f);before=state(f)
        self.assertEqual((o.stage,len(f.run.receipts),f.run.current_stage),(14,3,14))
        self.assertIs(f.sync_offer(),o);factory=Mock()
        for kind in ('attack','hp','move'):
            with self.assertRaisesRegex(ValueError,'Stage 15 is not available'):f.choose(o,kind,factory)
        factory.assert_not_called();g.advance(1000)
        self.assertEqual(state(f),before)
        for event in pending:self.assertEqual(g.encounter.ledger.state(event),'cancelled')
        self.assertIsNone(g.restart_stage_number);self.assertIsNone(g.next_stage_number)

    def test_game_over_resets_entry_stats_and_old_attacks(self):
        f=at13();old=f.game;oldrun=f.run;old.advance(80);events=old.encounter.ledger.pending
        attempt=old.parry.request(old.combat.tick);old.resolver.register_parry(attempt)
        finish(old,'dead');g,_=f.restart(main._new_stage_game)
        self.assertEqual((g.stage_number,g.resolver.player_damage,g.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(11,5,3,18,0))
        self.assertTrue(oldrun.retired);self.assertIsNone(g.parry.last_attempt)
        with self.assertRaises(ValueError):g.resolver.register_parry(attempt)
        for e in events:
            with self.assertRaises(ValueError):g.resolver.resolve_enemy_attack(e)

    def test_simultaneous_player_and_last_enemy_death_prefers_game_over(self):
        g=main._new_stage_game(13)
        g.player.health.apply_damage(g.player.health.current_hp,tick=0)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.update_state()
        self.assertEqual((g.state,g.transition_count),(GameState.GAME_OVER,1))

    def test_original_mixed_roster_one_and_eight_tick_determinism(self):
        traces=[]
        for stride in (1,8):
            g=main._new_stage_game(13)
            for _ in range(640//stride):g.advance(stride)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies],
                           [(r.event.start_tick,r.event.hit_tick,r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(traces[0],traces[1])

    def test_four_builds_clear_actual_original_roster(self):
        for style in STYLES:
            with self.subTest(style=style):
                r=measure(style,13,limit=3600)
                self.assertEqual(r['result'],'UPGRADE');self.assertGreater(r['remaining_hp'],0)
                self.assertEqual(r['hp'],[14,10,7,7,7]);self.assertGreater(r['hits'],0)
