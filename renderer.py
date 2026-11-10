"""Procedural board foundation, not final texture or sprite assets.

No Pico2D import: the active canvas is supplied by main. Static draw commands
are built once per theme, with no per-frame texture loading or randomness.
"""
from board import is_light_tile, iter_tiles, tile_bounds
from chapter_themes import get_theme
from config import (
    BOARD_BOTTOM, BOARD_LEFT, BOARD_PIXEL_SIZE, HUD_BOTTOM, HUD_HEIGHT,
    HUD_LEFT, HUD_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH,
)


def tint(color, amount):
    return tuple(max(0, min(255, channel + amount)) for channel in color)


class BoardRenderer:
    def __init__(self, chapter=1):
        self.theme = get_theme(chapter)
        self._commands = tuple(self._build_commands())

    def _build_commands(self):
        t = self.theme
        left, bottom = BOARD_LEFT, BOARD_BOTTOM
        right, top = left + BOARD_PIXEL_SIZE, bottom + BOARD_PIXEL_SIZE
        # Each rect has half-open bounds. Adapt to Pico2D inclusive pixels in draw().
        yield ('rect', (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), t.background)
        yield ('rect', (left - 24, bottom - 27, right + 28, top + 19), tint(t.background, -8))
        yield ('rect', (left - 20, bottom - 20, right + 20, top + 20), t.accent)
        yield ('rect', (left - 18, bottom - 18, right + 18, top + 18), t.frame)
        yield ('rect', (left - 7, bottom - 7, right + 7, top + 7), tint(t.accent, -28))
        yield ('rect', (left - 4, bottom - 4, right + 4, top + 4), tint(t.tile_dark, -18))

        for col, row in iter_tiles():
            x1, y1, x2, y2 = tile_bounds(col, row)
            light = is_light_tile(col, row)
            color = t.tile_light if light else t.tile_dark
            yield ('rect', (x1, y1, x2, y2), color)
            # Fine edge bevels keep the grid visible without gaps between cells.
            yield ('line', (x1, y2 - 1, x2 - 1, y2 - 1), tint(color, 9))
            yield ('line', (x2 - 1, y1, x2 - 1, y2 - 2), tint(color, -12))
            if t.chapter == 1:
                # Sparse, deterministic marble seams; keep the cell center quiet.
                offset = (col * 13 + row * 7) % 18
                vein = tint(color, -7 if light else 6)
                yield ('line', (x1 + 7, y1 + 15 + offset, x1 + 26, y1 + 21 + offset), vein)
                yield ('line', (x1 + 26, y1 + 21 + offset, x1 + 39, y1 + 18 + offset), vein)

        # Corner inlays stay outside playable cells.
        for x in (left - 12, right + 12):
            for y in (bottom - 12, top + 12):
                for a, b in [((-4, 0), (0, 4)), ((0, 4), (4, 0)),
                             ((4, 0), (0, -4)), ((0, -4), (-4, 0))]:
                    yield ('line', (x + a[0], y + a[1], x + b[0], y + b[1]), t.accent)

        # HUD is a visual frame only: no invented health, currency, or stage data.
        x1, y1 = HUD_LEFT, HUD_BOTTOM
        x2, y2 = x1 + HUD_WIDTH, y1 + HUD_HEIGHT
        yield ('rect', (x1, y1, x2, y2), tint(t.frame, -5))
        yield ('rect', (x1 + 2, y1 + 2, x2 - 2, y2 - 2), t.hud_background)
        yield ('rect', (x1 + 24, y2 - 32, x2 - 24, y2 - 29), t.hud_accent)
        yield ('line', (x1 + 24, y1 + 24, x2 - 25, y1 + 24), tint(t.hud_accent, -55))

    def draw(self, canvas):
        for kind, bounds, color in self._commands:
            if kind == 'rect':
                x1, y1, x2, y2 = bounds
                canvas.draw_rectangle(x1, y1, x2 - 1, y2 - 1, *color, filled=True)
            else:
                canvas.draw_line(*bounds, *color)
