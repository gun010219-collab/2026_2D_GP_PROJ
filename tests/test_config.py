"""Screen geometry tests without importing Pico2D."""
import unittest

import config as c


class ConfigTests(unittest.TestCase):
    def test_window_size(self):
        self.assertEqual((c.WINDOW_WIDTH, c.WINDOW_HEIGHT), (1440, 900))

    def test_board_size(self):
        self.assertEqual((c.BOARD_SIZE, c.TILE_SIZE, c.BOARD_PIXEL_SIZE), (10, 75, 750))
        self.assertEqual(c.BOARD_PIXEL_SIZE, c.BOARD_SIZE * c.TILE_SIZE)

    def test_board_bounds(self):
        self.assertEqual((c.BOARD_LEFT, c.BOARD_BOTTOM), (75, 75))
        self.assertGreaterEqual(c.BOARD_LEFT, 0)
        self.assertGreaterEqual(c.BOARD_BOTTOM, 0)
        self.assertLessEqual(c.BOARD_LEFT + c.BOARD_PIXEL_SIZE, c.WINDOW_WIDTH)
        self.assertLessEqual(c.BOARD_BOTTOM + c.BOARD_PIXEL_SIZE, c.WINDOW_HEIGHT)

    def test_hud_bounds(self):
        self.assertEqual((c.HUD_LEFT, c.HUD_BOTTOM, c.HUD_WIDTH, c.HUD_HEIGHT),
                         (900, 75, 465, 750))
        self.assertGreaterEqual(c.HUD_LEFT, 0)
        self.assertGreaterEqual(c.HUD_BOTTOM, 0)
        self.assertLessEqual(c.HUD_LEFT + c.HUD_WIDTH, c.WINDOW_WIDTH)
        self.assertLessEqual(c.HUD_BOTTOM + c.HUD_HEIGHT, c.WINDOW_HEIGHT)

    def test_board_and_hud_do_not_overlap(self):
        self.assertLessEqual(c.BOARD_LEFT + c.BOARD_PIXEL_SIZE, c.HUD_LEFT)

    def test_all_cell_centers_and_edges(self):
        for col in range(10):
            for row in range(10):
                with self.subTest(col=col, row=row):
                    x, y = c.cell_center(col, row)
                    self.assertEqual((x, y), (112.5 + 75 * col, 112.5 + 75 * row))
                    self.assertGreaterEqual(x - c.TILE_SIZE / 2, 0)
                    self.assertGreaterEqual(y - c.TILE_SIZE / 2, 0)
                    self.assertLessEqual(x + c.TILE_SIZE / 2, c.WINDOW_WIDTH)
                    self.assertLessEqual(y + c.TILE_SIZE / 2, c.WINDOW_HEIGHT)
                    self.assertEqual(int((x - c.BOARD_LEFT) / c.TILE_SIZE), col)
                    self.assertEqual(int((y - c.BOARD_BOTTOM) / c.TILE_SIZE), row)

    def test_row_zero_is_bottom(self):
        self.assertEqual(c.cell_center(0, 0), (112.5, 112.5))
        self.assertEqual(c.cell_center(9, 9), (787.5, 787.5))
        self.assertEqual(c.cell_center(0, 1)[1] - c.cell_center(0, 0)[1], 75)

    def test_invalid_coordinates(self):
        for col, row in [(-1, 0), (10, 0), (0, -1), (0, 10)]:
            with self.subTest(col=col, row=row), self.assertRaises(ValueError):
                c.cell_center(col, row)
        for col, row in [(0.5, 0), (0, '1'), (True, 0)]:
            with self.subTest(col=col, row=row), self.assertRaises(TypeError):
                c.cell_center(col, row)


if __name__ == '__main__':
    unittest.main()
