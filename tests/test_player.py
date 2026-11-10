import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from config import cell_center
from player import Player, load_stage1_player


class PlayerTests(unittest.TestCase):
    def test_stage1_spawn_and_screen_center(self):
        p = load_stage1_player()
        self.assertEqual(p.position, (5, 1))
        self.assertEqual(cell_center(p.col, p.row), (762, 156))
        self.assertEqual(p.facing, 'up')

    def test_four_cardinal_directions(self):
        for direction, expected in [('up', (5, 2)), ('down', (5, 0)),
                                    ('left', (4, 1)), ('right', (6, 1))]:
            with self.subTest(direction=direction):
                p = Player(5, 1)
                self.assertTrue(p.move(direction))
                self.assertEqual(p.position, expected)
                self.assertEqual(p.facing, direction)

    def test_sequence_is_deterministic(self):
        for _ in range(2):
            p = Player(5, 1)
            for direction, expected in [('up', (5, 2)), ('right', (6, 2)),
                                        ('down', (6, 1)), ('left', (5, 1))]:
                p.move(direction)
                self.assertEqual(p.position, expected)

    def test_edges_block_position_but_turn_facing(self):
        for col, row, direction in [(0, 4, 'left'), (9, 4, 'right'),
                                    (4, 0, 'down'), (4, 9, 'up')]:
            p = Player(col, row)
            self.assertFalse(p.move(direction))
            self.assertEqual(p.position, (col, row))
            self.assertEqual(p.facing, direction)

    def test_invalid_spawn_and_direction(self):
        for point in [(-1, 0), (10, 0), (0, -1), (0, 10), (True, 1), (1.5, 1), ('5', 1)]:
            with self.subTest(point=point), self.assertRaises(ValueError):
                Player(*point)
        with self.assertRaises(ValueError):
            Player(5, 1, facing='diagonal')
        p = Player(5, 1)
        with self.assertRaises(ValueError):
            p.move('diagonal')
        self.assertEqual(p.position, (5, 1))

    def test_loading_is_independent_of_cwd_and_graphics(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as other:
            script = (f'import sys; sys.path.insert(0, {str(root)!r}); '
                      'from player import load_stage1_player; '
                      'assert load_stage1_player().position == (5,1); '
                      'assert "pico2d" not in sys.modules')
            result = subprocess.run([sys.executable, '-c', script], cwd=other,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_corrupt_or_invalid_stage1_reports_cause(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stages.json'
            with self.assertRaisesRegex(ValueError, 'Cannot load Stage 1'):
                load_stage1_player(path)
            path.write_text('{broken', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Cannot load Stage 1'):
                load_stage1_player(path)
            for data in [[], {}, {'stages': []},
                         {'stages': [{'stage': 1, 'chapter': 1, 'player_spawn': [10, 1]}]},
                         {'stages': [{'stage': 1, 'chapter': 2, 'player_spawn': [5, 1]}]},
                         {'stages': [{'stage': 1, 'chapter': 1, 'player_spawn': [5]}]}]:
                path.write_text(json.dumps(data), encoding='utf-8')
                with self.subTest(data=data), self.assertRaisesRegex(ValueError, 'Stage 1'):
                    load_stage1_player(path)

    def test_valid_alternate_spawn_is_loaded_without_constant(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stage.json'
            path.write_text(json.dumps({'stages': [{'stage': 1, 'chapter': 1,
                                                    'player_spawn': [3, 4]}]}), encoding='utf-8')
            self.assertEqual(load_stage1_player(path).position, (3, 4))
