"""Immutable parry links/results and exact hit-relative 60Hz classification.

Preview durations in Parry are deliberately independent: the old eight-tick
gold ring is not the criterion for perfect success at an enemy hit_tick.
"""
from dataclasses import dataclass


def grade_for_delta(delta_ticks):
    if type(delta_ticks) is not int:
        raise TypeError('Parry delta must be an integer tick interval')
    if 1 <= delta_ticks <= 7:
        return 'perfect'
    if 8 <= delta_ticks <= 18:
        return 'normal'
    return None


@dataclass(frozen=True)
class ParryBinding:
    attempt_key: tuple
    parry_id: int
    parry_start_tick: int
    linked_enemy_event_key: tuple | None
    expected_hit_tick: int | None
    adjudication_grade: str | None


@dataclass(frozen=True)
class ParryResult:
    parry_id: int
    status: str
    tick: int
    player_cell: tuple[int, int]
    enemy_event_key: tuple | None
    reason: str

    @property
    def successful(self):
        return self.status in ('normal', 'perfect')
