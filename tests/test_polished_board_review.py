"""Uniform art fit, physical seat coverage and unchanged combat geometry."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from tests.art_review_fixtures import reference_sha256
from unittest.mock import Mock,patch

from tools.polished_board_review import ASSETS,CAMERA,THEMES,seat_bounds,seat_corners,blend_corners,uniform_fit,PolishedRenderer
from tools.stage5_art_preview import SCENARIOS


def rgba(path):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load
    a=IMG_Load(str(path).encode('utf-8'))
    if not a:raise FileNotFoundError(path)
    b=s.SDL_ConvertSurfaceFormat(a,s.SDL_PIXELFORMAT_RGBA32,0);s.SDL_FreeSurface(a)
    if not b:raise RuntimeError('RGBA conversion')
    try:return b.contents.pitch,ctypes.string_at(b.contents.pixels,b.contents.pitch*b.contents.h)
    finally:s.SDL_FreeSurface(b)


def sample(array,point):
    pitch,data=array;x,y=map(round,point);index=(899-y)*pitch+x*4
    return data[index:index+4]


def area(points):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1])))/2


class PolishedBoardTests(unittest.TestCase):
    def test_actual_assets_hashes_alpha_and_uniform_scale_without_axis_warp(self):
        records=json.loads((ASSETS/'asset_manifest.json').read_text())['assets']
        self.assertEqual({r['name'] for r in records},{t+'_'+k for t in THEMES for k in ('frame','light','dark')})
        for r in records:
            raw=(ASSETS/(r['name']+'.png')).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
            self.assertEqual(hashlib.sha256((ASSETS/'source'/r['source']).read_bytes()).hexdigest(),r['source_sha256'])
            self.assertEqual(list(struct.unpack('>II',raw[16:24])),r['size'])
            if r['name'].endswith('_frame'):
                self.assertGreater(r['transparent_pixels'],0)
                l,t,right,b=r['alpha_bounds']
                self.assertGreater(l,0);self.assertGreater(t,0);self.assertLess(right,1440);self.assertLess(b,900)
                # Same scalar for every source direction: circles/reliefs are
                # never independently squeezed to fit the front or side.
                scale=r['uniform_scale'];self.assertGreater(scale,0)
                w,h=r['source_size'];self.assertAlmostEqual((w*scale)/(h*scale),w/h)
            else:
                self.assertEqual(r['transparent_pixels'],0)
                self.assertEqual(hashlib.sha256((Path(__file__).resolve().parents[1]/r['base_source']).read_bytes()).hexdigest(),r['base_sha256'])
        scale,x,y=uniform_fit(1600,1000,(100,60,1500,950))
        self.assertGreaterEqual(x+100*scale,0);self.assertLessEqual(x+1500*scale,1440)
        self.assertGreaterEqual(y+60*scale,0);self.assertLessEqual(y+950*scale,900)

    def test_themed_pairs_keep_opaque_play_surface_and_clear_value_difference(self):
        means=[]
        for theme in THEMES:
            pair=[]
            for kind in ('light','dark'):
                pitch,data=rgba(ASSETS/(theme+'_'+kind+'.png'))
                self.assertEqual(pitch,128*4);self.assertEqual(set(data[3::4]),{255})
                pair.append(sum(.2126*data[i]+.7152*data[i+1]+.0722*data[i+2] for i in range(0,len(data),4))/(128*128))
            self.assertGreater(pair[0]-pair[1],60)
            self.assertGreater(pair[0],100);self.assertGreater(pair[1],25)
            means.append(tuple(round(v) for v in pair))
        self.assertEqual(len(set(means)),5)

    def test_measured_opening_is_inside_solid_seat_with_exact_inner_edges(self):
        records=json.loads((ASSETS/'asset_manifest.json').read_text())['assets']
        inner=((0,0),(10,0),(10,10),(0,10))
        for r in records:
            if not r['name'].endswith('_frame'):continue
            for pad in (.12,.20):
                bounds=seat_bounds(r['opening'],pad);outer=seat_corners(bounds)
                self.assertEqual(blend_corners(outer,1),inner)
                l,b,right,t=bounds
                for x,y in r['opening']:
                    u,v=CAMERA.inverse(x,899-y)
                    self.assertTrue(l<u<right and b<v<t)
                self.assertLess(l,0);self.assertLess(b,0);self.assertGreater(right,10);self.assertGreater(t,10)
                quads=[]
                for lo,hi in zip((0,.12,.82),(.12,.82,1)):
                    a,z=blend_corners(outer,lo),blend_corners(outer,hi)
                    quads.extend(tuple(CAMERA.project(*p) for p in (a[i],a[(i+1)%4],z[(i+1)%4],z[i])) for i in range(4))
                self.assertAlmostEqual(sum(area(q) for q in quads),area(tuple(CAMERA.project(*p) for p in outer))-area(CAMERA.corners),places=5)

    def test_missing_polish_assets_fail_and_close_instead_of_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            canvas=Mock()
            with self.assertRaises(FileNotFoundError):PolishedRenderer(canvas,Path(folder))
            self.assertEqual(canvas.load_image.call_count,35)

    def test_native_replay_joint_crops_actual_warning_geometry_and_pixel_contracts(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            result=subprocess.run([sys.executable,'tools/polished_board_review.py','--capture-dir',folder],cwd=root,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=90)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((out/'review_manifest.json').read_text())
            self.assertEqual(data,json.loads((ASSETS/'review/review_manifest.json').read_text()))
            old=json.loads((root/'assets/highend_board/review/review_manifest.json').read_text())
            self.assertEqual(data['scenes'],old['scenes']);self.assertEqual(data['textures_loaded'],50)
            self.assertEqual(len(data['captures']),55);self.assertEqual(len(list(out.glob('*.png'))),66)
            for p in out.glob('*.png'):
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),reference_sha256(ASSETS/'review'/p.name))
                pitch,pix=rgba(p);self.assertTrue(pitch>0 and pix)
            for r in data['captures']:
                scene=next(s for s in data['scenes'] if s['scenario']==r['scenario'])
                cells=[cell for e in scene['events'] if e['state']=='telegraph' for cell in e['cells']]
                self.assertEqual(r['warning_cells'],cells)
                if not r['compare']:
                    self.assertEqual(r['tile_quads'],[[list(p) for p in CAMERA.tile(c,row)] for c in range(10) for row in range(10)])
                for shape in r['cue_segments']+r['seat_quads']:
                    xs,ys=zip(*shape)
                    self.assertTrue(max(xs)<=0 or min(xs)>=10 or max(ys)<=0 or min(ys)>=10)
            points=[CAMERA.project(c+u,r+v) for c in range(10) for r in range(10)
                    for u in (.12,.5,.88) for v in (.12,.5,.88)]
            for theme in THEMES:
                a=rgba(out/(theme+'_a_normal.png'));original=rgba(root/'assets/highend_board/review'/(theme+'_r3_normal.png'))
                b=rgba(out/(theme+'_b_normal.png'));c=rgba(out/(theme+'_c_normal.png'))
                for p in points:
                    self.assertEqual(sample(a,p),sample(original,p))
                    self.assertEqual(sample(b,p),sample(c,p))
            for name in SCENARIOS:
                modes=[rgba(out/('royal_mode_'+str(m)+'_'+name+'.png')) for m in range(3)]
                for p in points:self.assertEqual(len({sample(a,p) for a in modes}),1)
            for theme in THEMES:
                a=rgba(out/('prior_R3_'+theme+'_normal.png'));b=rgba(root/'assets/highend_board/review'/(theme+'_r3_normal.png'))
                for row in range(900):self.assertEqual(a[1][row*a[0]+280*4:(row+1)*a[0]],b[1][row*b[0]+280*4:(row+1)*b[0]])

    def test_variant_mode_theme_repeat_settings_and_resolved_pulse_routing(self):
        import tools.polished_board_review as preview
        from pico2d import pico2d as c
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_2),key(c.SDLK_5,True),key(c.SDLK_6),key(c.SDLK_q),key(c.SDLK_r)],
            [key(c.SDLK_b),key(c.SDLK_l)],[key(c.SDLK_9),key(c.SDLK_t),key(c.SDLK_F11)],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
            [key(c.SDLK_5),key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer'),patch.object(preview,'PolishedRenderer') as renderer, \
             patch.object(c,'window',object(),create=True),patch.object(c,'renderer',object(),create=True), \
             patch.object(c,'hide_lattice'),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(preview,'sleep'):
            preview.run(SimpleNamespace(capture_dir=None,assets=ASSETS))
            calls=renderer.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[0].name,'parry_window');self.assertEqual(calls[-1].args[0].name,'pulse_resolved')
            self.assertEqual(renderer.return_value.theme,1);self.assertEqual(renderer.return_value.variant,2)
            self.assertEqual(renderer.return_value.mode,1);self.assertFalse(renderer.return_value.compare)
            display.return_value.toggle.assert_called_once_with()
