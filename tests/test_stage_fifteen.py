"""Original Stage15 boss, authenticated fourth choice, Pulse and replay."""
import unittest
from unittest.mock import Mock,patch,PropertyMock
from dataclasses import replace
import main
from game import GameState
from chapter_run import ChapterRun
from stage_progression import StageProgression
from tests.test_stage_fourteen import at14
from tests.test_chapter_three_entry import state
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish
from tests.balance_driver import measure,STYLES


def at15():
    f=at14();f.choose(clear(f),'attack',main._new_stage_game);return f


def pulse_game(delta=7):
    g=main._new_stage_game(15)
    while g.playing and g.encounter.pulse.event is None and g.combat.tick<900:g.advance()
    event=g.encounter.pulse.event
    if event is None:raise AssertionError('Stage15 Pulse absent')
    g.advance(event.hit_tick-delta-g.combat.tick)
    g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(delta)
    return g,event


class StageFifteenTests(unittest.TestCase):
    def test_exact_roster_pulse_and_original_hp(self):
        from stage_manager import StageCatalog
        g=main._new_stage_game(15);es=g.encounter.enemies
        self.assertEqual((g.chapter,g.boss,g.player.position),(3,True,(5,1)))
        self.assertEqual(StageCatalog.load().get_stage(15).boss_hp,12)
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in es],
          [('s15_king_1','king',(5,9),48,60),('s15_queen_1','queen',(4,7),62,14),('s15_rook_1','rook',(2,4),75,12),('s15_pawn_1','pawn',(1,6),88,7),('s15_pawn_2','pawn',(8,6),101,7)])
        self.assertIs(g.encounter.pulse.king,es[0]);self.assertEqual(g.encounter.pulse.next_use_tick,240)
        self.assertTrue(all(e.forward==(0,-1) for e in es[3:]))

    def test_third_choice_three_kinds_and_duplicate_rejection(self):
        for kind in ('attack','hp','move'):
            f=at14();o=clear(f);old=f.game;r=f.run
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(r,f.run);self.assertEqual((r.current_stage,len(r.receipts)),(15,4))
            self.assertEqual(g.player.health.current_hp,r.stats.max_hp)
            self.assertEqual(g.resolver.player_damage,r.stats.attack_damage)
            for name in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(old,name),getattr(g,name))
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())

    def test_copied_offer_and_receipt_and_max_do_not_consume(self):
        f=at14();o=clear(f);before=state(f);factory=Mock()
        with self.assertRaises(ValueError):f.choose(replace(o),'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=tuple(replace(r) for r in f.run.receipts)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)
        r=ChapterRun(3,entry_attack_level=15);f=StageProgression(main._new_stage_game(11,stats=r.stats),r)
        for kind in ('hp','move','hp'):f.choose(clear(f),kind,main._new_stage_game)
        o=clear(f);before=state(f)
        with self.assertRaises(ValueError):f.choose(o,'attack',factory)
        self.assertEqual(state(f),before);factory.assert_not_called()

    def test_every_candidate_fault_preserves_offer_and_retry(self):
        for mode in ('factory','input','stage','chapter','boss','king_hp','queen_hp','rook_hp','pawn_hp','pulse','king_ref','pulse_owner','missing','extra','order','forward','spawn','resolver','roster','position','delay','player_hp','session','stage_id','ledger'):
            with self.subTest(mode=mode):
                f=at14();o=clear(f);before=state(f)
                def factory(n,*,stats):
                    if mode=='factory':raise RuntimeError(mode)
                    g=main._new_stage_game(n,stats=stats);e=g.encounter.enemies[0]
                    if mode=='stage':g._stage_number=14
                    if mode=='chapter':g._chapter=2
                    if mode=='boss':g._boss=False
                    if mode.endswith('_hp') and mode!='player_hp':g.encounter.enemies[{'king_hp':0,'queen_hp':1,'rook_hp':2,'pawn_hp':3}[mode]].health.apply_damage(1,tick=0)
                    if mode=='missing':g.encounter.enemies=g.encounter.enemies[:-1]
                    if mode=='extra':g.encounter.enemies+= (g.encounter.enemies[-1],)
                    if mode=='order':g.encounter.enemies=tuple(reversed(g.encounter.enemies))
                    if mode=='forward':g.encounter.enemies[-1].forward=(0,1)
                    if mode=='spawn':g.player._col=0
                    if mode=='pulse':g.encounter.pulse=None
                    if mode=='king_ref':g.encounter.pulse.king=g.encounter.enemies[1]
                    if mode=='pulse_owner':g.encounter.pulse.encounter=f.game.encounter
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
                self.assertEqual(len(f.run.receipts),4)

    def test_pulse_normal_perfect_and_single_consumption(self):
        for delta,status,hp,bonus in ((7,'perfect',58,2),(18,'normal',60,0)):
            g,event=pulse_game(delta)
            self.assertEqual((len(event.target_cells),event.hit_tick-event.start_tick),(100,120))
            self.assertEqual((g.resolver.last_parry_result.status,g.encounter.pulse.king.health.current_hp,g.combat.pending_attack_bonus),(status,hp,bonus))
            self.assertIsNone(g.resolver.resolve_enemy_attack(event))

    def test_original_queen_plan_drains_then_freezes_and_resumes(self):
        g=main._new_stage_game(15);p=g.encounter.pulse;seen_drain=False
        while g.playing and p.event is None and g.combat.tick<900:
            g.advance();seen_drain |=p.state=='DRAINING'
        self.assertTrue(seen_drain);self.assertIsNotNone(p.event)
        self.assertTrue(all(k==p.event.key for k in g.encounter._attack_moves))
        frozen=[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies[1:]]
        steps=g.encounter.queen_steps.copy();saved=p._remaining.copy();event=p.event
        g.advance(100);self.assertEqual(frozen,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies[1:]])
        self.assertEqual(steps,g.encounter.queen_steps)
        g.advance(event.hit_tick-7-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(7)
        g.advance(29);self.assertEqual(p.state,'CLEANUP');g.advance();self.assertEqual(p.state,'NORMAL')
        for e in g.encounter.enemies[1:]:
            if saved[e.entity_instance_id][1]>0:self.assertEqual(e.next_action_tick,event.hit_tick+30+saved[e.entity_instance_id][1])

    def test_king_death_releases_pulse_without_reviving_dead_queen(self):
        g=main._new_stage_game(15);p=g.encounter.pulse
        while p.event is None and g.playing:g.advance()
        q=g.encounter.enemies[1];q.health.apply_damage(14,tick=g.combat.tick);g.encounter.deactivate(q.entity_instance_id,tick=g.combat.tick)
        k=p.king;k.health.apply_damage(60,tick=g.combat.tick);g.encounter.deactivate(k.entity_instance_id,tick=g.combat.tick)
        g.advance();self.assertTrue(g.playing);self.assertIsNone(p.freeze_tick);self.assertFalse(q.active)
        self.assertEqual(g.encounter.ledger.state(p.event),'cancelled')

    def test_boss_clear_replay_no_offer_and_n_blocked(self):
        f=at15();g=f.game;r=f.run;finish(g,'clear');before=state(f);factory=Mock()
        self.assertIsNone(f.sync_offer());self.assertIsNone(g.next_stage_number)
        with self.assertRaises(ValueError):f.enter_next_chapter(factory)
        factory.assert_not_called()
        for fail in ('factory','input'):
            with self.assertRaises(RuntimeError):f.restart(Mock(side_effect=RuntimeError()) if fail=='factory' else main._new_stage_game,Mock(side_effect=RuntimeError()))
            self.assertEqual(state(f),before)
        new,_=f.restart(main._new_stage_game);self.assertIs(r,f.run);self.assertEqual(len(r.receipts),4)
        self.assertEqual((new.stage_number,new.encounter.pulse.king.health.current_hp,new.player.health.current_hp),(15,60,r.stats.max_hp))
        self.assertIsNot(g.encounter.pulse,new.encounter.pulse);self.assertNotEqual(g.combat.combat_session_id,new.combat.combat_session_id)

    def test_game_over_restores_entry_and_rejects_previous_pulse(self):
        f=at15();g=f.game;r=f.run
        while g.encounter.pulse.event is None and g.playing:g.advance()
        event=g.encounter.pulse.event;finish(g,'dead');before=state(f)
        with self.assertRaises(RuntimeError):f.restart(main._new_stage_game,Mock(side_effect=RuntimeError()))
        self.assertEqual(state(f),before);new,_=f.restart(main._new_stage_game)
        self.assertTrue(r.retired);self.assertEqual((new.stage_number,new.resolver.player_damage,new.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(11,5,3,18,0))
        with self.assertRaises(ValueError):new.resolver.resolve_enemy_attack(event)

    def test_annihilation_and_death_priority_and_tick_determinism(self):
        for dead in (False,True):
            g=main._new_stage_game(15)
            for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
            if dead:g.player.health.apply_damage(3,tick=0)
            g.update_state();self.assertEqual(g.state,GameState.GAME_OVER if dead else GameState.BOSS_CLEAR)
            g.advance(999);self.assertEqual((g.transition_count,g.combat.tick),(1,0))
        traces=[]
        for step in (1,8):
            g=main._new_stage_game(15)
            for _ in range(800//step):g.advance(step)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(*traces)

    def test_four_styles_actual_boss_clear(self):
        for style in STYLES:
            r=measure(style,15,limit=3600)
            self.assertEqual(r['hp'],[60,14,12,7,7]);self.assertEqual(r['result'],'BOSS_CLEAR');self.assertGreater(r['remaining_hp'],0)

    def test_queen_perfect_has_no_king_reflection(self):
        g=main._new_stage_game(15)
        for e in (g.encounter.enemies[0],*g.encounter.enemies[2:]):e.next_action_tick=1000
        g.advance(63);q=g.encounter.enemies[1];ev=q.current_attack
        g.advance(1);g.player.move('right',occupied=g.encounter.occupied_cells)
        g.advance(18);g.player.move('up',occupied=g.encounter.occupied_cells)
        self.assertIn(g.player.position,ev.target_cells)
        g.advance(ev.hit_tick-7-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(7)
        self.assertEqual(g.encounter.ledger.outcome(ev),'parried_perfect')
        self.assertEqual((g.encounter.enemies[0].health.current_hp,g.combat.pending_attack_bonus,q.stun_until_tick),(60,2,ev.hit_tick+60))

    def test_pulse_reflection_kills_king_and_resumes_others(self):
        g=main._new_stage_game(15);p=g.encounter.pulse
        while p.event is None and g.playing:g.advance()
        # Low-health fixture isolates the lethal reflection branch, not a clear measurement.
        p.king.health.apply_damage(58,tick=g.combat.tick)
        ev=p.event;g.advance(ev.hit_tick-7-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(7)
        self.assertFalse(p.king.alive);self.assertTrue(g.playing)
        g.advance();self.assertIsNone(p.freeze_tick)
