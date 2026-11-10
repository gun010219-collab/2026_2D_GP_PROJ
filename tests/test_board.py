"""Board geometry independent of graphics and occupancy rules."""
from collections import Counter
import unittest

import board
import config as c


class BoardTests(unittest.TestCase):
    def test_one_hundred_distinct_tiles(self):
        tiles = list(board.iter_tiles())
        self.assertEqual(len(tiles), 100)
        self.assertEqual(len(set(tiles)), 100)
        self.assertEqual(tiles[0], (0, 0))
        self.assertEqual(tiles[-1], (9, 9))

    def test_fifty_fifty_colors_and_alternation(self):
        self.assertEqual(Counter(board.is_light_tile(*cell) for cell in board.iter_tiles()),
                         {False: 50, True: 50})
        self.assertFalse(board.is_light_tile(0, 0))
        for col, row in board.iter_tiles():
            if col < 9:
                self.assertNotEqual(board.is_light_tile(col, row), board.is_light_tile(col + 1, row))
            if row < 9:
                self.assertNotEqual(board.is_light_tile(col, row), board.is_light_tile(col, row + 1))

    def test_bounds_and_center_round_trip_for_every_tile(self):
        for cell in board.iter_tiles():
            with self.subTest(cell=cell):
                left, bottom, right, top = board.tile_bounds(*cell)
                self.assertEqual((right - left, top - bottom), (84, 84))
                self.assertTrue(c.BOARD_LEFT <= left < right <= c.BOARD_RIGHT)
                self.assertTrue(c.BOARD_BOTTOM <= bottom < top <= c.BOARD_TOP)
                self.assertEqual(board.cell_center(*cell), ((left + right) / 2, (bottom + top) / 2))
                self.assertEqual(board.screen_to_cell(*board.cell_center(*cell)), cell)
                self.assertEqual(board.screen_to_cell(left, bottom), cell)
                self.assertEqual(board.screen_to_cell(right - 0.01, top - 0.01), cell)

    def test_half_open_board_edges(self):
        self.assertEqual(board.screen_to_cell(300, 30), (0, 0))
        self.assertEqual(board.screen_to_cell(1139.99, 869.99), (9, 9))
        self.assertEqual(board.screen_to_cell(384, 114), (1, 1))
        for point in [(299.99, 30), (300, 29.99), (1140, 30), (300, 870),
                      (-1, -1), (1440, 900), (float('nan'), 30), (300, float('inf'))]:
            with self.subTest(point=point):
                self.assertIsNone(board.screen_to_cell(*point))

    def test_invalid_grid_coordinates(self):
        for cell in [(-1, 0), (10, 0), (0, -1), (0, 10), (True, 0), (1.5, 0)]:
            with self.subTest(cell=cell):
                self.assertFalse(board.in_bounds(*cell))
                for function in (board.tile_bounds, board.is_light_tile):
                    with self.assertRaises((TypeError, ValueError)):
                        function(*cell)

    def test_tiles_join_without_gaps_or_overlap(self):
        for col, row in board.iter_tiles():
            left, bottom, right, top = board.tile_bounds(col, row)
            if col < c.BOARD_SIZE - 1:
                self.assertEqual(right, board.tile_bounds(col + 1, row)[0])
            if row < c.BOARD_SIZE - 1:
                self.assertEqual(top, board.tile_bounds(col, row + 1)[1])
