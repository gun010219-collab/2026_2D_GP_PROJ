"""Stage19 seven-enemy mixed combat and owned third upgrade."""
from dataclasses import replace
from unittest.mock import Mock,patch,PropertyMock
import unittest
import main
from chapter_run import ChapterRun
from stage_progression import StageProgression
from game import GameState
from queen_behavior import queen_ray_targets
from enemy_attack_renderer import EnemyAttackRenderer
from tests.test_stage_eighteen import at18
from tests.test_chapter_three_entry import state
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish
from tests.balance_driver import measure,STYLES


def at19():
    f=at18();f.choose(clear(f),'attack',main._new_stage_game);return f


class StageNineteenTests(unittest.TestCase):
    def test_original_seven_roster_hp_delay_and_initial31(self):
        g=main._new_stage_game(19)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(4,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],[
          ('s19_queen_1','queen',(4,7),48,24),('s19_knight_1','knight',(3,6),62,18),
          ('s19_knight_2','knight',(6,6),75,18),('s19_rook_1','rook',(2,4),88,21),
          ('s19_rook_2','rook',(7,4),101,21),('s19_bishop_1','bishop',(2,8),114,18),
          ('s19_pawn_1','pawn',(1,6),128,13)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),133)
        self.assertEqual(g.encounter.enemies[-1].forward,(0,-1))
        self.assertEqual(len(queen_ray_targets((4,7))),31)

    def test_three_choices_one_receipt_fresh_runtime_and_max_rejection(self):
        for kind in ('attack','hp','move'):
            f=at18();o=clear(f);old=f.game;r=f.run
            self.assertTrue(old.upgrade_selection_enabled)
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((r.current_stage,len(r.receipts),r.active_offer),(19,3,None))
            self.assertEqual((g.resolver.player_damage,g.player.health.current_hp),(r.stats.attack_damage,r.stats.max_hp))
            for name in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(g,name),getattr(old,name))
            self.assertIsNot(g.encounter.ledger,old.encounter.ledger)
            self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
            self.assertNotEqual(g.combat.stage_instance_id,old.combat.stage_instance_id)
            self.assertTrue({id(e.health) for e in g.encounter.enemies}.isdisjoint({id(e.health) for e in old.encounter.enemies}))
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())
        r=ChapterRun(4,entry_attack_level=15);f=StageProgression(main._new_stage_game(16,stats=r.stats),r);f.choose(clear(f),'move',main._new_stage_game);f.choose(clear(f),'move',main._new_stage_game)
        o=clear(f);before=state(f);factory=Mock()
        with self.assertRaises(ValueError):f.choose(o,'attack',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)
        f.choose(o,'hp',main._new_stage_game);self.assertEqual(f.game.player.health.max_hp,4)

    def test_copied_foreign_offers_and_previous_run_receipts_rejected(self):
        f=at18();o=clear(f);other=at18();foreign=clear(other);before=state(f);factory=Mock()
        for forged in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(forged,'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=other.run.receipts+(Mock(),)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        self.assertEqual(state(f),before);factory.assert_not_called()

    def test_candidate_faults_preserve_offer_and_retry(self):
        modes=('factory','input','stage','chapter','boss','hp0','hp1','hp2','hp3','hp4','hp5','hp6','missing','extra','order','id','position','delay','forward','spawn','player_hp','session','stage_id','ledger','resolver')
        for mode in modes:
            with self.subTest(mode=mode):
                f=at18();o=clear(f);before=state(f)
                def factory(n,*,stats):
                    if mode=='factory':raise RuntimeError('factory')
                    g=main._new_stage_game(n,stats=stats);es=g.encounter.enemies
                    if mode=='stage':g._stage_number=18
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
                self.assertEqual(len(f.run.receipts),3)


    def test_sources_die_cancel_and_simultaneous_player_death_wins(self):
        for index in range(7):
            g=main._new_stage_game(19);g.advance(110);e=g.encounter.enemies[index];event=e.current_attack
            e.health.apply_damage(e.health.current_hp,tick=110);g.encounter.deactivate(e.entity_instance_id,tick=110);g.update_state()
            self.assertTrue(g.playing)
            if event:self.assertEqual(g.encounter.ledger.state(event),'cancelled')
        g=main._new_stage_game(19)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state();self.assertEqual(g.state,GameState.GAME_OVER)

    def test_third_offer_holds_without_factory_and_restart_restores_entry(self):
        from tests.test_stage_twenty import at20
        f=at20();g=f.game;g.advance(100);pending=g.encounter.ledger.pending
        clear(f);before=state(f);factory=Mock()
        self.assertIsNone(f.offer);self.assertIsNone(f.sync_offer())
        self.assertEqual((g.state,f.run.current_stage,len(f.run.receipts)),(GameState.BOSS_CLEAR,20,4))
        for kind in ('attack','hp','move'):
            with self.assertRaises(ValueError):f.choose(None,kind,factory)
        with self.assertRaises(ValueError):f.enter_next_chapter(factory)
        factory.assert_not_called();g.advance(999);self.assertEqual(state(f),before)
        for ev in pending:self.assertEqual(g.encounter.ledger.state(ev),'cancelled')
        self.assertIsNone(g.next_stage_number);self.assertEqual(g.restart_stage_number,20)
        f=at19();old=f.game;run=f.run;old.advance(100);events=old.encounter.ledger.pending
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
            g=main._new_stage_game(19)
            for _ in range(640//stride):g.advance(stride)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(*traces)

    def test_four_styles_real_seven_enemy_combat(self):
        for style in STYLES:
            r=measure(style,19,limit=3600);self.assertEqual(r['hp'],[24,18,18,21,21,18,13])
            # F2: preserve the real failed evasion measurement rather than force a clear.
            if style=='evasion':
                self.assertEqual((r['result'],r['ticks'],r['received'],r['perfect'],r['remaining_hp']),('GAME_OVER',395,3,4,0))
            else:
                self.assertEqual(r['result'],'UPGRADE');self.assertGreater(r['remaining_hp'],0)

    def test_queen_two_knights_and_bishop_real_snapshots(self):
        g=main._new_stage_game(19);q,k1,k2=g.encounter.enemies[:3]
        g.advance(47);self.assertEqual(q.position,(4,7));g.advance();self.assertNotEqual(q.position,(4,7));self.assertIsNone(q.current_attack)
        g.advance();laser=q.current_attack;origin=q.position
        self.assertEqual(laser.target_cells,queen_ray_targets(origin));self.assertEqual(laser.hit_tick-laser.start_tick,72)
        g.advance(26);events=[k1.current_attack,k2.current_attack]
        self.assertTrue(all(events));self.assertNotEqual(events[0].key,events[1].key)
        self.assertNotEqual(events[0].target_cells,events[1].target_cells)
        for k,e in zip((k1,k2),events):
            self.assertEqual(e.start_tick,k.initial_delay_ticks)
            dx,dy=abs(e.target_cells[0][0]-k.col),abs(e.target_cells[0][1]-k.row)
            self.assertEqual({dx,dy},{1,2})
        for e,k in zip(events,(k1,k2)):
            g.advance(e.hit_tick-g.combat.tick);self.assertEqual(k.position,e.target_cells[0])
        g.advance(3);b=g.encounter.enemies[5];be=b.current_attack
        self.assertEqual((be.hit_tick-be.start_tick,len(be.target_cells)),(108,50))
        self.assertEqual(set(be.target_cells),{(x,y) for x in range(10) for y in range(10) if (x+y)%2==0})
        self.assertEqual(laser.target_cells,queen_ray_targets(origin))
        g.advance(laser.hit_tick-g.combat.tick);self.assertEqual(g.player.health.current_hp,2)
        self.assertIsNone(g.resolver.resolve_enemy_attack(laser));self.assertEqual(q.next_action_tick,301)

    def test_knight_death_cancels_only_owned_plan(self):
        for index,other in ((1,2),(2,1)):
            g=main._new_stage_game(19);g.advance(75);es=g.encounter.enemies
            own,foreign=es[index].current_attack,es[other].current_attack
            es[index].health.apply_damage(es[index].health.current_hp,tick=75);g.encounter.deactivate(es[index].entity_instance_id,tick=75)
            self.assertEqual(g.encounter.ledger.state(own),'cancelled')
            self.assertEqual(g.encounter.ledger.state(foreign),'telegraph')
            g.advance(foreign.hit_tick-g.combat.tick)
            self.assertEqual(es[other].position,foreign.target_cells[0]);self.assertTrue(g.playing)

    def test_actual_queen_parry_and_bishop_isolated_source_rewards(self):
        for kind in ('queen','bishop'):
            for grade,delta in (('normal',18),('perfect',7),('miss',None)):
                g=main._new_stage_game(19);source=next(e for e in g.encounter.enemies if e.kind==kind)
                if kind=='bishop':
                    # Isolate Bishop adjudication; full original seven-enemy battles are separate.
                    for e in g.encounter.enemies:
                        if e is not source:e.next_action_tick=1000
                g.advance(source.initial_delay_ticks+(kind=='queen'));event=source.current_attack
                if delta:
                    g.advance(event.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
                else:g.player.move('right',occupied=g.encounter.occupied_cells)
                g.advance(event.hit_tick-g.combat.tick)
                self.assertEqual(g.player.health.current_hp,3)
                self.assertEqual(g.encounter.ledger.outcome(event),'miss' if grade=='miss' else 'parried_'+grade)
                if grade=='perfect':
                    self.assertEqual((source.stun_until_tick,g.combat.pending_attack_bonus),(event.hit_tick+60,2))
                    self.assertTrue(all(e.stun_until_tick==0 for e in g.encounter.enemies if e is not source))

    def test_original_rook_pair_shared_hurt_window_and_dense_occupancy(self):
        g=main._new_stage_game(19);g.advance(195)
        for e in g.encounter.enemies[3:5]:
            ev=e.current_attack;self.assertIsNotNone(ev)
            self.assertTrue(all(c[0]==e.col or c[1]==e.row for c in ev.target_cells))
            self.assertFalse(set(ev.target_cells)&(g.encounter.occupied_cells-{e.position}))
        g.advance(13);self.assertEqual(g.player.health.current_hp,1)
        self.assertEqual(g.resolver.player_invulnerable_until_tick,256)
        g.advance(14)
        records=g.encounter.ledger._records.values()
        self.assertEqual([r.outcome for r in records if r.event.hit_tick in (221,222)],['invulnerable','invulnerable'])
        for _ in range(100):
            g.advance();cells=[e.position for e in g.encounter.enemies if e.active]
            self.assertEqual(len(cells),len(set(cells)))
        self.assertEqual(g.state,GameState.GAME_OVER)
