import hashlib
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from arena_art_common import ArenaArtError
from game_renderer import GameFlowRenderer
from render_motion import RenderMotion
from stage11_art_renderer import FROZEN_PROFILE, Stage11ArtPath, Stage11ArtRenderer
from tests.test_stage6_live_art import canvas
from tests.test_stage11_live_art import advance, sync
from tools.stage11_play import session
from tools.stage5_art_preview import capture_png, open_preview


def verify_live_pixels():
    from pico2d import pico2d as c

    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'artifacts/stage11_d2/capture_manifest.json').read_bytes())
    hashes = {row['file']: row['sha256'] for row in manifest['captures']}
    game, _ = session()
    motion = RenderMotion()
    path = Stage11ArtPath(c, motion=motion)
    try:
        open_preview(c, capture=True)
        sync(game, motion, 0)
        with tempfile.TemporaryDirectory() as folder:
            for tick, name in ((0, 'normal.png'), (114, 'knight_peak.png'), (134, 'dual_rook.png')):
                advance(game, motion, tick)
                before = pickle.dumps((game, motion))
                if not path.draw(game, motion.positions):
                    raise AssertionError('The live session fell back')
                hud = GameFlowRenderer()
                hud.draw_stage_label(c, game)
                hud.draw(c, game)
                out = Path(folder) / name
                capture_png(c, out)
                if hashlib.sha256(out.read_bytes()).hexdigest() != hashes[name]:
                    raise AssertionError(name)
                if before != pickle.dumps((game, motion)):
                    raise AssertionError('Rendering mutated the session')
    finally:
        path.close()
        if c.window:
            c.close_canvas()
            c.window = c.renderer = None


class ProfileTests(unittest.TestCase):
    def test_approved_images_through_live_session_factory(self):
        subprocess.run([sys.executable, '-m', 'tests.test_arena_art_profile'], check=True,
                       cwd=Path(__file__).resolve().parents[1], timeout=60,
                       env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy',
                            'CHECKMATE_STAGE11_ART': '1'})

    def test_roster_selects_unique_sprites_and_keeps_profile_layout(self):
        c = canvas()
        renderer = Stage11ArtRenderer(c, kinds=['pawn', 'pawn'])
        self.addCleanup(renderer.close)
        self.assertEqual(set(renderer.images), {'player', 'pawn', 'background', 'frame', 'light', 'dark'})
        self.assertEqual(c.load_image.call_count, 6)
        self.assertEqual(renderer.profile.pieces['pawn'].animation_profile, 'pawn')
        renderer.close()
        self.assertEqual(c.SDL_DestroyTexture.call_count, 6)

    def test_unregistered_piece_falls_back_before_loading_textures(self):
        c = canvas()
        game, _ = session()
        path = Stage11ArtPath(c)
        # Simulate a future roster whose chapter art has not cleared review.
        with patch.dict(FROZEN_PROFILE.pieces, {}, clear=True), \
                patch.dict(os.environ, CHECKMATE_STAGE11_ART='1'), \
                self.assertLogs('stage11_art_renderer', level='ERROR'):
            self.assertFalse(path.draw(game, {}))
            self.assertTrue(path.failed)
        self.assertFalse(c.load_image.called)
        with self.assertRaises(ArenaArtError):
            FROZEN_PROFILE.files_for(['queen'])


if __name__ == '__main__':
    verify_live_pixels()
