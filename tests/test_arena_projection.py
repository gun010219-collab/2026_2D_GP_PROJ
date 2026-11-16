"""Display math and native camera review; combat remains on the original grid."""
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.arena_projection import CAMERAS
from display_settings import logical_mouse_to_canvas


def area(points):
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1])))/2


class ArenaProjectionTests(unittest.TestCase):
    def test_all_300_centers_round_trip_and_unique(self):
        for cam in CAMERAS:
            centers=[]
            for col in range(10):
                for row in range(10):
                    p=cam.center(col,row);centers.append(p)
                    self.assertEqual(cam.pick(*p),(col,row))
                    u,v=cam.inverse(*p)
                    self.assertAlmostEqual(u,col+.5);self.assertAlmostEqual(v,row+.5)
            self.assertEqual(len(set(centers)),100)

    def test_shared_edges_convex_tiles_and_area_no_gaps_or_overlap(self):
        for cam in CAMERAS:
            total=0
            for c in range(10):
                for r in range(10):
                    p=cam.tile(c,r);total+=area(p)
                    self.assertGreater(area(p),1000)
                    for i in range(4):
                        a,b,d=p[i],p[(i+1)%4],p[(i+2)%4]
                        self.assertGreater((b[0]-a[0])*(d[1]-b[1])-(b[1]-a[1])*(d[0]-b[0]),0)
                    if c<9:
                        q=cam.tile(c+1,r);self.assertEqual((p[1],p[2]),(q[0],q[3]))
                    if r<9:
                        q=cam.tile(c,r+1);self.assertEqual((p[3],p[2]),(q[0],q[1]))
            self.assertAlmostEqual(total,area(cam.corners),places=6)

    def test_boundaries_half_open_and_outside_rejected(self):
        for cam in CAMERAS:
            self.assertEqual(cam.pick(*cam.project(0,0)),(0,0))
            for k in range(10):
                self.assertIsNone(cam.pick(*cam.project(10,k+.5)))
                self.assertIsNone(cam.pick(*cam.project(k+.5,10)))
                self.assertIsNone(cam.pick(*cam.project(-.01,k+.5)))
                self.assertIsNone(cam.pick(*cam.project(k+.5,-.01)))
            for c in range(1,10):
                for r in range(1,10):self.assertEqual(cam.pick(*cam.project(c,r)),(c,r))

    def test_finite_validity_and_fractional_render_interpolation(self):
        for cam in CAMERAS:
            for bad in (float('nan'),float('inf')):
                self.assertIsNone(cam.pick(bad,5))
                with self.assertRaises(ValueError):cam.project(0,bad)
            for pos in ((-1,0),(10,0),(0,False),(.5,2)):
                with self.assertRaises(ValueError):cam.tile(*pos)
            for t in (0,.125,.5,.875,1):
                p=cam.project(3.5+t,4.5)
                self.assertAlmostEqual(cam.inverse(*p)[0],3.5+t)

    def test_board_bounds_and_existing_logical_mouse_conversion(self):
        for cam in CAMERAS:
            for c in range(10):
                for r in range(10):
                    for x,y in cam.tile(c,r):
                        self.assertGreaterEqual(x,300);self.assertLessEqual(x,1180)
                        self.assertGreaterEqual(y,30);self.assertLessEqual(y,870)
                    x,y=cam.center(c,r)
                    point=logical_mouse_to_canvas(x,899-y)
                    self.assertEqual(cam.pick(*point),(c,r))
        self.assertIsNone(logical_mouse_to_canvas(-1,450))
        self.assertIsNone(logical_mouse_to_canvas(1440,450))
        # Native textured vertices and Pico2D warning lines must use the same
        # bottom-left -> SDL pixel conversion, including the last pixel.
        from tools.stage5_camera_review import polygon
        with patch('sdl2.SDL_RenderGeometry',return_value=0) as render:
            polygon(SimpleNamespace(renderer=object()),CAMERAS[0].tile(0,0))
            self.assertEqual(render.call_args.args[2][0].position.y,869)

    def test_native_two_captures_are_identical_and_warning_cells_authentic(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as first,tempfile.TemporaryDirectory() as second:
            for folder in (first,second):
                run=subprocess.run([sys.executable,'tools/stage5_camera_review.py','--capture-dir',folder],cwd=root,
                    env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=40)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            a=Path(first);b=Path(second)
            self.assertEqual({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.iterdir()},
                             {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in b.iterdir()})
            data=json.loads((a/'camera_manifest.json').read_text())
            old=json.loads((root/'assets/art_samples/stage5_r2/review/capture_manifest.json').read_text())
            self.assertEqual(data['scenes'],old['frozen_snapshots'])
            self.assertEqual(data['textures_loaded'],10)
            self.assertEqual(len(list(a.glob('*.png'))),21)
            for capture in data['captures']:
                name=capture['file'];raw=(a/name).read_bytes()
                self.assertEqual(struct.unpack('>II',raw[16:24]),(1440,900))
                scene=next(s for s in data['scenes'] if name[2:-4]==s['scenario'])
                cells=[tuple(cell) for e in scene['events'] if e['state']=='telegraph' for cell in e['cells']]
                self.assertEqual(capture['warning_cells'],[list(p) for p in cells])
                for record in capture['bounds']:
                    l,bottom,r,top=record['box']
                    self.assertGreaterEqual(l,0);self.assertLess(r,1440)
                    self.assertGreaterEqual(bottom,0);self.assertLess(top+20,900)

    def test_camera_scene_settings_fullscreen_probe_and_repeat_input_routing(self):
        from pico2d import pico2d as c
        import tools.stage5_camera_review as preview
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_1),key(c.SDLK_3,True),key(c.SDLK_9),key(c.SDLK_g)],
            [key(c.SDLK_2),key(c.SDLK_F11)],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
            [key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        args=SimpleNamespace(capture_dir=None)
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer'),patch.object(preview,'CameraRenderer') as draw, \
             patch.object(c,'hide_lattice'),patch.object(c,'window',object(),create=True), \
             patch.object(c,'renderer',object(),create=True),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(preview,'sleep'):
            preview.run(args)
            calls=draw.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[1],CAMERAS[0])
            self.assertEqual(calls[0].args[0].name,'pulse')
            self.assertTrue(calls[0].kwargs['grid'])
            self.assertEqual(calls[-1].args[1],CAMERAS[1])
            display.return_value.toggle.assert_called_once_with()
