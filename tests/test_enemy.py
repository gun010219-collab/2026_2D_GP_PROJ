import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from enemy import Enemy, load_stage1_enemies

ROOT = Path(__file__).resolve().parents[1]


class EnemyDataTests(unittest.TestCase):
    def test_stage1_two_original_pawns_and_delays(self):
        enemies = load_stage1_enemies()
        self.assertEqual(len(enemies), 2)
        self.assertEqual([(e.data_id, e.position, e.forward, e.initial_delay, e.initial_delay_ticks)
                          for e in enemies], [('s1_pawn_1', (1, 6), (0, -1), .8, 48),
                                             ('s1_pawn_2', (8, 6), (0, -1), 1.02, 62)])
        self.assertTrue(all(e.kind == 'pawn' and e.state == 'initial_wait' for e in enemies))
        self.assertEqual(len({e.entity_instance_id for e in enemies}), 2)

    def test_reload_has_fresh_instance_ids(self):
        first, second = load_stage1_enemies(), load_stage1_enemies()
        self.assertEqual([e.data_id for e in first], [e.data_id for e in second])
        self.assertTrue({e.entity_instance_id for e in first}.isdisjoint(e.entity_instance_id for e in second))

    def test_path_is_independent_of_cwd_and_renderer(self):
        with tempfile.TemporaryDirectory() as directory:
            script = (f'import sys; sys.path.insert(0,{str(ROOT)!r}); '
                      'from enemy import load_stage1_enemies; '
                      'assert len(load_stage1_enemies()) == 2; assert "pico2d" not in sys.modules')
            result = subprocess.run([sys.executable, '-c', script], cwd=directory,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_model_data(self):
        for field, value in [('col', -1), ('row', 10), ('col', True), ('row', 1.5),
                             ('forward', (0, 1)), ('forward', (False, -1)),
                             ('initial_delay', -1), ('initial_delay', float('nan')),
                             ('initial_delay', True), ('initial_delay', 11), ('data_id', ' ')]:
            values = dict(data_id='pawn', col=1, row=6, forward=(0, -1), initial_delay=0)
            values[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                Enemy(**values)

    def test_invalid_json_missing_fields_and_overlapping_spawns(self):
        baseline = json.loads((ROOT / 'stage_data.json').read_text('utf-8'))
        cases = []
        for field, value in [('type', 'rook'), ('col', 10), ('forward', [0, 1]),
                             ('initial_delay', '0.8'), ('row', -1)]:
            data = copy.deepcopy(baseline)
            data['stages'][0]['enemies'][0][field] = value
            cases.append(data)
        for overlap in ('id', 'position', 'player'):
            data = copy.deepcopy(baseline)
            first, second = data['stages'][0]['enemies']
            if overlap == 'id':
                second['id'] = first['id']
            elif overlap == 'position':
                second['col'], second['row'] = first['col'], first['row']
            else:
                first['col'], first['row'] = data['stages'][0]['player_spawn']
            cases.append(data)
        missing = copy.deepcopy(baseline)
        del missing['stages'][0]['enemies'][0]['initial_delay']
        cases += [missing, {}, {'board_size': 10, 'stages': []}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stages.json'
            with self.assertRaisesRegex(ValueError, 'Cannot load Stage 1'):
                load_stage1_enemies(path)
            path.write_text('{broken', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Cannot load Stage 1'):
                load_stage1_enemies(path)
            for data in cases:
                path.write_text(json.dumps(data), encoding='utf-8')
                with self.subTest(data=data['stages'][0] if data.get('stages') else data):
                    with self.assertRaisesRegex(ValueError, 'Stage 1|board_size'):
                        load_stage1_enemies(path)
