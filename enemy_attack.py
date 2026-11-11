"""Scoped immutable enemy attack schedules and explicit single-use receipts.

The ledger records telegraph/due/resolved/cancelled lifecycle. Reaching hit_tick
does not apply damage, resolve a parry, or consume an event for any target.
Records and cancellation tombstones live until this stage ledger is discarded.
"""
from dataclasses import dataclass
from uuid import uuid4

from board import in_bounds


def _identifier(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be a nonempty string')
    return value


def _tick(value, name):
    if type(value) is not int:
        raise TypeError(f'{name} must be an integer tick')
    if value < 0:
        raise ValueError(f'{name} cannot be negative')
    return value


def _targets(cells):
    try:
        result = tuple(tuple(cell) for cell in cells)
    except TypeError as exc:
        raise ValueError('target_cells must contain coordinate pairs') from exc
    if not result:
        raise ValueError('target_cells cannot be empty')
    if any(len(cell) != 2 or not in_bounds(*cell) for cell in result):
        raise ValueError('target_cells must be integer in-bounds coordinate pairs')
    if len(set(result)) != len(result):
        raise ValueError('target_cells cannot contain duplicate cells')
    return result


@dataclass(frozen=True)
class EnemyAttackEvent:
    attack_id: int
    combat_session_id: str
    stage_instance_id: str
    source_entity_instance_id: str
    start_tick: int
    telegraph_start_tick: int
    hit_tick: int
    target_cells: tuple[tuple[int, int], ...]

    def __post_init__(self):
        if type(self.attack_id) is not int or self.attack_id < 1:
            raise ValueError('attack_id must be a positive integer')
        for field in ('combat_session_id', 'stage_instance_id', 'source_entity_instance_id'):
            _identifier(getattr(self, field), field)
        for field in ('start_tick', 'telegraph_start_tick', 'hit_tick'):
            _tick(getattr(self, field), field)
        if not self.start_tick <= self.telegraph_start_tick < self.hit_tick:
            raise ValueError('Attack ticks must satisfy start <= telegraph start < hit')
        object.__setattr__(self, 'target_cells', _targets(self.target_cells))

    @property
    def key(self):
        return (self.combat_session_id, self.stage_instance_id,
                self.source_entity_instance_id, self.attack_id)


@dataclass
class _AttackRecord:
    event: EnemyAttackEvent
    state: str = 'telegraph'
    outcome: str | None = None


class EnemyAttackLedger:
    def __init__(self, combat_session_id=None, stage_instance_id=None):
        self._combat_session_id = _identifier(
            uuid4().hex if combat_session_id is None else combat_session_id, 'combat_session_id')
        self._stage_instance_id = _identifier(
            uuid4().hex if stage_instance_id is None else stage_instance_id, 'stage_instance_id')
        self._next_attack_id = 1
        self._records = {}
        self._consumed = set()

    @property
    def combat_session_id(self):
        return self._combat_session_id

    @property
    def stage_instance_id(self):
        return self._stage_instance_id

    def create(self, source_entity_instance_id, start_tick, hit_tick, target_cells):
        event = EnemyAttackEvent(self._next_attack_id, self.combat_session_id,
                                 self.stage_instance_id, source_entity_instance_id,
                                 start_tick, start_tick, hit_tick, target_cells)
        self._next_attack_id += 1
        self._records[event.key] = _AttackRecord(event)
        return event

    def _record(self, event):
        if not isinstance(event, EnemyAttackEvent):
            return None
        record = self._records.get(event.key)
        # Matching IDs alone must not authorize a stale or altered event payload.
        return record if record is not None and record.event == event else None

    def state(self, event):
        record = self._record(event)
        return 'unknown' if record is None else record.state

    @property
    def telegraphs(self):
        return tuple(record.event for record in self._records.values()
                     if record.state == 'telegraph')

    def mark_due(self, event, tick):
        _tick(tick, 'Current tick')
        record = self._record(event)
        if record is None or record.state != 'telegraph' or tick < event.hit_tick:
            return False
        record.state = 'due'
        return True

    def consume(self, event, target_entity_instance_id):
        """Claim a due event once per target; this method applies no damage."""
        _identifier(target_entity_instance_id, 'target_entity_instance_id')
        record = self._record(event)
        if record is None or record.state != 'due':
            return False
        receipt = event.key, target_entity_instance_id
        if receipt in self._consumed:
            return False
        self._consumed.add(receipt)
        return True

    def finish(self, event, outcome):
        """Finish one adjudicated event, including misses and invulnerable hits.

        Target receipts remain available as history, but no new target can
        consume a resolved event. This method itself never applies damage.
        """
        if outcome not in ('hit', 'miss', 'invulnerable', 'target_dead', 'expired',
                           'parried_normal', 'parried_perfect'):
            raise ValueError('Unknown enemy attack outcome')
        record = self._record(event)
        if record is None or record.state != 'due':
            return False
        record.state = 'resolved'
        record.outcome = outcome
        return True

    def outcome(self, event):
        record = self._record(event)
        return None if record is None else record.outcome

    def cancel(self, event):
        record = self._record(event)
        if record is None or record.state in ('cancelled', 'resolved'):
            return False
        record.state = 'cancelled'
        return True

    def cancel_source(self, source_entity_instance_id):
        _identifier(source_entity_instance_id, 'source_entity_instance_id')
        return sum(self.cancel(record.event) for record in self._records.values()
                   if record.event.source_entity_instance_id == source_entity_instance_id)
