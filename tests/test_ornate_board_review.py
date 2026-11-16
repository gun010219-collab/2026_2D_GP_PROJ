"""Decorated perimeter stays outside the unchanged, authentic combat picture."""
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

from tools.ornate_board_review import ASSETS,CAMERA,OrnateRenderer,cue_for,parry_window_scene,pulse_phase
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS
from tools.themed_arena_review import SIZE_CAMERAS,THEMES


def outside(points):
    xs,ys=zip(*points)
    return max(xs)<=0 or min(xs)>=10 or max(ys)<=0 or min(ys)>=10


def rgba(path):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load
    loaded=IMG_Load(str(path).encode('utf-8'))
    if not loaded:raise RuntimeError(str(path))
    image=s.SDL_ConvertSurfaceFormat(loaded,s.SDL_PIXELFORMAT_RGBA32,0)
    s.SDL_FreeSurface(loaded)
    if not image:raise RuntimeError('RGBA conversion')
    try:
        return image.contents.pitch,ctypes.string_at(image.contents.pixels,image.contents.pitch*image.contents.h)
    finally:s.SDL_FreeSurface(image)


class OrnateBoardTests(unittest.TestCase):
    def test_real_ledger_and_parry_results_classify_without_consuming_state(self):
        expected=('ready','player_attack','danger','parry_success','perfect_success','pulse')
        for name,kind in zip(SCENARIOS,expected):
            scene=make_scene(name);g=scene.game
            before=(snapshot(scene),vars(g.parry).copy())
            for _ in range(5):self.assertEqual(cue_for(scene).kind,kind)
            self.assertEqual(before,(snapshot(scene),vars(g.parry).copy()))

    def test_ready_active_window_success_and_cooldown_are_not_conflated(self):
        ready=cue_for(make_scene('normal'))
        self.assertTrue(ready.ready);self.assertFalse(ready.active_window)
        scene=parry_window_scene();cue=cue_for(scene)
        self.assertEqual(cue.kind,'parry_window');self.assertTrue(cue.active_window)
        self.assertFalse(cue.ready);self.assertIsNone(scene.game.resolver.last_parry_result)
        scene=make_scene('normal');g=scene.game
        g.resolver.register_parry(g.parry.request(0));g.advance(20)
        self.assertGreater(g.parry.next_parry_tick,g.combat.tick)
        cue=cue_for(scene)
        self.assertEqual(cue.kind,'quiet');self.assertFalse(cue.ready);self.assertFalse(cue.active_window)

    def test_pulse_runner_uses_three_real_event_times_and_all_100_cells(self):
        for elapsed in (10,60,110):
            scene=pulse_phase(elapsed);cue=cue_for(scene)
            self.assertEqual(cue.kind,'pulse');self.assertAlmostEqual(cue.progress,elapsed/120)
            record=next(r for r in scene.game.encounter.ledger._records.values()
                        if r.state=='telegraph' and r.event.attack_kind=='king_pulse')
            self.assertEqual(set(record.event.target_cells),{(x,y) for x in range(10) for y in range(10)})
            self.assertEqual(record.event.hit_tick-record.event.start_tick,120)
            scene.game.advance(record.event.hit_tick-scene.game.combat.tick)
            self.assertEqual(record.state,'resolved')
            self.assertEqual(scene.game.encounter.pulse.state,'CLEANUP')
            self.assertNotEqual(cue_for(scene).kind,'pulse')

    def test_new_transparent_crests_and_originals_match_recorded_hashes(self):
        records=json.loads((ASSETS/'asset_manifest.json').read_text())['assets']
        self.assertEqual({r['name'] for r in records},set(THEMES))
        for r in records:
            data=(ASSETS/(r['name']+'.png')).read_bytes()
            self.assertEqual(struct.unpack('>II',data[16:24]),(256,256))
            self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
            self.assertEqual(hashlib.sha256((ASSETS/'source'/(r['name']+'.png')).read_bytes()).hexdigest(),r['source_sha256'])
            self.assertGreater(r['transparent_pixels'],20000)
            l,t,right,bottom=r['alpha_bbox']
            self.assertGreater(l,0);self.assertGreater(t,0)
            self.assertLess(right,256);self.assertLess(bottom,256)

    def test_missing_crest_fails_and_releases_previously_loaded_images(self):
        with tempfile.TemporaryDirectory() as folder:
            canvas=Mock()
            with self.assertRaises(FileNotFoundError):OrnateRenderer(canvas,Path(folder))
            self.assertEqual(canvas.load_image.call_count,15)

    def test_native_capture_replay_perimeter_geometry_and_central_pixel_invariance(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)
            result=subprocess.run([sys.executable,'tools/ornate_board_review.py','--capture-dir',folder],cwd=root,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((output/'review_manifest.json').read_text())
            stored=json.loads((ASSETS/'review/review_manifest.json').read_text())
            self.assertEqual(data,stored)
            old=json.loads((root/'assets/themed_arena/review/review_manifest.json').read_text())
            self.assertEqual(data['scenes'][:6],old['scenes'])
            self.assertEqual(CAMERA,SIZE_CAMERAS[2]);self.assertEqual(data['textures_loaded'],20)
            self.assertEqual(data['camera'],[list(p) for p in CAMERA.corners])
            self.assertEqual(len(data['captures']),37);self.assertEqual(len(data['scenes']),10)
            for r in data['captures']:
                raw=(output/r['file']).read_bytes()
                self.assertEqual(struct.unpack('>II',raw[16:24]),(1440,900))
                self.assertEqual(hashlib.sha256(raw).hexdigest(),reference_sha256(ASSETS/'review'/r['file']))
                self.assertTrue(all(outside(segment) for segment in r['decor_segments']+r['cue_segments']))
                self.assertTrue(all(outside(quad) for quad in r['decor_quads']))
                if r['mode']==0:self.assertEqual(r['cue_segments'],[])
                if r['file'].endswith('_pulse.png') or r['file'].startswith('pulse_phase_'):
                    self.assertEqual(len(r['warning_cells']),100)
            # 9 points inside every logical tile: neither ornament nor any cue
            # mode changes the actual play surface, actors, HP or attack picture.
            points=[CAMERA.project(c+u,r+v) for c in range(10) for r in range(10)
                    for u in (.12,.5,.88) for v in (.12,.5,.88)]
            for name in SCENARIOS:
                paths=[output/('royal_mode_'+str(m)+'_'+name+'.png') for m in range(3)]
                if name=='normal':paths.append(output/'prior_Q.png')
                arrays=[rgba(p) for p in paths]
                for x,y in points:
                    values=[pixels[(899-round(y))*pitch+round(x)*4:(899-round(y))*pitch+round(x)*4+4]
                            for pitch,pixels in arrays]
                    self.assertTrue(all(value==values[0] for value in values),f'{name} at {x},{y}')

    def test_theme_variant_mode_scene_repeat_and_settings_input_are_review_only(self):
        import tools.ornate_board_review as preview
        from pico2d import pico2d as c
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_2),key(c.SDLK_5,True),key(c.SDLK_6),key(c.SDLK_q),key(c.SDLK_p)],
            [key(c.SDLK_8),key(c.SDLK_e),key(c.SDLK_r)],[key(c.SDLK_b),key(c.SDLK_l)],
            [key(c.SDLK_9),key(c.SDLK_F11)],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
            [key(c.SDLK_5),key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer'),patch.object(preview,'OrnateRenderer') as renderer, \
             patch.object(c,'window',object(),create=True),patch.object(c,'renderer',object(),create=True), \
             patch.object(c,'hide_lattice'),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(preview,'sleep'):
            preview.run(SimpleNamespace(capture_dir=None,assets=ASSETS))
            calls=renderer.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[0].name,'pulse')
            self.assertEqual(calls[1].args[0].name,'parry_window')
            self.assertEqual(calls[-1].args[0].name,'pulse_phase_10')
            self.assertEqual(renderer.return_value.theme,1)
            self.assertEqual(renderer.return_value.variant,2);self.assertEqual(renderer.return_value.mode,1)
            self.assertFalse(renderer.return_value.compare)
            display.return_value.toggle.assert_called_once_with()
