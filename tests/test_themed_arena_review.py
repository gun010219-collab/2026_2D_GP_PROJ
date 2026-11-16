"""B-only theme/size review preserves projected events and existing assets."""
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
from unittest.mock import Mock,patch

from tools.themed_arena_review import SIZE_CAMERAS,SCALES,THEMES,RECOMMENDED,ThemedRenderer,ASSETS
from tools.arena_projection import CAMERAS


def area(points):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1])))/2


class ThemedArenaTests(unittest.TestCase):
    def test_sizes_keep_b_perspective_and_all_centers_pick_correctly(self):
        self.assertEqual(SIZE_CAMERAS[0].corners,CAMERAS[1].corners)
        for scale,cam in zip(SCALES,SIZE_CAMERAS):
            self.assertAlmostEqual(area(cam.corners)/area(CAMERAS[1].corners),scale*scale)
            for c in range(10):
                for r in range(10):self.assertEqual(cam.pick(*cam.center(c,r)),(c,r))
            for x,y in cam.corners:
                self.assertGreater(x,278);self.assertLess(x,1200)
                self.assertGreater(y-cam.thickness-25,0);self.assertLess(y+100,838)
        self.assertEqual(RECOMMENDED,2)

    def test_five_actual_backgrounds_match_manifest(self):
        records=json.loads((ASSETS/'asset_manifest.json').read_text())['assets']
        self.assertEqual({r['name'] for r in records},set(THEMES))
        self.assertEqual(len({r['sha256'] for r in records}),5)
        for r in records:
            data=(ASSETS/(r['name']+'.png')).read_bytes()
            self.assertEqual(struct.unpack('>II',data[16:24]),(1440,900))
            self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])

    def test_missing_theme_fails_instead_of_silent_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            canvas=Mock()
            with self.assertRaises(FileNotFoundError):ThemedRenderer(canvas,Path(folder))
            self.assertEqual(canvas.load_image.call_count,10)

    def test_native_five_themes_all_scenes_and_old_b_preserve_state(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,'tools/themed_arena_review.py','--capture-dir',folder],cwd=root,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=45)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((Path(folder)/'review_manifest.json').read_text())
            self.assertEqual(data['textures_loaded'],15)
            self.assertEqual(len(data['captures']),34)
            old=json.loads((root/'assets/camera_review/camera_manifest.json').read_text())
            self.assertEqual(data['scenes'],old['scenes'])
            for record in data['captures']:
                self.assertEqual(struct.unpack('>II',(Path(folder)/record['file']).read_bytes()[16:24]),(1440,900))
                for actor in record['bounds']:
                    l,y,r,t=actor['box'];self.assertGreater(l,278);self.assertLess(r,1200)
                    self.assertGreater(y,0);self.assertLess(t+20,838)
                if record['file'].endswith('_pulse.png'):self.assertEqual(len(record['warning_cells']),100)

    def test_theme_size_scene_repeat_settings_and_fullscreen_routing(self):
        import tools.themed_arena_review as preview
        from pico2d import pico2d as c
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_2),key(c.SDLK_5,True),key(c.SDLK_6),key(c.SDLK_p)],
                     [key(c.SDLK_b),key(c.SDLK_9),key(c.SDLK_F11)],
                     [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
                     [key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer'),patch.object(preview,'ThemedRenderer') as renderer, \
             patch.object(c,'window',object(),create=True),patch.object(c,'renderer',object(),create=True), \
             patch.object(c,'hide_lattice'),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(preview,'sleep'):
            preview.run(SimpleNamespace(capture_dir=None,assets=ASSETS))
            calls=renderer.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[1],SIZE_CAMERAS[0]);self.assertEqual(calls[-1].args[1],SIZE_CAMERAS[RECOMMENDED])
            self.assertEqual(calls[-1].args[0].name,'pulse')
            self.assertEqual(renderer.return_value.theme,1)
            self.assertFalse(renderer.return_value.compare)
            display.return_value.toggle.assert_called_once_with()
