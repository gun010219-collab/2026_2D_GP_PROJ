"""High-end art remains exterior to the authentic, unchanged 100-cell combat."""
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

from tools.highend_board_review import ASSETS,CAMERA,OPENING,HighendRenderer,project_art,resolved_pulse_scene
from tools.arena_projection import ArenaCamera
from tools.themed_arena_review import THEMES,SIZE_CAMERAS
from tools.ornate_board_review import cue_for
from tools.stage5_art_preview import SCENARIOS


def pixels(path):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load
    image=IMG_Load(str(path).encode('utf-8'))
    if not image:raise RuntimeError(str(path))
    rgba=s.SDL_ConvertSurfaceFormat(image,s.SDL_PIXELFORMAT_RGBA32,0);s.SDL_FreeSurface(image)
    if not rgba:raise RuntimeError('RGBA conversion')
    try:return rgba.contents.pitch,ctypes.string_at(rgba.contents.pixels,rgba.contents.pitch*rgba.contents.h)
    finally:s.SDL_FreeSurface(rgba)


class HighendBoardTests(unittest.TestCase):
    def test_calibrated_opening_preserves_b12_and_all_100_cells(self):
        self.assertIs(CAMERA,SIZE_CAMERAS[2])
        source=ArenaCamera('SOURCE',tuple((x,1-y) for x,y in OPENING),0,1)
        for c in range(10):
            for r in range(10):
                for u,v in ((c,r),(c+.5,r+.5),(c+1,r+1)):
                    sx,sy=source.project(u,v);point=project_art(sx,1-sy)
                    expected=CAMERA.project(u,v)
                    self.assertAlmostEqual(point[0],expected[0]);self.assertAlmostEqual(point[1],expected[1])
                self.assertEqual(CAMERA.pick(*CAMERA.center(c,r)),(c,r))

    def test_fifteen_distinct_actual_shells_have_alpha_margin_and_matching_hashes(self):
        records=json.loads((ASSETS/'asset_manifest.json').read_text())['assets']
        self.assertEqual({r['name'] for r in records},{f'{t}_r{v}' for t in THEMES for v in range(1,4)})
        self.assertEqual(len({r['sha256'] for r in records}),15)
        for r in records:
            raw=(ASSETS/(r['name']+'.png')).read_bytes()
            self.assertEqual(struct.unpack('>II',raw[16:24]),(1440,900))
            self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
            self.assertEqual(hashlib.sha256((ASSETS/'source'/(r['name']+'.png')).read_bytes()).hexdigest(),r['source_sha256'])
            self.assertGreater(r['source_transparent_pixels'],0)
            self.assertGreater(r['transparent_pixels'],300000)
            left,top,right,bottom=r['alpha_bounds']
            self.assertGreater(left,0);self.assertGreater(top,0);self.assertLess(right,1440);self.assertLess(bottom,900)

    def test_actual_resolved_pulse_is_not_reported_as_a_live_warning(self):
        scene=resolved_pulse_scene();g=scene.game
        record=next(r for r in g.encounter.ledger._records.values() if r.event.attack_kind=='king_pulse')
        self.assertEqual(record.state,'resolved');self.assertEqual(g.encounter.pulse.state,'CLEANUP')
        self.assertNotEqual(cue_for(scene).kind,'pulse')

    def test_missing_shell_fails_after_cleaning_the_existing_resources(self):
        with tempfile.TemporaryDirectory() as folder:
            canvas=Mock()
            with self.assertRaises(FileNotFoundError):HighendRenderer(canvas,Path(folder))
            self.assertEqual(canvas.load_image.call_count,20)

    def test_native_replay_all_variants_unchanged_state_cells_and_central_pixels(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)
            run=subprocess.run([sys.executable,'tools/highend_board_review.py','--capture-dir',folder],cwd=root,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=90)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            data=json.loads((output/'review_manifest.json').read_text())
            old=json.loads((root/'assets/ornate_board/review/review_manifest.json').read_text())
            self.assertEqual(data,json.loads((ASSETS/'review/review_manifest.json').read_text()))
            self.assertEqual(data['scenes'][:10],old['scenes'])
            self.assertEqual(data['textures_loaded'],35);self.assertEqual(len(data['captures']),51)
            self.assertEqual(data['camera'],[list(p) for p in CAMERA.corners])
            sheet=(output/data['contact_sheet']).read_bytes()
            self.assertEqual(struct.unpack('>II',sheet[16:24]),(1440,1500))
            self.assertEqual(hashlib.sha256(sheet).hexdigest(),reference_sha256(ASSETS/'review'/data['contact_sheet']))
            for r in data['captures']:
                raw=(output/r['file']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),reference_sha256(ASSETS/'review'/r['file']))
                pitch,image=pixels(output/r['file'])
                self.assertEqual((pitch,len(image)),(1440*4,1440*900*4))
                for shape in r['cue_segments']+r['decor_quads']:
                    xs,ys=zip(*shape)
                    self.assertTrue(max(xs)<=0 or min(xs)>=10 or max(ys)<=0 or min(ys)>=10)
                    for p in shape:
                        x,y=CAMERA.project(*p);self.assertTrue(0<x<1440 and 0<y<900)
                if r['mode']==0:self.assertEqual(r['cue_segments'],[])
                if r['cue']['kind']=='pulse':self.assertEqual(len(r['warning_cells']),100)
            points=[CAMERA.project(c+u,r+v) for c in range(10) for r in range(10)
                    for u in (.12,.5,.88) for v in (.12,.5,.88)]
            for name in SCENARIOS:
                reference=root/'assets/ornate_board/review'/('royal_mode_1_'+name+'.png')
                arrays=[pixels(reference)]+[pixels(output/('royal_mode_'+str(m)+'_'+name+'.png')) for m in range(3)]
                for x,y in points:
                    samples=[raw[(899-round(y))*pitch+round(x)*4:(899-round(y))*pitch+round(x)*4+4] for pitch,raw in arrays]
                    self.assertTrue(all(s==samples[0] for s in samples),f'{name} at {x},{y}')
            # B comparison must be the actual R2 board, not the older Q board.
            for name in ('normal','pulse'):
                a=pixels(output/('prior_R2_'+name+'.png'))
                b=pixels(root/'assets/ornate_board/review'/('royal_recommended_'+name+'.png'))
                for y in range(900):self.assertEqual(a[1][y*a[0]+280*4:(y+1)*a[0]],b[1][y*b[0]+280*4:(y+1)*b[0]])

    def test_review_only_input_repeat_modes_comparison_settings_and_resolution(self):
        import tools.highend_board_review as preview
        from pico2d import pico2d as c
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_2),key(c.SDLK_5,True),key(c.SDLK_6),key(c.SDLK_q),key(c.SDLK_r)],
            [key(c.SDLK_8),key(c.SDLK_e),key(c.SDLK_b),key(c.SDLK_l)],
            [key(c.SDLK_9),key(c.SDLK_t),key(c.SDLK_F11)],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
            [key(c.SDLK_5),key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer'),patch.object(preview,'HighendRenderer') as renderer, \
             patch.object(c,'window',object(),create=True),patch.object(c,'renderer',object(),create=True), \
             patch.object(c,'hide_lattice'),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(preview,'sleep'):
            preview.run(SimpleNamespace(capture_dir=None,assets=ASSETS))
            calls=renderer.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[0].name,'parry_window')
            self.assertEqual(calls[1].args[0].name,'pulse_phase_10')
            self.assertEqual(calls[-1].args[0].name,'pulse_resolved')
            self.assertEqual(renderer.return_value.theme,1)
            self.assertEqual(renderer.return_value.variant,2);self.assertEqual(renderer.return_value.mode,1)
            self.assertFalse(renderer.return_value.compare);display.return_value.toggle.assert_called_once_with()
