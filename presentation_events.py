"""Immutable notifications from combat owners for animation, VFX and audio."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from combat import AttackEvent
    from combat_resolution import DamageResult
    from enemy_attack import EnemyAttackEvent
    from parry_resolution import ParryResult


EventKind = Literal['telegraph', 'attack_start', 'hit', 'hurt', 'parry_normal',
                    'parry_perfect', 'parry_failed', 'stun', 'death', 'stage_transition',
                    'attack_move', 'rook_blocked', 'move']


@dataclass(frozen=True)
class PresentationEvent:
    kind: EventKind
    cause_key: tuple  # Begins with combat_session_id and stage_instance_id.
    tick: int
    subject: str | None
    payload: AttackEvent | EnemyAttackEvent | DamageResult | ParryResult | tuple[int, int] | None

    origin: tuple[int, int] | None = None
    destination: tuple[int, int] | None = None

    @property
    def key(self):
        return self.cause_key, self.kind, self.subject


class PresentationEvents:
    """One optional queue per active flow. Drain once and share the batch."""
    def __init__(self):
        self._pending = []

    def record(self, kind, cause_key, tick, subject, payload, *, origin=None, destination=None):
        self._pending.append(PresentationEvent(kind, cause_key, tick, subject, payload, origin, destination))

    def drain(self):
        batch = tuple(self._pending)
        self._pending.clear()
        return batch
