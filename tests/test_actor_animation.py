import unittest
from types import SimpleNamespace
from unittest.mock import patch
from actor_animation import ActorAnimation, Pose, State
from actor_mesh import deformation, weighted_vertices
from chapter_run import ChapterRun
from main import _new_stage_game
from render_motion import RenderMotion
from stage_progression import StageProgression


class ActorAnimationTests(unittest.TestCase):
    def setUp(self):
        self.game = _new_stage_game(1)
        self.anim = ActorAnimation()
        self.anim.update(self.game, 0, ())

    def test_distinct_idle_regions_and_chapter_material_response(self):
        idle = Pose(State.IDLE, .82)
        shapes = [deformation(kind, 1, idle)
                  for kind in ('player','pawn','rook','knight','bishop','queen','king')]
        self.assertEqual(len(set(shapes)), 7)
        self.assertEqual(len({deformation('queen', ch, idle) for ch in range(1,6)}), 5)
        vertices = weighted_vertices('knight', 5, 236/256)
        self.assertEqual(sum(v == 236/256 for _,v,*_ in vertices), 6)
        self.assertNotEqual(weighted_vertices('knight', 1, 236/256), vertices)

    def test_independent_units_and_continuous_clock_pause_and_large_gap(self):
        game, anim = self.game, self.anim
        a,b = game.encounter.enemies
        self.assertNotEqual(anim.pose(game,a,None),anim.pose(game,b,None))
        for fps in (60, 144, 180):
            other = ActorAnimation()
            other.update(game,0,())
            for _ in range(fps):
                other.update(game,1/fps,())
            self.assertAlmostEqual(other.time,1.)
            other.update(game, .1, (), paused=True)
            other.update(game, 6, ())
            self.assertAlmostEqual(other.time,1.)
            self.assertEqual(other.pose(game,a,None).state,State.IDLE)

    def test_real_missed_attack_duplicates_and_old_scope(self):
        g,a = self.game,self.anim
        queue = StageProgression(g).enable_presentation()
        attack = g.combat.request_attack(g.player)
        self.assertIsNone(g.resolver.resolve_player_attack(attack))
        batch = queue.drain()
        self.assertEqual([e.kind for e in batch], ['attack_start'])
        a.update(g,0,batch)
        self.assertEqual(a.pose(g,g.player,None).state,State.ATTACK)
        a.update(g,.1,batch)
        self.assertGreater(a.pose(g,g.player,None).phase,.4)
        a.update(g,.14,batch)
        self.assertEqual(a.pose(g,g.player,None).state,State.IDLE)
        fresh = _new_stage_game(1)
        a.update(fresh,0,batch)
        self.assertEqual(a.pose(fresh,fresh.player,None).state,State.IDLE)
        self.assertEqual(a.time,0)

    def test_damage_death_and_catch_up_batch_resolve_once(self):
        run = ChapterRun(1, entry_attack_level=3)
        g,a = _new_stage_game(1, stats=run.stats),self.anim
        queue = StageProgression(g, run).enable_presentation()
        a.update(g, 0, ())
        enemy=g.encounter.enemies[0]
        for direction in ('left',)*4 + ('up',)*4:
            self.assertTrue(g.player.move(direction, occupied=g.encounter.occupied_cells))
        strike=g.combat.request_attack(g.player)
        g.resolver.resolve_player_attack(strike)
        self.assertFalse(enemy.alive)
        g.advance(5)
        batch=queue.drain()
        self.assertEqual([e.kind for e in batch[:4]],['attack_start','hit','hurt','death'])
        a.update(g, .08, batch)
        (sprite,)=a.deaths
        self.assertEqual(sprite.position,enemy.position)
        pose=a.pose(g,sprite,None)
        self.assertEqual(pose.state,State.DEATH)
        self.assertGreater(pose.phase,0)
        for _ in range(5):
            a.update(g,.13,batch)
        self.assertEqual(list(a.deaths),[])
        self.assertFalse(enemy.alive)

    def test_ground_motion_and_stun_use_live_state(self):
        g = _new_stage_game(3)
        motion=RenderMotion()
        motion.update((g.player,*g.encounter.enemies),0,session=g.combat.combat_session_id)
        g.player.move('up', occupied=g.encounter.occupied_cells)
        motion.update((g.player,*g.encounter.enemies),1/60,session=g.combat.combat_session_id)
        self.anim.update(g,0,())
        self.assertEqual(self.anim.pose(g,g.player,motion).state,State.MOVE)
        knight=g.encounter.enemies[0]
        knight.stun_until_tick=30
        self.assertIs(self.anim.pose(g,knight,motion).state,State.STUN)

    def test_native_sequence_qa(self):
        # Native software SDL runs in a fresh process so desktop SDL flags do not leak.
        import subprocess
        import sys
        from pathlib import Path

        result=subprocess.run([sys.executable,'-m','tools.animation_qa'],
                              cwd=Path(__file__).resolve().parents[1],
                              capture_output=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))

    def test_main_drains_one_batch_per_frame_and_blocks_modal_time(self):
        import os
        import sys
        import main
        from presentation_events import PresentationEvents
        from tests.test_main import WindowLoopTests

        g = self.game
        flow = StageProgression(g)
        c = WindowLoopTests().make_canvas()
        c.get_events.side_effect = [
            [SimpleNamespace(type=768, key=32)], [],
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [], [SimpleNamespace(type=768, key=27)], [], [SimpleNamespace(type=256)],
        ]
        now = [0.]
        c.update_canvas.side_effect = lambda: now.__setitem__(0, now[0] + .05)
        batches, animation_times = [], []
        drain, update = PresentationEvents.drain, ActorAnimation.update

        def drain_once(queue):
            result = drain(queue)
            batches.append(result)
            return result

        def update_once(animation, game, dt, batch, **options):
            self.assertIs(batch, batches[-1])
            update(animation, game, dt, batch, **options)
            animation_times.append(animation.time)

        with patch.dict(os.environ, CHECKMATE_STAGE1_ART='0', CHECKMATE_ANIMATION='1'), \
             patch.dict(sys.modules, {'pico2d':SimpleNamespace(pico2d=c)}), \
             patch.object(main,'DisplaySettings'), patch.object(main,'SettingsRenderer'), \
             patch.object(main,'perf_counter',side_effect=lambda:now[0]), patch.object(main,'sleep'), \
             patch.object(PresentationEvents,'drain',drain_once), patch.object(ActorAnimation,'update',update_once):
            main.run_session(g,flow,default_art=True)
        self.assertEqual(len(batches), c.update_canvas.call_count)
        self.assertEqual(sum(e.kind=='attack_start' for batch in batches for e in batch),1)
        self.assertEqual(animation_times[1:5], [animation_times[1]]*4)
        self.assertGreater(animation_times[5],animation_times[4])
