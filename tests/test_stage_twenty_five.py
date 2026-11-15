"""Original Stage25 boss, authenticated fourth choice, Pulse and replay."""
import unittest
from unittest.mock import Mock,patch,PropertyMock
from dataclasses import replace
import main
from game import GameState
from chapter_run import ChapterRun
from stage_progression import StageProgression
from tests.test_chapter_three_entry import state
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish,run_loop,key
from tests.balance_driver import measure,STYLES

def at24(hp=3,level=7,choices=('hp','move','attack')):
    r=ChapterRun(5,entry_attack_level=level)
    f=StageProgression(main._new_stage_game(21,stats=r.stats,initial_hp=hp),r)
    for kind in choices:f.choose(clear(f),kind,main._new_stage_game)
    return f

def at25():
    f=at24();f.choose(clear(f),'attack',main._new_stage_game);return f

def assert_final_boundary(test):
    from game_renderer import GameFlowRenderer
    from upgrade_renderer import UpgradeRenderer
    f=at25();g=f.game;r=f.run;g.advance(100);pending=g.encounter.ledger.pending
    finish(g,'clear');test.assertEqual((g.state,g.transition_count,len(r.receipts)),(GameState.BOSS_CLEAR,1,4))
    test.assertIsNone(f.sync_offer());test.assertIsNone(g.next_stage_number)
    for ev in pending:test.assertEqual(g.encounter.ledger.state(ev),'cancelled')
    for _ in range(3):test.assertFalse(g.update_state());test.assertIsNone(f.sync_offer())
    factory=Mock()
    with test.assertRaises(ValueError):f.enter_next_chapter(factory)
    for kind in ('attack','hp','move'):
        with test.assertRaises(ValueError):f.choose(None,kind,factory)
    factory.assert_not_called()
    with patch.object(GameFlowRenderer,'_center') as text:GameFlowRenderer().draw(Mock(),g)
    labels=[c.args[1] for c in text.call_args_list]
    for label in ('CHECKMATE','ALL 25 STAGES CLEARED','FINAL BOSS DEFEATED','R TO REPLAY BOSS','ESC TO EXIT'):test.assertIn(label,labels)
    test.assertFalse(any('N TO' in l for l in labels))
    with patch.object(UpgradeRenderer,'_text') as text:UpgradeRenderer().draw(Mock(),g,None)
    text.assert_not_called();g.advance(1000);test.assertEqual(g.combat.tick,g.end_tick)
    new,_=f.restart(main._new_stage_game);test.assertIs(f.run,r);test.assertEqual(len(r.receipts),4)
    test.assertIsNot(g.encounter.pulse,new.encounter.pulse)
    finish(new,'dead');new,_=f.restart(main._new_stage_game)
    test.assertEqual((new.stage_number,new.player.health.current_hp,len(f.run.receipts)),(21,3,0))

def pulse_game(delta=7):
    g=main._new_stage_game(25)
    while g.playing and g.encounter.pulse.event is None and g.combat.tick<900:g.advance()
    event=g.encounter.pulse.event
    if event is None:raise AssertionError('Stage25 Pulse absent')
    g.advance(event.hit_tick-delta-g.combat.tick)
    g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(delta)
    return g,event


class StageTwentyFiveTests(unittest.TestCase):
    def test_exact_roster_pulse_and_original_hp(self):
        from stage_manager import StageCatalog
        g=main._new_stage_game(25);es=g.encounter.enemies
        self.assertEqual((g.chapter,g.boss,g.player.position),(5,True,(5,1)))
        self.assertEqual(StageCatalog.load().get_stage(25).boss_hp,16)
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in es],[
            ('s25_king_1','king',(5,9),48,110),('s25_queen_1','queen',(4,7),62,22),
            ('s25_rook_1','rook',(2,4),75,20),('s25_rook_2','rook',(7,4),88,20),
            ('s25_knight_1','knight',(3,6),101,16),('s25_knight_2','knight',(6,6),114,16),
            ('s25_bishop_1','bishop',(2,8),128,16),('s25_pawn_1','pawn',(1,6),141,13)])
        self.assertEqual(sum(e.health.max_hp for e in es),233)
        self.assertIs(g.encounter.pulse.encounter,g.encounter);self.assertIs(g.encounter.pulse.king,es[0]);self.assertEqual(g.encounter.pulse.next_use_tick,240)
        self.assertTrue(all(e.forward==(0,-1) for e in es[-1:]))

    def test_third_choice_three_kinds_and_duplicate_rejection(self):
        for kind in ('attack','hp','move'):
            f=at24();o=clear(f);old=f.game;r=f.run
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(r,f.run);self.assertEqual((r.current_stage,len(r.receipts)),(25,4))
            self.assertEqual(g.player.health.current_hp,r.stats.max_hp)
            self.assertEqual(g.resolver.player_damage,r.stats.attack_damage)
            for name in ('player','combat','parry','encounter','resolver'):self.assertIsNot(getattr(old,name),getattr(g,name))
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())

    def test_copied_offer_and_receipt_and_max_do_not_consume(self):
        f=at24();o=clear(f);before=state(f);factory=Mock()
        with self.assertRaises(ValueError):f.choose(replace(o),'hp',factory)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=tuple(replace(r) for r in f.run.receipts)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        factory.assert_not_called();self.assertEqual(state(f),before)
        r=ChapterRun(5,entry_attack_level=15);f=StageProgression(main._new_stage_game(21,stats=r.stats),r)
        for kind in ('hp','move','hp'):f.choose(clear(f),kind,main._new_stage_game)
        o=clear(f);before=state(f)
        with self.assertRaises(ValueError):f.choose(o,'attack',factory)
        self.assertEqual(state(f),before);factory.assert_not_called()

    def test_every_candidate_fault_preserves_offer_and_retry(self):
        for mode in ('factory','input','stage','chapter','boss','king_hp','queen_hp','bishop_hp','pawn_hp','pulse','king_ref','pulse_owner','missing','extra','order','forward','spawn','resolver','roster','position','delay','player_hp','session','stage_id','ledger'):
            with self.subTest(mode=mode):
                f=at24();o=clear(f);before=state(f)
                def factory(n,*,stats):
                    if mode=='factory':raise RuntimeError(mode)
                    g=main._new_stage_game(n,stats=stats);e=g.encounter.enemies[0]
                    if mode=='stage':g._stage_number=19
                    if mode=='chapter':g._chapter=2
                    if mode=='boss':g._boss=False
                    if mode.endswith('_hp') and mode!='player_hp':g.encounter.enemies[{'king_hp':0,'queen_hp':1,'bishop_hp':6,'pawn_hp':7}[mode]].health.apply_damage(1,tick=0)
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
        for delta,status,hp,bonus in ((7,'perfect',108,2),(18,'normal',110,0)):
            g,event=pulse_game(delta)
            self.assertEqual((len(event.target_cells),event.hit_tick-event.start_tick),(100,120))
            self.assertEqual((g.resolver.last_parry_result.status,g.encounter.pulse.king.health.current_hp,g.combat.pending_attack_bonus),(status,hp,bonus))
            self.assertIsNone(g.resolver.resolve_enemy_attack(event))

    def test_original_queen_plan_drains_then_freezes_and_resumes(self):
        g=main._new_stage_game(25);p=g.encounter.pulse;seen_drain=False
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
        g=main._new_stage_game(25);p=g.encounter.pulse
        while p.event is None and g.playing:g.advance()
        q=g.encounter.enemies[1];q.health.apply_damage(q.health.current_hp,tick=g.combat.tick);g.encounter.deactivate(q.entity_instance_id,tick=g.combat.tick)
        k=p.king;k.health.apply_damage(k.health.current_hp,tick=g.combat.tick);g.encounter.deactivate(k.entity_instance_id,tick=g.combat.tick)
        g.advance();self.assertTrue(g.playing);self.assertIsNone(p.freeze_tick);self.assertFalse(q.active)
        self.assertEqual(g.encounter.ledger.state(p.event),'cancelled')

    def test_boss_clear_replay_no_offer_and_n_blocked(self):
        f=at25();g=f.game;r=f.run;finish(g,'clear');before=state(f);factory=Mock()
        self.assertIsNone(f.sync_offer());self.assertIsNone(g.next_stage_number)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=()):
            with self.assertRaises(ValueError):f.enter_next_chapter(factory)
        factory.assert_not_called()
        for fail in ('factory','input'):
            with self.assertRaises(RuntimeError):f.restart(Mock(side_effect=RuntimeError()) if fail=='factory' else main._new_stage_game,Mock(side_effect=RuntimeError()))
            self.assertEqual(state(f),before)
        new,_=f.restart(main._new_stage_game);self.assertIs(r,f.run);self.assertEqual(len(r.receipts),4)
        self.assertEqual((new.stage_number,new.encounter.pulse.king.health.current_hp,new.player.health.current_hp),(25,110,r.stats.max_hp))
        self.assertIsNot(g.encounter.pulse,new.encounter.pulse);self.assertNotEqual(g.combat.combat_session_id,new.combat.combat_session_id)

    def test_game_over_restores_entry_and_rejects_previous_pulse(self):
        f=at25();g=f.game;r=f.run
        while g.encounter.pulse.event is None and g.playing:g.advance()
        event=g.encounter.pulse.event;finish(g,'dead');before=state(f)
        with self.assertRaises(RuntimeError):f.restart(main._new_stage_game,Mock(side_effect=RuntimeError()))
        self.assertEqual(state(f),before);new,_=f.restart(main._new_stage_game)
        self.assertTrue(r.retired);self.assertEqual((new.stage_number,new.resolver.player_damage,new.player.health.current_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(21,r.entry_attack_level+1,3,18,0))
        with self.assertRaises(ValueError):new.resolver.resolve_enemy_attack(event)

    def test_annihilation_and_death_priority_and_tick_determinism(self):
        for dead in (False,True):
            g=main._new_stage_game(25)
            for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
            if dead:g.player.health.apply_damage(3,tick=0)
            g.update_state();self.assertEqual(g.state,GameState.GAME_OVER if dead else GameState.BOSS_CLEAR)
            g.advance(999);self.assertEqual((g.transition_count,g.combat.tick),(1,0))
        traces=[]
        for step in (1,8):
            g=main._new_stage_game(25)
            for _ in range(800//step):g.advance(step)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(*traces)

    def test_four_styles_actual_boss_clear(self):
        for style in STYLES:
            row=measure(style,25,limit=3600)
            self.assertEqual(row['hp'],[110,22,20,20,16,16,16,13])
            self.assertEqual((row['result'],row['ticks'],row['remaining_hp']),('BOSS_CLEAR',{'attack':638,'survival':1428,'evasion':807,'balanced':854}[style],{'attack':5,'survival':3,'evasion':2,'balanced':1}[style]))
            self.assertGreater(row['hits'],0)

    def test_queen_perfect_has_no_king_reflection(self):
        g=main._new_stage_game(25)
        for e in (g.encounter.enemies[0],*g.encounter.enemies[2:]):e.next_action_tick=1000
        g.advance(63);q=g.encounter.enemies[1];ev=q.current_attack
        g.advance(1);g.player.move('up',occupied=g.encounter.occupied_cells)
        g.advance(18);g.player.move('up',occupied=g.encounter.occupied_cells)
        self.assertIn(g.player.position,ev.target_cells)
        g.advance(ev.hit_tick-7-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(7)
        self.assertEqual(g.encounter.ledger.outcome(ev),'parried_perfect')
        self.assertEqual((g.encounter.enemies[0].health.current_hp,g.combat.pending_attack_bonus,q.stun_until_tick),(110,2,ev.hit_tick+60))

    def test_pulse_reflection_kills_king_and_resumes_others(self):
        g=main._new_stage_game(25);p=g.encounter.pulse
        while p.event is None and g.playing:g.advance()
        # Low-health fixture isolates the lethal reflection branch, not a clear measurement.
        p.king.health.apply_damage(p.king.health.current_hp-2,tick=g.combat.tick)
        ev=p.event;g.advance(ev.hit_tick-7-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(7)
        self.assertFalse(p.king.alive);self.assertTrue(g.playing)
        g.advance();self.assertIsNone(p.freeze_tick)

    def test_king_alone_pursues_melee_and_does_not_overlap(self):
        g=main._new_stage_game(25);k=g.encounter.pulse.king
        # Companion-death fixture for the King-only branch, not a balance clear.
        for e in g.encounter.enemies[1:]:
            e.health.apply_damage(e.health.current_hp,tick=0);g.encounter.deactivate(e.entity_instance_id,tick=0)
        old=k.position;seen=False
        for _ in range(1000):
            if k.current_attack and k.current_attack.attack_kind=='basic':
                ev=k.current_attack;self.assertEqual(ev.target_cells,(g.player.position,));seen=True;break
            if any(e.attack_kind=='king_pulse' and e.hit_tick-g.combat.tick==7 for e in g.encounter.ledger.pending):g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.advance();self.assertNotEqual(k.position,g.player.position)
            if not g.playing:break
        self.assertNotEqual(k.position,old);self.assertTrue(seen);self.assertTrue(g.playing)

    def test_final_screen_and_chapter6_guard(self):
        assert_final_boundary(self)

    def test_carryover_and_double_max_leave_move_legal(self):
        for kind,hp,max_hp,move in (('attack',2,4,15),('hp',3,5,15),('move',2,4,12)):
            f=at24(hp=1);r=f.run;old=f.game
            g,_=f.choose(clear(f),kind,main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((len(r.receipts),g.player.health.current_hp,g.player.health.max_hp,r.stats.move_interval_ticks),(4,hp,max_hp,move))
            self.assertIsNot(g.player.health,old.player.health)
        f=at24(level=15,choices=('hp','hp','hp'));o=clear(f);before=state(f)
        self.assertEqual([x.enabled for x in o.options],[False,False,True])
        for kind in ('attack','hp'):
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())
            self.assertEqual(state(f),before)
        f.choose(o,'move',main._new_stage_game);self.assertEqual(f.run.stats.move_interval_ticks,15)
        # All three caps require 3 HP + 2 MOVE choices even when entering at ATTACK MAX.
        # Only three choices precede Stage25, so an all-MAX fourth offer is unreachable.

    def test_final_fps_and_main_n_replay(self):
        from simulation_clock import SimulationClock
        traces=[]
        for fps in (30,60,120,144,160,180,240):
            g=main._new_stage_game(25);clock=SimulationClock()
            for _ in range(fps*6):g.advance(clock.advance(1/fps))
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies]))
        self.assertTrue(all(t==traces[0] for t in traces))
        from upgrades import ChapterBuild
        factory=main._new_stage_game
        games,*_=run_loop([[key(110)],[key(114)]],initial_stage=25,entry_attack_level=7,initial_factory=lambda:factory(25,stats=ChapterBuild(8,1,2).stats))
        self.assertEqual([g.stage_number for g in games],[25,25])

    def test_actual_chapter5_chain_final_and_low_hp_failure(self):
        from tests.test_hp_carryover import fight
        for style,entry,expected in (
            ('attack',15,[(432,2,3),(423,3,4),(435,4,5),(522,5,6),(638,4,6)]),
            ('balanced',8,[(651,2,3),(684,1,3),(687,2,4),(677,1,4),(136,0,4)])):
            r=ChapterRun(5,entry_attack_level=entry)
            f=StageProgression(main._new_stage_game(21,stats=r.stats),r)
            for i,(tick,hp,max_hp) in enumerate(expected):
                row=fight(f);status='UPGRADE' if i<4 else 'BOSS_CLEAR' if hp else 'GAME_OVER'
                self.assertEqual(row,(21+i,status,tick,hp,max_hp));self.assertEqual(len(r.receipts),i)
                if i<4:
                    choice=('move' if i==3 else 'hp') if style=='attack' else STYLES[style][i]
                    f.choose(f.sync_offer(),choice,main._new_stage_game)
                    self.assertEqual(f.game.player.health.current_hp,hp+(choice=='hp'))
