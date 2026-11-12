"""Edge-triggered cardinal movement, independent of SDL and rendering."""
from player import DIRECTIONS


class InputController:
    def __init__(self, *, move_interval_ticks=None):
        if move_interval_ticks is not None and (type(move_interval_ticks) is not int
                                                or move_interval_ticks <= 0):
            raise ValueError('Movement interval must be positive integer ticks or None')
        self._held = set()
        self._move_interval_ticks = move_interval_ticks
        self._next_move_tick = 0
        self._last_tick = 0

    @property
    def next_move_tick(self):
        return self._next_move_tick

    @property
    def move_interval_ticks(self):
        return self._move_interval_ticks

    def key_down(self, direction, player, blocked=False, occupied=(), *, tick=None):
        if direction not in DIRECTIONS:
            return False
        if self.move_interval_ticks is not None or tick is not None:
            if type(tick) is not int or tick < self._last_tick:
                raise ValueError('Movement requires nonnegative monotonic Combat ticks')
            self._last_tick = tick
        if direction in self._held:
            return False
        chord_in_progress = bool(self._held)
        self._held.add(direction)
        if blocked or chord_in_progress:
            return False
        if self.move_interval_ticks is not None and tick < self.next_move_tick:
            return False  # Discard the whole input, including facing; never queue it.
        moved = player.move(direction, occupied=occupied)
        if moved and self.move_interval_ticks is not None:
            self._next_move_tick = tick + self.move_interval_ticks
        return moved

    def key_up(self, direction):
        self._held.discard(direction)

    def reconcile(self, held_directions):
        """Recover keys after focus loss without movement or per-frame resets."""
        self._held = set(held_directions) & DIRECTIONS.keys()
