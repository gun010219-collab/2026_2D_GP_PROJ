"""Measured alignment shares the exact board boundary, combat stays unchanged."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from tests.art_review_fixtures import reference_sha256
from unittest.mock import Mock,patch
from math import hypot

from tools.aligned_board_review import ASSETS,ROOT,CAMERA,THEMES,AlignedRenderer,registered_point,survey_frame
from tools.arena_projection import ArenaCamera
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


def sample(a,p):
    x,y=map(round,p);i=(899-y)*a[0]+x*4
    return a[1][i:i+4]


class AlignedBoardTests(unittest.TestCase):
    def records(self):return json.loads((ASSETS/'asset_manifest.json').read_text())['assets']

    def test_surveyed_frame_edges_and_all_four_corners_register_to_the_board(self):
        for r in self.records():
            source=ArenaCamera('SOURCE',r['survey']['corners'],0,1)
            if r['name'].endswith('_a'):
                _,measured,_,_=survey_frame(ROOT/r['source'])
                self.assertEqual(json.loads(json.dumps(measured)),r['survey'])
            self.assertLessEqual(max(line['max_residual'] for line in r['survey']['lines']),2)
            self.assertEqual(r['target_opening'],[list(p) for p in CAMERA.corners])
            variant='abc'.index(r['name'][-1])
            for k in range(41):
                t=k/4
                for u,v in ((0,t),(10,t),(t,0),(t,10)):
                    point=registered_point(source,*source.project(u,v),variant,r['exterior_uniform_gain'])
                    expected=CAMERA.project(u,v)
                    self.assertLess(hypot(point[0]-expected[0],point[1]-expected[1]),1e-8)

    def test_fix_c_corners_use_uniform_scale_rotation_and_continuous_edge_join(self):
        for r in self.records():
            if not r['name'].endswith('_c'):continue
            source=ArenaCamera('SOURCE',r['survey']['corners'],0,1);gain=r['exterior_uniform_gain']
            for u,v in ((-.6,-.6),(10.6,-.6),(10.6,10.6),(-.6,10.6)):
                x,y=source.project(u,v)
                p=registered_point(source,x,y,2,gain)
                q=registered_point(source,x+3,y,2,gain)
                z=registered_point(source,x,y+4,2,gain)
                self.assertAlmostEqual(hypot(q[0]-p[0],q[1]-p[1]),3*gain)
                self.assertAlmostEqual(hypot(z[0]-p[0],z[1]-p[1]),4*gain)
                self.assertAlmostEqual((q[0]-p[0])*(z[0]-p[0])+(q[1]-p[1])*(z[1]-p[1]),0,places=7)
            for u in (-.5,10.5):
                for v in (0,10):
                    a=registered_point(source,*source.project(u,v-1e-6),2,gain)
                    b=registered_point(source,*source.project(u,v+1e-6),2,gain)
                    self.assertLess(hypot(a[0]-b[0],a[1]-b[1]),.001)

    def test_frame_hashes_alpha_margin_and_a_truly_open_play_area(self):
        records=self.records()
        self.assertEqual({r['name'] for r in records},{t+'_'+v for t in THEMES for v in 'abc'})
        for r in records:
            path=ASSETS/(r['name']+'.png')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),r['sha256'])
            self.assertEqual(hashlib.sha256((ROOT/r['source']).read_bytes()).hexdigest(),r['source_sha256'])
            l,t,right,b=r['alpha_bounds']
            self.assertTrue(0<l<right<1440 and 0<t<b<900)
            data=rgba(path)
            for c in range(10):
                for row in range(10):self.assertEqual(sample(data,CAMERA.center(c,row))[3],0)

    def test_missing_alignment_assets_fail_without_silent_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            canvas=Mock()
            with self.assertRaises(FileNotFoundError):AlignedRenderer(canvas,Path(folder))
            self.assertEqual(canvas.load_image.call_count,50)

    def test_native_fixes_modes_actual_state_warning_cells_and_r4_pixels(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            result=subprocess.run([sys.executable,'tools/aligned_board_review.py','--capture-dir',folder],cwd=ROOT,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=120)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((out/'review_manifest.json').read_text())
            self.assertEqual(data,json.loads((ASSETS/'review/review_manifest.json').read_text()))
            old=json.loads((ROOT/'assets/polished_board/review/review_manifest.json').read_text())
            self.assertEqual(data['scenes'],old['scenes']);self.assertEqual(data['textures_loaded'],65)
            self.assertEqual(len(data['captures']),55);self.assertEqual(len(list(out.glob('*.png'))),76)
            for p in out.glob('*.png'):
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),reference_sha256(ASSETS/'review'/p.name))
                self.assertTrue(rgba(p)[1])
            for r in data['captures']:
                scene=next(s for s in data['scenes'] if s['scenario']==r['scenario'])
                self.assertEqual(r['warning_cells'],[cell for e in scene['events'] if e['state']=='telegraph' for cell in e['cells']])
                if not r['compare']:
                    self.assertEqual(r['tile_quads'],[[list(p) for p in CAMERA.tile(c,row)] for c in range(10) for row in range(10)])
                    for quad in r['rim_quads']:
                        xs,ys=zip(*quad)
                        self.assertTrue(max(xs)<=0 or min(xs)>=10 or max(ys)<=0 or min(ys)>=10)
            points=[CAMERA.project(c+u,r+v) for c in range(10) for r in range(10)
                    for u in (.12,.5,.88) for v in (.12,.5,.88)]
            for theme in THEMES:
                old=rgba(ROOT/'assets/polished_board/review'/(theme+'_c_normal.png'))
                fixes=[rgba(out/(theme+'_'+v+'_normal.png')) for v in 'abc']
                for p in points:self.assertTrue(all(sample(f,p)==sample(old,p) for f in fixes))
                before=rgba(out/('prior_R4_'+theme+'_normal.png'))
                for y in range(900):self.assertEqual(before[1][y*before[0]+280*4:(y+1)*before[0]],old[1][y*old[0]+280*4:(y+1)*old[0]])
            for name in SCENARIOS:
                modes=[rgba(out/('royal_mode_'+str(m)+'_'+name+'.png')) for m in range(3)]
                old=rgba(ROOT/'assets/polished_board/review'/('royal_mode_1_'+name+'.png'))
                for p in points:self.assertTrue(all(sample(m,p)==sample(old,p) for m in modes))

    def test_review_input_repeat_comparison_modes_settings_and_resolution(self):
        import tools.aligned_board_review as preview
        from pico2d import pico2d as c
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_2),key(c.SDLK_5,True),key(c.SDLK_6),key(c.SDLK_q),key(c.SDLK_r)],
            [key(c.SDLK_b),key(c.SDLK_l)],[key(c.SDLK_9),key(c.SDLK_t),key(c.SDLK_F11)],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
            [key(c.SDLK_5),key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer'),patch.object(preview,'AlignedRenderer') as renderer, \
             patch.object(c,'window',object(),create=True),patch.object(c,'renderer',object(),create=True), \
             patch.object(c,'hide_lattice'),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(preview,'sleep'):
            preview.run(SimpleNamespace(capture_dir=None,assets=ASSETS))
            calls=renderer.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[0].name,'parry_window');self.assertEqual(calls[-1].args[0].name,'pulse_resolved')
            self.assertEqual(renderer.return_value.theme,1);self.assertEqual(renderer.return_value.variant,2)
            self.assertEqual(renderer.return_value.mode,1);self.assertFalse(renderer.return_value.compare)
            display.return_value.toggle.assert_called_once_with()
