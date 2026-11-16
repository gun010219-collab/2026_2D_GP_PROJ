"""Chapter4/5 finishing stays below the deck and preserves R6b elsewhere."""
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

from tools.front_crest_fine_review import (ROOT,ASSETS,OUTPUT,THEMES,TARGETS,CAMERA,
    FRONT_REGION,DECK_Y,FineRenderer,fine_layout,panel_layout)
from tests.test_aligned_board_review import rgba,sample


class FrontCrestFineTests(unittest.TestCase):
    def test_complete_panels_keep_uniform_scale_below_the_deck_and_above_canvas_bottom(self):
        records=json.loads((ASSETS/'asset_manifest.json').read_text())['assets']
        for record in records:
            if record['theme'] not in ('volcanic','gothic'):continue
            base=panel_layout(record,2);self.assertEqual(base['deck_clearance'],2)
            for choice,clearance in enumerate((6,4,9)):
                a=fine_layout(record,choice);l,b,r,t=a['opaque'];_,_,w,h=a['image']
                self.assertAlmostEqual(w/h,2);self.assertAlmostEqual(a['deck_clearance'],clearance)
                self.assertLess(t,DECK_Y);self.assertGreaterEqual(b,5)
                self.assertGreaterEqual(l,FRONT_REGION[0]);self.assertLessEqual(r,FRONT_REGION[2])
                self.assertAlmostEqual((r-l)/(base['opaque'][2]-base['opaque'][0]),a['gain'])
                self.assertAlmostEqual((t-b)/(base['opaque'][3]-base['opaque'][1]),a['gain'])

    def test_failed_board_draw_restores_selection_and_never_leaves_fine_mode_enabled(self):
        import tools.front_crest_fine_review as p
        for theme,comparison in ((3,False),(4,False),(2,False),(4,True)):
            r=FineRenderer.__new__(FineRenderer);r.theme=theme;r.variant=1;r.compare=comparison
            with patch.object(p.SideCleanupRenderer,'board',side_effect=RuntimeError('draw failed')):
                with self.assertRaisesRegex(RuntimeError,'draw failed'):r.board(CAMERA,False)
            self.assertEqual(r.variant,1);self.assertEqual(r.compare,comparison);self.assertFalse(r.use_fine)

    def test_underside_separator_is_outside_tiles_and_drawn_before_real_cues(self):
        import tools.front_crest_fine_review as p
        r=FineRenderer.__new__(FineRenderer);r.theme=4;r.fine_choice=2;r.use_fine=True
        r.c=Mock();r.images={'polish_gothic_light':Mock()};r.front_layout=dict(opaque=(565,10,905,124.5));r.separator_quads=[]
        order=[]
        with patch.object(p,'polygon',side_effect=lambda *a,**k:order.append('seam')), \
             patch.object(p.SideCleanupRenderer,'draw_cue',side_effect=lambda *a:order.append('cue')):
            r.draw_cue(CAMERA)
        self.assertEqual(order,['seam','seam','cue'])
        for quad in r.separator_quads:
            for x,y in quad:self.assertIsNone(CAMERA.pick(x,y));self.assertLess(y,DECK_Y)

    def test_fine_entry_rejects_asset_preparation_without_touching_existing_art(self):
        result=subprocess.run([sys.executable,'tools/side_cleanup_review.py','--fine','--prepare'],cwd=ROOT,
            capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,2);self.assertIn('--prepare is not needed',result.stderr)

    def test_native_fine_capture_preserves_chapters_one_to_three_tiles_warnings_and_r6b_compare(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            result=subprocess.run([sys.executable,'tools/side_cleanup_review.py','--fine','--capture-dir',folder],cwd=ROOT,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((out/'review_manifest.json').read_text())
            self.assertEqual(data,json.loads((OUTPUT/'review/review_manifest.json').read_text()))
            old=json.loads((ASSETS/'review/review_manifest.json').read_text())
            self.assertEqual(data['scenes'],old['scenes']);self.assertEqual(data['textures_loaded'],69)
            self.assertEqual(len(data['captures']),61);self.assertEqual(len(list(out.glob('*.png'))),71)
            for p in out.glob('*.png'):
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),reference_sha256(OUTPUT/'review'/p.name))
                self.assertTrue(rgba(p)[1])
            for path,digest in data['input_sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
            captures={r['file']:r for r in data['captures']}
            for record in data['captures']:
                scene=next(s for s in data['scenes'] if s['scenario']==record['scenario'])
                self.assertEqual(record['warning_cells'],[cell for e in scene['events'] if e['state']=='telegraph' for cell in e['cells']])
                self.assertEqual(record['tile_quads'],[[list(p) for p in CAMERA.tile(c,row)] for c in range(10) for row in range(10)])
                for quad in record['separator_quads']:
                    for x,y in quad:self.assertIsNone(CAMERA.pick(x,y))
            def equal_rows(a,b):
                for y in range(900):self.assertEqual(a[1][y*a[0]+280*4:(y+1)*a[0]],b[1][y*b[0]+280*4:(y+1)*b[0]])
            for t in THEMES[:3]:
                base=rgba(ASSETS/'review'/(t+'_c_normal.png'))
                for v in 'abc':equal_rows(base,rgba(out/(t+'_'+v+'_normal.png')))
            points=[CAMERA.project(c+u,r+v) for c in range(10) for r in range(10)
                for u in (.12,.5,.88) for v in (.12,.5,.88)]
            l,b,r,t=FRONT_REGION
            for theme in ('volcanic','gothic'):
                prior=rgba(out/('before_'+theme+'_normal.png'))
                equal_rows(prior,rgba(ASSETS/'review'/(theme+'_c_normal.png')))
                for record in data['captures']:
                    if record['theme']!=THEMES.index(theme) or record['compare']:continue
                    image=rgba(out/record['file']);base=rgba(out/('before_'+theme+'_'+record['scenario']+'.png'))
                    for point in points:self.assertEqual(sample(image,point),sample(base,point))
                    if record['mode']!=1:continue
                    for y in range(900):
                        spans=((280,l),(r,1440)) if 899-t<=y<899-b else ((280,1440),)
                        for x0,x1 in spans:
                            start=y*image[0];self.assertEqual(image[1][start+x0*4:start+x1*4],base[1][start+x0*4:start+x1*4])
                    before=captures['before_'+theme+'_'+record['scenario']+'.png']
                    for field in ('cue','warning_cells','cue_segments','tile_quads','rim_quads'):self.assertEqual(record[field],before[field])
                self.assertEqual(captures[theme+'_c_parry_perfect.png']['cue']['kind'],'perfect_success')
                self.assertEqual(captures[theme+'_c_parry_window.png']['cue']['kind'],'parry_window')
                self.assertEqual(captures[theme+'_c_pulse_resolved.png']['cue']['kind'],'ready')
                self.assertEqual(captures[theme+'_c_pulse_resolved.png']['warning_cells'],[])
                self.assertEqual(captures[theme+'_mode_0_pulse.png']['cue_segments'],[])
                self.assertTrue(captures[theme+'_mode_2_pulse.png']['cue_segments'])

    def test_fine_controls_keep_theme_repeat_comparison_settings_and_real_phase_selection(self):
        import tools.front_crest_fine_review as p
        from pico2d import pico2d as c
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_5),key(c.SDLK_2,True),key(c.SDLK_6),key(c.SDLK_q),key(c.SDLK_r)],
            [key(c.SDLK_b),key(c.SDLK_l)],[key(c.SDLK_9),key(c.SDLK_t),key(c.SDLK_F11)],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
            [key(c.SDLK_2),key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        with patch.object(p,'open_preview'),patch.object(p,'DisplaySettings') as display, \
             patch.object(p,'SettingsRenderer'),patch.object(p,'FineRenderer') as renderer, \
             patch.object(c,'window',object(),create=True),patch.object(c,'renderer',object(),create=True), \
             patch.object(c,'hide_lattice'),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(p,'sleep'):
            p.run(SimpleNamespace(capture_dir=None,assets=ASSETS))
            calls=renderer.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[0].name,'parry_window');self.assertEqual(calls[-1].args[0].name,'pulse_resolved')
            self.assertEqual(renderer.return_value.theme,4);self.assertEqual(renderer.return_value.variant,2)
            self.assertEqual(renderer.return_value.mode,1);self.assertFalse(renderer.return_value.compare)
            display.return_value.toggle.assert_called_once_with()
