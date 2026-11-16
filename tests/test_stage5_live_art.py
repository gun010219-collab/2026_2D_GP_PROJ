import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock,patch
import main
from stage5_art_renderer import CAMERA,FILES,ROOT,Stage5ArtPath,Stage5ArtRenderer,Stage5ArtError,cue_kind,pick_event
from tools.stage5_art_preview import make_scene,snapshot


class Stage5LiveArtTests(unittest.TestCase):
    def test_only_stage_five_and_exact_opt_in_enable_assets(self):
        for flag in ('','0','1'):
            with patch.dict(os.environ,{'CHECKMATE_STAGE5_ART':flag}):
                factory=Mock();path=Stage5ArtPath(Mock(),factory)
                for n in (1,4,6,10,25):self.assertFalse(path.draw(main._new_stage_game(n),{}))
                self.assertEqual(path.draw(main._new_stage_game(5),{}),flag=='1')
                self.assertEqual(factory.call_count,int(flag=='1'));path.close()

    def test_session_changes_disable_and_shutdown_close_once_without_reloading_each_frame(self):
        with patch.dict(os.environ,{'CHECKMATE_STAGE5_ART':'1'}):
            factory=Mock();p=Stage5ArtPath(Mock(),factory);g=main._new_stage_game(5)
            for _ in range(10):self.assertTrue(p.draw(g,{}))
            self.assertEqual(factory.call_count,1)
            p.draw(main._new_stage_game(5),{});self.assertEqual(factory.call_count,2)
            p.draw(main._new_stage_game(6),{});p.close();self.assertEqual(factory.return_value.close.call_count,2)

    def test_missing_asset_falls_back_once_and_never_changes_combat(self):
        with patch.dict(os.environ,{'CHECKMATE_STAGE5_ART':'1'}):
            c=Mock();factory=Mock(side_effect=FileNotFoundError('missing'));p=Stage5ArtPath(c,factory)
            scene=make_scene('normal');before=snapshot(scene)
            with self.assertLogs('stage5_art_renderer',level='ERROR'):
                for _ in range(3):self.assertFalse(p.draw(scene.game,{}))
            self.assertEqual(factory.call_count,1);self.assertEqual(snapshot(scene),before)
            self.assertTrue(c.SDL_RenderClear.called)

    def test_draw_failure_closes_partial_frame_and_programming_errors_are_not_hidden(self):
        with patch.dict(os.environ,{'CHECKMATE_STAGE5_ART':'1'}):
            renderer=Mock();renderer.draw.side_effect=Stage5ArtError('device');p=Stage5ArtPath(Mock(),lambda c:renderer)
            with self.assertLogs('stage5_art_renderer',level='ERROR'):self.assertFalse(p.draw(main._new_stage_game(5),{}))
            renderer.close.assert_called_once()
            renderer.draw.side_effect=TypeError('bug');p=Stage5ArtPath(Mock(),lambda c:renderer)
            with self.assertRaises(TypeError):p.draw(main._new_stage_game(5),{})

    def test_all_cells_vertices_picking_and_approved_camera_match(self):
        from tools.themed_arena_review import SIZE_CAMERAS
        self.assertEqual(CAMERA.corners,SIZE_CAMERAS[2].corners)
        for col in range(10):
            for row in range(10):
                x,y=CAMERA.center(col,row);self.assertEqual(pick_event(x,899-y),(col,row))
                self.assertEqual(CAMERA.tile(col,row),SIZE_CAMERAS[2].tile(col,row))
        self.assertIsNone(pick_event(-1,0));self.assertIsNone(CAMERA.pick(*CAMERA.project(10,5)))

    def test_parry_input_is_not_success_and_pulse_resolution_is_not_warning(self):
        from tools.ornate_board_review import parry_window_scene,pulse_phase
        from tools.highend_board_review import resolved_pulse_scene
        self.assertEqual(cue_kind(parry_window_scene().game),'parry_window')
        self.assertEqual(cue_kind(make_scene('parry_perfect').game),'perfect_success')
        self.assertEqual(cue_kind(make_scene('parry_normal').game),'parry_success')
        self.assertEqual(cue_kind(pulse_phase(60).game),'pulse')
        self.assertNotEqual(cue_kind(resolved_pulse_scene().game),'pulse')

    def test_partial_resource_loading_and_repeated_close_release_handles(self):
        c=Mock();c.SDL_SetTextureColorMod.return_value=0
        first=Mock();c.load_image.side_effect=[first,OSError('corrupt')]
        with self.assertRaises(OSError):Stage5ArtRenderer(c)
        self.assertIsNone(first.texture);c.SDL_DestroyTexture.assert_called_once()
        c=Mock();c.SDL_SetTextureColorMod.return_value=0;c.load_image.side_effect=lambda p:Mock()
        r=Stage5ArtRenderer(c);self.assertEqual(c.load_image.call_count,8)
        r.close();r.close();self.assertEqual(c.SDL_DestroyTexture.call_count,8)

    def test_interpolated_feet_depth_labels_and_dead_actor_removal(self):
        from config import cell_center
        from health_renderer import HealthRenderer
        c=Mock();c.SDL_SetTextureColorMod.return_value=0;c.load_image.side_effect=lambda p:Mock()
        r=Stage5ArtRenderer(c);g=main._new_stage_game(5)
        positions={g.player.entity_instance_id:cell_center(5,6)}
        with patch('stage5_art_renderer.polygon'),patch.object(r,'image'),patch.object(HealthRenderer,'_text') as labels:
            r.draw(g,positions)
            foot=next(b for b in r.bounds if b[0]==g.player.entity_instance_id)
            self.assertEqual(foot[1:3],CAMERA.project(5.5,6.25))
            self.assertEqual(r.order[0],g.encounter.enemies[0].entity_instance_id)
            self.assertTrue(any(call.args[1]=='28/28' for call in labels.call_args_list))
            e=g.encounter.enemies[-1];e.health.apply_damage(999,tick=0);g.encounter.deactivate(e.entity_instance_id,tick=0)
            r.draw(g,positions);self.assertNotIn(e.entity_instance_id,r.order)
        r.close()

    def test_boss_replay_then_next_chapter_release_art_using_real_progression_api(self):
        from tools.stage5_play import session
        from tests.test_stage_transition import finish
        g,flow=session();factory=Mock();path=Stage5ArtPath(Mock(),factory)
        with patch.dict(os.environ,{'CHECKMATE_STAGE5_ART':'1'}):
            path.draw(g,{});finish(g,'clear')
            replay,_=flow.restart(main._new_stage_game,lambda stats:None)
            self.assertEqual(replay.stage_number,5);path.draw(replay,{})
            self.assertEqual(factory.call_count,2);finish(replay,'clear')
            next_game,_=flow.enter_next_chapter(main._new_stage_game,lambda stats:None)
            self.assertEqual(next_game.stage_number,6);self.assertFalse(path.draw(next_game,{}))
            self.assertEqual(factory.return_value.close.call_count,2)

    def test_native_live_frames_and_actual_main_loop_without_frozen_scene_constructor(self):
        script=r'''
from unittest.mock import patch
import sdl2 as s
from pico2d import pico2d as c
import main
from stage5_art_renderer import Stage5ArtRenderer
from tools.stage5_art_preview import open_preview,snapshot,Scene
from tools.stage5_play import session
from render_motion import RenderMotion
g,flow=session();open_preview(c,capture=True);r=Stage5ArtRenderer(c);motion=RenderMotion()
try:
    for _ in range(420):
        if g.playing:g.advance()
        motion.update((g.player,*g.encounter.enemies),1/180,session=g.combat.combat_session_id)
        before=snapshot(Scene('live',g));r.draw(g,motion.positions)
        assert snapshot(Scene('live',g))==before
        expected=[tuple(cell) for e in g.encounter.ledger.telegraphs for cell in e.target_cells] if g.playing else []
        assert r.warning_cells==expected
        assert set(r.order)=={e.entity_instance_id for e in (g.player,*g.encounter.enemies) if e.alive and getattr(e,'active',True)}
finally:r.close();c.close_canvas();c.window=c.renderer=None
g,flow=session();count=[0];native_open=lambda w,h:open_preview(c,capture=True)
def events():
    count[0]+=1
    return [] if count[0]<4 else [type('Quit',(),{'type':s.SDL_QUIT})()]
with patch.object(c,'open_canvas',native_open),patch.object(c,'get_events',events),patch.object(main,'sleep'):
    main.run_session(g,flow)
assert count[0]==4
print('LIVE ART NATIVE OK')
'''
        env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','CHECKMATE_STAGE5_ART':'1'}
        result=subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('LIVE ART NATIVE OK',result.stdout)
