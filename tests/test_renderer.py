"""Drawing-contract tests using recorded calls, without a real window."""
import unittest
from unittest.mock import Mock

from board import is_light_tile, iter_tiles, tile_bounds
from chapter_themes import get_theme
from renderer import BoardRenderer


class RendererTests(unittest.TestCase):
    def test_every_tile_fills_exactly_eighty_four_pixels(self):
        canvas = Mock()
        BoardRenderer().draw(canvas)
        calls = canvas.draw_rectangle.call_args_list
        for cell in iter_tiles():
            left, bottom, right, top = tile_bounds(*cell)
            color = get_theme(1).tile_light if is_light_tile(*cell) else get_theme(1).tile_dark
            matching = [call for call in calls if call.args == (left, bottom, right - 1, top - 1, *color)]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0].kwargs, {'filled': True})
            x1, y1, x2, y2 = matching[0].args[:4]
            self.assertEqual((x2 - x1 + 1, y2 - y1 + 1), (84, 84))

    def test_all_themes_render_inside_window(self):
        for chapter in range(1, 6):
            with self.subTest(chapter=chapter):
                canvas = Mock()
                BoardRenderer(chapter).draw(canvas)
                for call in canvas.draw_rectangle.call_args_list + canvas.draw_line.call_args_list:
                    x1, y1, x2, y2 = call.args[:4]
                    self.assertTrue(all(0 <= x < 1440 for x in (x1, x2)))
                    self.assertTrue(all(0 <= y < 900 for y in (y1, y2)))

    def test_repeated_frames_are_deterministic(self):
        renderer = BoardRenderer()
        first, second = Mock(), Mock()
        renderer.draw(first)
        renderer.draw(second)
        self.assertEqual(first.mock_calls, second.mock_calls)

    def test_invalid_chapter_is_rejected(self):
        with self.assertRaises(ValueError):
            BoardRenderer(6)

    def test_fixed_hud_removed_and_side_margins_clear(self):
        import config as c
        for chapter in range(1, 6):
            canvas = Mock()
            BoardRenderer(chapter).draw(canvas)
            for call in canvas.draw_rectangle.call_args_list:
                bounds = call.args[:4]
                self.assertNotEqual(bounds, (900, 75, 1364, 824))
                if bounds != (0, 0, c.WINDOW_WIDTH - 1, c.WINDOW_HEIGHT - 1):
                    self.assertTrue(c.BOARD_LEFT - 24 <= bounds[0] <= bounds[2] < c.BOARD_RIGHT + 28)
                    self.assertTrue(c.BOARD_BOTTOM - 27 <= bounds[1] <= bounds[3] < c.BOARD_TOP + 20)

    def test_settings_render_rect_matches_click_rect(self):
        from settings_menu import SETTINGS_BUTTON
        from settings_renderer import SettingsRenderer
        ui = object.__new__(SettingsRenderer)
        ui.canvas = Mock()
        ui._label = Mock()
        ui._button(SETTINGS_BUTTON, 'SETTINGS')
        x1, y1, x2, y2 = ui.canvas.draw_rectangle.call_args_list[0].args[:4]
        self.assertEqual((x1, y1, x2 + 1, y2 + 1),
                         (SETTINGS_BUTTON.left, SETTINGS_BUTTON.bottom,
                          SETTINGS_BUTTON.left + SETTINGS_BUTTON.width,
                          SETTINGS_BUTTON.bottom + SETTINGS_BUTTON.height))
        self.assertTrue(SETTINGS_BUTTON.contains((x1, y1)))
        self.assertTrue(SETTINGS_BUTTON.contains((x2, y2)))
