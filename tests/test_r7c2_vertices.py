import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from actor_animation import Pose, State
from actor_mesh import draw_actor
from chapter_art_renderer import CHAPTER_PROFILES
from combat_vfx_renderer import Mesh


class PackedVertexTests(unittest.TestCase):
    def test_king_mesh_matches_original_native_positions_uv_color_and_alpha(self):
        layout = CHAPTER_PROFILES[5].layout('king',4,4)
        digests = []
        def capture(renderer,texture,vertices,count,indices,n):
            digests.append(hashlib.sha256(bytes(vertices)).hexdigest())
            return 0
        with patch('sdl2.SDL_RenderGeometry',capture):
            for state,phase in ((State.IDLE,.31),(State.HIT,.17),(State.DEATH,.52)):
                draw_actor(SimpleNamespace(renderer=None),None,'king',5,layout,Pose(state,phase))
        self.assertEqual(digests,[
            '3c79e36f543f038692dc83108b2d23a78b583e3796b19210670d220141cf8ce2',
            'a5997e91b266c87062a56e608ed363592526021a7dc143f5b04b6af54514c9fc',
            '145727713d21614f98d8c075ad399967a57f17d6471dd670ea456244cc25e954',
        ])

    def test_triangle_batch_flush_retains_float_positions_rgba_and_order(self):
        import sdl2 as s
        mesh = Mesh()
        mesh.vertices = (s.SDL_Vertex*3)()
        captured = []
        def capture(renderer,texture,vertices,count,indices,n):
            captured.append([(v.position.x,v.position.y,bytes(v.color)) for v in vertices])
            return 0
        points = ((1.25,7.5),(19.,-2.),(-3.,898.25))
        colors = ((4,189,22,0),(253,7,109,200))
        with patch('sdl2.SDL_RenderGeometry',capture):
            for color in colors:
                mesh.tri(*points,color)
            mesh.flush()
        self.assertEqual(captured,[[(x,899-y,bytes(color)) for x,y in points] for color in colors])
