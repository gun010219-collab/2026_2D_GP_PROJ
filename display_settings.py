"""SDL desktop-fullscreen adapter. Never recreates the window or renderer."""
import ctypes
import logging
from math import isfinite

from config import WINDOW_HEIGHT, WINDOW_WIDTH

LOG = logging.getLogger(__name__)


def logical_mouse_to_canvas(x, y):
    """SDL logical mouse pixels (top-left) -> Pico2D pixels (bottom-left).

    SDL_RenderSetLogicalSize already scales mouse events, including letterbox
    offsets. Do not call SDL_RenderWindowToLogical again on these event values.
    """
    if not isfinite(x) or not isfinite(y):
        return None
    if not (0 <= x < WINDOW_WIDTH and 0 <= y < WINDOW_HEIGHT):
        return None
    return x, WINDOW_HEIGHT - 1 - y


class DisplaySettings:
    def __init__(self, canvas):
        self.canvas = canvas
        self.error = ''
        self._windowed_bounds = None
        canvas.SDL_SetHint(b'SDL_RENDER_LOGICAL_SIZE_MODE', b'letterbox')
        if canvas.SDL_RenderSetLogicalSize(canvas.renderer, WINDOW_WIDTH, WINDOW_HEIGHT) != 0:
            raise RuntimeError('Cannot configure SDL logical rendering: ' + self._sdl_error())

    def _sdl_error(self):
        return self.canvas.SDL_GetError().decode('utf-8', errors='replace')

    @property
    def fullscreen(self):
        # Read actual flags, including changes outside this menu.
        return bool(self.canvas.SDL_GetWindowFlags(self.canvas.window)
                    & self.canvas.SDL_WINDOW_FULLSCREEN)

    def _bounds(self):
        x, y, w, h = (ctypes.c_int() for _ in range(4))
        self.canvas.SDL_GetWindowPosition(self.canvas.window, ctypes.byref(x), ctypes.byref(y))
        self.canvas.SDL_GetWindowSize(self.canvas.window, ctypes.byref(w), ctypes.byref(h))
        return x.value, y.value, w.value, h.value

    def toggle(self):
        c = self.canvas
        was_fullscreen = self.fullscreen
        if not was_fullscreen:
            self._windowed_bounds = self._bounds()
        target = 0 if was_fullscreen else c.SDL_WINDOW_FULLSCREEN_DESKTOP
        result = c.SDL_SetWindowFullscreen(c.window, target)
        self.error = ''
        if result != 0:
            self.error = 'Fullscreen switch failed: ' + self._sdl_error()
        elif self.fullscreen == was_fullscreen:
            self.error = 'Fullscreen switch did not reach the requested state'
        elif was_fullscreen and self._windowed_bounds is not None:
            x, y, w, h = self._windowed_bounds
            c.SDL_SetWindowSize(c.window, w, h)
            c.SDL_SetWindowPosition(c.window, x, y)
            if self._bounds() != self._windowed_bounds:
                self.error = 'Window manager did not restore the saved window bounds'
        if self.error:
            LOG.error(self.error)
        return not self.error
