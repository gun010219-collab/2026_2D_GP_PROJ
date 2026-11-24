import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from arena_art_common import CAMERA
from chapter_art_renderer import FROZEN, ROYAL, LiveArenaArtPath
from main import _new_stage_game
from stage5_art_renderer import ROOT, Stage5ArtRenderer, actor_layout
from stage11_art_renderer import actor_layout as eleven_layout
from stage12_art_renderer import actor_layout as twelve_layout
from stage13_art_renderer import actor_layout as thirteen_layout
from tests.test_stage6_live_art import canvas
from tools.chapter_art_play import session

ART_FLAGS = {f'CHECKMATE_STAGE{n}_ART' for n in range(1, 26)}
ART_FLAGS.update(f'CHECKMATE_CHAPTER{n}_ART' for n in range(1, 6))


class ChapterArtTests(unittest.TestCase):
    def setUp(self):
        environment = {key: val for key, val in os.environ.items() if key not in ART_FLAGS}
        self.enterContext(patch.dict(os.environ, environment, clear=True))

    def test_actual_rosters_health_and_textures(self):
        expected_hp = {1: 8, 2: 16, 3: 15, 4: 23, 5: 44, 14: 65, 15: 127}
        expected_counts = (6, 7, 7, 8, 8, 7, 7, 9, 9, 9, 8, 8, 8, 9, 9)
        device = canvas()
        art = LiveArenaArtPath(device)
        self.addCleanup(art.close)
        for n in (1, 2, 3):
            os.environ[f'CHECKMATE_CHAPTER{n}_ART'] = '1'
        with patch.object(Stage5ArtRenderer, 'draw'):
            for n in range(1, 26):
                with self.subTest(stage=n):
                    game = _new_stage_game(n)
                    device.load_image.reset_mock()
                    self.assertEqual(art.draw(game, {}), n <= 15)
                    loaded = [Path(call.args[0]).stem for call in device.load_image.call_args_list]
                    if n <= 15:
                        kinds = {e.kind for e in game.encounter.enemies}
                        self.assertEqual(len(loaded), expected_counts[n-1])
                        for kind in kinds:
                            self.assertTrue(any(kind in name for name in loaded))
                        if n in expected_hp:
                            self.assertEqual(sum(e.health.current_hp for e in game.encounter.enemies), expected_hp[n])
                    else:
                        self.assertEqual(loaded, [])

    def test_chapter_flags_and_exact_per_stage_overrides(self):
        art = LiveArenaArtPath(canvas())
        self.addCleanup(art.close)
        with patch.object(Stage5ArtRenderer, 'draw'):
            for chapter in (1, 2, 3):
                flag = f'CHECKMATE_CHAPTER{chapter}_ART'
                with patch.dict(os.environ, {flag: '1'}):
                    for n in range(1, 16):
                        self.assertEqual(art.draw(_new_stage_game(n), {}), (n-1)//5+1 == chapter)
                    for n in range(chapter * 5 - 4, chapter * 5 + 1):
                        with patch.dict(os.environ, {f'CHECKMATE_STAGE{n}_ART': '0'}):
                            self.assertFalse(art.draw(_new_stage_game(n), {}))
            for n in range(1, 16):
                game = _new_stage_game(n)
                self.assertFalse(art.draw(game, {}))
                with patch.dict(os.environ, {f'CHECKMATE_STAGE{n}_ART': '1'}):
                    self.assertTrue(art.draw(game, {}))

    def test_layout_assets_foot_and_hp_for_royal_and_frozen(self):
        self.assertNotIn('queen', ROYAL.pieces)
        for u in range(10):
            for v in range(10):
                for kind in ('player', 'pawn', 'rook', 'king'):
                    self.assertEqual(ROYAL.layout(kind, u, v), actor_layout(kind, u, v))
                for kind, layout in (('rook', eleven_layout), ('bishop', twelve_layout), ('queen', thirteen_layout)):
                    self.assertEqual(FROZEN.layout(kind, u, v), layout(kind, u, v))
                for kind, profile, rows in (('knight', ROYAL, (21, 235)), ('bishop', ROYAL, (18, 238)),
                                            ('king', FROZEN, (18, 238))):
                    layout = profile.layout(kind, u, v)
                    self.assertEqual(layout['foot'], CAMERA.project(u+.5, v+.25))
                    self.assertAlmostEqual(layout['center'][1] + layout['height'] * (.5 - rows[1]/256),
                                           layout['foot'][1])
                    self.assertAlmostEqual(layout['top'] - layout['foot'][1],
                                           layout['height'] * (rows[1]-rows[0])/256)
                self.assertGreater(FROZEN.layout('king', u, v)['top'], FROZEN.layout('queen', u, v)['top'])
        concepts = ROOT / 'assets/character_concepts'
        asset_rows = json.loads((concepts/'asset_manifest.json').read_bytes())['assets']
        for name in ('ch1_knight', 'ch1_bishop', 'ch3_king'):
            row = next(row for row in asset_rows if row['name'] == name)
            self.assertEqual(hashlib.sha256((concepts/(name+'.png')).read_bytes()).hexdigest(), row['sha256'])
            self.assertEqual(hashlib.sha256((concepts/'source'/(name+'.png')).read_bytes()).hexdigest(),
                             row['source_sha256'])

    def test_development_only_chapter_entry_with_authentic_upgrades(self):
        for stage, hp, damage in ((1, 3, 1), (5, 2, 5), (13, 3, 5), (14, 4, 5), (15, 4, 6)):
            game, flow = session(stage)
            self.assertEqual(game.stage_number, stage)
            self.assertEqual(game.player.health.current_hp, hp)
            self.assertEqual(game.resolver.player_damage, damage)
            self.assertEqual(len(flow.run.receipts), (stage-1)%5)
            self.assertEqual(game.combat.tick, 0)
            for receipt in flow.run.receipts:
                flow.run.verify_receipt(receipt)

    def test_native_software_render_combat_and_resource_lifetime(self):
        subprocess.run([sys.executable, '-m', 'tools.chapter_art_qa'], cwd=ROOT, check=True,
                       capture_output=True, timeout=60)
