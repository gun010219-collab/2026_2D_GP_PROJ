from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from actor_animation import ActorAnimation
from chapter_art_renderer import LiveArenaArtPath
from main import _new_stage_game
from player_armor import PlayerArmor
from presentation_events import PresentationEvents
from release_game import ReleaseGame
from save_manager import SaveStore
from sprite_atlas import opted_in_catalog
from tests.test_hp_carryover import owned
from tests.test_stage_transition import finish
from tests.test_upgrade_flow import clear
from tools.stage5_art_preview import open_preview
from upgrades import ChapterBuild


class ArmorCacheTests(TestCase):
    def test_tracks_max_hp_and_destroys_each_owned_texture_once(self):
        canvas = Mock()
        images = [SimpleNamespace(texture=object()) for _ in range(2)]
        textures = [image.texture for image in images]
        canvas.load_image.side_effect = images
        with patch('player_armor.SpriteAtlases') as atlases:
            armor = PlayerArmor(canvas, combat_sprites=True)
            self.assertIsNone(armor.select(3))
            first = armor.select(4)
            for _ in range(20):
                self.assertIs(first, armor.select(4))
            self.assertEqual(atlases.call_count, 1)
            self.assertIsNot(first, armor.select(5))
            self.assertIsNone(first.image.texture)
            self.assertIsNone(armor.select(3))
            armor.close()
        self.assertEqual([call.args[0] for call in canvas.SDL_DestroyTexture.call_args_list], textures)
        self.assertEqual(atlases.return_value.close.call_count, 2)

    def test_broken_atlas_uses_tier_mesh_without_retrying_each_frame(self):
        canvas = Mock()
        with patch('player_armor.SpriteCatalog.read', side_effect=ValueError) as read:
            armor = PlayerArmor(canvas, combat_sprites=True)
            with self.assertLogs('player_armor', level='WARNING'):
                appearance = armor.select(5)
            self.assertIsNone(appearance.sprites)
            self.assertIs(armor.select(5), appearance)
            read.assert_called_once()
            armor.close()


class ArmorRenderingTests(TestCase):
    def setUp(self):
        from pico2d import pico2d as canvas

        env = patch.dict('os.environ', {'SDL_VIDEODRIVER': 'dummy', 'CHECKMATE_ATTACK_SPRITES': '1',
                                        'CHECKMATE_SPRITE_MANIFEST': ''})
        env.start()
        self.addCleanup(env.stop)
        open_preview(canvas, capture=True)
        self.addCleanup(self.close_canvas, canvas)
        self.animation = ActorAnimation(player_actions=True, improved=True, articulated=True, sprites=True)
        self.art = LiveArenaArtPath(canvas, default_enabled=True, animation=self.animation,
                                    enlarged=True, player_combat_visual=True, sprite_catalog=opted_in_catalog())
        self.addCleanup(self.art.close)

    @staticmethod
    def close_canvas(canvas):
        canvas.close_canvas()
        canvas.window = canvas.renderer = None

    def draw(self, game, events=None, elapsed=0):
        self.animation.update(game, elapsed, events.drain() if events is not None else ())
        self.assertTrue(self.art.draw(game, {}))
        layout = self.art.path.renderer.actor_layouts[game.player.entity_instance_id]
        self.assertEqual(layout.get('armor_hp', 3), game.player.health.max_hp)
        return layout

    def test_chapter_upgrade_retry_and_same_tier_atlas_reuse(self):
        flow = owned(hp=1)
        self.draw(flow.game)
        for expected_hp, kind in ((4, 'hp'), (4, 'attack'), (5, 'hp'), (6, 'hp')):
            previous = self.art.player_armor.appearance
            already_loaded = self.art.player_armor.max_hp
            flow.choose(clear(flow), kind, _new_stage_game)
            self.draw(flow.game)
            self.assertEqual(flow.game.player.health.max_hp, expected_hp)
            if expected_hp == already_loaded:
                self.assertIs(self.art.player_armor.appearance, previous)
        self.assertEqual(flow.game.player.health.current_hp, 4)
        previous = self.art.player_armor.appearance
        clear(flow)
        flow.enter_next_chapter(_new_stage_game)
        self.draw(flow.game)
        self.assertEqual(flow.game.player.health.current_hp, 6)
        self.assertIs(self.art.player_armor.appearance, previous)
        finish(flow.game, 'dead')
        flow.restart(_new_stage_game)
        self.draw(flow.game)
        self.assertIs(self.art.player_armor.appearance, previous)
        fresh = owned()
        fresh.choose(clear(fresh), 'hp', _new_stage_game)
        self.draw(fresh.game)
        finish(fresh.game, 'dead')
        fresh.restart(_new_stage_game)
        self.draw(fresh.game)
        self.assertIsNone(self.art.player_armor.appearance)

    def test_title_continue_select_and_new_game_use_checkpoint(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'save.json'
            store = SaveStore(path)
            store.remember(replace(store.data, unlocked=(1, 2), cleared=(1,), continue_chapter=2,
                                   entry_builds=(ChapterBuild(), ChapterBuild(hp_level=2))))
            store.flush()
            app = ReleaseGame.__new__(ReleaseGame)
            app.store, app.factory = SaveStore(path), _new_stage_game
            app.front_loop = Mock(side_effect=['continue', 2, 'new', 'exit'])
            app.menu = SimpleNamespace()
            observed = []

            def play(game, flow, **kwargs):
                observed.append((game.chapter, self.draw(game).get('armor_hp', 3)))
                return 'main'

            app.run(play)
        self.assertEqual(observed, [(2, 5), (2, 5), (1, 3)])

    def test_real_attacks_use_tier_atlas_in_every_direction_at_one_current_hp(self):
        for tier in (4, 5, 6):
            for facing in ('up', 'down', 'left', 'right'):
                with self.subTest(tier=tier, facing=facing):
                    game = _new_stage_game(1, stats=ChapterBuild(hp_level=tier - 3).stats, initial_hp=1)
                    events = game.encounter.ledger.presentation = PresentationEvents()
                    self.draw(game, events)
                    if facing == 'down':
                        game.player.move('up')
                    game.player.move(facing)
                    game.resolver.resolve_player_attack(game.combat.request_attack(game.player))
                    atlas = self.art.player_armor.appearance.sprites
                    resolve_frame = atlas.controller.sample
                    with patch.object(atlas.controller, 'sample', wraps=resolve_frame) as sample:
                        self.assertTrue(self.draw(game, events)['sprite_frame'])
                        clip, frame = resolve_frame(*sample.call_args.args, **sample.call_args.kwargs)
                        self.assertEqual(clip.facing, facing)
                        self.assertIs(frame, clip.frames[clip.impact])

    def test_real_pulse_guard_parry_hurt_and_death_use_max_hp(self):
        for tier, hp, delta, result in ((4, 4, 18, 'normal'), (5, 5, 7, 'perfect'),
                                         (6, 4, None, 'hit'), (6, 1, None, 'death')):
            with self.subTest(tier=tier, result=result):
                game = _new_stage_game(25, stats=ChapterBuild(hp_level=tier - 3).stats, initial_hp=hp)
                events = game.encounter.ledger.presentation = PresentationEvents()
                self.draw(game, events)
                if delta is not None:
                    for _ in range(385 - delta):
                        game.advance()
                        self.animation.update(game, 1/60, events.drain())
                    game.resolver.register_parry(game.parry.request(game.combat.tick))
                    self.assertTrue(self.draw(game, events)['sprite_frame'])
                    for _ in range(delta - 1):
                        game.advance()
                        self.animation.update(game, 1/60, events.drain())
                    game.advance()
                else:
                    game.advance(385)
                layout = self.draw(game, events, 1/60)
                self.assertEqual(layout['animation'], f'parry_{result}' if delta else result)
                self.assertEqual(layout.get('sprite_frame', False), delta is not None)
                if result == 'death':
                    self.assertEqual(next(d.max_hp for d in self.animation.deaths if d.kind == 'player'), 6)
