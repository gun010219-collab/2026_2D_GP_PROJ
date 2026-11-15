"""Stage24 eight-enemy combat, atomic third upgrade and HP carryover."""
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


def at23(hp=1,level=7,choices=('hp','hp')):
    r=ChapterRun(5,entry_attack_level=level)
    f=StageProgression(main._new_stage_game(21,stats=r.stats,initial_hp=hp),r)
    for choice in choices:f.choose(clear(f),choice,main._new_stage_game)
    return f

def at24():
    f=at23();f.choose(clear(f),'hp',main._new_stage_game);return f

class StageTwentyFourTests(unittest.TestCase):
    def test_third_three_upgrade_kinds_carry_hurt_hp_in_fresh_owned_runtime(self):
        for kind in ('attack','hp','move'):
            f=at23();old=f.game;r=f.run;offer=clear(f)
            g,_=f.choose(offer,kind,main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((r.current_stage,len(r.receipts),r.active_offer),(24,3,None))
            self.assertEqual((g.resolver.player_damage,g.player.health.current_hp,g.player.health.max_hp,f.run.stats.move_interval_ticks),{'attack':(9,3,5,18),'hp':(8,4,6,18),'move':(8,3,5,15)}[kind])
            for attr in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(old,attr),getattr(g,attr))
            self.assertIsNot(old.player.health,g.player.health);self.assertIsNot(old.encounter.ledger,g.encounter.ledger)
            self.assertNotEqual(old.combat.combat_session_id,g.combat.combat_session_id)
            self.assertIsNone(g.player.health.last_damage_tick);self.assertEqual((g.resolver.player_invulnerable_until_tick,g.combat.pending_attack_bonus),(0,0))
            with self.assertRaises(ValueError):f.choose(offer,kind,Mock())

    def test_max_cannot_consume_but_hp_and_move_work(self):
        for kind in ('hp','move'):
            f=at23(level=15);o=clear(f);before=state(f);factory=Mock()
            self.assertFalse(o.options[0].enabled)
            with self.assertRaises(ValueError):f.choose(o,'attack',factory)
            factory.assert_not_called();self.assertEqual(state(f),before)
            f.choose(o,kind,main._new_stage_game);self.assertEqual(len(f.run.receipts),3)

    def test_forged_foreign_offers_and_bad_receipts_rejected(self):
        f=at23();o=clear(f);foreign=clear(at23());factory=Mock();before=state(f)
        for fake in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(fake,'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=(Mock(),)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)

    def test_fault_candidates_and_input_preserve_offer_hp_and_retry(self):
        for mode in ('factory','input','stage','chapter','boss','missing','order','hp','delay','id','position','forward','player_hp','session','ledger','health','resolver'):
            with self.subTest(mode=mode):
                f=at23();o=clear(f);before=(state(f),f.game.player.health.current_hp)
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
                f.choose(o,'hp',main._new_stage_game);self.assertEqual(f.game.player.health.current_hp,4)

    def test_keyboard_mouse_max_and_same_frame_duplicate_inputs(self):
        from types import SimpleNamespace
        factory=main._new_stage_game
        for inputs in ([key(50),key(50,repeat=True),key(49)], [SimpleNamespace(type=1025,button=1,x=730,y=500),key(50)]):
            games,snapshots,*_=run_loop([inputs,[]],initial_stage=23,entry_attack_level=15,initial_factory=lambda:factory(23,stats=__import__('upgrades').ChapterBuild(15,0,2).stats,initial_hp=1))
            self.assertEqual([g.stage_number for g in games],[23,24]);self.assertEqual(games[-1].player.health.current_hp,2)
        games,*_=run_loop([[key(49)],[SimpleNamespace(type=1025,button=1,x=450,y=500)],[key(50)]],initial_stage=23,entry_attack_level=15,initial_factory=lambda:factory(23,stats=__import__('upgrades').ChapterBuild(15,0,2).stats,initial_hp=1))
        self.assertEqual([g.stage_number for g in games],[23,24]);self.assertEqual(games[-1].player.health.current_hp,2)



    def test_move_max_and_hp_max_use_valid_owned_receipts(self):
        f=at23(choices=('move','move'));o=clear(f);before=state(f)
        self.assertFalse(o.options[2].enabled)
        with self.assertRaises(ValueError):f.choose(o,'move',main._new_stage_game)
        self.assertEqual(state(f),before)
        f.choose(o,'hp',main._new_stage_game)
        self.assertEqual((len(f.run.receipts),f.run.stats.move_interval_ticks),(3,12))
        f=at24();o=clear(f)
        self.assertFalse(o.options[1].enabled);self.assertEqual(f.run.stats.max_hp,6)
        with self.assertRaises(ValueError):f.run.build.upgraded('hp')

    def test_original_roster_delay_hp_and_theme(self):
        from renderer import BoardRenderer
        g=main._new_stage_game(24)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(5,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],[
            ('s24_queen_1','queen',(4,7),48,22),('s24_queen_2','queen',(8,4),62,22),
            ('s24_rook_1','rook',(2,4),75,20),('s24_rook_2','rook',(7,4),88,20),
            ('s24_bishop_1','bishop',(2,8),101,16),('s24_knight_1','knight',(3,6),114,16),
            ('s24_knight_2','knight',(6,6),128,16),('s24_pawn_1','pawn',(1,6),141,13)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),145)
        self.assertEqual(g.encounter.enemies[-1].forward,(0,-1))
        self.assertEqual(BoardRenderer(chapter=5).theme.name,'Gothic Throne')
        for n in (25,26):
            with self.assertRaises(ValueError):main._new_stage_game(n)

    def test_original_double_queen_snapshots_and_source_owned_cancel(self):
        from queen_behavior import queen_ray_targets
        from enemy_attack_renderer import EnemyAttackRenderer
        g=main._new_stage_game(24);g.advance(101);a,b=g.encounter.enemies[:2]
        ea,eb=a.current_attack,b.current_attack
        self.assertEqual((ea.start_tick,eb.start_tick),(49,63));self.assertNotEqual(ea.key,eb.key)
        for q,ev in ((a,ea),(b,eb)):
            self.assertEqual(ev.target_cells,queen_ray_targets(q.position));self.assertEqual(ev.hit_tick-ev.start_tick,72)
        snapshots=(ea.target_cells,eb.target_cells);before=(g.combat.tick,g.player.health.current_hp)
        r=EnemyAttackRenderer();r.tick=g.combat.tick;r.source_cells={e.entity_instance_id:e.position for e in g.encounter.enemies if e.active}
        for _ in range(5):r.draw(Mock(),g.encounter.ledger)
        self.assertEqual(before,(g.combat.tick,g.player.health.current_hp))
        a.health.apply_damage(a.health.current_hp,tick=101);g.encounter.deactivate(a.entity_instance_id,tick=101)
        self.assertEqual(g.encounter.ledger.state(ea),'cancelled');self.assertEqual(g.encounter.ledger.state(eb),'telegraph')
        g.player.move('left',occupied=g.encounter.occupied_cells);g.advance(34)
        self.assertEqual((ea.target_cells,eb.target_cells),snapshots)
        self.assertEqual(b.next_action_tick,eb.hit_tick+180)
        for _ in range(100):
            g.advance();cells=[e.position for e in g.encounter.enemies if e.active]
            self.assertEqual(len(cells),len(set(cells)))

    def test_overlapping_queen_hits_share_immunity_and_parry_source(self):
        # Synchronize actual AI-ready times only in this adjudication fixture.
        for grade,delta in (('hit',None),('normal',18),('perfect',7)):
            g=main._new_stage_game(24)
            for i,e in enumerate(g.encounter.enemies):e.next_action_tick=1 if i<2 else 1000
            g.advance(2);a,b=g.encounter.enemies[:2];ea,eb=a.current_attack,b.current_attack
            self.assertEqual(ea.hit_tick,eb.hit_tick)
            common=(set(ea.target_cells)&set(eb.target_cells))-set(g.encounter.occupied_cells)
            self.assertTrue(common);target=sorted(common)[0]
            while g.player.col!=target[0]:g.player.move('right' if g.player.col<target[0] else 'left')
            while g.player.row!=target[1]:g.player.move('up' if g.player.row<target[1] else 'down')
            if delta:
                g.advance(ea.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.advance(ea.hit_tick-g.combat.tick)
            self.assertEqual(g.player.health.current_hp,2)
            self.assertEqual(g.encounter.ledger.outcome(ea),'hit' if grade=='hit' else 'parried_'+grade)
            self.assertEqual(g.encounter.ledger.outcome(eb),'invulnerable' if grade=='hit' else 'hit')
            for ev in (ea,eb):self.assertIsNone(g.resolver.resolve_enemy_attack(ev))
            if grade=='perfect':
                self.assertGreater(a.stun_until_tick,g.combat.tick)
                self.assertEqual(g.combat.pending_attack_bonus,2)
    def test_game_over_restarts_chapter_and_simultaneous_death_priority(self):
        f=at24();old=f.game;r=f.run
        finish(old,'dead');g,_=f.restart(main._new_stage_game)
        self.assertTrue(r.retired);self.assertIsNot(f.run,r)
        self.assertEqual((g.stage_number,g.resolver.player_damage,g.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(21,8,3,18,0))
        self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
        self.assertIsNot(g.encounter.ledger,old.encounter.ledger)
        self.assertIsNone(g.player.health.last_damage_tick)
        g=main._new_stage_game(24)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state()
        self.assertEqual(g.state,GameState.GAME_OVER);self.assertTrue(g.resolver.stopped)

    def test_seven_fps_and_single_eight_tick_determinism(self):
        def snapshot(g):
            return (g.combat.tick,g.state,g.player.health.current_hp,
                    [(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],
                    [(r.event.target_cells,r.event.hit_tick,r.state,r.outcome) for r in g.encounter.ledger._records.values()])
        rows=[]
        for fps in (30,60,120,144,160,180,240):
            g=main._new_stage_game(24);c=SimulationClock()
            for _ in range(fps*4):g.advance(c.advance(1/fps))
            rows.append(snapshot(g))
        for stride in (1,8):
            g=main._new_stage_game(24)
            for _ in range(240//stride):g.advance(stride)
            rows.append(snapshot(g))
        self.assertTrue(all(r==rows[0] for r in rows))

    def test_four_actual_fights_preserve_survival_failure(self):
        for style,result,tick,hp in (('attack','UPGRADE',522,6),('survival','GAME_OVER',704,0),('evasion','UPGRADE',605,2),('balanced','UPGRADE',677,3)):
            row=measure(style,24)
            self.assertEqual((row['result'],row['ticks'],row['remaining_hp']),(result,tick,hp))
            self.assertEqual(row['hp'],[22,22,20,20,16,16,16,13])
    def test_third_offer_boundary_no_cards_or_input_consumption(self):
        from types import SimpleNamespace
        f=at24();g=f.game;g.advance(88);pending=g.encounter.ledger.pending;o=clear(f)
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

    def test_real_chapter_five_chain_uses_remaining_hp_and_issued_second_offer(self):
        # Actual AI kills throughout; no clear fixture, damage edit, or healing.
        for style,entry,expected in (
            ('attack',15,[(432,2,3),(423,3,4),(435,4,5),(522,5,6)]),
            ('balanced',8,[(651,2,3),(684,1,3),(687,2,4),(677,1,4)])):
            r=ChapterRun(5,entry_attack_level=entry)
            f=StageProgression(main._new_stage_game(21,stats=r.stats),r)
            for i,(tick,hp,max_hp) in enumerate(expected):
                result=fight(f)
                self.assertEqual(result,(21+i,'UPGRADE',tick,hp,max_hp))
                self.assertEqual(len(r.receipts),i);self.assertIs(f.run,r)
                offer=f.sync_offer();self.assertIs(f.sync_offer(),offer)
                if i<3:
                    choice='hp' if style=='attack' else STYLES[style][i]
                    f.choose(offer,choice,main._new_stage_game)
                    self.assertEqual(f.game.player.health.current_hp,hp+(choice=='hp'))
                else:self.assertFalse(f.game.upgrade_selection_enabled)

    def test_original_knights_rooks_bishop_and_pawn_owned_plans(self):
        g=main._new_stage_game(24);g.advance(128)
        a,b=g.encounter.enemies[5:7];own,foreign=a.current_attack,b.current_attack
        self.assertEqual((own.start_tick,foreign.start_tick),(114,128));self.assertNotEqual(own.key,foreign.key)
        bishop=g.encounter.enemies[4].current_attack
        self.assertEqual((len(bishop.target_cells),bishop.hit_tick-bishop.start_tick),(50,108))
        a.health.apply_damage(a.health.current_hp,tick=128);g.encounter.deactivate(a.entity_instance_id,tick=128)
        self.assertEqual(g.encounter.ledger.state(own),'cancelled');self.assertEqual(g.encounter.ledger.state(foreign),'telegraph')
        g=main._new_stage_game(24);g.advance(165)
        for r in g.encounter.enemies[2:4]:
            self.assertIsNotNone(r.current_attack);self.assertEqual(r.current_attack.hit_tick-r.current_attack.start_tick,48)
        for contact in (True,False):
            # Per-source contact/diagonal fixture, not a clear measurement.
            g=main._new_stage_game(24);p=g.encounter.enemies[-1]
            for e in g.encounter.enemies[:-1]:e.next_action_tick=1000
            target=(p.col if contact else p.col+1,p.row-1)
            while g.player.col!=target[0]:g.player.move('right' if g.player.col<target[0] else 'left')
            while g.player.row!=target[1]:g.player.move('up' if g.player.row<target[1] else 'down')
            g.advance(141);ev=p.current_attack
            self.assertEqual(ev.attack_kind,'pawn_contact' if contact else 'basic')
            self.assertIn(g.player.position,ev.target_cells)
            g.advance(ev.hit_tick-g.combat.tick);self.assertEqual(g.player.health.current_hp,2)
            self.assertIsNone(g.resolver.resolve_enemy_attack(ev))
