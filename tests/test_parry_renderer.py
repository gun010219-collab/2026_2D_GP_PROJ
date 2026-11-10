import unittest
from unittest.mock import Mock

from config import cell_center
from parry import Parry
from parry_renderer import ParryRenderer
from player import Player


class ParryRendererTests(unittest.TestCase):
    def test_perfect_possible_gold_then_normal_blue_then_inactive(self):
        parry, player = Parry(), Player(5, 1)
        parry.request(10)
        for tick, circle_count, mark_count in [(9, 0, 0), (10, 3, 4), (17, 3, 4),
                                              (18, 3, 0), (27, 3, 0), (28, 0, 0)]:
            with self.subTest(tick=tick):
                canvas = Mock()
                ParryRenderer().draw(canvas, player, parry, tick)
                self.assertEqual(canvas.draw_circle.call_count, circle_count)
                self.assertEqual(canvas.draw_line.call_count, mark_count)
                # No success text, full-screen flash, sound, or blend mutation.
                self.assertTrue(all(call[0] in ('draw_circle', 'draw_line') for call in canvas.mock_calls))
                for call in canvas.draw_circle.call_args_list:
                    self.assertFalse(call.kwargs.get('filled', False))

    def test_halo_follows_player_and_stays_inside_all_cells(self):
        parry = Parry()
        parry.request(0)
        for col in range(10):
            for row in range(10):
                canvas = Mock()
                ParryRenderer().draw(canvas, Player(col, row), parry, 0)
                x, y = cell_center(col, row)
                for call in canvas.draw_circle.call_args_list:
                    cx, cy, radius = call.args[:3]
                    self.assertEqual((cx, cy), (x, y))
                    self.assertTrue(x - 42 < cx - radius <= cx + radius < x + 42)
                    self.assertTrue(y - 42 < cy - radius <= cy + radius < y + 42)
                for call in canvas.draw_line.call_args_list:
                    x1, y1, x2, y2 = call.args[:4]
                    self.assertTrue(all(x - 42 < px < x + 42 for px in (x1, x2)))
                    self.assertTrue(all(y - 42 < py < y + 42 for py in (y1, y2)))

    def test_rendering_does_not_create_or_renew_attempt(self):
        parry = Parry()
        attempt = parry.request(0)
        for _ in range(20):
            ParryRenderer().draw(Mock(), Player(5, 1), parry, 8)
        self.assertIs(parry.last_attempt, attempt)
        self.assertEqual(parry.next_parry_tick, 60)
