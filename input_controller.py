"""Edge-triggered cardinal movement, independent of SDL and rendering."""
from player import DIRECTIONS


class InputController:
    def __init__(self):
        self._held = set()

    def key_down(self, direction, player, blocked=False):
        if direction not in DIRECTIONS:
            return False
        if direction in self._held:
            return False
        chord_in_progress = bool(self._held)
        self._held.add(direction)
        if blocked or chord_in_progress:
            return False
        return player.move(direction)

    def key_up(self, direction):
        self._held.discard(direction)
