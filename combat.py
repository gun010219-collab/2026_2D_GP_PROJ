"""One-cell attack events and cooldowns on integer combat ticks.

This module emits immutable attack snapshots and owns their scoped receipts.
Only CombatResolver applies damage; the nine-tick effect is a read-only view.
"""
from dataclasses import dataclass
from math import ceil, isfinite
from uuid import uuid4

from board import in_bounds
from config import ATTACK_COOLDOWN_SECONDS, ATTACK_EFFECT_SECONDS, FIXED_TIME_STEP
from player import DIRECTIONS, Player


def _duration_ticks(seconds):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise TypeError('Attack duration must be a number of seconds')
    if not isfinite(seconds) or seconds <= 0:
        raise ValueError('Attack duration must be finite and positive')
    # Ignore floating-point noise at exact tick boundaries, not elapsed ticks.
    return max(1, ceil(seconds / FIXED_TIME_STEP - 1e-12))


@dataclass(frozen=True)
class AttackEvent:
    attack_id: int
    origin_cell: tuple[int, int]
    facing: str
    target_cell: tuple[int, int]
    start_tick: int
    combat_session_id: str = ''
    stage_instance_id: str = ''
    source_entity_instance_id: str = ''

    def __post_init__(self):
        if type(self.attack_id) is not int or self.attack_id < 1:
            raise ValueError('attack_id must be a positive integer')
        if type(self.start_tick) is not int:
            raise TypeError('Attack start_tick must be an integer')
        if self.start_tick < 0:
            raise ValueError('Attack start_tick cannot be negative')
        for name in ('origin_cell', 'target_cell'):
            value = getattr(self, name)
            if (not isinstance(value, (tuple, list)) or len(value) != 2
                    or not in_bounds(*value)):
                raise ValueError(f'{name} must be an in-bounds integer cell')
            object.__setattr__(self, name, tuple(value))
        if not isinstance(self.facing, str) or self.facing not in DIRECTIONS:
            raise ValueError('Unknown attack facing')
        dx, dy = DIRECTIONS[self.facing]
        if self.target_cell != (self.origin_cell[0] + dx, self.origin_cell[1] + dy):
            raise ValueError('Attack target must be one cell in its snapshot facing')
        scopes = (self.combat_session_id, self.stage_instance_id, self.source_entity_instance_id)
        # Keep the original five-field constructor for read-only callers. Such
        # unscoped snapshots are never registered/authorized by a Combat.
        if scopes != ('', '', '') and any(not isinstance(v, str) or not v.strip() for v in scopes):
            raise ValueError('Attack scopes must be three nonempty strings')

    @property
    def key(self):
        return (self.combat_session_id, self.stage_instance_id,
                self.source_entity_instance_id, self.attack_id)


@dataclass
class _PlayerAttackRecord:
    event: AttackEvent
    state: str = 'pending'


class Combat:
    def __init__(self, cooldown_seconds=ATTACK_COOLDOWN_SECONDS,
                 effect_seconds=ATTACK_EFFECT_SECONDS, *,
                 combat_session_id=None, stage_instance_id=None):
        self.cooldown_ticks = _duration_ticks(cooldown_seconds)
        self.effect_ticks = _duration_ticks(effect_seconds)
        self.tick = 0
        self.next_attack_tick = 0
        self._next_attack_id = 1
        self._last_attack = None
        self._combat_session_id = self._scope(combat_session_id)
        self._stage_instance_id = self._scope(stage_instance_id)
        self._attack_records = {}
        self._consumed = set()

    @staticmethod
    def _scope(value):
        if value is None:
            return uuid4().hex
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Combat scope must be a nonempty string')
        return value

    @property
    def combat_session_id(self):
        return self._combat_session_id

    @property
    def stage_instance_id(self):
        return self._stage_instance_id

    def bind_stage(self, stage_instance_id):
        """Bind subsequent input to a stage without deleting old receipts."""
        stage_instance_id = self._scope(stage_instance_id)
        if stage_instance_id != self.stage_instance_id:
            self._stage_instance_id = stage_instance_id
            self._last_attack = None

    def _record(self, event):
        if not isinstance(event, AttackEvent):
            return None
        try:
            record = self._attack_records.get(event.key)
        except TypeError:
            return None
        return record if record is not None and record.event == event else None

    def attack_state(self, event):
        record = self._record(event)
        if (record is None or event.combat_session_id != self.combat_session_id
                or event.stage_instance_id != self.stage_instance_id):
            return 'unknown'
        return record.state

    def consume_attack(self, event, target_entity_instance_id):
        """Claim one target of an authentic pending event; apply no damage."""
        if not isinstance(target_entity_instance_id, str) or not target_entity_instance_id.strip():
            raise ValueError('Target instance ID must be a nonempty string')
        if self.attack_state(event) != 'pending':
            return False
        receipt = event.key, target_entity_instance_id
        if receipt in self._consumed:
            return False
        self._consumed.add(receipt)
        return True

    def finish_attack(self, event):
        """Close hits and misses so the effect cannot be replayed later."""
        if self.attack_state(event) != 'pending':
            return False
        self._record(event).state = 'resolved'
        return True

    def request_attack(self, player):
        """Emit one snapshot, or None on cooldown/outside the board.

        An invalid target consumes neither cooldown nor an attack ID. IDs are
        monotonic and unique for this Combat session; callers receive an event
        only when a new attack is accepted, not on subsequent effect frames.
        """
        if not isinstance(player, Player):
            raise TypeError('Attack source must be a Player')
        if not player.alive or self.tick < self.next_attack_tick:
            return None
        origin = tuple(player.position)
        facing = player.facing
        dx, dy = DIRECTIONS[facing]
        target = origin[0] + dx, origin[1] + dy
        if not in_bounds(*target):
            return None
        event = AttackEvent(self._next_attack_id, origin, facing, target, self.tick,
                            self.combat_session_id, self.stage_instance_id,
                            player.entity_instance_id)
        self._next_attack_id += 1
        self.next_attack_tick = self.tick + self.cooldown_ticks
        self._last_attack = event
        self._attack_records[event.key] = _PlayerAttackRecord(event)
        return event

    def advance(self, ticks=1):
        if type(ticks) is not int:
            raise TypeError('Combat ticks must be an integer')
        if ticks < 0:
            raise ValueError('Combat ticks cannot move backwards')
        self.tick += ticks

    @property
    def active_attack(self):
        event = self._last_attack
        if event is not None and self.tick < event.start_tick + self.effect_ticks:
            return event
        return None
