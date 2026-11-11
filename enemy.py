"""Pawn/Rook live combat model and legacy Stage 1 loading; no rendering."""
from dataclasses import dataclass, field
import json
from math import isfinite
from pathlib import Path
from uuid import uuid4

from board import in_bounds
from combat import _duration_ticks
from config import BOARD_SIZE, PAWN_INITIAL_HP, ROOK_INITIAL_HP
from health import Health


@dataclass
class Enemy:
    data_id: str
    col: int
    row: int
    forward: tuple[int, int] | None
    initial_delay: float
    entity_instance_id: str = field(default_factory=lambda: uuid4().hex)
    kind: str = field(default='pawn', kw_only=True)
    state: str = field(default='initial_wait', init=False)
    next_action_tick: int = field(default=0, init=False)
    stun_until_tick: int = field(default=0, init=False)
    current_attack: object = field(default=None, init=False, repr=False)
    health: Health = field(init=False)

    def __post_init__(self):
        if self.kind not in ('pawn', 'rook'):
            raise ValueError('Only Pawn and Rook combat instances are supported')
        label = self.kind.title()
        if not isinstance(self.data_id, str) or not self.data_id.strip():
            raise ValueError(f'{label} data ID must be a nonempty string')
        if not isinstance(self.entity_instance_id, str) or not self.entity_instance_id.strip():
            raise ValueError(f'{label} instance ID must be a nonempty string')
        if not in_bounds(self.col, self.row):
            raise ValueError(f'{label} coordinates must be integers between 0 and 9')
        if self.kind == 'pawn':
            if (not isinstance(self.forward, (list, tuple)) or len(self.forward) != 2
                    or any(type(v) is not int for v in self.forward) or tuple(self.forward) != (0, -1)):
                raise ValueError('Stage 1 Pawn forward must be [0, -1]')
            self.forward = tuple(self.forward)
        elif self.forward is not None:
            raise ValueError('Rook has no Pawn forward vector; use None')
        if (type(self.initial_delay) not in (int, float) or not isfinite(self.initial_delay)
                or not 0 <= self.initial_delay <= 10):
            raise ValueError(f'{label} initial_delay must be finite and between 0 and 10 seconds')
        self.health = Health(PAWN_INITIAL_HP if self.kind == 'pawn' else ROOK_INITIAL_HP)

    @property
    def position(self):
        return self.col, self.row

    @property
    def active(self):
        return self.state != 'inactive' and self.alive

    @property
    def alive(self):
        return self.health.alive

    @property
    def initial_delay_ticks(self):
        return 0 if self.initial_delay == 0 else _duration_ticks(self.initial_delay)


def load_stage1_enemies(path=None):
    source = Path(path) if path is not None else Path(__file__).resolve().with_name('stage_data.json')
    try:
        data = json.loads(source.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot load Stage 1 enemy data from {source}: {exc}') from exc
    if (not isinstance(data, dict) or type(data.get('board_size')) is not int
            or data['board_size'] != BOARD_SIZE or not isinstance(data.get('stages'), list)):
        raise ValueError(f'{source}: expected board_size {BOARD_SIZE} and a stages list')
    stages = [s for s in data['stages'] if isinstance(s, dict)
              and type(s.get('stage')) is int and s['stage'] == 1]
    if len(stages) != 1:
        raise ValueError(f'{source}: expected exactly one Stage 1 entry')
    stage = stages[0]
    spawn, rows = stage.get('player_spawn'), stage.get('enemies')
    if (type(stage.get('chapter')) is not int or stage['chapter'] != 1
            or not isinstance(spawn, list) or len(spawn) != 2 or not in_bounds(*spawn)
            or not isinstance(rows, list) or len(rows) != 2):
        raise ValueError(f'{source}: Stage 1 requires a valid player_spawn and two Pawn entries')
    enemies, ids, occupied = [], set(), {tuple(spawn)}
    for row in rows:
        try:
            if not isinstance(row, dict) or row.get('type') != 'pawn':
                raise ValueError('Stage 1 supports Pawn entries only')
            enemy = Enemy(row['id'], row['col'], row['row'], row['forward'], row['initial_delay'])
            if enemy.data_id in ids or enemy.position in occupied:
                raise ValueError('Duplicate enemy ID or occupied spawn cell')
        except (KeyError, ValueError) as exc:
            raise ValueError(f'{source}: invalid Stage 1 enemy entry {row!r}: {exc}') from exc
        enemies.append(enemy)
        ids.add(enemy.data_id)
        occupied.add(enemy.position)
    return tuple(enemies)
