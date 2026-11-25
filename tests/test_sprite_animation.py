
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from actor_animation import ActorAnimation
from attack_telegraph import TelegraphRenderer
from chapter_art_renderer import LiveArenaArtPath
from main import _new_stage_game
from player import DIRECTIONS
from presentation_events import PresentationEvents
from sprite_animation import SpriteCatalog, SpriteController
from sprite_atlas import SpriteAtlases, opted_in_catalog
from tools.sprite_animation_qa import test_fixture
from tools.stage5_art_preview import open_preview


def metadata():
    def clip(design, action, facing, impact=2, loop=False):
        return dict(design=design, action=action, facing=facing, atlas='sheet', reference_height=16,
                    impact=impact, loop=loop,
                    frames=[dict(rect=[i*16, 0, 16, 16], foot=[8, 13], visible_top=2, ms=ms)
                            for i, ms in enumerate((20,60,55,80,120,135))])
    return dict(version=1, purpose='test', atlases={'sheet': dict(file='atlas.png', size=[96,16])},
                clips=[*(clip('player','attack',side) for side in DIRECTIONS),
                       *(clip('player',state,side,0,state=='parry_ready')
                         for side in DIRECTIONS for state in ('parry_ready','parry_normal','parry_perfect','parry_failed')),
                       clip('bishop','attack','neutral')])


class SpriteTimelineTests(unittest.TestCase):
    def setUp(self):
        self.catalog = SpriteCatalog.parse(metadata(), Path('.'), allow_test=True)
        self.controller = SpriteController(self.catalog)

    def new(self, stage=1):
        game = _new_stage_game(stage)
        game.encounter.ledger.presentation = PresentationEvents()
        animation = ActorAnimation(improved=True,enemy_attacks=True,player_actions=True,articulated=True,sprites=True)
        self.sync(game,animation)
        return game,animation

    def sync(self,game,animation,elapsed=0,paused=False):
        animation.update(game,elapsed,game.encounter.ledger.presentation.drain(),paused=paused)

    def select(self,game,animation,actor=None):
        actor = actor or game.player
        pose = animation.pose(game,actor,None)
        return self.controller.sample(game,actor,getattr(actor,'kind','player'),animation,pose)

    def attack(self,game,animation,facing):
        if facing == 'down':
            game.player.move('up',occupied=game.encounter.occupied_cells)
        game.player.move(facing,occupied=game.encounter.occupied_cells)
        event = game.combat.request_attack(game.player)
        self.assertIsNotNone(event)
        game.resolver.resolve_player_attack(event)
        self.sync(game,animation)
        return event

    def test_variable_preparation_impact_followthrough_and_end(self):
        clip = self.catalog.clip(1,'player','attack','right','basic')
        self.assertEqual([clip.frames.index(clip.preparation(p)) for p in (0.,.249,.25,.999)],[0,0,1,1])
        self.assertEqual([clip.frames.index(clip.reaction(t)) for t in (0.,.054,.055,.135,.255)],[2,2,3,4,5])
        self.assertIsNone(clip.reaction(.390))
        ready = self.catalog.clip(1,'player','parry_ready','right','basic')
        self.assertIs(ready.reaction(.470),ready.frames[0])

    def test_impact_is_the_accepted_attack_and_facing_does_not_follow_turn(self):
        for facing in DIRECTIONS:
            game,animation = self.new()
            event = self.attack(game,animation,facing)
            self.assertEqual(event.start_tick,game.combat.tick)
            dx,dy = DIRECTIONS[facing]
            self.assertEqual(event.target_cell,(event.origin_cell[0]+dx,event.origin_cell[1]+dy))
            game.player.move(next(side for side in DIRECTIONS if side!=facing),occupied=game.encounter.occupied_cells)
            clip,frame = self.select(game,animation)
            self.assertEqual(clip.facing,facing)
            self.assertIs(frame,clip.frames[clip.impact])
            self.assertEqual(game.combat.attack_state(event),'resolved')

    def test_elapsed_sample_is_identical_at_60_144_180_hz_and_during_pause(self):
        for fps in (60,144,180):
            game,animation = self.new()
            self.attack(game,animation,'right')
            self.sync(game,animation,1/fps,paused=True)
            clip,frame = self.select(game,animation)
            self.assertIs(frame,clip.frames[2])
            # .333s is past the old mesh's .32s swing, inside the last sprite frame.
            for _ in range(fps//3):
                self.sync(game,animation,1/fps)
            self.assertIs(self.select(game,animation)[1],clip.frames[5])
            for _ in range(fps//6):
                self.sync(game,animation,1/fps)
            self.assertIsNone(self.select(game,animation))

    def test_enemy_windup_ends_on_hit_or_cancellation(self):
        for cancel in (False, True):
            game,animation = self.new(12)
            bishop = next(e for e in game.encounter.enemies if e.kind=='bishop')
            while bishop.current_attack is None:
                game.advance()
                self.sync(game,animation,1/60)
            event = bishop.current_attack
            clip,frame = self.select(game,animation,bishop)
            self.assertIs(frame,clip.frames[0])
            game.advance(event.hit_tick - game.combat.tick - 1)
            self.sync(game,animation,1/60)
            self.assertIs(self.select(game,animation,bishop)[1],clip.frames[1])
            if cancel:
                self.assertTrue(game.encounter.ledger.cancel(event))
                self.assertIsNone(self.select(game,animation,bishop))
            game.advance()
            self.sync(game,animation,1/60)
            if cancel:
                self.assertIsNone(self.select(game,animation,bishop))
            else:
                self.assertEqual(game.combat.tick,event.hit_tick)
                self.assertIs(self.select(game,animation,bishop)[1],clip.frames[clip.impact])

    def test_actual_normal_perfect_and_unbound_parry_results(self):
        for delta,expected in ((18,'normal'),(7,'perfect')):
            game,animation = self.new(5)
            rook = next(e for e in game.encounter.enemies if e.kind=='rook')
            while rook.current_attack is None:
                game.advance()
                self.sync(game,animation,1/60)
            hit = rook.current_attack.hit_tick
            game.advance(hit-delta-game.combat.tick)
            game.resolver.register_parry(game.parry.request(game.combat.tick))
            self.sync(game,animation)
            self.assertEqual(self.select(game,animation)[0].action,'parry_ready')
            game.advance(delta)
            self.sync(game,animation)
            self.assertEqual(game.resolver.last_parry_result.status,expected)
            clip,frame = self.select(game,animation)
            self.assertEqual(clip.action,f'parry_{expected}')
            self.assertIs(frame,clip.frames[0])
        game,animation = self.new()
        game.resolver.register_parry(game.parry.request(game.combat.tick))
        self.sync(game,animation)
        self.assertEqual(game.resolver.last_parry_result.status,'unbound')
        self.assertEqual(self.select(game,animation)[0].action,'parry_failed')

    def test_hurt_stun_death_and_stage_change_preempt(self):
        game,animation = self.new()
        event = self.attack(game,animation,'right')
        game.player.health.apply_damage(1,game.combat.tick)
        game.encounter.ledger.presentation.record('hurt',event.key,game.combat.tick,
                                                   game.player.entity_instance_id,None)
        self.sync(game,animation)
        self.assertIsNone(self.select(game,animation))
        game.player.health.apply_damage(game.player.health.current_hp,game.combat.tick)
        game.encounter.ledger.presentation.record('death',event.key,game.combat.tick,
                                                  game.player.entity_instance_id,None)
        self.sync(game,animation)
        self.assertIsNone(self.select(game,animation))
        next_game = _new_stage_game(12)
        self.assertIsNone(self.select(next_game,animation))
        next_game.encounter.ledger.presentation = PresentationEvents()
        self.sync(next_game,animation)
        bishop = next(e for e in next_game.encounter.enemies if e.kind=='bishop')
        while bishop.current_attack is None:
            next_game.advance()
            self.sync(next_game,animation,1/60)
        self.assertIsNotNone(self.select(next_game,animation,bishop))
        bishop.stun_until_tick = next_game.combat.tick+18
        self.assertIsNone(self.select(next_game,animation,bishop))

    def test_metadata_overlap_with_chapter_override_and_invalid_bounds(self):
        data = metadata()
        chapter_clip = dict(data['clips'][0],chapter=3)
        data['clips'].append(chapter_clip)
        catalog = SpriteCatalog.parse(data,Path('.'),allow_test=True)
        self.assertEqual(catalog.clip(3,'player','attack',chapter_clip['facing'],'basic').chapter,3)
        self.assertIsNone(catalog.clip(1,'player','attack',chapter_clip['facing'],'basic').chapter)
        data['clips'][0]['frames'][0]['rect'][0] = 95
        with self.assertRaises(ValueError):
            SpriteCatalog.parse(data,Path('.'),allow_test=True)

    def test_foot_lift_offsets_and_hp(self):
        clip = self.catalog.clip(1,'player','attack','right','basic')
        layout = dict(height=80,foot=(100,170),elevation=18,hp_y=235,top=225)
        frame = clip.frames[0]
        rect,label = frame.placement(layout,clip.reference_height)
        self.assertEqual((rect[0] + frame.foot[0]*5,899-rect[1]-frame.foot[1]*5),(100,188))
        self.assertEqual(label,(100,253))
        self.assertEqual(rect[2:],(80,80))


class SpriteAtlasTests(unittest.TestCase):
    def test_opt_in_catalog_policy_and_missing_or_corrupt_manifest(self):
        with TemporaryDirectory() as directory:
            manifest = Path(directory)/'manifest.json'
            manifest.write_text(json.dumps(metadata()),encoding='utf-8')
            with patch.dict(os.environ,{'CHECKMATE_ATTACK_SPRITES':'0','CHECKMATE_SPRITE_MANIFEST':str(manifest)}):
                self.assertIsNone(opted_in_catalog())
            with patch.dict(os.environ,{'CHECKMATE_ATTACK_SPRITES':'1','CHECKMATE_SPRITE_MANIFEST':str(manifest)}):
                self.assertIsNotNone(opted_in_catalog())
                with self.assertRaises(ValueError):
                    SpriteCatalog.read(manifest)
                manifest.write_text('bad json')
                with self.assertLogs('sprite_atlas',level='WARNING'):
                    self.assertIsNone(opted_in_catalog())
                manifest.unlink()
                with self.assertLogs('sprite_atlas',level='WARNING'):
                    self.assertIsNone(opted_in_catalog())

    def test_native_atlas_lifetime_fallback_and_warning_and_hp_placement(self):
        from pico2d import pico2d as c
        import sdl2 as s

        with TemporaryDirectory() as directory, patch.dict(os.environ,{'SDL_VIDEODRIVER':'dummy'}):
            manifest = test_fixture(Path(directory)/'qa')
            data = json.loads(manifest.read_text())
            data['atlases']['alias'] = data['atlases']['actors']
            data['clips'].append(dict(data['clips'][0],facing='left',atlas='alias'))
            catalog = SpriteCatalog.parse(data,manifest.parent,allow_test=True)
            open_preview(c,capture=True)
            try:
                animation = ActorAnimation(improved=True,enemy_attacks=True,player_actions=True,sprites=True)
                warning = TelegraphRenderer()
                path = LiveArenaArtPath(c,default_enabled=True,animation=animation,sprite_catalog=catalog,
                                       telegraph=warning,player_combat_visual=True)
                try:
                    game = _new_stage_game(24)
                    game.encounter.ledger.presentation = PresentationEvents()
                    game.advance(135)
                    game.player.move('right',occupied=game.encounter.occupied_cells)
                    game.resolver.resolve_player_attack(game.combat.request_attack(game.player))
                    animation.update(game,0,game.encounter.ledger.presentation.drain())
                    assert game.resolver.live_telegraphs(game.combat.tick)
                    with patch.object(SpriteAtlases,'_load',autospec=True,side_effect=SpriteAtlases._load) as load:
                        self.assertTrue(path.draw(game,{}))
                        self.assertTrue(path.draw(game,{}))
                        load.assert_called_once()
                    renderer = path.path.renderer
                    bank = renderer.sprite_atlases
                    self.assertEqual(bank.textures['alias'],bank.textures['actors'])
                    self.assertTrue(renderer.actor_layouts[game.player.entity_instance_id]['sprite_frame'])
                    cells = set(renderer.warning_cells)
                    self.assertTrue(cells)
                    original = s.SDL_RenderCopyF
                    sprite_texture = bank.textures['actors']

                    def fail_atlas(renderer_handle,texture,source,dest):
                        if texture is sprite_texture:
                            return -1
                        return original(renderer_handle,texture,source,dest)

                    with patch('sdl2.SDL_RenderCopyF',side_effect=fail_atlas), self.assertLogs('sprite_atlas'):
                        self.assertTrue(path.draw(game,{}))
                    self.assertEqual(set(renderer.warning_cells),cells)
                    self.assertFalse(bank.textures)
                    self.assertFalse(renderer.animation_failed)
                    self.assertNotIn('sprite_frame',renderer.actor_layouts[game.player.entity_instance_id])
                    replacement = _new_stage_game(24)
                    data['atlases']['actors']['size'][0] -= 1
                    bad = SpriteCatalog.parse(data,manifest.parent,allow_test=True)
                    path.path.sprite_catalog = bad
                    with self.assertLogs('sprite_atlas'):
                        self.assertTrue(path.draw(replacement,{}))
                    self.assertFalse(path.path.renderer.sprite_atlases.textures)
                    atlas = manifest.parent/'atlas.png'
                    atlas.write_text('corrupt')
                    path.path.sprite_catalog = catalog
                    with self.assertLogs('sprite_atlas'):
                        self.assertTrue(path.draw(_new_stage_game(24),{}))
                    self.assertFalse(path.path.renderer.sprite_atlases.textures)
                    atlas.unlink()
                    with self.assertLogs('sprite_atlas'):
                        self.assertTrue(path.draw(_new_stage_game(24),{}))
                    self.assertFalse(path.path.renderer.sprite_atlases.textures)
                finally:
                    path.close()
            finally:
                c.close_canvas()
                c.renderer = c.window = None
