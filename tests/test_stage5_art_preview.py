"""Stage5 art review isolation, native capture and once-only resource ownership."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tools.stage5_art_preview import (SCENARIOS, REQUIRED_ASSETS, BODY_SIZE,
                                     ArtResources, SampleRenderer, make_scene, snapshot)


class Stage5ArtPreviewTests(unittest.TestCase):
    def test_revision_two_native_art_capture_loads_all_assets_and_preserves_events(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,'tools/stage5_art_preview.py',
                '--capture-dir',folder,'--benchmark-frames','2'],cwd=root,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((Path(folder)/'capture_manifest.json').read_text())
            self.assertEqual(data['textures_loaded'],7)
            self.assertEqual(len(list(Path(folder).glob('*.png'))),13)
            self.assertEqual(data['board'],[300,30,840,840])
            expected=json.loads((root/'assets/art_samples/stage5/review/capture_manifest.json').read_text())
            self.assertEqual(data['frozen_snapshots'],expected['frozen_snapshots'])
            for name in SCENARIOS:
                raw=(Path(folder)/('art_'+name+'.png')).read_bytes()
                self.assertEqual(struct.unpack('>II',raw[16:24]),(1440,900))

    def test_authentic_warning_parry_and_pulse_snapshots(self):
        normal=make_scene('normal')
        self.assertEqual([(e.kind,e.position,e.health.current_hp) for e in normal.game.encounter.enemies],
                         [('king',(5,9),28),('rook',(2,4),8),('pawn',(1,6),4),('pawn',(8,6),4)])
        warning=make_scene('enemy_warning')
        event=next(e.current_attack for e in warning.game.encounter.enemies if e.kind=='rook')
        self.assertEqual(event.hit_tick-event.start_tick,48)
        self.assertIn(warning.game.player.position,event.target_cells)
        for name,status in (('parry_normal','normal'),('parry_perfect','perfect')):
            scene=make_scene(name);g=scene.game;r=g.resolver.last_parry_result
            self.assertEqual(r.status,status);self.assertEqual(r.tick,g.combat.tick)
            self.assertEqual(g.player.health.current_hp,3)
        pulse=make_scene('pulse');g=pulse.game;ev=g.encounter.pulse.event
        self.assertEqual(len(ev.target_cells),100);self.assertEqual(ev.hit_tick-ev.start_tick,120)
        self.assertEqual(g.encounter.pulse.state,'PULSE_TELEGRAPH')
        attack=make_scene('player_attack')
        self.assertEqual(attack.player_attack.target_cell,(5,2))
        self.assertTrue(all(size<=68 for size in BODY_SIZE.values()))

    def test_original_and_art_draws_preserve_every_snapshot_and_cache_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in REQUIRED_ASSETS:(Path(folder)/(name+'.png')).touch()
            canvas=Mock();resources=ArtResources(canvas,folder)
            self.assertEqual(resources.load_count,6)
            renderer=SampleRenderer(canvas,resources)
            for name in SCENARIOS:
                scene=make_scene(name);before=snapshot(scene)
                for _ in range(2):
                    renderer.draw(scene,art=False);renderer.draw(scene,art=True)
                self.assertEqual(snapshot(scene),before)
            self.assertEqual(canvas.load_image.call_count,6)
            renderer.contact_sheet()
            self.assertEqual(canvas.load_image.call_count,6)
            resources.close();self.assertEqual(resources.images,{})

    def test_missing_assets_fail_before_partial_resource_load(self):
        with tempfile.TemporaryDirectory() as folder:
            canvas=Mock()
            with self.assertRaisesRegex(FileNotFoundError,'baseline-only'):ArtResources(canvas,folder)
            canvas.load_image.assert_not_called()

    def test_native_sdl_original_capture_png_geometry_and_clean_shutdown(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,'tools/stage5_art_preview.py','--baseline-only',
                '--capture-dir',folder,'--benchmark-frames','2'],cwd=root,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            manifest=json.loads((Path(folder)/'capture_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['board'],[300,30,840,840]);self.assertEqual(manifest['tile'],84)
            self.assertEqual(manifest['textures_loaded'],0)
            self.assertEqual([r['scenario'] for r in manifest['frozen_snapshots']],list(SCENARIOS))
            for name in SCENARIOS:
                data=(Path(folder)/('original_'+name+'.png')).read_bytes()
                self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
                self.assertEqual(struct.unpack('>II',data[16:24]),(1440,900))

    def test_art_parry_label_uses_actual_success_and_stays_below_king_hud(self):
        resources=SimpleNamespace(images={name:Mock() for name in REQUIRED_ASSETS})
        renderer=SampleRenderer(Mock(),resources)
        from health_renderer import HealthRenderer
        for name,expected in (('normal',None),('player_attack',None),
                              ('parry_normal','PARRY SUCCESS'),('parry_perfect','PERFECT PARRY')):
            scene=make_scene(name)
            with patch.object(HealthRenderer,'_text') as text:
                renderer.draw(scene,art=True)
            labels=[call.args[1] for call in text.call_args_list if call.args[3]==505]
            self.assertEqual(labels,[] if expected is None else [expected])
            with patch.object(HealthRenderer,'_text') as text:
                renderer.draw(scene,art=False)
            self.assertFalse(any(call.args[3]==505 for call in text.call_args_list))

    def test_preview_settings_f11_escape_routing_without_combat_advance(self):
        from pico2d import pico2d as canvas
        import tools.stage5_art_preview as preview
        events=iter([
            [SimpleNamespace(type=canvas.SDL_MOUSEBUTTONDOWN,button=canvas.SDL_BUTTON_LEFT,x=1295,y=41)],
            [SimpleNamespace(type=canvas.SDL_KEYDOWN,key=canvas.SDLK_F11)],
            [SimpleNamespace(type=canvas.SDL_MOUSEBUTTONDOWN,button=canvas.SDL_BUTTON_LEFT,x=720,y=427)],
            [SimpleNamespace(type=canvas.SDL_KEYDOWN,key=canvas.SDLK_ESCAPE)],
            [SimpleNamespace(type=canvas.SDL_KEYDOWN,key=canvas.SDLK_ESCAPE)]])
        states=[]
        args=SimpleNamespace(capture_dir=None,baseline_only=True,assets=Path('.'),benchmark_frames=1)
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer') as settings,patch.object(preview,'SampleRenderer') as draw, \
             patch.object(canvas,'SDL_SetWindowTitle'),patch.object(canvas,'hide_lattice'), \
             patch.object(canvas,'get_events',side_effect=lambda:next(events)), \
             patch.object(canvas,'update_canvas'),patch.object(canvas,'close_canvas') as close, \
             patch.object(canvas,'window',object(),create=True),patch.object(canvas,'renderer',object(),create=True),patch.object(preview,'sleep'):
            settings.return_value.draw.side_effect=lambda menu,d:states.append(menu.is_open)
            preview.run(args)
            self.assertEqual(display.return_value.toggle.call_count,2)
            self.assertEqual(states,[True,True,True,False,False])
            self.assertEqual(draw.return_value.draw.call_count,5)
            close.assert_called_once_with();settings.return_value.close.assert_called_once_with()
