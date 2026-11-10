"""Logical player state and minimal Stage 1 spawn loading; no Pico2D."""
import json
from pathlib import Path

from board import in_bounds

DIRECTIONS = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}


class Player:
    def __init__(self, col, row, facing='up'):
        if not in_bounds(col, row):
            raise ValueError('Player coordinates must be integers between 0 and 9')
        if facing not in DIRECTIONS:
            raise ValueError('Unknown player facing')
        self._col, self._row, self._facing = col, row, facing

    @property
    def col(self):
        return self._col

    @property
    def row(self):
        return self._row

    @property
    def facing(self):
        return self._facing

    @property
    def position(self):
        return self.col, self.row

    def move(self, direction):
        if direction not in DIRECTIONS:
            raise ValueError('Unknown movement direction')
        self._facing = direction
        dx, dy = DIRECTIONS[direction]
        col, row = self.col + dx, self.row + dy
        if not in_bounds(col, row):
            return False
        self._col, self._row = col, row
        return True


def load_stage1_player(path=None):
    source = Path(path) if path is not None else Path(__file__).resolve().with_name('stage_data.json')
    try:
        data = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot load Stage 1 player data from {source}: {exc}') from exc
    if not isinstance(data, dict) or not isinstance(data.get('stages'), list):
        raise ValueError(f'{source}: expected a stages list for Stage 1 player data')
    stages = [stage for stage in data['stages'] if isinstance(stage, dict)
              and type(stage.get('stage')) is int and stage['stage'] == 1]
    if len(stages) != 1:
        raise ValueError(f'{source}: expected exactly one Stage 1 entry')
    stage = stages[0]
    spawn = stage.get('player_spawn')
    if (type(stage.get('chapter')) is not int or stage['chapter'] != 1
            or not isinstance(spawn, list) or len(spawn) != 2):
        raise ValueError(f'{source}: Stage 1 requires chapter 1 and a two-coordinate player_spawn')
    try:
        return Player(*spawn)
    except ValueError as exc:
        raise ValueError(f'{source}: invalid Stage 1 player_spawn: {exc}') from exc
