"""Input-relative parry availability windows; no enemy or success resolution.

The caller supplies Combat.tick. This module owns no clock and never infers a
successful block from an availability window.
"""
from dataclasses import dataclass

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

    @property
    def last_attempt(self):
        return self._last_attempt

    def request(self, tick):
        """Start one availability window, or reject without renewing it."""
        _validate_tick(tick)
        if tick < self.next_parry_tick or self.active_at(tick):
            return None
        attempt = ParryAttempt(self._next_parry_id, tick,
                               tick + self.perfect_ticks, tick + self.window_ticks)
        self._next_parry_id += 1
        self._last_attempt = attempt
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
