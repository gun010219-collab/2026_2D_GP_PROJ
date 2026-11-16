"""Forest opt-in reuses the approved display pipeline without changing combat."""
import hashlib
import json
import os
import pickle
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import main
import stage5_art_renderer as royal
import stage6_art_renderer as forest
from arena_art_common import CAMERA
from config import cell_center
from render_motion import RenderMotion
from tools.stage6_play import session


def canvas():
    c = Mock()
    c.SDL_SetTextureColorMod.return_value = 0
    c.load_image.side_effect = lambda p: Mock()
    return c


class Stage6LiveArtTests(unittest.TestCase):
    def test_independent_flags_all_stages_and_default_legacy(self):
        for f5, f6 in (('0', '0'), ('1', '0'), ('0', '1'), ('1', '1')):
            with patch.dict(os.environ, CHECKMATE_STAGE5_ART=f5, CHECKMATE_STAGE6_ART=f6):
                a, b = Mock(), Mock()
                path = forest.LiveArenaArtPath(canvas(), a, b)
                for n in range(1, 26):
                    self.assertEqual(path.draw(main._new_stage_game(n), {}),
                                     n == 5 and f5 == '1' or n == 6 and f6 == '1', (n, f5, f6))
                self.assertEqual(a.call_count, int(f5 == '1'))
                self.assertEqual(b.call_count, int(f6 == '1'))
                path.close()

    def test_shared_camera_maps_all_cells_and_half_open_boundaries(self):
        self.assertIs(CAMERA, royal.CAMERA)
        for col in range(10):
            for row in range(10):
                self.assertEqual(CAMERA.pick(*CAMERA.center(col, row)), (col, row))
                self.assertEqual(CAMERA.tile(col, row), royal.CAMERA.tile(col, row))
        for v in (0, 5, 9.99):
            self.assertIsNone(CAMERA.pick(*CAMERA.project(10, v)))
            self.assertIsNone(CAMERA.pick(*CAMERA.project(v, 10)))
            self.assertEqual(CAMERA.pick(*CAMERA.project(0, v)), (0, int(v)))

    def test_assets_source_hashes_transparency_and_measured_alpha_geometry(self):
        from tests.test_aligned_board_review import rgba
        from tools.prepare_stage5_art import alpha_bounds
        import sdl2 as s
        from sdl2.sdlimage import IMG_Load
        root = royal.ROOT / 'assets/chapter2_units'
        data = json.loads((root / 'asset_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual({a['name'] for a in data['assets']}, {'pawn', 'rook'})
        for a in data['assets']:
            for file, digest in ((a['file'], a['sha256']), (a['source'], a['source_sha256'])):
                self.assertEqual(hashlib.sha256((root / file).read_bytes()).hexdigest(), digest)
            pitch, pixels = rgba(root / a['file'])
            self.assertEqual((pitch, len(pixels)), (1024, 256*256*4))
            self.assertTrue(any(pixels[i] == 0 for i in range(3, len(pixels), 4)))
            source = IMG_Load(str(root / a['file']).encode('utf-8'))
            converted = s.SDL_ConvertSurfaceFormat(source, s.SDL_PIXELFORMAT_RGBA32, 0)
            try:
                box, _ = alpha_bounds(converted)
                self.assertEqual(list(box), a['alpha_bbox'])
                self.assertEqual((box[1], box[3]), forest.ALPHA_ROWS[a['name']])
            finally:
                s.SDL_FreeSurface(converted)
                s.SDL_FreeSurface(source)
        self.assertNotIn('king', forest.FILES)

    def test_seven_textures_load_once_and_release_on_restart_exit_and_close(self):
        with patch.dict(os.environ, CHECKMATE_STAGE6_ART='1'):
            c = canvas()
            path = forest.Stage6ArtPath(c)
            g, _ = session()
            with patch.object(forest.Stage6ArtRenderer, 'draw'):
                for _ in range(10):
                    self.assertTrue(path.draw(g, {}))
                self.assertEqual(c.load_image.call_count, 7)
                path.draw(session()[0], {})
                self.assertEqual(c.SDL_DestroyTexture.call_count, 7)
                path.draw(main._new_stage_game(7), {})
                path.close()
                self.assertEqual(c.load_image.call_count, 14)
                self.assertEqual(c.SDL_DestroyTexture.call_count, 14)

    def test_partial_load_and_sdl_errors_fallback_without_mutating_state(self):
        c = canvas()
        first = Mock()
        c.load_image.side_effect = [first, OSError('corrupt image')]
        with self.assertRaises(OSError):
            forest.Stage6ArtRenderer(c)
        c.SDL_DestroyTexture.assert_called_once()
        self.assertIsNone(first.texture)
        with patch.dict(os.environ, CHECKMATE_STAGE6_ART='1'):
            g, _ = session()
            before = pickle.dumps(g)
            factory = Mock(side_effect=FileNotFoundError('missing forest asset'))
            path = forest.Stage6ArtPath(canvas(), factory)
            with self.assertLogs('stage6_art_renderer', level='ERROR'):
                for _ in range(3):
                    self.assertFalse(path.draw(g, {}))
            factory.assert_called_once()
            self.assertEqual(pickle.dumps(g), before)
            renderer = Mock()
            renderer.draw.side_effect = royal.Stage5ArtError('SDL device')
            path = forest.Stage6ArtPath(canvas(), lambda c: renderer)
            with self.assertLogs('stage6_art_renderer', level='ERROR'):
                self.assertFalse(path.draw(g, {}))
            renderer.close.assert_called_once()
            renderer.draw.side_effect = TypeError('programming error')
            path = forest.Stage6ArtPath(canvas(), lambda c: renderer)
            with self.assertRaises(TypeError):
                path.draw(g, {})

    def test_real_missing_file_releases_already_loaded_textures(self):
        with tempfile.TemporaryDirectory() as d:
            c = canvas()
            root = Path(d)
            for _, name in list(forest.FILES.items())[:2]:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(b'file existence fixture')
            with self.assertRaises(FileNotFoundError):
                forest.Stage6ArtRenderer(c, root=root)
            self.assertEqual(c.load_image.call_count, 2)
            self.assertEqual(c.SDL_DestroyTexture.call_count, 2)

    def test_alpha_foot_and_hp_clearance_preserve_uniform_sprite_proportions(self):
        for kind in ('player', 'pawn', 'rook'):
            for v in (0, 4, 6, 8, 9, 3.25):
                p = forest.actor_layout(kind, 4.5, v)
                top, bottom = forest.ALPHA_ROWS.get(kind, (18, 238))
                self.assertEqual(p['foot'], CAMERA.project(5, v + .25))
                self.assertAlmostEqual(p['center'][1] - p['height'] * (.5 - (256-bottom)/256), p['foot'][1])
                self.assertAlmostEqual(p['top'] - p['foot'][1], p['height']*(bottom-top)/256)
                self.assertGreaterEqual(p['hp_y'] - 3 - p['top'], 2)
                self.assertLess(p['hp_y'] + 13, 900)
        for kind in royal.BASE_SIZE:
            self.assertEqual(royal.actor_layout(kind, 4, 3), royal.Stage5ArtRenderer.layout(None, kind, 4, 3))

    def test_live_motion_depth_hp_warnings_and_rendering_preserve_entire_game(self):
        g, _ = session()
        r = forest.Stage6ArtRenderer(canvas())
        motion = RenderMotion()
        try:
            with patch.object(royal, 'polygon'), patch.object(r, 'image') as images:
                for _ in range(230):
                    if g.playing:
                        g.advance()
                    motion.update((g.player, *g.encounter.enemies), 1/180, session=g.combat.combat_session_id)
                    before = pickle.dumps(g)
                    r.draw(g, motion.positions)
                    self.assertEqual(pickle.dumps(g), before)
                    self.assertIsNone(g.encounter.pulse)
                    expected = [tuple(p) for e in g.encounter.ledger.telegraphs for p in e.target_cells] if g.playing else []
                    self.assertEqual(r.warning_cells, expected)
                    actors = [e for e in (g.player, *g.encounter.enemies) if e.alive and getattr(e, 'active', True)]
                    actors.sort(key=lambda e: (-motion.positions[e.entity_instance_id][1],
                                               motion.positions[e.entity_instance_id][0], e.entity_instance_id))
                    self.assertEqual(r.order, [e.entity_instance_id for e in actors])
                    for e in actors:
                        x, y = motion.positions[e.entity_instance_id]
                        p = r.actor_layouts[e.entity_instance_id]
                        self.assertEqual(p['foot'], CAMERA.project((x-300)/84, (y-30)/84-.25))
                for call in images.call_args_list:
                    if call.args[0] in forest.BASE_SIZE:
                        self.assertEqual(call.args[3], call.args[4])
        finally:
            r.close()

    def test_actual_parry_window_normal_perfect_and_expiry_not_fabricated(self):
        r = forest.Stage6ArtRenderer(canvas())
        try:
            for delta, status, cue in ((18, 'normal', 'parry_success'), (7, 'perfect', 'perfect_success')):
                g, _ = session()
                rook = g.encounter.enemies[-1]
                while g.playing and rook.current_attack is None:
                    g.advance()
                event = rook.current_attack
                g.advance(event.hit_tick - delta - g.combat.tick)
                g.resolver.register_parry(g.parry.request(g.combat.tick))
                self.assertEqual(royal.cue_kind(g), 'parry_window')
                self.assertIsNone(g.resolver.last_parry_result)
                g.advance(delta)
                self.assertEqual(g.resolver.last_parry_result.status, status)
                with patch.object(royal, 'polygon'), patch.object(r, 'image'):
                    before = pickle.dumps(g)
                    r.draw(g, {})
                    self.assertEqual(pickle.dumps(g), before)
                    self.assertEqual(r.cue, cue)
                g.advance(18)
                self.assertNotEqual(royal.cue_kind(g), cue)
        finally:
            r.close()

    def test_real_progression_five_six_restart_seven_and_texture_ownership(self):
        from tools.stage5_play import session as stage5
        from tests.test_stage_transition import finish
        with patch.dict(os.environ, CHECKMATE_STAGE5_ART='1', CHECKMATE_STAGE6_ART='1'):
            five, six = Mock(side_effect=lambda c: Mock()), Mock(side_effect=lambda c: Mock())
            path = forest.LiveArenaArtPath(canvas(), five, six)
            g, flow = stage5()
            path.draw(g, {})
            finish(g, 'clear')  # Transition fixture only, not campaign measurement.
            g, _ = flow.enter_next_chapter(main._new_stage_game, lambda stats: None)
            self.assertEqual((g.stage_number, flow.run.current_stage, len(flow.run.receipts)), (6, 6, 0))
            path.draw(g, {})
            finish(g, 'dead')
            g, _ = flow.restart(main._new_stage_game, lambda stats: None)
            self.assertEqual(g.stage_number, 6)
            path.draw(g, {})
            finish(g, 'clear')
            offer = flow.sync_offer()
            g, _ = flow.choose(offer, 'hp', main._new_stage_game, lambda stats: None)
            self.assertEqual(g.stage_number, 7)
            self.assertIsNotNone(offer)
            self.assertFalse(path.draw(g, {}))
            self.assertEqual((five.call_count, six.call_count), (1, 2))
            path.close()

    def test_native_sdl_real_main_and_capture_pngs(self):
        script = r"""
import tempfile
from pathlib import Path
from unittest.mock import patch
import sdl2 as s
from pico2d import pico2d as c
import main
from stage6_art_renderer import Stage6ArtRenderer
from tools.stage6_play import session
from tools.capture_stage6_live import capture
from tools.stage5_art_preview import open_preview
g, flow = session()
count = [0]
def events():
    count[0] += 1
    return [] if count[0] < 5 else [type('Quit', (), {'type': s.SDL_QUIT})()]
with patch.object(c, 'open_canvas', lambda w,h: open_preview(c,capture=True)), patch.object(c, 'get_events', events), patch.object(main, 'sleep'):
    main.run_session(g, flow)
assert count[0] == 5
with tempfile.TemporaryDirectory() as d:
    capture(Path(d))
    assert len(list(Path(d).glob('*.png'))) == 5
print('FOREST NATIVE MAIN / REAL PARRY CAPTURES OK')
"""
        result = subprocess.run([sys.executable, '-c', script], cwd=royal.ROOT,
            env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy',
                 'CHECKMATE_STAGE6_ART': '1'}, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('FOREST NATIVE MAIN / REAL PARRY CAPTURES OK', result.stdout)
