"""Stage23 eight-enemy combat, atomic second upgrade and HP carryover."""
from dataclasses import replace
from unittest.mock import Mock,patch,PropertyMock
import unittest
import main
from chapter_run import ChapterRun
from stage_progression import StageProgression
from game import GameState
from simulation_clock import SimulationClock
from game_renderer import GameFlowRenderer
from upgrade_renderer import UpgradeRenderer
from tests.test_chapter_five_entry import entered_five
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish,run_loop,key
from tests.test_chapter_three_entry import state
from tests.test_hp_carryover import fight
from tests.balance_driver import STYLES,measure


def at22(hp=1,level=7):
    r=ChapterRun(5,entry_attack_level=level)
    f=StageProgression(main._new_stage_game(21,stats=r.stats,initial_hp=hp),r)
    f.choose(clear(f),'move',main._new_stage_game)
    return f


def at23():
    f=at22();f.choose(clear(f),'hp',main._new_stage_game);return f


class StageTwentyThreeTests(unittest.TestCase):
    def test_second_three_upgrade_kinds_carry_hurt_hp_in_fresh_owned_runtime(self):
        for kind in ('attack','hp','move'):
            f=at22();old=f.game;r=f.run;offer=clear(f)
            g,_=f.choose(offer,kind,main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((r.current_stage,len(r.receipts),r.active_offer),(23,2,None))
            self.assertEqual((g.resolver.player_damage,g.player.health.current_hp,g.player.health.max_hp,f.run.stats.move_interval_ticks),{'attack':(9,1,3,15),'hp':(8,2,4,15),'move':(8,1,3,12)}[kind])
            for attr in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(old,attr),getattr(g,attr))
            self.assertIsNot(old.player.health,g.player.health);self.assertIsNot(old.encounter.ledger,g.encounter.ledger)
            self.assertNotEqual(old.combat.combat_session_id,g.combat.combat_session_id)
            self.assertIsNone(g.player.health.last_damage_tick);self.assertEqual((g.resolver.player_invulnerable_until_tick,g.combat.pending_attack_bonus),(0,0))
            with self.assertRaises(ValueError):f.choose(offer,kind,Mock())

    def test_max_cannot_consume_but_hp_and_move_work(self):
        for kind in ('hp','move'):
            f=at22(level=15);o=clear(f);before=state(f);factory=Mock()
            self.assertFalse(o.options[0].enabled)
            with self.assertRaises(ValueError):f.choose(o,'attack',factory)
            factory.assert_not_called();self.assertEqual(state(f),before)
            f.choose(o,kind,main._new_stage_game);self.assertEqual(len(f.run.receipts),2)

    def test_forged_foreign_offers_and_bad_receipts_rejected(self):
        f=at22();o=clear(f);foreign=clear(at22());factory=Mock();before=state(f)
        for fake in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(fake,'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=(Mock(),)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)

    def test_fault_candidates_and_input_preserve_offer_hp_and_retry(self):
        for mode in ('factory','input','stage','chapter','boss','missing','order','hp','delay','id','position','forward','player_hp','session','ledger','health','resolver'):
            with self.subTest(mode=mode):
                f=at22();o=clear(f);before=(state(f),f.game.player.health.current_hp)
                def factory(n,**kw):
                    if mode=='factory':raise RuntimeError()
                    g=main._new_stage_game(n,**kw);e=g.encounter.enemies[0]
                    if mode=='stage':g._stage_number=21
                    if mode=='chapter':g._chapter=4
                    if mode=='boss':g._boss=True
                    if mode=='missing':g.encounter.enemies=g.encounter.enemies[:-1]
                    if mode=='order':g.encounter.enemies=tuple(reversed(g.encounter.enemies))
                    if mode=='hp':e.health.apply_damage(1,tick=0)
                    if mode=='delay':e.initial_delay=.9
                    if mode=='id':e.data_id='tampered'
                    if mode=='position':e.col=0
                    if mode=='forward':g.encounter.enemies[-1].forward=(0,1)
                    if mode=='player_hp':g.player.health.apply_damage(1,tick=0)
                    if mode=='session':g.combat._combat_session_id=f.game.combat.combat_session_id
                    if mode=='ledger':g.encounter.ledger=f.game.encounter.ledger
                    if mode=='health':e.health=f.game.encounter.enemies[0].health
                    if mode=='resolver':g.resolver.player=f.game.player
                    return g
                prepare=Mock(side_effect=RuntimeError()) if mode=='input' else lambda stats:None
                with self.assertRaises((ValueError,RuntimeError)):f.choose(o,'hp',factory,prepare)
                self.assertEqual((state(f),f.game.player.health.current_hp),before)
                f.choose(o,'hp',main._new_stage_game);self.assertEqual(f.game.player.health.current_hp,2)

    def test_keyboard_mouse_max_and_same_frame_duplicate_inputs(self):
        from types import SimpleNamespace
        factory=main._new_stage_game
        for inputs in ([key(50),key(50,repeat=True),key(49)], [SimpleNamespace(type=1025,button=1,x=730,y=500),key(50)]):
            games,snapshots,*_=run_loop([inputs,[]],initial_stage=22,entry_attack_level=15,initial_factory=lambda:factory(22,stats=__import__('upgrades').ChapterBuild(15,0,1).stats,initial_hp=1))
            self.assertEqual([g.stage_number for g in games],[22,23]);self.assertEqual(games[-1].player.health.current_hp,2)
        games,*_=run_loop([[key(49)],[SimpleNamespace(type=1025,button=1,x=450,y=500)],[key(51)]],initial_stage=22,entry_attack_level=15,initial_factory=lambda:factory(22,stats=__import__('upgrades').ChapterBuild(15,0,1).stats,initial_hp=1))
        self.assertEqual([g.stage_number for g in games],[22,23]);self.assertEqual(games[-1].player.health.current_hp,1)


    def test_exact_original_eight_sources_delay_hp_theme_and_unsupported(self):
        from renderer import BoardRenderer
        g=main._new_stage_game(23)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(5,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],[
            ('s23_rook_1','rook',(2,4),48,20),('s23_rook_2','rook',(7,4),62,20),
            ('s23_knight_1','knight',(3,6),75,16),('s23_knight_2','knight',(6,6),88,16),
            ('s23_bishop_1','bishop',(2,8),101,16),('s23_bishop_2','bishop',(7,8),114,16),
            ('s23_pawn_1','pawn',(1,6),128,13),('s23_pawn_2','pawn',(8,6),141,13)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),130)
        self.assertTrue(all(e.forward==(0,-1) for e in g.encounter.enemies[-2:]))
        self.assertEqual(BoardRenderer(chapter=5).theme.name,'Gothic Throne')
        for n in (25,26):
            with self.assertRaises(ValueError):main._new_stage_game(n)

    def test_paired_knights_rooks_pawns_independent_cancel_and_occupancy(self):
        g=main._new_stage_game(23);g.advance(88)
        a,b=g.encounter.enemies[2:4];own,foreign=a.current_attack,b.current_attack
        self.assertEqual((own.start_tick,foreign.start_tick),(75,88))
        self.assertNotEqual(own.key,foreign.key)
        a.health.apply_damage(a.health.current_hp,tick=88)
        g.encounter.deactivate(a.entity_instance_id,tick=88)
        self.assertEqual(g.encounter.ledger.state(own),'cancelled')
        self.assertEqual(g.encounter.ledger.state(foreign),'telegraph')
        # Full original roster, no timer overrides: inspect real scheduled Rook attacks.
        g=main._new_stage_game(23);g.advance(150)
        rooks=g.encounter.enemies[:2];events=[e.current_attack for e in rooks]
        self.assertTrue(all(events));self.assertNotEqual(events[0].key,events[1].key)
        for e in events:
            self.assertEqual(e.hit_tick-e.start_tick,48)
            self.assertIn(g.player.position,e.target_cells)
        before=g.player.health.current_hp;g.advance(32)
        self.assertGreaterEqual(g.player.health.current_hp,before-1)
        for _ in range(100):
            g.advance()
            cells=[e.position for e in g.encounter.enemies if e.active]
            self.assertEqual(len(cells),len(set(cells)))
        # Isolate each Pawn's real diagonal/contact logic from the other seven AIs.
        for index in (6,7):
            for contact in (False,True):
                g=main._new_stage_game(23);p=g.encounter.enemies[index]
                for i,e in enumerate(g.encounter.enemies):
                    if i!=index:e.next_action_tick=1000
                target=(p.col,p.row-1) if contact else (p.col+1,p.row-1)
                while g.player.col!=target[0]:g.player.move('right' if g.player.col<target[0] else 'left')
                while g.player.row!=target[1]:g.player.move('up' if g.player.row<target[1] else 'down')
                g.advance(p.initial_delay_ticks);ev=p.current_attack
                self.assertIsNotNone(ev);self.assertIn(g.player.position,ev.target_cells)
                self.assertEqual(ev.attack_kind,'pawn_contact' if contact else 'basic')
                g.advance(ev.hit_tick-g.combat.tick)
                self.assertEqual(g.player.health.current_hp,2)
                self.assertIsNone(g.resolver.resolve_enemy_attack(ev))

    def test_third_offer_boundary_no_cards_or_input_consumption(self):
        from types import SimpleNamespace
        f=at23();f.choose(clear(f),'hp',main._new_stage_game);g=f.game;g.advance(88);pending=g.encounter.ledger.pending;o=clear(f)
        self.assertEqual((g.state,len(f.run.receipts),o.stage,g.transition_count),(GameState.UPGRADE,3,24,1))
        for _ in range(3):self.assertIs(f.sync_offer(),o)
        for kind in ('attack','hp','move'):
            factory=Mock()
            with self.assertRaises(ValueError):f.choose(o,kind,factory)
            factory.assert_not_called()
        for ev in pending:self.assertEqual(g.encounter.ledger.state(ev),'cancelled')
        with patch.object(GameFlowRenderer,'_center') as t:GameFlowRenderer().draw(Mock(),g)
        labels=[c.args[1] for c in t.call_args_list]
        self.assertIn('STAGE 24 CLEAR',labels);self.assertIn('STAGE 25 NOT AVAILABLE',labels)
        with patch.object(UpgradeRenderer,'_text') as t:UpgradeRenderer().draw(Mock(),g,o)
        t.assert_not_called()
        games,*_=run_loop([[key(49),key(50),key(51),key(110),key(114)],[SimpleNamespace(type=1025,button=1,x=450,y=500)]],initial_stage=24)
        self.assertEqual([g.stage_number for g in games],[24])
        g.advance(1000);self.assertEqual(g.combat.tick,g.end_tick)

    def test_game_over_restarts_chapter_and_simultaneous_death_priority(self):
        f=at23();old=f.game;r=f.run
        finish(old,'dead');g,_=f.restart(main._new_stage_game)
        self.assertTrue(r.retired);self.assertIsNot(f.run,r)
        self.assertEqual((g.stage_number,g.resolver.player_damage,g.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(21,8,3,18,0))
        self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
        self.assertIsNot(g.encounter.ledger,old.encounter.ledger)
        self.assertIsNone(g.player.health.last_damage_tick)
        g=main._new_stage_game(23)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state()
        self.assertEqual(g.state,GameState.GAME_OVER);self.assertTrue(g.resolver.stopped)

    def test_real_four_build_eight_enemy_fights(self):
        for style,tick,hp,hits,received,perfect in (
            ('attack',435,5,10,0,1),('survival',1084,3,28,2,5),
            ('evasion',601,2,17,1,3),('balanced',687,4,16,0,1)):
            row=measure(style,23)
            self.assertEqual(row['hp'],[20,20,16,16,16,16,13,13])
            self.assertEqual((row['result'],row['ticks'],row['remaining_hp'],row['hits'],row['received'],row['perfect']),('UPGRADE',tick,hp,hits,received,perfect))

    def test_seven_fps_and_single_eight_tick_determinism(self):
        def snapshot(g):
            return (g.combat.tick,g.state,g.player.health.current_hp,
                    [(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],
                    [(r.event.target_cells,r.event.hit_tick,r.state,r.outcome) for r in g.encounter.ledger._records.values()])
        rows=[]
        for fps in (30,60,120,144,160,180,240):
            g=main._new_stage_game(23);c=SimulationClock()
            for _ in range(fps*4):g.advance(c.advance(1/fps))
            rows.append(snapshot(g))
        for stride in (1,8):
            g=main._new_stage_game(23)
            for _ in range(240//stride):g.advance(stride)
            rows.append(snapshot(g))
        self.assertTrue(all(r==rows[0] for r in rows))
    def test_both_bishops_serialize_disjoint_snapshots_and_actual_hits(self):
        g=main._new_stage_game(23)
        # Timing fixture isolates Bishops; original eight-source fights are separate.
        for i,e in enumerate(g.encounter.enemies):
            if i not in (4,5):e.next_action_tick=1000
        a,b=g.encounter.enemies[4:6];g.advance(101);first=a.current_attack
        self.assertEqual((first.start_tick,first.hit_tick),(101,209));self.assertEqual(len(first.target_cells),50)
        g.advance(108);self.assertEqual(g.player.health.current_hp,2);self.assertIsNone(b.current_attack)
        g.advance();second=b.current_attack
        self.assertEqual((second.start_tick,second.hit_tick),(210,318));self.assertEqual(len(second.target_cells),50)
        self.assertFalse(set(first.target_cells)&set(second.target_cells))
        g.player.move('right',occupied=g.encounter.occupied_cells);g.advance(108)
        self.assertEqual(g.player.health.current_hp,1)
        for ev in (first,second):self.assertEqual(g.encounter.ledger.outcome(ev),'hit');self.assertIsNone(g.resolver.resolve_enemy_attack(ev))

    def test_each_bishop_normal_perfect_and_miss_use_only_own_snapshot(self):
        for index in (4,5):
            for grade,delta in (('normal',18),('perfect',7),('miss',None)):
                g=main._new_stage_game(23)
                # Per-source parry fixture, not an independent clear measurement.
                for i,e in enumerate(g.encounter.enemies):
                    if i not in (4,5):e.next_action_tick=1000
                g.advance(101)
                if index==5:g.player.move('right',occupied=g.encounter.occupied_cells);g.advance(109)
                source=g.encounter.enemies[index];event=source.current_attack;snapshot=event.target_cells
                if delta:
                    g.advance(event.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
                else:g.player.move('up',occupied=g.encounter.occupied_cells)
                g.advance(event.hit_tick-g.combat.tick)
                self.assertEqual(g.player.health.current_hp,3);self.assertEqual(event.target_cells,snapshot)
                self.assertEqual(g.encounter.ledger.outcome(event),'miss' if grade=='miss' else 'parried_'+grade)
                if grade=='perfect':self.assertEqual((source.stun_until_tick,g.combat.pending_attack_bonus),(event.hit_tick+60,2))

    def test_real_chapter_five_chain_uses_remaining_hp_and_issued_second_offer(self):
        # Actual AI kills throughout; no clear fixture, damage edit, or healing.
        for style,entry,expected in (
            ('attack',15,[(432,2,3),(423,3,4),(435,4,5)]),
            ('balanced',8,[(651,2,3),(684,1,3),(687,2,4)])):
            r=ChapterRun(5,entry_attack_level=entry)
            f=StageProgression(main._new_stage_game(21,stats=r.stats),r)
            for i,(tick,hp,max_hp) in enumerate(expected):
                result=fight(f)
                self.assertEqual(result,(21+i,'UPGRADE',tick,hp,max_hp))
                self.assertEqual(len(r.receipts),i);self.assertIs(f.run,r)
                offer=f.sync_offer();self.assertIs(f.sync_offer(),offer)
                if i<2:
                    choice='hp' if style=='attack' else STYLES[style][i]
                    f.choose(offer,choice,main._new_stage_game)
                    self.assertEqual(f.game.player.health.current_hp,hp+(choice=='hp'))
                else:self.assertTrue(f.game.upgrade_selection_enabled)
