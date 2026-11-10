"""Menu layout and input state, with no rendering or SDL dependency."""
from dataclasses import dataclass

from config import WINDOW_HEIGHT, WINDOW_WIDTH


@dataclass(frozen=True)
class Rect:
    left: int
    bottom: int
    width: int
    height: int

    def contains(self, point):
        if point is None:
            return False
        x, y = point
        return (self.left <= x < self.left + self.width
                and self.bottom <= y < self.bottom + self.height)


# The top-right control is anchored to the window, independently of board/HUD.
SETTINGS_BUTTON = Rect(WINDOW_WIDTH - 240, WINDOW_HEIGHT - 62, 190, 40)
PANEL = Rect((WINDOW_WIDTH - 600) // 2, (WINDOW_HEIGHT - 400) // 2, 600, 400)
CLOSE_BUTTON = Rect(PANEL.left + 520, PANEL.bottom + 336, 48, 40)
FULLSCREEN_BUTTON = Rect(PANEL.left + 60, PANEL.bottom + 190, 480, 64)
RETURN_BUTTON = Rect(PANEL.left + 60, PANEL.bottom + 70, 480, 64)


class SettingsMenu:
    def __init__(self):
        self.is_open = False

    def key(self, key):
        """Return an action. Callers must not forward consumed input to gameplay."""
        if key == 'f11':
            return 'toggle_fullscreen'
        if key == 'escape':
            if self.is_open:
                self.is_open = False
                return 'consumed'
            return 'quit'
        return 'consumed' if self.is_open else 'gameplay'

    def click(self, point):
        if self.is_open:
            if CLOSE_BUTTON.contains(point) or RETURN_BUTTON.contains(point):
                self.is_open = False
            elif FULLSCREEN_BUTTON.contains(point):
                return 'toggle_fullscreen'
            return 'consumed'
        if SETTINGS_BUTTON.contains(point):
            self.is_open = True
            return 'consumed'
        return 'gameplay'

    def blocks_gameplay(self):
        return self.is_open
