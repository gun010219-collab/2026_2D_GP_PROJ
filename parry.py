"""Input-relative parry availability windows; no enemy or success resolution.

The caller supplies Combat.tick. This module owns no clock and never infers a
successful block from an availability window.
"""
from dataclasses import dataclass
from uuid import uuid4

from combat import _duration_ticks
from config import PARRY_COOLDOWN_SECONDS, PARRY_WINDOW_SECONDS, PERFECT_PARRY_WINDOW_SECONDS


def _validate_tick(tick):
    if type(tick) is not int:
        raise TypeError('Parry tick must be an integer')
    if tick < 0:
        raise ValueError('Parry tick cannot be negative')


@dataclass(frozen=True)
class ParryAttempt:
    parry_id: int
    start_tick: int
    perfect_end_tick: int
    end_tick: int
    parry_session_id: str = ''
    stage_instance_id: str = ''

    def __post_init__(self):
        if type(self.parry_id) is not int or self.parry_id < 1:
            raise ValueError('parry_id must be a positive integer')
        for tick in (self.start_tick, self.perfect_end_tick, self.end_tick):
            _validate_tick(tick)
        if not self.start_tick < self.perfect_end_tick <= self.end_tick:
            raise ValueError('Parry preview ticks must satisfy start < perfect end <= end')
        scopes = self.parry_session_id, self.stage_instance_id
        if scopes != ('', '') and any(not isinstance(s, str) or not s.strip() for s in scopes):
            raise ValueError('Parry scopes must be two nonempty strings')

    @property
    def key(self):
        return self.parry_session_id, self.stage_instance_id, self.parry_id


class Parry:
    def __init__(self, window_seconds=PARRY_WINDOW_SECONDS,
                 perfect_seconds=PERFECT_PARRY_WINDOW_SECONDS,
                 cooldown_seconds=PARRY_COOLDOWN_SECONDS):
        # Share the existing attack duration conversion, including ceil policy.
        self.window_ticks = _duration_ticks(window_seconds)
        self.perfect_ticks = _duration_ticks(perfect_seconds)
        self.cooldown_ticks = _duration_ticks(cooldown_seconds)
        if self.perfect_ticks > self.window_ticks:
            raise ValueError('Perfect parry window cannot exceed total parry window')
        self.next_parry_tick = 0
        self._next_parry_id = 1
        self._last_attempt = None
        self._session_id = uuid4().hex
        self._stage_instance_id = uuid4().hex
        self._attempts = {}

    @property
    def stage_instance_id(self):
        return self._stage_instance_id

    def bind_stage(self, stage_instance_id):
        """Invalidate earlier-stage attempts without deleting their history."""
        if not isinstance(stage_instance_id, str) or not stage_instance_id.strip():
            raise ValueError('Parry stage instance ID must be a nonempty string')
        if stage_instance_id != self.stage_instance_id:
            self._stage_instance_id = stage_instance_id
            self._last_attempt = None

    def owns(self, attempt):
        """Only a genuine request in this stage can be linked to an attack."""
        return (isinstance(attempt, ParryAttempt)
                and attempt.parry_session_id == self._session_id
                and attempt.stage_instance_id == self.stage_instance_id
                and self._attempts.get(attempt.key) == attempt)

    @property
    def last_attempt(self):
        return self._last_attempt

    def request(self, tick):
        """Start one availability window, or reject without renewing it."""
        _validate_tick(tick)
        if tick < self.next_parry_tick or self.active_at(tick):
            return None
        attempt = ParryAttempt(self._next_parry_id, tick,
                               tick + self.perfect_ticks, tick + self.window_ticks,
                               self._session_id, self.stage_instance_id)
        self._next_parry_id += 1
        self._last_attempt = attempt
        self._attempts[attempt.key] = attempt
        self.next_parry_tick = tick + self.cooldown_ticks
        return attempt

    def state_at(self, tick):
        """Classify a tick using start-inclusive, end-exclusive windows."""
        _validate_tick(tick)
        attempt = self._last_attempt
        if attempt is None or not (attempt.start_tick <= tick < attempt.end_tick):
            return 'inactive'
        if tick < attempt.perfect_end_tick:
            return 'perfect_window'
        return 'normal_window'

    def active_at(self, tick):
        return self.state_at(tick) != 'inactive'

    def perfect_at(self, tick):
        return self.state_at(tick) == 'perfect_window'

    def normal_at(self, tick):
        return self.state_at(tick) == 'normal_window'
