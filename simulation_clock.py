"""Small fixed-step accumulator. Wall time and combat ticks stay separate."""
from math import isfinite

from config import FIXED_TIME_STEP, MAX_SIMULATION_STEPS_PER_FRAME


class SimulationClock:
    def __init__(self):
        self.accumulator = 0.0

    def reset(self):
        self.accumulator = 0.0

    def advance(self, elapsed, paused=False):
        if not isfinite(elapsed) or elapsed < 0:
            raise ValueError('Elapsed frame time must be finite and nonnegative')
        if paused:
            self.reset()
            return 0
        # Drop excessive backlog rather than freeze input in an unbounded loop.
        self.accumulator += min(elapsed, FIXED_TIME_STEP * MAX_SIMULATION_STEPS_PER_FRAME)
        steps = min(int((self.accumulator + 1e-12) / FIXED_TIME_STEP),
                    MAX_SIMULATION_STEPS_PER_FRAME)
        self.accumulator = max(0.0, self.accumulator - steps * FIXED_TIME_STEP)
        return steps
