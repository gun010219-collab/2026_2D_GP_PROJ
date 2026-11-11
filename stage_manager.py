"""Read-only stage definitions, not live combat instances or stage progression.

StageCatalog.load() reads the canonical JSON relative to this module. Loading
validates all 25 definitions; querying one does not make it playable. The legacy
Stage 1 loaders intentionally retain their narrower input/error contracts.
"""
from dataclasses import dataclass
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from validate_stage_data import validate


STAGE_FILE = Path(__file__).with_name('stage_data.json')
ENEMY_KINDS = frozenset(('pawn', 'rook', 'knight', 'bishop', 'queen', 'king'))
_ENEMY_FIELDS = frozenset(('id', 'type', 'col', 'row', 'initial_delay'))
_STAGE_FIELDS = frozenset(('stage', 'chapter', 'boss', 'boss_hp', 'player_spawn', 'enemies'))


class StageDataError(ValueError):
    """The source cannot be read as a valid CHECKMATE stage catalog."""


def _require(condition, path, expectation):
    if not condition:
        raise StageDataError(f'{path}: expected {expectation}')


def _freeze(value, path='catalog'):
    """Copy JSON values recursively, rejecting non-JSON or non-finite values.

    A mapping proxy wraps a NEW dictionary, never a caller-owned dictionary.
    Array order, explicit null/false/zero and absent optional keys stay distinct.
    """
    if type(value) is dict:
        _require(all(type(key) is str for key in value), path, 'string object keys')
        return MappingProxyType({key: _freeze(item, f'{path}.{key}')
                                 for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item, f'{path}[{index}]') for index, item in enumerate(value))
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise StageDataError(f'{path}: expected finite JSON data')


def _check_shape(data):
    """Type/shape checks complement the shared baseline's semantic rules."""
    _require(type(data) is dict, 'catalog', 'object')
    _require(type(data.get('board_size')) is int, 'board_size', 'integer')
    _require(type(data.get('stages')) is list, 'stages', 'array')
    for index, stage in enumerate(data['stages']):
        path = f'stages[{index}]'
        _require(type(stage) is dict, path, 'object')
        _require(_STAGE_FIELDS <= stage.keys(), path, 'all required stage fields')
        for field in ('stage', 'chapter'):
            _require(type(stage[field]) is int, f'{path}.{field}', 'integer')
        _require(type(stage['boss']) is bool, f'{path}.boss', 'boolean')
        hp = stage['boss_hp']
        _require(hp is None or (type(hp) is int and hp > 0), f'{path}.boss_hp',
                 'null or positive integer')
        spawn = stage['player_spawn']
        _require(type(spawn) is list and len(spawn) == 2
                 and all(type(v) is int for v in spawn), f'{path}.player_spawn',
                 'two integer coordinates')
        _require(type(stage['enemies']) is list, f'{path}.enemies', 'array')
        for enemy_index, enemy in enumerate(stage['enemies']):
            ep = f'{path}.enemies[{enemy_index}]'
            _require(type(enemy) is dict, ep, 'object')
            _require(_ENEMY_FIELDS <= enemy.keys(), ep, 'all required enemy fields')
            _require(type(enemy['id']) is str and bool(enemy['id'].strip()),
                     f'{ep}.id', 'non-empty string')
            _require(type(enemy['type']) is str and enemy['type'] in ENEMY_KINDS,
                     f'{ep}.type', 'supported chess piece name')
            for field in ('col', 'row'):
                _require(type(enemy[field]) is int, f'{ep}.{field}', 'integer')
            _require(type(enemy['initial_delay']) in (int, float),
                     f'{ep}.initial_delay', 'number (not boolean)')
            if enemy['type'] == 'pawn':
                forward = enemy.get('forward')
                _require(type(forward) is list and len(forward) == 2
                         and all(type(v) is int for v in forward),
                         f'{ep}.forward', 'two integer direction components')


@dataclass(frozen=True, slots=True)
class EnemyDefinition:
    """Spawn data only. Optional piece settings have no invented defaults."""
    data_id: str
    kind: str
    col: int
    row: int
    initial_delay: int | float
    options: Mapping[str, object]

    @property
    def position(self):
        return self.col, self.row


@dataclass(frozen=True, slots=True)
class StageDefinition:
    number: int
    chapter: int
    boss: bool
    boss_hp: int | None
    player_spawn: tuple[int, int]
    enemies: tuple[EnemyDefinition, ...]
    options: Mapping[str, object]


@dataclass(frozen=True, slots=True, init=False)
class StageCatalog:
    """Immutable validated snapshot. Construct from JSON data or load a file.

    Use get_stage(1..25) to retrieve definitions in original JSON enemy order.
    This layer does not allocate entity IDs, HP, AI, event ledgers or windows.
    """
    board_size: int
    stages: tuple[StageDefinition, ...]
    metadata: Mapping[str, object]

    def __init__(self, data):
        _check_shape(data)
        try:
            frozen = _freeze(data)
        except RecursionError as exc:
            raise StageDataError('catalog: cyclic or excessively nested JSON data') from exc
        try:
            validate(data)
        except (AssertionError, KeyError, TypeError, ValueError) as exc:
            raise StageDataError(f'Catalog violates stage baseline: {exc}') from exc
        stages = []
        for stage in frozen['stages']:
            enemies = tuple(EnemyDefinition(
                enemy['id'], enemy['type'], enemy['col'], enemy['row'],
                enemy['initial_delay'], MappingProxyType({key: value for key, value in enemy.items()
                                                        if key not in _ENEMY_FIELDS}))
                for enemy in stage['enemies'])
            stages.append(StageDefinition(
                stage['stage'], stage['chapter'], stage['boss'], stage['boss_hp'],
                stage['player_spawn'], enemies,
                MappingProxyType({key: value for key, value in stage.items()
                                  if key not in _STAGE_FIELDS})))
        object.__setattr__(self, 'board_size', frozen['board_size'])
        object.__setattr__(self, 'stages', tuple(stages))
        object.__setattr__(self, 'metadata', MappingProxyType(
            {key: value for key, value in frozen.items() if key not in ('board_size', 'stages')}))

    @classmethod
    def load(cls, path=None):
        source = Path(path) if path is not None else STAGE_FILE
        try:
            data = json.loads(source.read_text(encoding='utf-8'),
                              object_pairs_hook=_unique_object)
            return cls(data)
        except (OSError, ValueError, RecursionError) as exc:
            raise StageDataError(f'Cannot load stage catalog from {source}: {exc}') from exc

    def get_stage(self, number):
        if type(number) is not int:
            raise TypeError('Stage number must be an integer (not boolean)')
        if not 1 <= number <= len(self.stages):
            raise ValueError(f'Stage number must be in 1..{len(self.stages)}')
        return self.stages[number - 1]


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StageDataError(f'Duplicate JSON field: {key}')
        result[key] = value
    return result
