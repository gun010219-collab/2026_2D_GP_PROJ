import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import main
from arena_art_common import CAMERA
from chapter_art_renderer import CHAPTER_PROFILES, LiveArenaArtPath
from chapter_run import ChapterRun
from late_chapter_art import DECK_EDGE, PANEL_TOP, RIM_EDGE
from stage5_art_renderer import ROOT
from tests.test_stage6_live_art import canvas


class ReleaseArtTests(unittest.TestCase):
    def test_current_balance_and_grouped_paths_cover_every_stage(self):
        art = LiveArenaArtPath(canvas(), default_enabled=True)
        self.assertEqual(set(art.stage_paths), set(range(1, 26)))
        self.assertEqual(set(CHAPTER_PROFILES), set(range(1, 6)))
        totals = []
        for number in range(1, 26):
            game = main._new_stage_game(number)
            profile = CHAPTER_PROFILES[game.chapter]
            roster = {e.kind for e in game.encounter.enemies}
            files = profile.files_for(roster)
            self.assertTrue(all((ROOT/file).is_file() for file in files.values()))
            self.assertEqual(len(files), len(roster) + (6 if game.chapter >= 4 else 5))
            if number >= 16:
                totals.append(sum(e.health.max_hp for e in game.encounter.enemies))
        self.assertEqual(totals, [109,109,110,133,191,123,119,130,145,233])

    def test_main_passes_release_default_and_explicit_flags_win(self):
        with patch.object(main, 'run_session') as start:
            main.main()
            self.assertIs(start.call_args.kwargs['default_art'], True)
            main.main(run=ChapterRun())
            self.assertIs(start.call_args.kwargs['default_art'], False)
        a = LiveArenaArtPath(canvas(), default_enabled=True)
        b = LiveArenaArtPath(canvas())
        for stage in (1, 5, 6, 10, 11, 15, 16, 20, 21, 25):
            chapter = (stage-1)//5 + 1
            with patch.dict(os.environ, {}, clear=True):
                self.assertTrue(a.stage_paths[stage].enabled(stage))
                self.assertFalse(b.stage_paths[stage].enabled(stage))
                os.environ[f'CHECKMATE_CHAPTER{chapter}_ART'] = '0'
                self.assertFalse(a.stage_paths[stage].enabled(stage))
                os.environ[f'CHECKMATE_STAGE{stage}_ART'] = '1'
                self.assertTrue(a.stage_paths[stage].enabled(stage))
                os.environ[f'CHECKMATE_CHAPTER{chapter}_ART'] = '1'
                os.environ[f'CHECKMATE_STAGE{stage}_ART'] = '0'
                self.assertFalse(a.stage_paths[stage].enabled(stage))

    def test_late_assets_match_manifest_and_foot_uses_alpha(self):
        data = json.loads((ROOT/'assets/late_chapter_units/manifest.json').read_bytes())
        self.assertEqual(len(data), 12)
        for row in data:
            for key in ('source', 'file'):
                png = (ROOT / row[key]).read_bytes()
                self.assertEqual(hashlib.sha256(png).hexdigest(),
                                 row['source_sha256' if key == 'source' else 'sha256'])
            box = row['prepared']['alpha_bbox']
            self.assertEqual(row['prepared']['size'], [256, 256])
            self.assertEqual(max(box[2]-box[0], box[3]-box[1]), 220)
            profile = CHAPTER_PROFILES[row['chapter']]
            self.assertEqual(profile.pieces[row['kind']].sprite, row['file'])
            for v in (0, 9):
                pose = profile.layout(row['kind'], 5, v)
                self.assertEqual(pose['foot'], CAMERA.project(5.5, v+.25))
                self.assertAlmostEqual(pose['center'][1] + pose['height'] * (.5-box[3]/256),
                                       pose['foot'][1])
                self.assertGreater(pose['hp_y'], pose['top'])
        self.assertLess(PANEL_TOP + 10, RIM_EDGE)
        self.assertLess(RIM_EDGE, DECK_EDGE)

    def test_release_smoke_real_sdl_and_campaign(self):
        env = {k:v for k,v in os.environ.items() if not (k.startswith('CHECKMATE_') and k.endswith('_ART'))}
        command = [sys.executable, '-m', 'tools.release_art_qa']
        result = subprocess.run(command, cwd=Path(ROOT), env=env, capture_output=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
