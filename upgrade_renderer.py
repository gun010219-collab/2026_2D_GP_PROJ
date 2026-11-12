"""Read-only three-card view and shared logical hit rectangles."""
from health_renderer import HealthRenderer
from settings_menu import Rect
from config import WINDOW_WIDTH


CARD_RECTS = tuple(Rect(330 + i * 260, 255, 240, 325) for i in range(3))


def card_at(point):
    return next((i for i, rect in enumerate(CARD_RECTS) if rect.contains(point)), None)


class UpgradeRenderer:
    def draw(self, canvas, game, offer, error=False):
        if offer is None:
            return
        canvas.draw_rectangle(310, 180, 1130, 740, 17, 20, 28, filled=True)
        self._center(canvas, 'UPGRADE', 675, 6)
        self._center(canvas, f'STAGE {game.stage_number} CLEAR', 626, 3)
        self._center(canvas, 'CHOOSE ONE  1 2 3 OR CLICK', 205, 3)
        for i, (rect, option) in enumerate(zip(CARD_RECTS, offer.options)):
            color = (224, 192, 116) if option.enabled else (110, 115, 122)
            l, b, w, h = rect.left, rect.bottom, rect.width, rect.height
            canvas.draw_rectangle(l, b, l+w, b+h, *color, filled=True)
            canvas.draw_rectangle(l+3, b+3, l+w-3, b+h-3, 25, 31, 42, filled=True)
            label = ('ATTACK', 'MAX HP', 'MOVE')[i]
            self._text(canvas, f'{i+1} {label}', l+20, b+265, scale=3, color=color)
            self._text(canvas, f'LEVEL {option.current_level}', l+20, b+210, scale=3)
            self._text(canvas, f'NOW {option.current_value}', l+20, b+155, scale=3)
            if option.is_max:
                self._text(canvas, 'MAX', l+20, b+95, scale=5, color=color)
            else:
                self._text(canvas, f'NEXT {option.next_value}', l+20, b+95, scale=3, color=color)
            if i == 2:
                self._text(canvas, 'TICKS PER MOVE', l+20, b+40, scale=2)
        if error:
            self._text(canvas, 'COULD NOT START STAGE  TRY AGAIN', 355, 160, scale=2, color=(231, 130, 115))

    _text = staticmethod(HealthRenderer._text)

    def _center(self, canvas, label, y, scale):
        width = (len(label) * 4 - 1) * scale
        self._text(canvas, label, (WINDOW_WIDTH-width)/2, y, scale=scale)
