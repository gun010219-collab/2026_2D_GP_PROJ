"""Stage22 original mixed combat, atomic first upgrade and HP carryover."""
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


def at21(hp=1,level=7):
    r=ChapterRun(5,entry_attack_level=level)
    return StageProgression(main._new_stage_game(21,stats=r.stats,initial_hp=hp),r)


def at22():
    f=at21();f.choose(clear(f),'hp',main._new_stage_game);return f


class StageTwentyTwoTests(unittest.TestCase):
    def test_exact_original_roster_hp_delay_theme_and_opposite_colors(self):
        g=main._new_stage_game(22)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(5,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],[
            ('s22_queen_1','queen',(4,7),48,22),('s22_bishop_1','bishop',(2,8),62,16),('s22_bishop_2','bishop',(7,8),75,16),('s22_rook_1','rook',(2,4),88,20),('s22_knight_1','knight',(3,6),101,16),('s22_knight_2','knight',(6,6),114,16),('s22_pawn_1','pawn',(1,6),128,13)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),119)
        self.assertEqual(g.encounter.enemies[-1].forward,(0,-1))
        self.assertEqual([(sum(e.position)%2) for e in g.encounter.enemies[1:3]],[0,1])

    def test_first_three_upgrade_kinds_carry_hurt_hp_in_fresh_owned_runtime(self):
        for kind in ('attack','hp','move'):
            f=at21();old=f.game;r=f.run;offer=clear(f)
            g,_=f.choose(offer,kind,main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((r.current_stage,len(r.receipts),r.active_offer),(22,1,None))
            self.assertEqual((g.resolver.player_damage,g.player.health.current_hp,g.player.health.max_hp,f.run.stats.move_interval_ticks),{'attack':(9,1,3,18),'hp':(8,2,4,18),'move':(8,1,3,15)}[kind])
            for attr in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(old,attr),getattr(g,attr))
            self.assertIsNot(old.player.health,g.player.health);self.assertIsNot(old.encounter.ledger,g.encounter.ledger)
            self.assertNotEqual(old.combat.combat_session_id,g.combat.combat_session_id)
            self.assertIsNone(g.player.health.last_damage_tick);self.assertEqual((g.resolver.player_invulnerable_until_tick,g.combat.pending_attack_bonus),(0,0))
            with self.assertRaises(ValueError):f.choose(offer,kind,Mock())

    def test_max_cannot_consume_but_hp_and_move_work(self):
        for kind in ('hp','move'):
            f=at21(level=15);o=clear(f);before=state(f);factory=Mock()
            self.assertFalse(o.options[0].enabled)
            with self.assertRaises(ValueError):f.choose(o,'attack',factory)
            factory.assert_not_called();self.assertEqual(state(f),before)
            f.choose(o,kind,main._new_stage_game);self.assertEqual(len(f.run.receipts),1)

    def test_forged_foreign_offers_and_bad_receipts_rejected(self):
        f=at21();o=clear(f);foreign=clear(at21());factory=Mock();before=state(f)
        for fake in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(fake,'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=(Mock(),)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)

    def test_fault_candidates_and_input_preserve_offer_hp_and_retry(self):
        for mode in ('factory','input','stage','chapter','boss','missing','order','hp','delay','id','position','forward','player_hp','session','ledger','health','resolver'):
            with self.subTest(mode=mode):
                f=at21();o=clear(f);before=(state(f),f.game.player.health.current_hp)
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
            games,snapshots,*_=run_loop([inputs,[]],initial_stage=21,entry_attack_level=15,initial_factory=lambda:factory(21,stats=__import__('upgrades').ChapterBuild(15).stats,initial_hp=1))
            self.assertEqual([g.stage_number for g in games],[21,22]);self.assertEqual(games[-1].player.health.current_hp,2)
        games,*_=run_loop([[key(49)],[SimpleNamespace(type=1025,button=1,x=450,y=500)],[key(51)]],initial_stage=21,entry_attack_level=15,initial_factory=lambda:factory(21,stats=__import__('upgrades').ChapterBuild(15).stats,initial_hp=1))
        self.assertEqual([g.stage_number for g in games],[21,22]);self.assertEqual(games[-1].player.health.current_hp,1)

    def test_both_bishops_serialize_disjoint_snapshots_and_actual_hits(self):
        g=main._new_stage_game(22)
        # Timing fixture isolates Bishops; original seven-source fights are separate.
        for i,e in enumerate(g.encounter.enemies):
            if i not in (1,2):e.next_action_tick=1000
        a,b=g.encounter.enemies[1:3];g.advance(62);first=a.current_attack
        self.assertEqual((first.start_tick,first.hit_tick),(62,170));self.assertEqual(len(first.target_cells),50)
        g.advance(108);self.assertEqual(g.player.health.current_hp,2);self.assertIsNone(b.current_attack)
        g.advance();second=b.current_attack
        self.assertEqual((second.start_tick,second.hit_tick),(171,279));self.assertEqual(len(second.target_cells),50)
        self.assertFalse(set(first.target_cells)&set(second.target_cells))
        g.player.move('right',occupied=g.encounter.occupied_cells);g.advance(108)
        self.assertEqual(g.player.health.current_hp,1)
        for ev in (first,second):self.assertEqual(g.encounter.ledger.outcome(ev),'hit');self.assertIsNone(g.resolver.resolve_enemy_attack(ev))

    def test_original_queen_bishop_knight_rook_occupancy_and_owned_death_cancel(self):
        g=main._new_stage_game(22);g.advance(114);q,a,b,r,k1,k2,p=g.encounter.enemies
        self.assertEqual(q.current_attack.attack_kind,'queen_diagonal');self.assertEqual(len(a.current_attack.target_cells),50)
        self.assertIsNone(b.current_attack);self.assertIsNotNone(k1.current_attack);self.assertIsNotNone(k2.current_attack)
        own,foreign=k1.current_attack,k2.current_attack
        k1.health.apply_damage(k1.health.current_hp,tick=114);g.encounter.deactivate(k1.entity_instance_id,tick=114)
        self.assertEqual(g.encounter.ledger.state(own),'cancelled');self.assertEqual(g.encounter.ledger.state(foreign),'telegraph')
        for _ in range(180):
            g.advance();cells=[e.position for e in g.encounter.enemies if e.active];self.assertEqual(len(cells),len(set(cells)))

    def test_clear_boundary_preserves_second_offer_and_blocks_factory(self):
        f=at22();f.choose(clear(f),'hp',main._new_stage_game);o=clear(f);factory=Mock();self.assertEqual((f.game.state,len(f.run.receipts),o.stage),(GameState.UPGRADE,2,23))
        for _ in range(3):self.assertIs(f.sync_offer(),o)
        for kind in ('attack','hp','move'):
            with self.assertRaises(ValueError):f.choose(o,kind,factory)
        factory.assert_not_called()
        with patch.object(GameFlowRenderer,'_center') as t:GameFlowRenderer().draw(Mock(),f.game)
        self.assertIn('STAGE 24 NOT AVAILABLE',[c.args[1] for c in t.call_args_list])
        with patch.object(UpgradeRenderer,'_text') as t:UpgradeRenderer().draw(Mock(),f.game,o)
        t.assert_not_called()

    def test_game_over_resets_entry_attack_and_player_death_priority(self):
        f=at21();f.choose(clear(f),'attack',main._new_stage_game);r=f.run;old=f.game
        finish(old,'dead');new,_=f.restart(main._new_stage_game)
        self.assertTrue(r.retired);self.assertEqual((new.stage_number,new.resolver.player_damage,new.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(21,8,3,18,0))
        self.assertNotEqual(new.combat.stage_instance_id,old.combat.stage_instance_id)
        f=at22();g=f.game
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(g.player.health.current_hp,tick=0);g.update_state();self.assertEqual(g.state,GameState.GAME_OVER)

    def test_real_four_build_fights(self):
        for style,tick,hp in (('attack',423,4),('survival',1059,3),('evasion',605,1),('balanced',684,2)):
            row=measure(style,22);self.assertEqual((row['result'],row['ticks'],row['remaining_hp']),('UPGRADE',tick,hp));self.assertEqual(row['hp'],[22,16,16,20,16,16,13])

    def test_seven_fps_and_single_eight_tick_determinism(self):
        def snapshot(g):return(g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()])
        rows=[]
        for fps in (30,60,120,144,160,180,240):
            g=main._new_stage_game(22);c=SimulationClock()
            for _ in range(fps*4):g.advance(c.advance(1/fps))
            rows.append(snapshot(g))
        for stride in (1,8):
            g=main._new_stage_game(22)
            for _ in range(240//stride):g.advance(stride)
            rows.append(snapshot(g))
        self.assertTrue(all(r==rows[0] for r in rows))

    def test_each_bishop_normal_perfect_and_miss_use_only_own_snapshot(self):
        for index in (1,2):
            for grade,delta in (('normal',18),('perfect',7),('miss',None)):
                g=main._new_stage_game(22)
                # Per-source parry fixture, not an independent clear measurement.
                for i,e in enumerate(g.encounter.enemies):
                    if i not in (1,2):e.next_action_tick=1000
                g.advance(62)
                if index==2:g.player.move('right',occupied=g.encounter.occupied_cells);g.advance(109)
                source=g.encounter.enemies[index];event=source.current_attack;snapshot=event.target_cells
                if delta:
                    g.advance(event.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
                else:g.player.move('up',occupied=g.encounter.occupied_cells)
                g.advance(event.hit_tick-g.combat.tick)
                self.assertEqual(g.player.health.current_hp,3);self.assertEqual(event.target_cells,snapshot)
                self.assertEqual(g.encounter.ledger.outcome(event),'miss' if grade=='miss' else 'parried_'+grade)
                if grade=='perfect':self.assertEqual((source.stun_until_tick,g.combat.pending_attack_bonus),(event.hit_tick+60,2))
