from math import hypot
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from actor_animation import ActorAnimation, Pose, State
from actor_mesh import draw_actor
from arena_art_common import enlarge_sprite
from chapter_art_renderer import CHAPTER_PROFILES
from main import _new_stage_game
from presentation_events import PresentationEvents


class AttackArticulationTests(unittest.TestCase):
    def test_actual_vertex_change_without_folds_across_chapters_and_directions(self):
        arrays = []
        def collect(renderer,texture,v,n,indices,count):
            points = [(v[i].position.x,v[i].position.y) for i in range(n)]
            for i in range(0,count,3):
                a,b,c = (points[indices[i+j]] for j in range(3))
                self.assertGreater((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]),0.)
            arrays.append(points)
            return 0
        with patch('sdl2.SDL_RenderGeometry',side_effect=collect):
            for chapter,profile in CHAPTER_PROFILES.items():
                for kind in profile.pieces:
                    layout = enlarge_sprite(profile.layout(kind,4,0),kind)
                    if kind=='player':
                        actions = (('swing',.19),)
                    elif kind in ('rook','knight'):
                        actions = (('anticipation',1.),('travel',0.),('arrival',0.))
                    else:
                        actions = (('anticipation',1.),('release',0.))
                    for side,depth in ((-1.,0.),(1.,0.),(0.,-1.),(0.,1.)):
                        for action,phase in actions:
                            args = dict(direction=side,depth_direction=depth,attack_motion=action)
                            for new in (False,True):
                                draw_actor(SimpleNamespace(renderer=None),None,kind,chapter,layout,
                                           Pose(State.ATTACK,phase,articulated=new,**args))
                            old,new = arrays[-2:]
                            self.assertGreater(max(hypot(x-u,y-v) for (x,y),(u,v) in zip(old,new)),2.)
                            ground = 899-layout['foot'][1]
                            self.assertEqual([p for p in old if p[1]>ground],[p for p in new if p[1]>ground])
                    if kind=='king':
                        draw_actor(SimpleNamespace(renderer=None),None,kind,chapter,layout,
                                   Pose(State.ATTACK,0.,direction=0.,attack_kind='king_pulse',
                                        attack_motion='release',articulated=True))

    def test_player_launch_is_same_receipt_and_wider_visual_recovery(self):
        game = _new_stage_game(1)
        events = game.encounter.ledger.presentation = PresentationEvents()
        old = ActorAnimation(improved=True,player_actions=True)
        new = ActorAnimation(improved=True,player_actions=True,articulated=True)
        attack = game.combat.request_attack(game.player)
        game.resolver.resolve_player_attack(attack)
        batch = events.drain()
        self.assertEqual([e.payload for e in batch if e.kind=='attack_start'],[attack])
        for animation in (old,new):
            animation.update(game,0,batch)
            self.assertEqual(animation.pose(game,game.player,None).state,State.ATTACK)
            for _ in range(15):
                animation.update(game,1/60,())
        self.assertIsNot(old.pose(game,game.player,None).state,State.ATTACK)
        self.assertTrue(new.pose(game,game.player,None).articulated)
        self.assertIs(game.combat.active_attack,attack)
