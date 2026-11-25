import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from arena_art_common import ArenaArtError, CAMERA
from attack_vfx import CRIMSON, LAYERED_STYLES, STYLES, projected_beams
from combat_vfx import CombatVFX, Effect
from combat_vfx_renderer import VFXRenderer
from layered_attack_vfx import bishop_cells, beam, draw, material
from queen_behavior import queen_ray_targets
from tools.make_vfx_atlas import atlas_png
from vfx_atlas import ATLAS, TILES, VFXAtlas


class LayeredVFXTests(unittest.TestCase):
    def test_atlas_asset_reproduces_with_matching_tile_order(self):
        metadata = json.loads(ATLAS.with_name('manifest.json').read_text())
        png = ATLAS.read_bytes()
        self.assertEqual(png, atlas_png())
        self.assertEqual(metadata['tiles'], list(TILES))
        self.assertEqual(metadata['sha256'], hashlib.sha256(png).hexdigest())

    def test_materials_differ_and_gothic_keeps_crimson_and_black(self):
        theme = LAYERED_STYLES[5]
        self.assertEqual((theme.color,CRIMSON,theme.edge,theme.shadow),
                         ((237,24,43),(120,11,22),(255,208,208),(8,8,10)))
        self.assertEqual(STYLES[5].material,'void')
        tiles = set()
        for style in LAYERED_STYLES.values():
            atlas = Mock()
            material(atlas,100,100,20,.3,.7,style)
            tiles.add(tuple(call.args[0] for call in atlas.stamp.call_args_list))
        self.assertEqual(len(tiles),5)

    def test_moving_beam_stays_in_its_own_real_ray_and_leaves_holes(self):
        origin = (5,5)
        cells = queen_ray_targets(origin)
        fx = Effect('queen_fire',(),origin,origin,cells,0,1,0,0,0)
        rays = projected_beams(origin,cells)
        self.assertEqual(len(rays),8)
        for t in (.1,.35,.59):
            atlas = Mock()
            beam(atlas,fx,t,LAYERED_STYLES[5])
            for i,(start,end) in enumerate(rays):
                calls = atlas.quad.call_args_list[i*4:i*4+4]
                self.assertEqual([c.args[0] for c in calls],['smoke','ribbon','ribbon','ribbon'])
                self.assertEqual([c.args[1:3] for c in calls[:3]],[(start,end)]*3)
                for point in calls[3].args[1:3]:
                    self.assertIn(CAMERA.pick(*point),cells)
                    self.assertNotEqual(CAMERA.pick(*point),origin)

    def test_bishop_decorations_and_land_effect_use_receipt_cells(self):
        cells = tuple((x,y) for x in range(10) for y in range(10) if (x+y)%2==0)
        fx = Effect('bishop_cast',(),(4,4),(4,4),cells,0,1,0,0,0)
        atlas = Mock()
        bishop_cells(atlas,fx,.24,LAYERED_STYLES[3])
        self.assertGreater(atlas.stamp.call_count,1)
        self.assertTrue(all(CAMERA.pick(*call.args[1:3]) in cells
                            for call in atlas.stamp.call_args_list))
        fx = Effect('knight_land',(),(4,4),(6,5),((6,5),),0,1,0,0,0)
        atlas.reset_mock()
        draw(atlas,'ground',fx,.2,.2,LAYERED_STYLES[3],.2)
        atlas.stamp.assert_not_called()
        fx.landed = .19
        draw(atlas,'ground',fx,.2,.2,LAYERED_STYLES[3],.2)
        self.assertTrue(any(call.args[1:3] == CAMERA.center(6,5)
                            for call in atlas.stamp.call_args_list))

    @patch('vfx_atlas.s.SDL_SetTextureBlendMode',return_value=0)
    def test_atlas_is_loaded_once_has_fixed_budget_and_releases_once(self, blend):
        canvas = Mock()
        texture = object()
        canvas.load_image.return_value = SimpleNamespace(w=256,h=128,texture=texture)
        atlas = VFXAtlas()
        self.assertTrue(atlas.open(canvas))
        self.assertTrue(atlas.open(canvas))
        for _ in range(250):
            atlas.quad('halo',(1,2),(30,5),14,(255,201,170),.7)
        self.assertEqual(atlas.count,192*6)
        canvas.load_image.assert_called_once()
        blend.assert_called_once()
        atlas.close()
        atlas.close()
        canvas.SDL_DestroyTexture.assert_called_once_with(texture)

    def test_atlas_error_preserves_geometry_and_does_not_retry(self):
        manager = CombatVFX(layered=True)
        manager.effects = [Effect('pawn_thrust',(),(3,3),(4,3),((4,3),),0,1,0,0,0)]
        vfx = VFXRenderer(manager)
        canvas = SimpleNamespace(renderer=None,SDL_DestroyTexture=Mock())
        game = SimpleNamespace(chapter=5,combat=SimpleNamespace(tick=12))
        vfx.atlas.canvas = canvas
        vfx.atlas.image = SimpleNamespace(texture=object())
        with patch.object(vfx.atlas,'open',side_effect=ArenaArtError('injected')) as opened, \
             patch('combat_vfx_renderer.s.SDL_GetRenderDrawBlendMode',return_value=0), \
             patch('combat_vfx_renderer.s.SDL_SetRenderDrawBlendMode',return_value=0), \
             patch.object(vfx.mesh,'flush') as flush, self.assertLogs('combat_vfx_renderer'):
            vfx.draw('front',canvas,game)
            vfx.draw('front',canvas,game)
        self.assertTrue(vfx.atlas.failed)
        self.assertFalse(manager.failed)
        opened.assert_called_once_with(canvas)
        self.assertEqual(flush.call_count,2)
        canvas.SDL_DestroyTexture.assert_called_once()
