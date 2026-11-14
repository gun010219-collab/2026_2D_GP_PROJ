"""Display-only bounded motion. No combat clocks, entities or ledgers are mutated."""
from math import isfinite, sin, pi
from config import cell_center, MOTION_SECONDS


class RenderMotion:
    def __init__(self, duration=MOTION_SECONDS):
        if isinstance(duration, bool) or not isfinite(duration) or duration <= 0:
            raise ValueError('Motion duration must be positive and finite')
        self.duration = duration
        self.time = 0.0
        self.session = None
        self._tracks = {}
        self.positions = {}

    def _sample(self, track):
        origin, target, started, kind = track
        t = min(1.0, max(0.0, (self.time - started) / self.duration))
        u = t * t * (3 - 2 * t)
        x = origin[0] + (target[0] - origin[0]) * u
        y = origin[1] + (target[1] - origin[1]) * u
        if kind == 'knight' and origin != target:
            y += 18 * sin(pi * t)
        return x, y

    def update(self, entities, elapsed, *, session, snap=False, frozen=()):
        if isinstance(elapsed, bool) or not isfinite(elapsed) or elapsed < 0:
            raise ValueError('Visual elapsed must be finite and nonnegative')
        if self.session != session:
            self._tracks.clear()
            self.session = session
        self.time += elapsed
        frozen = set(frozen)
        live = set()
        for entity in entities:
            key = entity.entity_instance_id
            if not entity.alive or not getattr(entity, 'active', True):
                continue
            live.add(key)
            target = cell_center(*entity.position)
            kind = getattr(entity, 'kind', 'player')
            track = self._tracks.get(key)
            if snap or key in frozen or track is None or kind == 'bishop':
                track = (target, target, self.time, kind)
            elif target != track[1]:
                # Never draw a diagonal shortcut through intervening occupied cells.
                origin = self._sample(track)
                old_cell = track[1]
                dx, dy = target[0] - old_cell[0], target[1] - old_cell[1]
                legal_line = kind == 'knight' or dx == 0 or dy == 0 or abs(dx) == abs(dy)
                track = (origin if legal_line else target, target, self.time, kind)
            self._tracks[key] = track
        self._tracks = {k: v for k, v in self._tracks.items() if k in live}
        self.positions = {k: self._sample(v) for k, v in self._tracks.items()}


def display_center(entity, positions=None):
    if positions is not None:
        return positions.get(entity.entity_instance_id, cell_center(*entity.position))
    return cell_center(*entity.position)
