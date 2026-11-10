import unittest
from unittest.mock import Mock

from config import cell_center
from player import Player
from player_renderer import PlayerRenderer


class PlayerRendererTests(unittest.TestCase):
    def test_center_matches_cell_center_and_state_unchanged(self):
        p = Player(5, 1)
        canvas = Mock()
        PlayerRenderer().draw(canvas, p)
        self.assertEqual(canvas.draw_circle.call_args_list[0].args[:2], cell_center(5, 1))
        self.assertEqual(p.position, (5, 1))

    def test_all_directions_stay_inside_every_cell(self):
        for col in range(10):
            for row in range(10):
                for facing in ('up', 'down', 'left', 'right'):
                    canvas = Mock()
                    PlayerRenderer().draw(canvas, Player(col, row, facing))
                    x, y = cell_center(col, row)
                    for call in canvas.draw_circle.call_args_list:
                        cx, cy, radius = call.args[:3]
                        self.assertTrue(x - 42 < cx - radius <= cx + radius < x + 42)
                        self.assertTrue(y - 42 < cy - radius <= cy + radius < y + 42)
                    for call in canvas.draw_line.call_args_list + canvas.draw_rectangle.call_args_list:
                        x1, y1, x2, y2 = call.args[:4]
                        self.assertTrue(all(x - 42 < px < x + 42 for px in (x1, x2)))
                        self.assertTrue(all(y - 42 < py < y + 42 for py in (y1, y2)))

    def test_direction_marker_points_toward_facing(self):
        for facing, delta in [('up', (0, 36)), ('down', (0, -36)),
                              ('left', (-36, 0)), ('right', (36, 0))]:
            canvas = Mock()
            PlayerRenderer().draw(canvas, Player(5, 1, facing))
            x, y = cell_center(5, 1)
            tip = canvas.draw_line.call_args_list[-3].args[2:4]
            self.assertEqual(tip, (x + delta[0], y + delta[1]))
