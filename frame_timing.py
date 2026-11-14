"""Independent render budget and bounded real frame-time statistics; no SDL imports."""
from collections import deque
from math import ceil, isfinite
from config import RENDER_TARGET_FPS


def seconds(value):
    if isinstance(value, bool) or not isfinite(value) or value < 0:
        raise ValueError('Time must be finite and nonnegative')
    return value


class FramePacer:
    def __init__(self, fps=RENDER_TARGET_FPS):
        if isinstance(fps, bool) or not isfinite(fps) or fps <= 0:
            raise ValueError('FPS must be positive and finite')
        self.interval = 1.0 / fps

    def remaining(self, work_seconds):
        return max(0.0, self.interval - seconds(work_seconds))


class FrameStats:
    def __init__(self, capacity=600):
        if type(capacity) is not int or capacity < 1:
            raise ValueError('Capacity must be positive integer')
        self.samples = deque(maxlen=capacity)
        self.previous = None

    def record(self, now, ticks=0, active=True):
        seconds(now)
        if type(ticks) is not int or ticks < 0:
            raise ValueError('Tick delta must be nonnegative integer')
        if self.previous is not None:
            dt = seconds(now - self.previous)
            if dt > 0:
                self.samples.append((dt, ticks, active))
        self.previous = now

    def report(self):
        if not self.samples:
            return None
        times = sorted(dt for dt, _, _ in self.samples)
        total = sum(times)
        active_time = sum(dt for dt, _, active in self.samples if active)
        ticks = sum(n for _, n, active in self.samples if active)
        return dict(fps=len(times)/total, mean_ms=total/len(times)*1000,
                    p95_ms=times[ceil(.95*len(times))-1]*1000,
                    p99_ms=times[ceil(.99*len(times))-1]*1000,
                    max_ms=times[-1]*1000, simulation_hz=ticks/active_time if active_time else 0,
                    samples=len(times))

    def log(self):
        r = self.report()
        if r:
            print('CHECKMATE FRAME target=180 fps={fps:.2f} mean_ms={mean_ms:.3f} '
                  'p95_ms={p95_ms:.3f} p99_ms={p99_ms:.3f} max_ms={max_ms:.3f} '
                  'active_sim_hz={simulation_hz:.2f} samples={samples}'.format(**r), flush=True)
