
"""Production atlas coverage for the shared player and real combat events."""
from dataclasses import replace
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from actor_animation import ActorAnimation, State
from chapter_art_renderer import CHAPTER_PROFILES, LiveArenaArtPath
from main import _new_stage_game
from presentation_events import PresentationEvents
from sprite_animation import SpriteCatalog, SpriteController
from sprite_atlas import DEFAULT_CATALOG
from tools.stage5_art_preview import open_preview


def scene(number):
    game = _new_stage_game(number)
    events = game.encounter.ledger.presentation = PresentationEvents()
    animation = ActorAnimation(improved=True, enemy_attacks=True, player_actions=True,
                               articulated=True, sprites=True)
    animation.update(game,0,())
    return game, events, animation


class PlayerCombatSpritesTests(TestCase):
    def setUp(self):
        self.catalog = SpriteCatalog.read(DEFAULT_CATALOG)
        self.controller = SpriteController(self.catalog)

    def sample(self, game, animation, *, ended=False):
        pose = animation.pose(game,game.player,None)
        return self.controller.sample(game,game.player,'player',animation,pose,include_finished=ended)

    def test_release_and_recovery_follow_four_real_attack_receipts(self):
        for facing in ('right','left','up','down'):
            with self.subTest(facing=facing):
                game,events,anim = scene(1)
                if facing=='down':
                    game.player.move('up')
                game.player.move(facing)
                receipt = game.combat.request_attack(game.player)
                game.resolver.resolve_player_attack(receipt)
                game.player.move('up' if facing!='up' else 'right')
                anim.update(game,0,events.drain())
                for now,index in enumerate([0]*4+[1]*4+[2]*5+[3]*5):
                    clip,frame = self.sample(game,anim)
                    self.assertEqual(clip.facing,receipt.facing)
                    self.assertIs(frame,clip.frames[index],now)
                    game.advance()
                    anim.update(game,1/60,events.drain())
                self.assertEqual(self.sample(game,anim,ended=True),(clip,None))

    def test_guard_and_both_actual_pulse_parry_grades(self):
        for delta,status in ((18,'normal'),(7,'perfect')):
            with self.subTest(status=status):
                game,events,anim = scene(25)
                game.advance(385-delta)
                attempt = game.parry.request(game.combat.tick)
                game.resolver.register_parry(attempt)
                anim.update(game,0,events.drain())
                ready,frame = self.sample(game,anim)
                self.assertEqual((ready.action,ready.facing,len(ready.frames)),('parry_ready','neutral',6))
                self.assertIs(frame,ready.frames[0])
                game.advance(delta)
                anim.update(game,0,events.drain())
                self.assertEqual(game.resolver.parry_result(attempt).status,status)
                clip,frame = self.sample(game,anim)
                self.assertEqual((clip.action,clip.facing,len(clip.frames)),(f'parry_{status}','neutral',6))
                self.assertIs(frame,clip.frames[0])

    def test_unbound_attempt_uses_failed_frames_and_does_not_return_to_guard(self):
        game,events,anim = scene(1)
        game.resolver.register_parry(game.parry.request(game.combat.tick))
        anim.update(game,0,events.drain())
        failure,frame = self.sample(game,anim)
        self.assertEqual(failure.action,'parry_failed')
        self.assertEqual(len(failure.frames),6)
        self.assertIs(frame,failure.frames[0])
        for _ in range(16):
            game.advance()
            anim.update(game,1/60,events.drain())
        self.assertIs(anim.pose(game,game.player,None).state,State.PARRY_READY)
        self.assertEqual(self.sample(game,anim,ended=True),(failure,None))

    def test_all_chapters_keep_projection_anchor_and_use_three_separate_pages(self):
        actions = {('attack',side) for side in ('left','up','right','down')}
        actions.update((action,'neutral') for action in
                       ('parry_ready','parry_normal','parry_perfect','parry_failed'))
        self.assertEqual(len(self.catalog.clips),len(actions))
        self.assertEqual(len(self.catalog.atlases),3)
        for chapter,profile in CHAPTER_PROFILES.items():
            for action,facing in actions:
                clip = self.catalog.clip(chapter,'player',action,facing,'basic')
                for frame in clip.frames:
                    layout = profile.layout('player',4,6)
                    rect,label = frame.placement(layout,clip.reference_height)
                    scale = layout['height']/256
                    self.assertAlmostEqual(rect[0]+frame.foot[0]*scale,layout['foot'][0])
                    self.assertAlmostEqual(899-rect[1]-frame.foot[1]*scale,layout['foot'][1])
                    self.assertGreaterEqual(label[1],layout['hp_y'])

    def test_missing_new_page_keeps_right_available_and_left_uses_mesh(self):
        from pico2d import pico2d as canvas

        atlases = dict(self.catalog.atlases)
        atlases['attacks'] = replace(atlases['attacks'],path=Path('_missing_attack_atlas.png'))
        damaged = replace(self.catalog,atlases=atlases)
        with patch.dict('os.environ',{'SDL_VIDEODRIVER':'dummy'}):
            open_preview(canvas,capture=True)
            try:
                for direction in ('left','right'):
                    game,events,anim = scene(1)
                    game.player.move(direction)
                    game.resolver.resolve_player_attack(game.combat.request_attack(game.player))
                    anim.update(game,0,events.drain())
                    art = LiveArenaArtPath(canvas,default_enabled=True,animation=anim,sprite_catalog=damaged)
                    try:
                        with self.assertLogs('sprite_atlas',level='WARNING'):
                            self.assertTrue(art.draw(game,{}))
                        renderer = art.path.renderer
                        layout = renderer.actor_layouts[game.player.entity_instance_id]
                        self.assertEqual(bool(layout.get('sprite_frame')),direction=='right')
                        self.assertFalse(renderer.animation_failed)
                    finally:
                        art.close()
            finally:
                canvas.close_canvas()
                canvas.window=canvas.renderer=None
