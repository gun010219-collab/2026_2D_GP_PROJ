"""Frame-rate independence and display-only motion contracts."""
from math import nan, inf
from unittest.mock import Mock
import unittest
import main
from config import cell_center, FIXED_TIME_STEP
from frame_timing import FramePacer, FrameStats
from render_motion import RenderMotion
from simulation_clock import SimulationClock
from player import Player
from player_renderer import PlayerRenderer
from enemy_renderer import EnemyRenderer
from health_renderer import HealthRenderer


class FrameTimingTests(unittest.TestCase):
    def test_independent_budget_subtracts_work_and_never_waits_when_late(self):
        p=FramePacer()
        self.assertAlmostEqual(p.remaining(.002),1/180-.002)
        self.assertEqual(p.remaining(.02),0)
        self.assertEqual(FIXED_TIME_STEP,1/60)

    def test_invalid_times_and_rates(self):
        for v in (-1,nan,inf,True):
            with self.assertRaises(ValueError):FramePacer().remaining(v)
            with self.assertRaises(ValueError):RenderMotion().update([],v,session='s')
            with self.assertRaises(ValueError):FrameStats().record(v)
        for v in (0,-1,nan,inf,True):
            with self.assertRaises(ValueError):FramePacer(v)
        s=FrameStats();s.record(1)
        with self.assertRaises(ValueError):s.record(.9)

    def test_stats_real_deltas_percentiles_and_bounded_memory(self):
        s=FrameStats(100);s.record(0)
        for i in range(1,101):s.record(i/180,1 if i%3==0 else 0)
        r=s.report();self.assertAlmostEqual(r['fps'],180);self.assertAlmostEqual(r['simulation_hz'],59.4)
        self.assertAlmostEqual(r['mean_ms'],1000/180);self.assertAlmostEqual(r['p99_ms'],1000/180)
        s.record(1);self.assertEqual(len(s.samples),100);self.assertGreater(s.report()['max_ms'],400)
        paused=FrameStats();paused.record(0);paused.record(1,0,False)
        self.assertEqual(paused.report()['simulation_hz'],0)

    def test_zero_one_multiple_steps_pause_and_long_stall(self):
        c=SimulationClock();self.assertEqual(c.advance(1/180),0)
        self.assertEqual(c.advance(2/180),1);self.assertEqual(c.advance(1/30),2)
        self.assertEqual(c.advance(99),8);self.assertEqual(c.advance(.1,paused=True),0)
        self.assertEqual(c.advance(1/180),0)

    def test_all_stages_same_combat_at_seven_render_rates(self):
        for stage in range(1,17):
            expected=None
            for fps in (30,60,120,144,160,180,240):
                g=main._new_stage_game(stage);clock=SimulationClock();motion=RenderMotion()
                for _ in range(fps*4):
                    g.advance(clock.advance(1/fps))
                    motion.update((g.player,*g.encounter.enemies),1/fps,session=g.combat.combat_session_id)
                trace=(g.combat.tick,g.state,g.player.position,g.player.health.current_hp,
                       [(e.position,e.state,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies],
                       [(r.event.start_tick,r.event.hit_tick,r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()])
                if expected is None:expected=trace
                else:self.assertEqual(trace,expected,(stage,fps))


class RenderMotionTests(unittest.TestCase):
    def setUp(self):
        self.p=Player(5,1);self.m=RenderMotion();self.update()

    def update(self,dt=0,**kw):self.m.update((self.p,),dt,session='s',**kw)
    def pos(self):return self.m.positions[self.p.entity_instance_id]

    def test_start_mid_end_and_no_entity_mutation(self):
        start=self.pos();self.p.move('right');self.update()
        self.assertEqual(self.pos(),start);self.update(.05)
        self.assertAlmostEqual(self.pos()[0],start[0]+42)
        self.assertEqual(self.p.position,(6,1));self.update(.05)
        self.assertEqual(self.pos(),cell_center(6,1))

    def test_blocked_move_and_facing_only_do_not_animate(self):
        self.assertFalse(self.p.move('up',occupied={(5,2)}));self.update(.01)
        self.assertEqual(self.pos(),cell_center(5,1));self.assertEqual(self.p.facing,'up')

    def test_rapid_retarget_is_continuous_and_settles_after_stall(self):
        self.p.move('right');self.update();self.update(.03);old=self.pos()
        self.p.move('left');self.update();self.assertEqual(self.pos(),old)
        self.update(2);self.assertEqual(self.pos(),cell_center(5,1))

    def test_modal_focus_display_and_catchup_snap(self):
        self.p.move('right');self.update();self.update(.02,snap=True)
        self.assertEqual(self.pos(),cell_center(6,1));self.update(0)
        self.assertEqual(self.pos(),cell_center(6,1))

    def test_session_and_death_remove_old_tracks(self):
        old=self.p.entity_instance_id;new=Player(2,2)
        self.m.update((new,),.01,session='new')
        self.assertNotIn(old,self.m.positions)
        new.health.apply_damage(3,tick=0);self.m.update((new,),.01,session='new')
        self.assertFalse(self.m.positions);self.assertFalse(self.m._tracks)

    def test_six_kinds_and_multi_cell_moves(self):
        for kind,hp in (('pawn',3),('rook',6),('knight',5),('bishop',5),('queen',14),('king',22)):
            # Factory supplies the supported explicit health API for all six types.
            g=main._new_stage_game(15 if kind in ('queen','king') else {'pawn':1,'rook':2,'knight':3,'bishop':4}[kind])
            e=next(e for e in g.encounter.enemies if e.kind==kind)
            m=RenderMotion();m.update((e,),0,session='s');origin=m.positions[e.entity_instance_id]
            e.col,e.row=5,5;m.update((e,),0,session='s');m.update((e,),.05,session='s')
            if kind=='bishop':self.assertEqual(m.positions[e.entity_instance_id],cell_center(5,5))
            elif kind=='knight':self.assertGreater(m.positions[e.entity_instance_id][1],(origin[1]+cell_center(5,5)[1])/2)
            m.update((e,),.1,session='s');self.assertEqual(m.positions[e.entity_instance_id],cell_center(5,5))

    def test_pulse_freeze_snaps_without_changing_queen_step(self):
        g=main._new_stage_game(15);q=g.encounter.enemies[1];m=RenderMotion()
        m.update((q,),0,session='s');q.col=5;m.update((q,),0,session='s')
        steps=g.encounter.queen_steps.copy();m.update((q,),.01,session='s',frozen=(q.entity_instance_id,))
        self.assertEqual(m.positions[q.entity_instance_id],cell_center(*q.position));self.assertEqual(steps,g.encounter.queen_steps)

    def test_repeated_render_and_labels_use_snapshot_without_combat_mutation(self):
        g=main._new_stage_game(15);m=RenderMotion();m.update((g.player,*g.encounter.enemies),0,session='s')
        before=(g.combat.tick,g.player.position,g.encounter.ledger.pending)
        for _ in range(3):
            for renderer,args in ((PlayerRenderer(),(g.player,)),(EnemyRenderer(),(g.encounter.enemies,)),(HealthRenderer(),(g.player,g.encounter.enemies,0))):
                renderer.positions=m.positions;renderer.draw(Mock(),*args)
        self.assertEqual(before,(g.combat.tick,g.player.position,g.encounter.ledger.pending))

    def test_real_main_high_fps_pending_inputs_pause_and_display(self):
        from tests.test_stage_transition import run_loop,key,UP,SPACE,SHIFT,F11
        # Use a live combat, no terminal fixture. Multiple render frames have zero ticks.
        batches=[[key(UP),key(UP,False)],[],[],[key(SPACE),key(SPACE,False)],[],[],[key(SHIFT),key(SHIFT,False)],[key(F11)],[],[]]
        games,*_=run_loop(batches,initial='playing',lengths=[1/180]*len(batches))
        self.assertTrue(games[0].playing)

    def test_rook_axis_tween_and_queen_diagonal_are_not_teleports(self):
        for kind,stage,delta in (('rook',2,(3,0)),('queen',15,(2,-2))):
            g=main._new_stage_game(stage);e=next(e for e in g.encounter.enemies if e.kind==kind)
            m=RenderMotion();m.update((e,),0,session='s');start=m.positions[e.entity_instance_id]
            e.col+=delta[0];e.row+=delta[1];target=cell_center(*e.position)
            m.update((e,),0,session='s');m.update((e,),.05,session='s')
            self.assertEqual(m.positions[e.entity_instance_id],tuple((a+b)/2 for a,b in zip(start,target)))
