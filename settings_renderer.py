"""Black/gold menu rendering and owned, cached text textures."""
import ctypes
import os
from pathlib import Path

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from settings_menu import SETTINGS_BUTTON, PANEL, CLOSE_BUTTON, FULLSCREEN_BUTTON, RETURN_BUTTON


class SettingsRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.textures = {}
        # Use the installed Windows font without copying or distributing it.
        font_path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'segoeui.ttf'
        font = canvas.load_font(str(font_path), 24)
        try:
            for text in ('SETTINGS', 'X', 'FULLSCREEN: ON', 'FULLSCREEN: OFF',
                         'RETURN TO GAME', 'F11 - TOGGLE DISPLAY', 'DISPLAY SWITCH FAILED'):
                self._cache_text(font, text)
        except Exception:
            self.close()
            raise
        finally:
            canvas.TTF_CloseFont(font.font)

    def _cache_text(self, font, text):
        c = self.canvas
        surface = c.TTF_RenderUTF8_Blended(font.font, text.encode('utf-8'), c.SDL_Color(223, 194, 130))
        if not surface:
            raise RuntimeError('Cannot render settings text')
        try:
            texture = c.SDL_CreateTextureFromSurface(c.renderer, surface)
            if not texture:
                raise RuntimeError('Cannot create settings text texture')
            self.textures[text] = texture, surface.contents.w, surface.contents.h
        finally:
            c.SDL_FreeSurface(surface)

    def _label(self, text, x, y):
        c = self.canvas
        texture, w, h = self.textures[text]
        target = c.SDL_Rect(int(x - w / 2), int(WINDOW_HEIGHT - 1 - y - h / 2), w, h)
        c.SDL_RenderCopy(c.renderer, texture, None, ctypes.byref(target))

    def _rect(self, rect, color, alpha=255):
        self.canvas.draw_rectangle(rect.left, rect.bottom,
                                   rect.left + rect.width - 1, rect.bottom + rect.height - 1,
                                   *color, a=alpha, filled=True)

    def _button(self, rect, label):
        from settings_menu import Rect
        self._rect(rect, (174, 139, 73))
        self._rect(Rect(rect.left + 2, rect.bottom + 2, rect.width - 4, rect.height - 4), (22, 22, 29))
        self._label(label, rect.left + rect.width / 2, rect.bottom + rect.height / 2)

    def draw(self, menu, display):
        from settings_menu import Rect
        c = self.canvas
        self._button(SETTINGS_BUTTON, 'SETTINGS')
        if not menu.is_open:
            return
        old_mode = ctypes.c_int()
        if c.SDL_GetRenderDrawBlendMode(c.renderer, ctypes.byref(old_mode)) != 0:
            raise RuntimeError('Cannot read SDL blend mode')
        if c.SDL_SetRenderDrawBlendMode(c.renderer, c.SDL_BLENDMODE_BLEND) != 0:
            raise RuntimeError('Cannot enable menu alpha blending')
        try:
            self._rect(Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), (0, 0, 0), 175)
        finally:
            c.SDL_SetRenderDrawBlendMode(c.renderer, old_mode.value)
        self._rect(PANEL, (174, 139, 73))
        self._rect(Rect(PANEL.left + 3, PANEL.bottom + 3, PANEL.width - 6, PANEL.height - 6), (17, 18, 25))
        self._label('SETTINGS', WINDOW_WIDTH / 2, PANEL.bottom + 345)
        self._button(CLOSE_BUTTON, 'X')
        self._button(FULLSCREEN_BUTTON, 'FULLSCREEN: ON' if display.fullscreen else 'FULLSCREEN: OFF')
        self._button(RETURN_BUTTON, 'RETURN TO GAME')
        self._label('F11 - TOGGLE DISPLAY', WINDOW_WIDTH / 2, PANEL.bottom + 160)
        if display.error:
            self._label('DISPLAY SWITCH FAILED', WINDOW_WIDTH / 2, PANEL.bottom + 38)

    def close(self):
        for texture, _, _ in self.textures.values():
            self.canvas.SDL_DestroyTexture(texture)
        self.textures.clear()
