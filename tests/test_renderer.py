"""Drawing-contract tests using recorded calls, without a real window."""
import unittest
from unittest.mock import Mock

from board import is_light_tile, iter_tiles, tile_bounds
from chapter_themes import get_theme
from renderer import BoardRenderer


class RendererTests(unittest.TestCase):
    def test_every_tile_fills_exactly_seventy_five_pixels(self):
        canvas = Mock()
        BoardRenderer().draw(canvas)
        calls = canvas.draw_rectangle.call_args_list
        for cell in iter_tiles():
            left, bottom, right, top = tile_bounds(*cell)
            color = get_theme(1).tile_light if is_light_tile(*cell) else get_theme(1).tile_dark
            matching = [call for call in calls if call.args == (left, bottom, right - 1, top - 1, *color)]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0].kwargs, {'filled': True})

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
