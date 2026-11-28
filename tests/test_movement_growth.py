from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from input_controller import InputController
from movement_vfx import fits_budget
from player import Player
from render_motion import RenderMotion
from stage5_art_renderer import Stage5ArtRenderer
from upgrade_renderer import move_speed_labels
from upgrades import UpgradeKind, UpgradeOption


class MovementGrowthTests(TestCase):
    def test_speed_card_derives_relative_speed_and_gain(self):
        actual = [move_speed_labels(UpgradeOption(UpgradeKind.MOVE, level)) for level in range(3)]
        self.assertEqual(actual, [('100%', '120%', '+20%'), ('120%', '150%', '+25%'), ('150%', None, 'MAX')])

    def test_success_block_and_settle_preserve_interpolation(self):
        for interval in (18, 15, 12):
            with self.subTest(interval=interval):
                player = Player(0, 0)
                input_ = InputController(move_interval_ticks=interval)
                motion, baseline = RenderMotion(improved=True), RenderMotion(improved=True)

                def update(elapsed):
                    motion.update((player,), elapsed, session=1, player_interval=interval)
                    baseline.update((player,), elapsed, session=1)
                    self.assertEqual(motion.positions, baseline.positions)

                update(0)
                self.assertFalse(input_.key_down('left', player, tick=0))
                input_.key_up('left')
                self.assertFalse(input_.key_down('up', player, occupied={(0, 1)}, tick=0))
                input_.key_up('up')
                update(.01)
                self.assertIsNone(motion.player_trail(player))
                self.assertTrue(input_.key_down('right', player, tick=0))
                update(.01)
                update(.03)
                trail = motion.player_trail(player)
                if interval == 18:
                    self.assertIsNone(trail)
                else:
                    self.assertEqual(trail[-1], interval == 12)
                    self.assertGreater(trail[2], 0)
                update(.10)
                self.assertIsNone(motion.player_trail(player))

    def test_attack_snap_and_session_reset_clear_trail(self):
        player = Player(4, 4)
        motion = RenderMotion(improved=True)
        motion.update((player,), 0, session=1)
        player.move('right')
        motion.update((player,), 0, session=1, player_interval=12)
        self.assertIsNotNone(motion.player_trail(player))
        motion.update((player,), .01, session=1, frozen=(player.entity_instance_id,), player_interval=12)
        self.assertIsNone(motion.player_trail(player))
        player.move('right')
        motion.update((player,), 0, session=2, player_interval=12)
        self.assertIsNone(motion.player_trail(player))

    def test_current_armor_texture_and_combat_budget(self):
        renderer = Stage5ArtRenderer.__new__(Stage5ArtRenderer)
        renderer.c = Mock()
        renderer.vfx = SimpleNamespace(manager=SimpleNamespace(effects=[]))
        renderer.animation_motion = Mock()
        renderer.images = {'player': SimpleNamespace(texture='base')}
        renderer.player_armor = Mock()
        with patch('movement_vfx.draw') as draw:
            for tier in (3, 4, 5, 6):
                renderer.player_armor.select.return_value = (
                    None if tier == 3 else SimpleNamespace(image=SimpleNamespace(texture=tier)))
                game = SimpleNamespace(player=Player(1, 1, max_hp=tier, initial_hp=1), playing=True)
                for fast in (False, True):
                    trail = ((342, 72), (426, 72), .5, .5, fast)
                    renderer.animation_motion.player_trail.return_value = trail
                    renderer.draw_movement(game)
                    renderer.player_armor.select.assert_called_with(tier)
                    self.assertEqual(draw.call_args.args[1], 'base' if tier == 3 else tier)
                    self.assertEqual(draw.call_args.args[-1], trail)

            renderer.vfx.manager.effects = [SimpleNamespace(particles=124)]
            self.assertTrue(fits_budget(renderer.vfx.manager, False))
            self.assertFalse(fits_budget(renderer.vfx.manager, True))
            draw.reset_mock()
            renderer.draw_movement(game)
            draw.assert_not_called()
            renderer.vfx.manager.effects = [SimpleNamespace(particles=0)] * 64
            self.assertFalse(fits_budget(renderer.vfx.manager, False))
