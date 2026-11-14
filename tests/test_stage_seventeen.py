"""Original Stage17 two-color combat and atomic first Chapter4 upgrade."""
from dataclasses import replace
from unittest.mock import Mock,patch,PropertyMock
import unittest
import main
from chapter_run import ChapterRun
from stage_progression import StageProgression
from game import GameState
from renderer import BoardRenderer
from tests.test_chapter_four_entry import entered_four
from tests.test_chapter_three_entry import state
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish
from tests.balance_driver import measure,STYLES


def at17():
    f=entered_four();f.choose(clear(f),'attack',main._new_stage_game);return f


class StageSeventeenTests(unittest.TestCase):
    def test_original_roster_order_hp_delays_and_lava(self):
        g=main._new_stage_game(17)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(4,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],
          [('s17_bishop_1','bishop',(2,8),48,13),('s17_bishop_2','bishop',(7,8),62,13),
           ('s17_rook_1','rook',(2,4),75,16),('s17_rook_2','rook',(7,4),88,16),
           ('s17_knight_1','knight',(3,6),101,13),('s17_pawn_1','pawn',(1,6),114,10)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),81)
        self.assertEqual(g.encounter.enemies[-1].forward,(0,-1))
        self.assertEqual(BoardRenderer(chapter=4).theme.name,'Obsidian Caldera')

    def test_three_choices_one_receipt_fresh_runtime_and_max_rejection(self):
        for kind in ('attack','hp','move'):
            f=entered_four();o=clear(f);old=f.game;r=f.run
            self.assertTrue(old.upgrade_selection_enabled)
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((r.current_stage,len(r.receipts),r.active_offer),(17,1,None))
            self.assertEqual((g.resolver.player_damage,g.player.health.current_hp),(r.stats.attack_damage,r.stats.max_hp))
            for name in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(g,name),getattr(old,name))
            self.assertIsNot(g.encounter.ledger,old.encounter.ledger)
            self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
            self.assertNotEqual(g.combat.stage_instance_id,old.combat.stage_instance_id)
            self.assertTrue({id(e.health) for e in g.encounter.enemies}.isdisjoint({id(e.health) for e in old.encounter.enemies}))
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())
        r=ChapterRun(4,entry_attack_level=15);f=StageProgression(main._new_stage_game(16,stats=r.stats),r)
        o=clear(f);before=state(f);factory=Mock()
        with self.assertRaises(ValueError):f.choose(o,'attack',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)
        f.choose(o,'hp',main._new_stage_game);self.assertEqual(f.game.player.health.max_hp,4)

    def test_copied_foreign_offers_and_previous_run_receipts_rejected(self):
        f=entered_four();o=clear(f);other=entered_four();foreign=clear(other);before=state(f);factory=Mock()
        for forged in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(forged,'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=other.run.receipts+(Mock(),)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        self.assertEqual(state(f),before);factory.assert_not_called()

    def test_candidate_faults_preserve_offer_and_retry(self):
        modes=('factory','input','stage','chapter','boss','hp0','hp1','hp2','hp3','hp4','hp5','missing','extra','order','id','position','delay','forward','spawn','player_hp','session','stage_id','ledger','resolver')
        for mode in modes:
            with self.subTest(mode=mode):
                f=entered_four();o=clear(f);before=state(f)
                def factory(n,*,stats):
                    if mode=='factory':raise RuntimeError('factory')
                    g=main._new_stage_game(n,stats=stats);es=g.encounter.enemies
                    if mode=='stage':g._stage_number=16
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
                self.assertEqual(len(f.run.receipts),1)

    def bishop_fixture(self):
        g=main._new_stage_game(17)
        # Isolate Bishop timing only; original six-enemy battles are measured separately.
        for e in g.encounter.enemies[2:]:e.next_action_tick=1000
        return g

    def test_opposite_colors_have_fixed_disjoint50_and_serialized_hit_ticks(self):
        g=self.bishop_fixture();g.advance(48);a,b=g.encounter.enemies[:2];first=a.current_attack
        self.assertEqual((first.start_tick,first.hit_tick),(48,156))
        self.assertEqual(set(first.target_cells),{(x,y) for x in range(10) for y in range(10) if (x+y)%2==0})
        g.advance(107);self.assertEqual(g.player.health.current_hp,3);self.assertIsNone(b.current_attack)
        g.advance();self.assertEqual(g.player.health.current_hp,2);self.assertIsNone(b.current_attack)
        g.advance();second=b.current_attack
        self.assertEqual((second.start_tick,second.hit_tick),(157,265))
        self.assertEqual(set(second.target_cells),{(x,y) for x in range(10) for y in range(10) if (x+y)%2==1})
        self.assertFalse(set(first.target_cells)&set(second.target_cells))
        g.player.move('right',occupied=g.encounter.occupied_cells);g.advance(108)
        self.assertEqual(g.player.health.current_hp,1)
        self.assertEqual([g.encounter.ledger.outcome(e) for e in (first,second)],['hit','hit'])
        self.assertIsNone(g.resolver.resolve_enemy_attack(first));self.assertIsNone(g.resolver.resolve_enemy_attack(second))

    def test_each_bishop_miss_normal_perfect_and_single_source_stun(self):
        for index in (0,1):
            for mode in ('miss','normal','perfect'):
                g=self.bishop_fixture();a,b=g.encounter.enemies[:2]
                if index==1:
                    g.advance(48);g.player.move('right',occupied=g.encounter.occupied_cells);g.advance(109)
                else:g.advance(48)
                source=(a,b)[index];ev=source.current_attack;self.assertIsNotNone(ev)
                if mode=='miss':g.player.move('up',occupied=g.encounter.occupied_cells)
                else:
                    delta=18 if mode=='normal' else 7
                    g.advance(ev.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
                snapshot=ev.target_cells;g.advance(ev.hit_tick-g.combat.tick)
                self.assertEqual(g.player.health.current_hp,3)
                self.assertEqual(g.encounter.ledger.outcome(ev),'miss' if mode=='miss' else 'parried_'+mode)
                self.assertEqual(snapshot,ev.target_cells)
                if mode=='perfect':
                    self.assertEqual((source.stun_until_tick,g.combat.pending_attack_bonus),(ev.hit_tick+60,2))
                    self.assertEqual((b,a)[index].stun_until_tick,0)

    def test_staggered_second_hit_respects_shared48_tick_invulnerability(self):
        # Original six-enemy AI, no forced immunity or rescheduled attacks.
        g=main._new_stage_game(17);g.advance(156)
        self.assertEqual(g.player.health.current_hp,2)
        self.assertEqual(g.resolver.player_invulnerable_until_tick,204)
        g.advance(39)
        records=list(g.encounter.ledger._records.values())
        protected=next(r for r in records if r.event.hit_tick==195)
        self.assertEqual(protected.outcome,'invulnerable')
        self.assertEqual(g.player.health.current_hp,2)
        self.assertIsNone(g.resolver.resolve_enemy_attack(protected.event))
        g.advance(13)
        self.assertEqual(g.player.health.current_hp,1)
        self.assertEqual(next(r.outcome for r in g.encounter.ledger._records.values() if r.event.hit_tick==208),'hit')

    def test_death_cancels_sources_and_all_death_prefers_game_over(self):
        for index in range(6):
            g=main._new_stage_game(17);g.advance(120);e=g.encounter.enemies[index];ev=e.current_attack
            e.health.apply_damage(e.health.current_hp,tick=120);g.encounter.deactivate(e.entity_instance_id,tick=120);g.update_state()
            self.assertTrue(g.playing)
            if ev:self.assertEqual(g.encounter.ledger.state(ev),'cancelled')
        g=main._new_stage_game(17)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state();self.assertEqual(g.state,GameState.GAME_OVER)

    def test_second_offer_held_before_factory_and_terminal_damage_stopped(self):
        f=at17();g=f.game;g.advance(120);pending=g.encounter.ledger.pending;o=clear(f);before=state(f);factory=Mock()
        self.assertEqual((o.stage,f.run.current_stage,len(f.run.receipts)),(17,17,1));self.assertIs(f.sync_offer(),o)
        for kind in ('attack','hp','move'):
            with self.assertRaisesRegex(ValueError,'Stage 18 is not available'):f.choose(o,kind,factory)
        factory.assert_not_called();g.advance(999);self.assertEqual(state(f),before)
        for ev in pending:self.assertEqual(g.encounter.ledger.state(ev),'cancelled')
        self.assertIsNone(g.next_stage_number);self.assertIsNone(g.restart_stage_number)

    def test_game_over_restores_entry_not_first_upgrade(self):
        f=at17();old=f.game;r=f.run;old.advance(120);events=old.encounter.ledger.pending
        attempt=old.parry.request(old.combat.tick);old.resolver.register_parry(attempt)
        finish(old,'dead');new,_=f.restart(main._new_stage_game)
        self.assertEqual((new.stage_number,new.resolver.player_damage,new.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(16,r.entry_attack_level+1,3,18,0))
        self.assertTrue(r.retired);self.assertIsNone(new.parry.last_attempt)
        self.assertNotEqual(new.combat.combat_session_id,old.combat.combat_session_id)
        with self.assertRaises(ValueError):new.resolver.register_parry(attempt)
        for ev in events:
            with self.assertRaises(ValueError):new.resolver.resolve_enemy_attack(ev)

    def test_original_mixed_combat_one_vs_eight_ticks(self):
        traces=[]
        for stride in (1,8):
            g=main._new_stage_game(17)
            for _ in range(640//stride):g.advance(stride)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(*traces)

    def test_four_builds_clear_original_six_enemy_combat(self):
        for style in STYLES:
            r=measure(style,17,limit=3600)
            self.assertEqual(r['hp'],[13,13,16,16,13,10]);self.assertEqual(r['result'],'UPGRADE');self.assertGreater(r['remaining_hp'],0)
