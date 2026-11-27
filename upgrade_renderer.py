"""Read-only three-card view and shared logical hit rectangles."""
from health_renderer import HealthRenderer
from game import GameState
from settings_menu import Rect
from config import WINDOW_WIDTH
from ui_theme import DIM, PALE, ROSE, SILVER, current


CARD_RECTS = tuple(Rect(330 + i * 260, 255, 240, 325) for i in range(3))


def card_at(point):
    return next((i for i, rect in enumerate(CARD_RECTS) if rect.contains(point)), None)


class UpgradeRenderer:
    def draw(self, canvas, game, offer, error=False):
        if offer is None or (game.state is GameState.UPGRADE and not game.upgrade_selection_enabled):
            return
        theme = current(canvas)
        if theme:
            self._draw_themed(theme,game,offer,error)
            return
        canvas.draw_rectangle(310, 180, 1130, 740, 17, 20, 28, filled=True)
        self._center(canvas, 'UPGRADE', 675, 6)
        self._center(canvas, f'STAGE {game.stage_number} CLEAR', 626, 3)
        if game.state is GameState.UPGRADE and not game.upgrade_selection_enabled:
            self._center(canvas, f'STAGE {game.stage_number + 1} NOT AVAILABLE', 492, 4)
            self._center(canvas, 'UPGRADE ON HOLD', 420, 4)
            self._center(canvas, 'ESC TO EXIT  SETTINGS / F11', 255, 3)
            return
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

    @staticmethod
    def _draw_themed(theme,game,offer,error):
        theme.combat_frame('rewards',302,184)
        theme.text(f'CHAPTER {game.chapter:02}   ·   STAGE {game.stage_number:02}',720,684,size=17,color=PALE)
        theme.text('STAGE CLEAR',720,645,size=51,display=True)
        theme.text('Choose a reward',720,602,size=22,color=PALE)
        pointer = theme.pointer()
        for i,(rect,option,name,icon) in enumerate(zip(CARD_RECTS,offer.options,
              ('ATTACK POWER','MAX HP','MOVE SPEED'),('attack','hp','move')),1):
            enabled = option.enabled
            hovered = enabled and rect.contains(pointer)
            x,y = rect.left+rect.width//2,rect.bottom
            tint = (255,161,175) if hovered else None if enabled else (156,147,152)
            theme.combat_frame('card',rect.left,y,tint=tint)
            theme.text(str(i),rect.left+30,y+290,size=17,color=ROSE if enabled else DIM)
            theme.sprite(icon,Rect(x-49,y+207,98,94))
            theme.text(name,x,y+187,size=24,display=True,color=SILVER if enabled else DIM,width=207)
            theme.rule(x,y+161,142)
            rank = f'LEVEL {option.current_level}'
            if enabled:
                rank += f'  →  {option.next_level}'
            theme.text(rank,x,y+135,size=17,color=PALE)
            delta = f'{option.current_value}  →  {option.next_value}' if enabled else str(option.current_value)
            theme.text(delta,x,y+96,size=40,color=ROSE if enabled else DIM,width=206)
            note = ('Maximum level' if option.is_max else 'Ticks per move · lower is faster' if icon=='move'
                    else 'Maximum health' if icon=='hp' else 'Damage per attack')
            theme.text(note,x,y+55 if enabled else y+43,size=18,color=PALE if enabled else DIM,width=213)
            if enabled:
                hp_note = '+1 current and max HP' if icon == 'hp' else 'Current HP carries over'
                theme.text(hp_note,x,y+28,size=16,color=PALE,width=213)
        theme.text('1 / 2 / 3  ·  Select a card',720,219,size=21,color=PALE)
        if error:
            theme.text('Could not start stage. Try again.',720,153,size=21,color=ROSE)
