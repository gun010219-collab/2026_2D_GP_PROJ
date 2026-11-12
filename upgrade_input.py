"""Selection edges are independent of frozen combat ticks and gameplay queues."""
from upgrade_renderer import card_at


class UpgradeInput:
    def __init__(self):
        self._held = set()
        self._mouse_held = False

    def reconcile(self, canvas):
        keys = canvas.SDL_GetKeyboardState(None)
        self._held = {ord('1')+i for i in range(3) if keys[30+i]}
        state = canvas.SDL_GetMouseState(None, None)
        self._mouse_held = bool(state & 1) if type(state) is int else False

    def handle(self, event, canvas, point=None, blocked=False):
        c = canvas
        if event.type in (c.SDL_KEYDOWN, c.SDL_KEYUP) and event.key in (49,50,51):
            if event.type == c.SDL_KEYUP:
                self._held.discard(event.key)
                return None
            held = event.key in self._held
            self._held.add(event.key)
            if not blocked and not held and not getattr(event,'repeat',False):
                return event.key-49
        elif event.type == c.SDL_MOUSEBUTTONDOWN and event.button == c.SDL_BUTTON_LEFT:
            held = self._mouse_held
            self._mouse_held = True
            if not blocked and not held:
                return card_at(point)
        elif event.type == 1026 and event.button == c.SDL_BUTTON_LEFT:
            self._mouse_held = False
        return None
