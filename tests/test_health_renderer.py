"""Read-only temporary health UI, checked without opening a Windows GUI."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from board import tile_bounds
from config import WINDOW_HEIGHT, WINDOW_WIDTH
from health_renderer import HealthRenderer


def entity(position=(5, 1), current=3, maximum=3, active=True, last_hit=None):
    return SimpleNamespace(position=position, active=active,
                           health=SimpleNamespace(current_hp=current, max_hp=maximum,
                                                  alive=current > 0,
                                                  last_damage_tick=last_hit))


class HealthRendererTests(unittest.TestCase):
    def setUp(self):
        self.renderer = HealthRenderer()
        self.player = entity()

    def test_labels_use_independent_actual_current_and_maximum_health(self):
        self.player.health.current_hp = 2
        pawns = (entity((1, 6), 1, 4), entity((8, 6), 5, 6))
        with patch.object(self.renderer, '_text') as text:
            self.renderer.draw(Mock(), self.player, pawns, 0)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertEqual(labels, ['PLAYER HP', '2/3', 'PARRY WINDOW',
                                  'SHIFT TO PARRY', '1/4', '5/6'])

    def test_next_render_reflects_health_change_without_cached_example_values(self):
        pawn = entity((1, 6), 3, 3)
        with patch.object(self.renderer, '_text') as text:
            self.renderer.draw(Mock(), self.player, (pawn,), 0)
            self.assertEqual(text.call_args_list[-1].args[1], '3/3')
            pawn.health.current_hp = 1
            self.renderer.draw(Mock(), self.player, (pawn,), 1)
            self.assertEqual(text.call_args_list[-1].args[1], '1/3')

    def test_inactive_dead_pawn_has_no_health_label_or_hit_flash(self):
        dead = entity((1, 6), 0, 3, active=False, last_hit=10)
        canvas = Mock()
        with patch.object(self.renderer, '_text') as text:
            self.renderer.draw(canvas, self.player, (dead,), 10)
        self.assertNotIn('0/3', [call.args[1] for call in text.call_args_list])
        canvas.draw_line.assert_not_called()

    def test_no_real_damage_means_no_hit_flash(self):
        canvas = Mock()
        self.renderer.draw(canvas, self.player, (entity((1, 6)),), 100)
        canvas.draw_line.assert_not_called()

    def test_hit_flash_is_start_inclusive_and_expires_after_six_combat_ticks(self):
        self.player.health.last_damage_tick = 10
        for tick, expected in ((9, 0), (10, 8), (15, 8), (16, 0), (100, 0)):
            with self.subTest(tick=tick):
                canvas = Mock()
                self.renderer.draw(canvas, self.player, (), tick)
                self.assertEqual(canvas.draw_line.call_count, expected)

    def test_pause_or_repeated_render_keeps_identical_feedback_without_mutation(self):
        self.player.health.last_damage_tick = 10
        pawns = (entity((1, 6), 2, 3, last_hit=9), entity((8, 6)))
        snapshot = deepcopy((self.player, pawns))
        first = Mock()
        self.renderer.draw(first, self.player, pawns, 11)
        for _ in range(10):
            canvas = Mock()
            self.renderer.draw(canvas, self.player, pawns, 11)
            self.assertEqual(canvas.mock_calls, first.mock_calls)
        self.assertEqual((self.player, pawns), snapshot)

    def test_dead_player_displays_real_zero_and_input_lock_without_game_over(self):
        self.player.health.current_hp = 0
        self.player.health.alive = False
        self.player.health.last_damage_tick = 10
        canvas = Mock()
        with patch.object(self.renderer, '_text') as text:
            self.renderer.draw(canvas, self.player, (), 10)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertEqual(labels, ['PLAYER HP', '0/3', 'DEAD', 'INPUT LOCKED'])
        canvas.draw_line.assert_not_called()

    def test_each_pawn_flash_stays_inside_its_own_cell_at_every_board_position(self):
        for col in range(10):
            for row in range(10):
                with self.subTest(col=col, row=row):
                    pawn = entity((col, row), last_hit=10)
                    canvas = Mock()
                    self.renderer.draw(canvas, self.player, (pawn,), 10)
                    left, bottom, right, top = tile_bounds(col, row)
                    self.assertEqual(canvas.draw_line.call_count, 8)
                    for call in canvas.draw_line.call_args_list:
                        x1, y1, x2, y2 = call.args[:4]
                        self.assertTrue(left < x1 < right and left < x2 < right)
                        self.assertTrue(bottom < y1 < top and bottom < y2 < top)
                    for call in canvas.draw_rectangle.call_args_list:
                        x1, y1, x2, y2 = call.args[:4]
                        if x1 >= 300:  # Exclude the player's left-margin HUD.
                            self.assertTrue(left <= x1 <= x2 < right)
                            self.assertTrue(bottom <= y1 <= y2 < top)

    def test_pawn_health_label_allocates_no_font_or_texture_resources(self):
        canvas = Mock()
        self.renderer.draw(canvas, self.player, (entity((1, 6), 2, 2),), 0)
        canvas.load_font.assert_not_called()
        canvas.SDL_CreateTextureFromSurface.assert_not_called()
        canvas.SDL_DestroyTexture.assert_not_called()

    def test_all_labels_and_flashes_stay_inside_logical_window(self):
        pawns = tuple(entity((col, row), last_hit=1)
                      for col in range(10) for row in range(10))
        self.player.health.last_damage_tick = 1
        canvas = Mock()
        self.renderer.draw(canvas, self.player, pawns, 1)
        for call in canvas.draw_rectangle.call_args_list + canvas.draw_line.call_args_list:
            x1, y1, x2, y2 = call.args[:4]
            self.assertTrue(all(0 <= x < WINDOW_WIDTH for x in (x1, x2)))
            self.assertTrue(all(0 <= y < WINDOW_HEIGHT for y in (y1, y2)))

    def test_player_health_bar_uses_actual_fraction_and_zero_has_no_fill(self):
        for current, expected_right in ((3, 255), (2, 184), (1, 114), (0, None)):
            with self.subTest(current=current):
                self.player.health.current_hp = current
                self.player.health.alive = current > 0
                canvas = Mock()
                self.renderer.draw(canvas, self.player, (), 0)
                fills = [call.args[:4] for call in canvas.draw_rectangle.call_args_list
                         if call.args[1] == 772 and call.args[4:7] == self.renderer.HEALTH]
                self.assertEqual(fills, [] if expected_right is None
                                 else [(44, 772, expected_right, 778)])


if __name__ == '__main__':
    unittest.main()
