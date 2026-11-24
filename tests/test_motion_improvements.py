from dataclasses import fields
from math import dist
from types import SimpleNamespace as Event
import unittest

from actor_animation import ActorAnimation, State
from arena_art_common import PIECE_INCREASE,enlarge_sprite
from chapter_art_renderer import CHAPTER_PROFILES
from config import cell_center
from main import _new_stage_game
from player import Player
from render_motion import RenderMotion
from sdl_input import GameplayInput
from tests import test_main


class MotionImprovementTests(unittest.TestCase):
    def test_size_anchor_and_full_board_bounds_in_all_profiles(self):
        for p in CHAPTER_PROFILES.values():
            for kind in p.pieces:
                for row in (0,9):
                    for col in range(10):
                        base=p.layout(kind,col,row)
                        new=enlarge_sprite(base,kind)
                        self.assertEqual(base['foot'],new['foot'])
                        self.assertAlmostEqual(new['height'],base['height']*PIECE_INCREASE.get(kind,1.))
                        self.assertAlmostEqual(new['hp_y']-new['top'],base['hp_y']-base['top'])
                        self.assertLess(new['hp_y']+13,900)
                        x,y=new['center']
                        self.assertGreater(x-new['height']/2,0)
                        self.assertLess(x+new['height']/2,1440)

    def test_move_response_stop_and_turn_remain_logical(self):
        a=Player(5,1)
        m=RenderMotion(improved=True)
        step=lambda dt,**options:m.update((a,),dt,session='abc',**options)
        step(0)
        old=m.ground_pose(a)[0]
        self.assertTrue(a.move('right'))
        step(0)
        self.assertGreater(m.ground_pose(a)[0][0],old[0])
        step(.04)
        before=m.ground_pose(a)[0]
        self.assertTrue(a.move('up'))
        step(0)
        after=m.ground_pose(a)[0]
        self.assertLess(dist(before,after),6)
        step(.09)
        self.assertEqual(m.ground_pose(a)[0],cell_center(6,2))
        self.assertTrue(a.move('left'))
        step(0,frozen=(a.entity_instance_id,))
        self.assertLessEqual(dist(m.ground_pose(a)[0],cell_center(*a.position)),8)
        step(.04,frozen=(a.entity_instance_id,))
        self.assertEqual(m.ground_pose(a)[0],cell_center(*a.position))

    def test_clock_and_blend_at_common_times(self):
        states=[]
        for fps in (60,144,180):
            g=_new_stage_game(1)
            a=g.player
            m=RenderMotion(improved=True)
            anim=ActorAnimation(improved=True)
            def update(dt):
                m.update((a,),dt,session=g.combat.combat_session_id)
                anim.update(g,dt,(),motion=m)
                return anim.mesh_pose(g,a,m)
            update(0)
            self.assertTrue(a.move('right'))
            self.assertIs(update(0)[0].state,State.MOVE)
            samples=[]
            for i in range(1,fps//6+1):
                pose,effect=update(1/fps)
                if i%(fps//12)==0:
                    samples.append((pose.state,m.ground_pose(a)[0],
                                    tuple(round(getattr(effect,f.name),8) for f in fields(effect))))
            states.append(samples)
        for value in states[1:]:
            self.assertEqual(states[0],value)

    def test_knight_18px_split_and_arrival_match_r6(self):
        g=_new_stage_game(3)
        knight=next(e for e in g.encounter.enemies if e.kind=='knight')
        old=RenderMotion()
        new=RenderMotion(improved=True)
        peak=0.
        for _ in range(105):
            g.advance()
            for m in (old,new):
                m.update((knight,),1/60,session='hop')
            self.assertEqual(old.ground_pose(knight),new.ground_pose(knight))
            peak=max(peak,new.ground_pose(knight)[1])
        self.assertAlmostEqual(peak,18)

    def test_actual_attack_blends_with_immediate_release_and_scope_reset(self):
        from actor_mesh import deformation
        from presentation_events import PresentationEvents

        g=_new_stage_game(1)
        a=g.player
        events=g.encounter.ledger.presentation=PresentationEvents()
        anim=ActorAnimation(improved=True)
        anim.update(g,0,())
        g.resolver.resolve_player_attack(g.combat.request_attack(a))
        anim.update(g,0,events.drain())
        pose,effect=anim.mesh_pose(g,a,None)
        self.assertIs(pose.state,State.ATTACK)
        self.assertGreater(effect.gear,deformation('player',1,pose).gear*.70)
        anim.update(g,.12,(),paused=True)
        self.assertEqual(anim.mesh_pose(g,a,None),(pose,effect))
        fresh=_new_stage_game(1)
        anim.update(fresh,0,(),reset=True)
        self.assertIs(anim.mesh_pose(fresh,fresh.player,None)[0].state,State.IDLE)

    def test_only_left_modifiers_trigger_combat(self):
        c=test_main.WindowLoopTests().make_canvas()
        g=_new_stage_game(1)
        controls=GameplayInput(c)
        for key in (32,1073742049,1073742053,1073742052,1073742054):
            self.assertFalse(controls.handle_key(Event(type=768,key=key),g.player,g.combat,parry=g.parry))
        for key in (c.SDLK_LCTRL,c.SDLK_LALT):
            for _ in range(2):
                self.assertTrue(controls.handle_key(Event(type=768,key=key),g.player,g.combat,parry=g.parry))
        self.assertEqual(g.parry.last_attempt.parry_id,1)
        self.assertEqual(g.combat.active_attack.attack_id,1)
