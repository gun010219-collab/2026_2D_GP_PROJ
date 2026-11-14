"""Stage14 original four-kind combat and authenticated third upgrade."""
import unittest
from unittest.mock import Mock, patch, PropertyMock
from dataclasses import replace
import main
from game import GameState
from chapter_run import ChapterRun
from stage_progression import StageProgression
from tests.test_stage_thirteen import at13
from tests.test_chapter_three_entry import state
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish
from tests.balance_driver import measure, STYLES
from queen_behavior import diagonal_targets
from rook_behavior import attack_path
from bishop_behavior import color_targets


def at14():
    f=at13();f.choose(clear(f),'hp',main._new_stage_game);return f


class StageFourteenTests(unittest.TestCase):
    def test_exact_roster_and_independent_sessions(self):
        a,b=main._new_stage_game(14),main._new_stage_game(14)
        self.assertEqual((a.chapter,a.boss,a.player.position,a.encounter.pulse),(3,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp,e.forward) for e in a.encounter.enemies],
            [('s14_queen_1','queen',(4,7),48,14,None),('s14_rook_1','rook',(2,4),62,12,None),
             ('s14_bishop_1','bishop',(2,8),75,10,None),('s14_pawn_1','pawn',(1,6),88,7,(0,-1)),('s14_pawn_2','pawn',(8,6),101,7,(0,-1))])
        for x,y in zip(a.encounter.enemies,b.encounter.enemies):
            self.assertIsNot(x.health,y.health);self.assertNotEqual(x.entity_instance_id,y.entity_instance_id)
        self.assertNotEqual(a.combat.combat_session_id,b.combat.combat_session_id)

    def test_third_choice_three_kinds_and_duplicate_rejection(self):
        for kind in ('attack','hp','move'):
            f=at13();o=clear(f);old=f.game;r=f.run
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(r,f.run);self.assertEqual((r.current_stage,len(r.receipts)),(14,3))
            self.assertEqual(g.player.health.current_hp,r.stats.max_hp)
            self.assertEqual(g.resolver.player_damage,r.stats.attack_damage)
            for name in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(old,name),getattr(g,name))
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())

    def test_copied_offer_and_receipt_and_max_do_not_consume(self):
        f=at13();o=clear(f);before=state(f);factory=Mock()
        with self.assertRaises(ValueError):f.choose(replace(o),'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=tuple(replace(r) for r in f.run.receipts)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)
        r=ChapterRun(3,entry_attack_level=15);f=StageProgression(main._new_stage_game(11,stats=r.stats),r)
        for kind in ('hp','move'):f.choose(clear(f),kind,main._new_stage_game)
        o=clear(f);before=state(f)
        with self.assertRaises(ValueError):f.choose(o,'attack',factory)
        self.assertEqual(state(f),before);factory.assert_not_called()

    def test_every_candidate_fault_preserves_offer_and_retry(self):
        for mode in ('factory','input','stage','chapter','boss','queen_hp','rook_hp','bishop_hp','pawn_hp','missing','extra','order','forward','spawn','resolver','roster','position','delay','player_hp','session','stage_id','ledger'):
            with self.subTest(mode=mode):
                f=at13();o=clear(f);before=state(f)
                def factory(n,*,stats):
                    if mode=='factory':raise RuntimeError(mode)
                    g=main._new_stage_game(n,stats=stats);e=g.encounter.enemies[0]
                    if mode=='stage':g._stage_number=13
                    if mode=='chapter':g._chapter=2
                    if mode=='boss':g._boss=True
                    if mode.endswith('_hp') and mode!='player_hp':g.encounter.enemies[{'queen_hp':0,'rook_hp':1,'bishop_hp':2,'pawn_hp':3}[mode]].health.apply_damage(1,tick=0)
                    if mode=='missing':g.encounter.enemies=g.encounter.enemies[:-1]
                    if mode=='extra':g.encounter.enemies+= (g.encounter.enemies[-1],)
                    if mode=='order':g.encounter.enemies=tuple(reversed(g.encounter.enemies))
                    if mode=='forward':g.encounter.enemies[-1].forward=(0,1)
                    if mode=='spawn':g.player._col=0
                    if mode=='resolver':g.resolver=f.game.resolver
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
                self.assertEqual(len(f.run.receipts),3)

    def test_original_overlap_and_independent_stationary_targets(self):
        g=main._new_stage_game(14);g.advance(80);q,r,b,*_=g.encounter.enemies
        qe,be=q.current_attack,b.current_attack
        self.assertEqual(qe.attack_kind,'queen_diagonal');self.assertEqual(len(be.target_cells),50)
        self.assertEqual(set(be.target_cells),set(color_targets((2,8))))
        self.assertTrue(set(qe.target_cells)&set(be.target_cells))
        self.assertEqual(q.position,(5,6))
        self.assertEqual(attack_path((q.col-2,q.row),(q.col+2,q.row),{q.position}),())
        frozen=qe.target_cells
        b.health.apply_damage(10,tick=80);g.encounter.deactivate(b.entity_instance_id,tick=80)
        self.assertEqual(qe.target_cells,frozen);self.assertEqual(g.encounter.ledger.state(be),'cancelled')
        self.assertTrue(g.playing)

    def test_all_sources_cancel_on_death_and_others_keep_playing(self):
        for index in range(5):
            g=main._new_stage_game(14);g.advance(80);e=g.encounter.enemies[index];ev=e.current_attack
            e.health.apply_damage(e.health.current_hp,tick=80);g.encounter.deactivate(e.entity_instance_id,tick=80);g.update_state()
            self.assertTrue(g.playing);self.assertEqual(sum(e.alive for e in g.encounter.enemies),4)
            if ev:self.assertEqual(g.encounter.ledger.state(ev),'cancelled');self.assertNotIn(ev.key,g.encounter._attack_moves)

    def test_fourth_offer_is_held_before_factory_and_render(self):
        f=at14();o=clear(f);self.assertTrue(f.game.upgrade_selection_enabled)
        g,_=f.choose(o,'attack',main._new_stage_game)
        self.assertEqual((g.stage_number,len(f.run.receipts)),(15,4))
        finish(g,'clear');factory=Mock();before=state(f)
        self.assertIsNone(f.sync_offer())
        with self.assertRaises(ValueError):f.enter_next_chapter(factory)
        factory.assert_not_called();self.assertEqual(state(f),before)

    def test_death_restarts11_entry_stats_and_rejects_old_events(self):
        f=at14();old=f.game;r=f.run;old.advance(80);events=old.encounter.ledger.pending
        attempt=old.parry.request(old.combat.tick);old.resolver.register_parry(attempt)
        finish(old,'dead');g,_=f.restart(main._new_stage_game)
        self.assertEqual((g.stage_number,g.resolver.player_damage,g.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(11,5,3,18,0))
        self.assertTrue(r.retired);self.assertIsNone(g.parry.last_attempt)
        for event in events:
            with self.assertRaises(ValueError):g.resolver.resolve_enemy_attack(event)
        with self.assertRaises(ValueError):g.resolver.register_parry(attempt)

    def test_simultaneous_death_and_mixed_tick_determinism(self):
        g=main._new_stage_game(14)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state();self.assertEqual(g.state,GameState.GAME_OVER)
        traces=[]
        for stride in (1,8):
            g=main._new_stage_game(14)
            for _ in range(640//stride):g.advance(stride)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(*traces)

    def test_four_styles_actual_combat(self):
        for style in STYLES:
            r=measure(style,14,limit=3600)
            self.assertEqual(r['hp'],[14,12,10,7,7]);self.assertEqual(r['result'],'UPGRADE');self.assertGreater(r['remaining_hp'],0)

    def test_stage14_queen_actual_delay_warning_and_parries(self):
        for grade,delta in (('hit',None),('normal',18),('perfect',7),('miss',None)):
            g=main._new_stage_game(14)
            # Isolate the original Queen scheduling; complete mixed combat is measured below.
            for e in g.encounter.enemies[1:]:e.next_action_tick=1000
            g.advance(47);q=g.encounter.enemies[0];self.assertEqual(q.position,(4,7))
            self.assertIsNone(q.current_attack);g.advance();self.assertIsNone(q.current_attack)
            g.advance();event=q.current_attack;self.assertEqual((event.start_tick,event.hit_tick),(49,121))
            g.advance();g.player.move('up',occupied=g.encounter.occupied_cells)
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
