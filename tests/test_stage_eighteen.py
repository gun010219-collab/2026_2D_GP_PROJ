"""Stage18 original Queen/Bishop/Rook/Pawn combat and owned second upgrade."""
from dataclasses import replace
from unittest.mock import Mock,patch,PropertyMock
import unittest
import main
from chapter_run import ChapterRun
from stage_progression import StageProgression
from game import GameState
from queen_behavior import queen_ray_targets
from enemy_attack_renderer import EnemyAttackRenderer
from tests.test_stage_seventeen import at17
from tests.test_chapter_three_entry import state
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish
from tests.balance_driver import measure,STYLES


def at18():
    f=at17();f.choose(clear(f),'attack',main._new_stage_game);return f


class StageEighteenTests(unittest.TestCase):
    def test_original_roster_hp_delay_and_initial31(self):
        g=main._new_stage_game(18)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(4,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],[
          ('s18_queen_1','queen',(4,7),48,18),('s18_bishop_1','bishop',(2,8),62,13),
          ('s18_rook_1','rook',(2,4),75,16),('s18_rook_2','rook',(7,4),88,16),
          ('s18_pawn_1','pawn',(1,6),101,10),('s18_pawn_2','pawn',(8,6),114,10)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),83)
        self.assertEqual([e.forward for e in g.encounter.enemies[-2:]],[(0,-1)]*2)
        self.assertEqual(len(queen_ray_targets((4,7))),31)

    def test_three_choices_one_receipt_fresh_runtime_and_max_rejection(self):
        for kind in ('attack','hp','move'):
            f=at17();o=clear(f);old=f.game;r=f.run
            self.assertTrue(old.upgrade_selection_enabled)
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((r.current_stage,len(r.receipts),r.active_offer),(18,2,None))
            self.assertEqual((g.resolver.player_damage,g.player.health.current_hp),(r.stats.attack_damage,r.stats.max_hp))
            for name in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(g,name),getattr(old,name))
            self.assertIsNot(g.encounter.ledger,old.encounter.ledger)
            self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
            self.assertNotEqual(g.combat.stage_instance_id,old.combat.stage_instance_id)
            self.assertTrue({id(e.health) for e in g.encounter.enemies}.isdisjoint({id(e.health) for e in old.encounter.enemies}))
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())
        r=ChapterRun(4,entry_attack_level=15);f=StageProgression(main._new_stage_game(16,stats=r.stats),r);f.choose(clear(f),'move',main._new_stage_game)
        o=clear(f);before=state(f);factory=Mock()
        with self.assertRaises(ValueError):f.choose(o,'attack',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)
        f.choose(o,'hp',main._new_stage_game);self.assertEqual(f.game.player.health.max_hp,4)

    def test_copied_foreign_offers_and_previous_run_receipts_rejected(self):
        f=at17();o=clear(f);other=at17();foreign=clear(other);before=state(f);factory=Mock()
        for forged in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(forged,'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=other.run.receipts+(Mock(),)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        self.assertEqual(state(f),before);factory.assert_not_called()

    def test_candidate_faults_preserve_offer_and_retry(self):
        modes=('factory','input','stage','chapter','boss','hp0','hp1','hp2','hp3','hp4','hp5','missing','extra','order','id','position','delay','forward','spawn','player_hp','session','stage_id','ledger','resolver')
        for mode in modes:
            with self.subTest(mode=mode):
                f=at17();o=clear(f);before=state(f)
                def factory(n,*,stats):
                    if mode=='factory':raise RuntimeError('factory')
                    g=main._new_stage_game(n,stats=stats);es=g.encounter.enemies
                    if mode=='stage':g._stage_number=17
                    if mode=='chapter':g._chapter=3
                    if mode=='boss':g._boss=True
                    if mode.startswith('hp'):es[int(mode[-1])].health.apply_damage(1,tick=0)
                    if mode=='missing':g.encounter.enemies=es[:-1]
                    if mode=='extra':g.encounter.enemies=es+(es[-1],)
                    if mode=='order':g.encounter.enemies=tuple(reversed(es))
                    if mode=='id':es[0].data_id='forged'
                    if mode=='position':es[0].col=0
                    if mode=='delay':es[0].initial_delay=.9
                    if mode=='forward':es[-1].forward=(0,1)
                    if mode=='spawn':g.player._col=0
                    if mode=='player_hp':g.player.health.apply_damage(1,tick=0)
                    if mode=='session':g.combat._combat_session_id=f.game.combat.combat_session_id
                    if mode=='stage_id':g.combat._stage_instance_id=f.game.combat.stage_instance_id
                    if mode=='ledger':g.encounter.ledger=f.game.encounter.ledger
                    if mode=='resolver':g.resolver=f.game.resolver
                    return g
                prepare=Mock(side_effect=RuntimeError('input')) if mode=='input' else lambda stats:None
                with self.assertRaises((ValueError,RuntimeError)):f.choose(o,'hp',factory,prepare)
                self.assertEqual(state(f),before);f.choose(o,'hp',main._new_stage_game)
                self.assertEqual(len(f.run.receipts),2)


    def test_real_initial_reposition_piercing_snapshot_and_bishop_coexist(self):
        g=main._new_stage_game(18);q,b=g.encounter.enemies[:2]
        g.advance(47);self.assertEqual(q.position,(4,7));self.assertIsNone(q.current_attack)
        g.advance();self.assertNotEqual(q.position,(4,7));self.assertIsNone(q.current_attack)
        g.advance();event=q.current_attack;origin=q.position
        self.assertEqual((event.start_tick,event.hit_tick),(49,121))
        self.assertEqual(event.target_cells,queen_ray_targets(origin))
        self.assertEqual(len(event.target_cells),len(set(event.target_cells)))
        g.advance(13);bishop=b.current_attack
        self.assertEqual((bishop.start_tick,bishop.hit_tick,len(bishop.target_cells)),(62,170,50))
        self.assertTrue(set(event.target_cells)&set(bishop.target_cells))
        snapshot=event.target_cells
        g.player.move('right',occupied=g.encounter.occupied_cells);g.advance(58)
        self.assertEqual(event.target_cells,snapshot);self.assertEqual(g.player.health.current_hp,3)
        g.advance();self.assertEqual(g.encounter.ledger.outcome(event),'miss')
        self.assertEqual(q.next_action_tick,301)
        # The vertical beam passes both the player's former cell and other occupants.
        self.assertIn((5,0),snapshot);self.assertIn((5,1),snapshot)

    def test_actual_laser_hit_normal_perfect_and_forgery_rejection(self):
        for grade,delta in (('hit',None),('normal',18),('perfect',7)):
            g=main._new_stage_game(18);g.advance(49);q=g.encounter.enemies[0];e=q.current_attack
            if delta:
                g.advance(e.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.advance(e.hit_tick-1-g.combat.tick);self.assertEqual(g.player.health.current_hp,3)
            g.advance();self.assertEqual(g.player.health.current_hp,2 if grade=='hit' else 3)
            self.assertEqual(g.encounter.ledger.outcome(e),'hit' if grade=='hit' else 'parried_'+grade)
            self.assertIsNone(g.resolver.resolve_enemy_attack(e))
            with self.assertRaises(ValueError):g.resolver.resolve_enemy_attack(replace(e,target_cells=((0,0),)))
            if grade=='perfect':self.assertEqual((q.stun_until_tick,g.combat.pending_attack_bonus),(181,2))

    def test_mixed_shared_immunity_and_unique_occupancy(self):
        g=main._new_stage_game(18);g.advance(170)
        self.assertEqual(g.player.health.current_hp,1)
        self.assertEqual(g.resolver.player_invulnerable_until_tick,218)
        g.advance(25);record=next(r for r in g.encounter.ledger._records.values() if r.event.hit_tick==195)
        self.assertEqual(record.outcome,'invulnerable');self.assertEqual(g.player.health.current_hp,1)
        for _ in range(30):
            g.advance();cells=[e.position for e in g.encounter.enemies if e.active]
            self.assertEqual(len(cells),len(set(cells)))

    def test_charge_fire_fade_is_read_only_at_actual_stage18(self):
        g=main._new_stage_game(18);g.advance(49);q=g.encounter.enemies[0];e=q.current_attack
        r=EnemyAttackRenderer();r.source_cells={x.entity_instance_id:x.position for x in g.encounter.enemies}
        r.tick=49;c=Mock();r.draw(c,g.encounter.ledger);self.assertIn(e.key,r._beams)
        g.advance(72);before=(g.combat.tick,g.player.health.current_hp,[(x.state,x.outcome) for x in g.encounter.ledger._records.values()])
        r.tick=121;c.reset_mock();r.draw(c,g.encounter.ledger)
        self.assertTrue(any(call.args[-3:]==(255,244,210) for call in c.draw_line.call_args_list))
        r.tick=125;c.reset_mock();r.draw(c,g.encounter.ledger)
        self.assertTrue(any(call.args[-3:]==(158,112,205) for call in c.draw_line.call_args_list))
        for _ in range(10):r.draw(c,g.encounter.ledger)
        self.assertEqual(before,(g.combat.tick,g.player.health.current_hp,[(x.state,x.outcome) for x in g.encounter.ledger._records.values()]))
        r.tick=133;r.draw(c,g.encounter.ledger);self.assertNotIn(e.key,r._beams)

    def test_sources_die_cancel_and_simultaneous_player_death_wins(self):
        for index in range(6):
            g=main._new_stage_game(18);g.advance(110);e=g.encounter.enemies[index];event=e.current_attack
            e.health.apply_damage(e.health.current_hp,tick=110);g.encounter.deactivate(e.entity_instance_id,tick=110);g.update_state()
            self.assertTrue(g.playing)
            if event:self.assertEqual(g.encounter.ledger.state(event),'cancelled')
        g=main._new_stage_game(18)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state();self.assertEqual(g.state,GameState.GAME_OVER)

    def test_third_offer_holds_without_factory_and_restart_restores_entry(self):
        f=at18();g=f.game;g.advance(100);events=g.encounter.ledger.pending;o=clear(f);before=state(f);factory=Mock()
        self.assertEqual((o.stage,f.run.current_stage,len(f.run.receipts)),(18,18,2));self.assertIs(f.sync_offer(),o)
        for kind in ('attack','hp','move'):
            with self.assertRaisesRegex(ValueError,'Stage 19 is not available'):f.choose(o,kind,factory)
        factory.assert_not_called();g.advance(100);self.assertEqual(state(f),before)
        for ev in events:self.assertEqual(g.encounter.ledger.state(ev),'cancelled')
        f=at18();old=f.game;run=f.run;old.advance(100);events=old.encounter.ledger.pending
        attempt=old.parry.request(old.combat.tick);old.resolver.register_parry(attempt)
        finish(old,'dead');new,_=f.restart(main._new_stage_game)
        self.assertEqual((new.stage_number,new.resolver.player_damage,new.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(16,run.entry_attack_level+1,3,18,0))
        self.assertTrue(run.retired);self.assertIsNone(new.parry.last_attempt)
        with self.assertRaises(ValueError):new.resolver.register_parry(attempt)
        for ev in events:
            with self.assertRaises(ValueError):new.resolver.resolve_enemy_attack(ev)

    def test_mixed_one_vs_eight_tick_trace(self):
        traces=[]
        for stride in (1,8):
            g=main._new_stage_game(18)
            for _ in range(640//stride):g.advance(stride)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(*traces)

    def test_four_styles_real_six_enemy_combat(self):
        for style in STYLES:
            r=measure(style,18,limit=3600);self.assertEqual(r['hp'],[18,13,16,16,10,10]);self.assertEqual(r['result'],'UPGRADE');self.assertGreater(r['remaining_hp'],0)
