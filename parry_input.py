"""Two Shift keys share one edge-triggered latch without SDL dependencies."""

SHIFT_KEYS = frozenset(('left', 'right'))


class ParryInput:
    def __init__(self):
        self._held = set()

    @property
    def held(self):
        return frozenset(self._held)

    def key_down(self, key, parry, tick, blocked=False):
        if key not in SHIFT_KEYS or key in self._held:
            return None
        chord_in_progress = bool(self._held)
        self._held.add(key)
        if blocked or chord_in_progress:
            return None
        return parry.request(tick)

    def key_up(self, key):
        self._held.discard(key)

    def reconcile(self, held_keys):
        """Synchronize transition state without creating a parry attempt."""
        self._held = set(held_keys) & SHIFT_KEYS
