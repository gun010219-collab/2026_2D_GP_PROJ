"""Read-only native concept review and actual-cell safety checks."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from tools.character_art_review import ASSETS, NAMES, SIZES


class CharacterArtReviewTests(unittest.TestCase):
    def test_actual_transparent_assets_fit_cell_and_leave_hp_space(self):
        records=json.loads((ASSETS/'asset_manifest.json').read_text())['assets']
        self.assertEqual({r['name'] for r in records},set(NAMES))
        self.assertEqual(len({r['sha256'] for r in records}),11)
        for item in records:
            raw=(ASSETS/(item['name']+'.png')).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'])
            self.assertEqual(struct.unpack('>II',raw[16:24]),(256,256))
            self.assertGreater(item['transparent_pixels'],0)
            l,t,r,b=item['alpha_bbox'];kind=item['name'].split('_')[-1]
            size=SIZES[kind]
            self.assertLessEqual(max(r-l,b-t),220)
            self.assertGreaterEqual((l-128)*size/256,-42)
            self.assertLessEqual((r-128)*size/256,42)
            self.assertGreaterEqual((128-b)*size/256-5,-42)
            self.assertLess((128-t)*size/256-5,30)

    def test_native_all_gallery_and_real_combat_captures_preserve_state(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,'tools/character_art_review.py','--capture-dir',folder],
                cwd=root,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((Path(folder)/'review_manifest.json').read_text())
            self.assertEqual(data['textures_loaded'],14)
            self.assertEqual(len(data['files']),9)
            old=json.loads((root/'assets/art_samples/stage5_r2/review/capture_manifest.json').read_text())
            self.assertEqual(data['scenes'],[r for r in old['frozen_snapshots'] if r['scenario']!='player_attack'])
            for name in data['files']:
                raw=(Path(folder)/name).read_bytes()
                self.assertEqual(struct.unpack('>II',raw[16:24]),(1440,900))
