
"""Regression checks for the shipping right attack and its A3D fallback."""
import json
import os
from unittest import TestCase
from unittest.mock import patch

from actor_animation import ActorAnimation, State
from chapter_art_renderer import CHAPTER_PROFILES
from main import _new_stage_game
from presentation_events import PresentationEvents
from sprite_animation import SpriteCatalog, SpriteController
from sprite_atlas import DEFAULT_CATALOG, opted_in_catalog


class PlayerRightSpriteTests(TestCase):
    def setUp(self):
        self.catalog = SpriteCatalog.read(DEFAULT_CATALOG)
        self.right_only = SpriteCatalog.read(DEFAULT_CATALOG.with_name('manifest_right_only.json'))

    def test_production_catalog_is_default_and_mesh_mode_can_be_forced(self):
        with patch.dict(os.environ, {'CHECKMATE_SPRITE_MANIFEST': 'ignored.json'}, clear=True):
            self.assertEqual(opted_in_catalog(),self.catalog)
        with patch.dict(os.environ, {'CHECKMATE_ATTACK_SPRITES': '0'}, clear=True):
            self.assertIsNone(opted_in_catalog())
        data = json.loads(DEFAULT_CATALOG.read_text(encoding='utf-8'))
        self.assertEqual(data['purpose'],'production')
        self.assertEqual(sum(clip['facing']=='right' for clip in data['clips']),1)
        self.assertEqual(self.catalog.clip(1,'player','attack','right','basic'),
                         self.right_only.clip(1,'player','attack','right','basic'))
        self.assertEqual(self.catalog.atlases['actors'],self.right_only.atlases['actors'])

    def test_visual_timing_and_reference_pixel_scale_in_every_chapter(self):
        timeline = [0]*4 + [1]*4 + [2]*5 + [3]*5
        for chapter, profile in CHAPTER_PROFILES.items():
            clip = self.catalog.clip(chapter,'player','attack','right','basic')
            self.assertEqual((clip.reference_height,clip.impact),(256,0))
            self.assertEqual([clip.frames.index(clip.reaction(tick/60)) for tick in range(18)],timeline)
            self.assertIsNone(clip.reaction(18/60))
            for row in (0,9):
                layout = profile.layout('player',5,row)
                for frame in clip.frames:
                    self.assertEqual((frame.rect[2:],frame.foot),((384,384),(192,302)))
                    rect,label = frame.placement(layout,clip.reference_height)
                    scale = layout['height']/256
                    self.assertAlmostEqual(rect[2],384*scale)
                    self.assertAlmostEqual(rect[0]+192*scale,layout['foot'][0])
                    self.assertAlmostEqual(899-rect[1]-302*scale,layout['foot'][1])
                    self.assertEqual(label,(layout['foot'][0],layout['hp_y']))

    def test_real_receipt_direction_and_return_before_mesh_cue_ends(self):
        for facing in ('right','left','up','down'):
            game = _new_stage_game(1)
            game.encounter.ledger.presentation = PresentationEvents()
            anim = ActorAnimation(improved=True, player_actions=True, articulated=True, sprites=True)
            anim.update(game,0,())
            if facing=='down':
                game.player.move('up')
            game.player.move(facing)
            attack = game.combat.request_attack(game.player)
            game.resolver.resolve_player_attack(attack)
            anim.update(game,0,game.encounter.ledger.presentation.drain())
            game.player.move('up' if facing!='up' else 'right')
            controller = SpriteController(self.right_only)
            pose = anim.pose(game,game.player,None)
            sample = controller.sample(game,game.player,'player',anim,pose)
            if facing!='right':
                self.assertIsNone(sample)
                continue
            self.assertEqual(attack.facing,'right')
            self.assertIs(sample[1],sample[0].frames[0])
            for _ in range(18):
                game.advance()
                anim.update(game,1/60,game.encounter.ledger.presentation.drain())
            pose = anim.pose(game,game.player,None)
            self.assertIs(pose.state,State.ATTACK)  # the old cue lasts 0.32s
            finished = controller.sample(game,game.player,'player',anim,pose,include_finished=True)
            self.assertEqual(finished,(sample[0],None))
            self.assertIs(anim.locomotion_pose(game,game.player,None).state,State.IDLE)
