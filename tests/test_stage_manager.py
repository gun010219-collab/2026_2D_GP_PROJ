from combat_balance import profile_for
"""Catalog fidelity, validation, immutability and Stage 1 compatibility."""
import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from stage_manager import StageCatalog, StageDataError
from validate_stage_data import validate


ROOT = Path(__file__).resolve().parents[1]


def thaw(value):
    """Compare immutable definitions to JSON without assuming container types."""
    from collections.abc import Mapping
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


class StageCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / 'stage_data.json').read_text(encoding='utf-8'))
        cls.catalog = StageCatalog.load()

    def test_all_25_stages_in_original_order(self):
        self.assertEqual(len(self.catalog.stages), 25)
        self.assertEqual([s.number for s in self.catalog.stages], list(range(1, 26)))
        for stage in self.catalog.stages:
            self.assertIs(self.catalog.get_stage(stage.number), stage)

    def test_chapter_mapping(self):
        self.assertEqual([s.chapter for s in self.catalog.stages],
                         [chapter for chapter in range(1, 6) for _ in range(5)])

    def test_boss_numbers_hp_and_king_definitions(self):
        self.assertEqual({s.number: s.boss_hp for s in self.catalog.stages if s.boss},
                         {5: 8, 10: 10, 15: 12, 20: 14, 25: 16})
        for stage in self.catalog.stages:
            self.assertEqual(sum(e.kind == 'king' for e in stage.enemies), int(stage.boss))
            if not stage.boss:
                self.assertIsNone(stage.boss_hp)

    def test_every_definition_preserves_all_source_fields(self):
        for raw, stage in zip(self.original['stages'], self.catalog.stages):
            with self.subTest(stage=stage.number):
                restored = dict(stage=stage.number, chapter=stage.chapter, boss=stage.boss,
                                boss_hp=stage.boss_hp, player_spawn=list(stage.player_spawn),
                                enemies=[], **thaw(stage.options))
                for enemy in stage.enemies:
                    restored['enemies'].append(dict(
                        id=enemy.data_id, type=enemy.kind, col=enemy.col, row=enemy.row,
                        initial_delay=enemy.initial_delay, **thaw(enemy.options)))
                self.assertEqual(restored, raw)

    def test_stage_one_two_original_pawns(self):
        stage = self.catalog.get_stage(1)
        self.assertEqual(stage.player_spawn, (5, 1))
        self.assertEqual([(e.data_id, e.kind, e.position, e.initial_delay, e.options['forward'])
                          for e in stage.enemies],
                         [('s1_pawn_1', 'pawn', (1, 6), 0.8, (0, -1)),
                          ('s1_pawn_2', 'pawn', (8, 6), 1.02, (0, -1))])

    def test_stage_two_rook_and_two_pawns(self):
        stage = self.catalog.get_stage(2)
        self.assertEqual(stage.player_spawn, (5, 1))
        self.assertEqual([(e.data_id, e.kind, e.position, e.initial_delay) for e in stage.enemies],
                         [('s2_rook_1', 'rook', (2, 4), 0.8),
                          ('s2_pawn_1', 'pawn', (1, 6), 1.02),
                          ('s2_pawn_2', 'pawn', (8, 6), 1.24)])
        self.assertNotIn('forward', stage.enemies[0].options)

    def test_all_six_piece_kinds_and_absent_optional_fields(self):
        self.assertEqual({e.kind for s in self.catalog.stages for e in s.enemies},
                         {'pawn', 'rook', 'knight', 'bishop', 'queen', 'king'})
        for stage in self.catalog.stages:
            for enemy in stage.enemies:
                self.assertEqual('forward' in enemy.options, enemy.kind == 'pawn')

    def test_root_metadata_preserved(self):
        self.assertEqual(self.catalog.board_size, self.original['board_size'])
        self.assertEqual(thaw(self.catalog.metadata),
                         {k: v for k, v in self.original.items() if k not in ('board_size', 'stages')})

    def test_optional_null_zero_false_and_nested_settings_preserved(self):
        data = copy.deepcopy(self.original)
        settings = {'nullable': None, 'enabled': False, 'delay': 0,
                    'pattern': [{'cells': [[2, 3]], 'label': 'future'}]}
        data['stages'][1]['enemies'][0]['settings'] = settings
        data['stages'][1]['note'] = {'tags': ['data only']}
        catalog = StageCatalog(data)
        self.assertEqual(thaw(catalog.get_stage(2).enemies[0].options['settings']), settings)
        self.assertEqual(thaw(catalog.get_stage(2).options), {'note': {'tags': ['data only']}})
        self.assertNotIn('settings', catalog.get_stage(1).enemies[0].options)

    def test_definitions_and_catalog_are_frozen(self):
        for obj, field, value in [(self.catalog, 'board_size', 3),
                                  (self.catalog.get_stage(1), 'chapter', 5),
                                  (self.catalog.get_stage(1).enemies[0], 'col', 7)]:
            with self.subTest(field=field), self.assertRaises(FrozenInstanceError):
                setattr(obj, field, value)

    def test_collections_and_option_mappings_cannot_be_modified(self):
        stage = self.catalog.get_stage(1)
        with self.assertRaises(TypeError):
            self.catalog.stages[0] = stage
        with self.assertRaises(TypeError):
            stage.enemies[0] = stage.enemies[1]
        with self.assertRaises(TypeError):
            stage.player_spawn[0] = 4
        with self.assertRaises(TypeError):
            stage.enemies[0].options['forward'] = (0, 1)
        with self.assertRaises(TypeError):
            self.catalog.metadata['coordinate_system'] = 'modified'

    def test_nested_optional_data_is_immutable_and_has_no_input_aliases(self):
        data = copy.deepcopy(self.original)
        data['settings'] = {'layers': [{'cells': [[1, 2]]}]}
        catalog = StageCatalog(data)
        cells = catalog.metadata['settings']['layers'][0]['cells']
        with self.assertRaises(TypeError):
            cells[0][0] = 8
        with self.assertRaises(TypeError):
            catalog.metadata['settings']['layers'][0]['cells'] = ()
        data['settings']['layers'][0]['cells'][0][0] = 8
        data['stages'][0]['enemies'][0]['forward'][1] = 1
        self.assertEqual(cells, ((1, 2),))
        self.assertEqual(catalog.get_stage(1).enemies[0].options['forward'], (0, -1))

    def test_repeated_loads_consistent_and_separate(self):
        other = StageCatalog.load()
        self.assertEqual(other, self.catalog)
        self.assertIsNot(other, self.catalog)
        self.assertIsNot(other.get_stage(1), self.catalog.get_stage(1))

    def test_valid_number_endpoints(self):
        self.assertEqual(self.catalog.get_stage(1).number, 1)
        self.assertEqual(self.catalog.get_stage(25).number, 25)

    def test_out_of_range_numbers_rejected(self):
        for value in (-1, 0, 26, 100):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, '1..25'):
                self.catalog.get_stage(value)

    def test_non_integer_numbers_rejected(self):
        for value in (True, False, '1', 1.0, None, [], {}):
            with self.subTest(value=value), self.assertRaises(TypeError):
                self.catalog.get_stage(value)

    def test_root_and_stage_shapes_rejected(self):
        for data in (None, [], {}, {'board_size': True, 'stages': []},
                     {'board_size': 10, 'stages': {}}, {'board_size': 10, 'stages': [None]}):
            with self.subTest(data=data), self.assertRaises(StageDataError):
                StageCatalog(data)

    def test_missing_required_stage_or_enemy_fields_rejected(self):
        for level, fields in [('stage', ('stage', 'chapter', 'boss', 'boss_hp', 'player_spawn', 'enemies')),
                              ('enemy', ('id', 'type', 'col', 'row', 'initial_delay', 'forward'))]:
            for field in fields:
                data = copy.deepcopy(self.original)
                target = data['stages'][0] if level == 'stage' else data['stages'][0]['enemies'][0]
                del target[field]
                with self.subTest(level=level, field=field), self.assertRaises(StageDataError):
                    StageCatalog(data)

    def test_invalid_stage_field_types_rejected(self):
        for field, value in [('stage', True), ('chapter', 1.0), ('boss', 0), ('boss_hp', True),
                             ('boss_hp', -1), ('player_spawn', [True, 1]), ('enemies', {}),
                             ('player_spawn', [5]), ('player_spawn', '5,1')]:
            data = copy.deepcopy(self.original)
            data['stages'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(StageDataError):
                StageCatalog(data)

    def test_invalid_enemy_types_rejected(self):
        for field, value in [('id', ''), ('id', ' '), ('id', 7), ('type', 'dragon'), ('type', []),
                             ('col', True), ('row', 2.0), ('initial_delay', False),
                             ('initial_delay', '0.8'), ('forward', [False, -1]),
                             ('forward', [0]), ('forward', None)]:
            data = copy.deepcopy(self.original)
            data['stages'][0]['enemies'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(StageDataError):
                StageCatalog(data)

    def test_non_object_enemy_rejected(self):
        data = copy.deepcopy(self.original)
        data['stages'][0]['enemies'][0] = None
        with self.assertRaisesRegex(StageDataError, r'enemies\[0\]'):
            StageCatalog(data)

    def test_baseline_stage_rules_shared_with_static_validator(self):
        for field, value in [('stage', 2), ('chapter', 2), ('boss', True),
                             ('boss_hp', 5), ('player_spawn', [4, 1])]:
            data = copy.deepcopy(self.original)
            data['stages'][0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(AssertionError):
                    validate(data)
                with self.assertRaisesRegex(StageDataError, 'Stage 1'):
                    StageCatalog(data)

    def test_wrong_total_stage_count_rejected(self):
        for stages in (self.original['stages'][:-1], self.original['stages'] * 2):
            data = dict(self.original, stages=stages)
            with self.assertRaisesRegex(StageDataError, '25 entries'):
                StageCatalog(data)

    def test_roster_bounds_delay_and_pawn_direction_rejected(self):
        for field, value in [('type', 'rook'), ('col', 10), ('row', -1),
                             ('initial_delay', -0.01), ('initial_delay', 10.01), ('forward', [0, 1])]:
            data = copy.deepcopy(self.original)
            data['stages'][0]['enemies'][0][field] = value
            with self.subTest(field=field), self.assertRaises(StageDataError):
                StageCatalog(data)

    def test_duplicate_enemy_id_or_position_and_player_overlap_rejected(self):
        for fields in [('id',), ('col', 'row'), ('player',)]:
            data = copy.deepcopy(self.original)
            first, second = data['stages'][0]['enemies']
            if fields == ('player',):
                first['col'], first['row'] = data['stages'][0]['player_spawn']
            else:
                for field in fields:
                    second[field] = first[field]
            with self.subTest(fields=fields), self.assertRaises(StageDataError):
                StageCatalog(data)

    def test_wrong_boss_hp_rejected(self):
        data = copy.deepcopy(self.original)
        data['stages'][24]['boss_hp'] = 17
        with self.assertRaisesRegex(StageDataError, 'Stage 25.*boss_hp'):
            StageCatalog(data)

    def test_non_json_and_non_finite_optional_values_rejected(self):
        for value in (float('nan'), float('inf'), float('-inf'), object(), {1, 2}, (1, 2), {1: 2}):
            data = copy.deepcopy(self.original)
            data['optional'] = value
            with self.subTest(value=value), self.assertRaises(StageDataError):
                StageCatalog(data)

    def test_non_finite_initial_delay_rejected(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            data = copy.deepcopy(self.original)
            data['stages'][0]['enemies'][0]['initial_delay'] = value
            with self.subTest(value=value), self.assertRaisesRegex(StageDataError, 'initial_delay'):
                StageCatalog(data)

    def test_cyclic_optional_data_rejected(self):
        data = copy.deepcopy(self.original)
        data['cycle'] = data
        with self.assertRaisesRegex(StageDataError, 'cyclic|nested'):
            StageCatalog(data)

    def test_load_custom_file_without_changing_original(self):
        data = copy.deepcopy(self.original)
        data['stages'][1]['enemies'][0]['settings'] = {'range': None}
        original_bytes = (ROOT / 'stage_data.json').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stages.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            self.assertEqual(StageCatalog.load(path).get_stage(2).enemies[0].options['settings']['range'], None)
        self.assertEqual((ROOT / 'stage_data.json').read_bytes(), original_bytes)

    def test_missing_invalid_json_or_encoding_reports_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'broken.json'
            for contents in (None, b'{bad', b'\xff', b'{}'):
                if contents is not None:
                    path.write_bytes(contents)
                with self.subTest(contents=contents), self.assertRaises(StageDataError) as error:
                    StageCatalog.load(path)
                self.assertIn(str(path), str(error.exception))

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'duplicate.json'
            path.write_text('{"board_size":10,"board_size":9,"stages":[]}', encoding='utf-8')
            with self.assertRaisesRegex(StageDataError, 'Duplicate JSON field: board_size'):
                StageCatalog.load(path)

    def test_import_and_default_load_are_pure_and_cwd_independent(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); "
                "from stage_manager import StageCatalog; "
                "c=StageCatalog.load(); print(len(c.stages), 'pico2d' in sys.modules, "
                "'main' in sys.modules, 'enemy' in sys.modules)")
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-c', code, str(ROOT)], cwd=directory,
                                    capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), '25 False False False')

    def test_optimized_python_still_enforces_shared_validation(self):
        code = """
import json
from pathlib import Path
from stage_manager import StageCatalog, StageDataError
from validate_stage_data import validate
data = json.loads(Path('stage_data.json').read_text(encoding='utf-8'))
data['stages'][0]['enemies'][0]['type'] = 'rook'
for constructor, expected in ((validate, AssertionError), (StageCatalog, StageDataError)):
    try:
        constructor(data)
    except expected:
        print('rejected')
    else:
        raise RuntimeError('optimized interpreter bypassed stage validation')
"""
        result = subprocess.run([sys.executable, '-O', '-c', code], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.splitlines(), ['rejected', 'rejected'])

    def test_legacy_stage_one_loader_values_and_instance_isolation(self):
        from enemy import load_stage1_enemies
        from player import load_stage1_player
        stage = self.catalog.get_stage(1)
        player = load_stage1_player()
        enemies = load_stage1_enemies()
        self.assertEqual(player.position, stage.player_spawn)
        self.assertEqual([(e.data_id, e.kind, e.position, e.forward, e.initial_delay) for e in enemies],
                         [(e.data_id, e.kind, e.position, e.options['forward'], e.initial_delay)
                          for e in stage.enemies])
        enemies[0].health.apply_damage(1, tick=0)
        self.assertEqual(load_stage1_enemies()[0].health.current_hp, 3)
        self.assertNotEqual(enemies[0].entity_instance_id, load_stage1_enemies()[0].entity_instance_id)
        self.assertEqual(stage.enemies[0].position, (1, 6))

    def test_legacy_minimal_player_json_and_error_contract_unchanged(self):
        from player import load_stage1_player
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'single.json'
            path.write_text(json.dumps({'stages': [{'stage': 1, 'chapter': 1,
                                                    'player_spawn': [3, 4]}]}), encoding='utf-8')
            self.assertEqual(load_stage1_player(path).position, (3, 4))
            with self.assertRaises(StageDataError):
                StageCatalog.load(path)
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Stage 1'):
                load_stage1_player(path)

    def test_stage_one_simulation_trace_matches_catalog_spawn_data(self):
        import main
        from combat import Combat
        from combat_resolution import CombatResolver
        from enemy import Enemy
        from enemy_behaviors import PawnEncounter
        from game import StageOneGame
        from parry import Parry
        from player import Player
        stage = self.catalog.get_stage(1)
        player = Player(*stage.player_spawn)
        combat, parry = Combat(), Parry()
        enemies = tuple(Enemy(e.data_id, e.col, e.row, e.options['forward'], e.initial_delay, max_hp=3)
                        for e in stage.enemies)
        encounter = PawnEncounter(enemies, combat_session_id=combat.combat_session_id,
                                  stage_instance_id=combat.stage_instance_id)
        resolver = CombatResolver(player, combat, encounter, parry=parry)
        from_definitions = StageOneGame(player, combat, encounter, parry, resolver)
        legacy = main._new_game()

        def snapshot(game):
            return (game.state, game.combat.tick, game.player.position, game.player.facing,
                    game.player.health.current_hp,
                    tuple((e.data_id, e.position, e.state, e.next_action_tick, e.health.current_hp,
                           None if e.current_attack is None else
                           (e.current_attack.start_tick, e.current_attack.hit_tick,
                            e.current_attack.target_cells)) for e in game.encounter.enemies))

        for tick in range(601):
            for game in (legacy, from_definitions):
                if game.playing and tick % 36 == 0:
                    attack = game.combat.request_attack(game.player)
                    game.resolver.resolve_player_attack(attack)
                game.advance()
            with self.subTest(tick=tick):
                self.assertEqual(snapshot(legacy), snapshot(from_definitions))


if __name__ == '__main__':
    unittest.main()
