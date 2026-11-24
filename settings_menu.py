"""Menu layout and input state, with no rendering or SDL dependency."""
from dataclasses import dataclass

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from game_audio import AudioSettings


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
PANEL = Rect((WINDOW_WIDTH - 600) // 2, (WINDOW_HEIGHT - 400) // 2, 600, 528)
CLOSE_BUTTON = Rect(PANEL.left + 520, PANEL.bottom + 458, 48, 40)
FULLSCREEN_BUTTON = Rect(PANEL.left + 60, PANEL.bottom + 190, 480, 64)
RETURN_BUTTON = Rect(PANEL.left + 60, PANEL.bottom + 70, 480, 64)


AUDIO_ROWS = {name: (Rect(PANEL.left+180,y,44,40), Rect(PANEL.left+328,y,44,40),
                     Rect(PANEL.left+390,y,150,40))
              for name,y in (('bgm',PANEL.bottom+369),('sfx',PANEL.bottom+308))}


MAIN_MENU_BUTTON = Rect(PANEL.left+60,PANEL.bottom+12,480,40)


class SettingsMenu:
    def __init__(self):
        self.is_open = False
        self.audio = AudioSettings()
        self.in_frontend = False
        self.can_return_to_title = False

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
            elif self.can_return_to_title and MAIN_MENU_BUTTON.contains(point):
                self.is_open = False
                return 'main_menu'
            elif FULLSCREEN_BUTTON.contains(point):
                return 'toggle_fullscreen'
            elif self._change_audio(point):
                return 'audio_changed'
            return 'consumed'
        if SETTINGS_BUTTON.contains(point):
            self.is_open = True
            return 'consumed'
        return 'gameplay'

    def _change_audio(self, point):
        for name, (minus, plus, mute) in AUDIO_ROWS.items():
            if mute.contains(point):
                attr = name + '_mute'
                setattr(self.audio,attr,not getattr(self.audio,attr))
                return True
            delta = -5 if minus.contains(point) else 5 if plus.contains(point) else 0
            value = getattr(self.audio,name)
            adjusted = max(0,min(100,value+delta))
            if adjusted != value:
                setattr(self.audio,name,adjusted)
                return True
        return False

    def blocks_gameplay(self):
        return self.is_open
