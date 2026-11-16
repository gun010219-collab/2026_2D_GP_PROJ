"""Display-only scaling preserves footprints, combat and renderer lifetimes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
import stage5_art_renderer as art
import main
from config import cell_center
from render_motion import RenderMotion
from tools.stage5_art_preview import make_scene,snapshot


class Stage5EnemySizeTests(unittest.TestCase):
    def test_candidates_uniform_ratio_anchoring_and_hp_clearance_all_rows(self):
        self.assertEqual(art.ENEMY_SCALE,{'pawn':1.16,'rook':1.11,'king':1.08})
        for kind in ('pawn','rook','king','player'):
            for row in (0,4,6,9,3.25):
                layout=art.actor_layout(kind,4.375,row)
                old=art.BASE_SIZE[kind]*art.CAMERA.sprite_scale*(1.10-.23*row/10)
                self.assertAlmostEqual(layout['height']/old,art.ENEMY_SCALE.get(kind,1))
                self.assertEqual(layout['foot'],art.CAMERA.project(4.875,row+.25))
                self.assertAlmostEqual(layout['center'][1]-layout['height']*(.5-18/256),layout['foot'][1])
                self.assertAlmostEqual(layout['hp_y']-3-layout['top'],art.HP_OFFSET[kind]-3)
                self.assertGreaterEqual(layout['hp_y']-3-layout['top'],2)

    def test_scale_does_not_change_readonly_state_warning_cells_parry_or_depth(self):
        c=Mock();c.SDL_SetTextureColorMod.return_value=0;c.load_image.side_effect=lambda p:Mock()
        renderer=art.Stage5ArtRenderer(c)
        try:
            for name in ('normal','player_attack','enemy_warning','parry_normal','parry_perfect','pulse'):
                scene=make_scene(name);before=snapshot(scene);g=scene.game
                with patch.object(art,'polygon'),patch.object(renderer,'image') as draw:
                    renderer.draw(g,{})
                    first=(renderer.order[:],renderer.warning_cells[:],renderer.cue)
                    old_feet={k:v['foot'] for k,v in renderer.actor_layouts.items()}
                    for call in draw.call_args_list:
                        if call.args[0] in art.BASE_SIZE:self.assertEqual(call.args[3],call.args[4])
                    with patch.dict(art.ENEMY_SCALE,{k:1 for k in art.ENEMY_SCALE}):renderer.draw(g,{})
                    self.assertEqual(first,(renderer.order,renderer.warning_cells,renderer.cue))
                    self.assertEqual(old_feet,{k:v['foot'] for k,v in renderer.actor_layouts.items()})
                self.assertEqual(snapshot(scene),before)
            self.assertEqual(c.load_image.call_count,8)
        finally:renderer.close()
        self.assertEqual(c.SDL_DestroyTexture.call_count,8)

    def test_interpolated_and_settled_feet_are_identical_before_after_scale(self):
        g=main._new_stage_game(5);e=g.encounter.enemies[1];motion=RenderMotion()
        motion.update((e,),0,session='size-test');e.col+=1
        for elapsed in (0,.025,.05,.1):
            motion.update((e,),elapsed,session='size-test');x,y=motion.positions[e.entity_instance_id]
            u=(x-300)/84-.5;v=(y-30)/84-.5
            a=art.actor_layout(e.kind,u,v)
            with patch.dict(art.ENEMY_SCALE,{'rook':1}):b=art.actor_layout(e.kind,u,v)
            self.assertEqual(a['foot'],b['foot'])
        self.assertEqual(motion.positions[e.entity_instance_id],cell_center(*e.position))

    def test_all_other_stages_and_legacy_mode_never_construct_new_renderer(self):
        factory=Mock();p=art.Stage5ArtPath(Mock(),factory)
        with patch.dict(os.environ,{'CHECKMATE_STAGE5_ART':'1'}):
            for n in range(1,26):
                if n!=5:self.assertFalse(p.draw(main._new_stage_game(n),{}))
        with patch.dict(os.environ,{'CHECKMATE_STAGE5_ART':'0'}):self.assertFalse(p.draw(main._new_stage_game(5),{}))
        factory.assert_not_called()

    def test_native_same_state_capture_and_no_cropped_rear_labels(self):
        from tests.test_aligned_board_review import rgba
        with tempfile.TemporaryDirectory() as d:
            run=subprocess.run([sys.executable,'tools/capture_stage5_scale.py','--capture-dir',d],cwd=art.ROOT,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=60)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            data=json.loads((Path(d)/'capture_manifest.json').read_text())['captures']
            self.assertEqual(len(data),8)
            for old,new in zip(data[::2],data[1::2]):
                self.assertEqual((old['tick'],old['state'],old['cue'],old['warning_cells']),(new['tick'],new['state'],new['cue'],new['warning_cells']))
                self.assertTrue(rgba(Path(d)/new['file'])[1])
                for key,layout in new['layouts'].items():
                    self.assertEqual(layout['foot'],old['layouts'][key]['foot'])
                    self.assertLess(layout['hp_y']+13,900)
