"""One-cell attack events and cooldowns on integer combat ticks.

This module emits immutable attack snapshots. It does not apply damage or
report hits; a future damage consumer can use attack_id to deduplicate events.
"""
from dataclasses import dataclass
from math import ceil, isfinite

from board import in_bounds
from config import ATTACK_COOLDOWN_SECONDS, ATTACK_EFFECT_SECONDS, FIXED_TIME_STEP
from player import DIRECTIONS


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


class Combat:
    def __init__(self, cooldown_seconds=ATTACK_COOLDOWN_SECONDS,
                 effect_seconds=ATTACK_EFFECT_SECONDS):
        self.cooldown_ticks = _duration_ticks(cooldown_seconds)
        self.effect_ticks = _duration_ticks(effect_seconds)
        self.tick = 0
        self.next_attack_tick = 0
        self._next_attack_id = 1
        self._last_attack = None

    def request_attack(self, player):
        """Emit one snapshot, or None on cooldown/outside the board.

        An invalid target consumes neither cooldown nor an attack ID. IDs are
        monotonic and unique for this Combat session; callers receive an event
        only when a new attack is accepted, not on subsequent effect frames.
        """
        if self.tick < self.next_attack_tick:
            return None
        origin = tuple(player.position)
        facing = player.facing
        dx, dy = DIRECTIONS[facing]
        target = origin[0] + dx, origin[1] + dy
        if not in_bounds(*target):
            return None
        event = AttackEvent(self._next_attack_id, origin, facing, target, self.tick)
        self._next_attack_id += 1
        self.next_attack_tick = self.tick + self.cooldown_ticks
        self._last_attack = event
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
