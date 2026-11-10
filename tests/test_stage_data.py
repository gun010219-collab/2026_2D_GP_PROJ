"""CHECKMATE stage baseline and rejection tests; no GUI dependency."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validate_stage_data import validate


class StageDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads((ROOT / 'stage_data.json').read_text(encoding='utf-8'))

    def setUp(self):
        self.data = copy.deepcopy(self.baseline)

    def test_complete_baseline(self):
        self.assertEqual(validate(self.data), 25)
        self.assertEqual(self.data['board_size'], 10)
        self.assertEqual([s['stage'] for s in self.data['stages']], list(range(1, 26)))

    def test_distinct_in_bounds_spawns(self):
        for stage in self.data['stages']:
            with self.subTest(stage=stage['stage']):
                positions = [tuple(stage['player_spawn'])]
                positions += [(e['col'], e['row']) for e in stage['enemies']]
                self.assertEqual(len(positions), len(set(positions)))
                self.assertTrue(all(0 <= c < 10 and 0 <= r < 10 for c, r in positions))

    def test_boss_stages_and_hp(self):
        bosses = {s['stage']: s['boss_hp'] for s in self.data['stages'] if s['boss']}
        self.assertEqual(bosses, {5: 8, 10: 10, 15: 12, 20: 14, 25: 16})
        for stage in self.data['stages']:
            kings = [e for e in stage['enemies'] if e['type'] == 'king']
            self.assertEqual(len(kings), int(stage['boss']))
            if not stage['boss']:
                self.assertIsNone(stage['boss_hp'])

    def test_invalid_top_level_values(self):
        for field, value in [('board_size', 9), ('stages', self.baseline['stages'][:-1])]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.baseline)
                data[field] = value
                with self.assertRaises(AssertionError):
                    validate(data)

    def test_invalid_stage_metadata(self):
        for field, value in [('stage', 2), ('chapter', 2), ('boss', True),
                             ('boss_hp', 8), ('player_spawn', [0, 0])]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.baseline)
                data['stages'][0][field] = value
                with self.assertRaises(AssertionError):
                    validate(data)

    def test_wrong_boss_hp(self):
        for index in [4, 9, 14, 19, 24]:
            with self.subTest(stage=index + 1):
                data = copy.deepcopy(self.baseline)
                data['stages'][index]['boss_hp'] += 1
                with self.assertRaises(AssertionError):
                    validate(data)

    def test_duplicate_id_or_position(self):
        for fields in [('id',), ('col', 'row')]:
            with self.subTest(fields=fields):
                data = copy.deepcopy(self.baseline)
                first, second = data['stages'][0]['enemies']
                for field in fields:
                    second[field] = first[field]
                with self.assertRaises(AssertionError):
                    validate(data)

    def test_player_enemy_overlap(self):
        enemy = self.data['stages'][0]['enemies'][0]
        enemy['col'], enemy['row'] = self.data['stages'][0]['player_spawn']
        with self.assertRaises(AssertionError):
            validate(self.data)

    def test_invalid_enemy_fields(self):
        cases = [('col', -1), ('col', 10), ('row', -1), ('row', 10),
                 ('col', 1.5), ('type', 'queen'), ('initial_delay', -0.1),
                 ('initial_delay', 10.1), ('forward', [0, 1])]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.baseline)
                data['stages'][0]['enemies'][0][field] = value
                with self.assertRaises(AssertionError):
                    validate(data)

    def test_too_few_or_too_many_enemies(self):
        enemies = self.baseline['stages'][0]['enemies']
        for replacement in [enemies[:1], enemies * 5]:
            with self.subTest(count=len(replacement)):
                self.data['stages'][0]['enemies'] = replacement
                with self.assertRaises(AssertionError):
                    validate(self.data)

    def test_same_color_bishops(self):
        bishops = [e for e in self.data['stages'][11]['enemies'] if e['type'] == 'bishop']
        occupied = {(e['col'], e['row']) for e in self.data['stages'][11]['enemies']}
        occupied.add(tuple(self.data['stages'][11]['player_spawn']))
        color = (bishops[0]['col'] + bishops[0]['row']) % 2
        position = next((c, r) for c in range(10) for r in range(10)
                        if (c + r) % 2 == color and (c, r) not in occupied)
        bishops[1]['col'], bishops[1]['row'] = position
        with self.assertRaises(AssertionError):
            validate(self.data)

    def test_missing_required_field(self):
        del self.data['stages'][0]['enemies'][0]['col']
        with self.assertRaises(KeyError):
            validate(self.data)


if __name__ == '__main__':
    unittest.main()
