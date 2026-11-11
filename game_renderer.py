"""Temporary, resource-free outcome overlay; settings are rendered above it."""
from game import GameState
from health_renderer import HealthRenderer
from config import WINDOW_HEIGHT, WINDOW_WIDTH


class GameFlowRenderer:
    def draw(self, canvas, game):
        if game.playing:
            return
        clear = game.state is GameState.STAGE_CLEAR
        accent = (224, 192, 116) if clear else (196, 112, 107)
        x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        canvas.draw_rectangle(x - 300, y - 165, x + 300, y + 165, *accent, filled=True)
        canvas.draw_rectangle(x - 296, y - 161, x + 296, y + 161, 17, 20, 28, filled=True)
        self._center(canvas, 'STAGE CLEAR' if clear else 'GAME OVER', 558, 6, accent)
        self._center(canvas, 'STAGE 1', 516, 3, (225, 218, 197))
        health = game.player.health
        self._center(canvas, f'HP {health.current_hp}/{health.max_hp}', 475, 4, (231, 230, 220))
        alive = sum(enemy.alive for enemy in game.encounter.enemies)
        self._center(canvas, f'PAWNS LEFT {alive}/{len(game.encounter.enemies)}', 439, 3,
                     (202, 204, 209))
        self._center(canvas, 'R TO RESTART', 384, 4, (224, 192, 116))
        self._center(canvas, 'ESC TO EXIT', 343, 3, (213, 214, 218))
        self._center(canvas, 'SETTINGS / F11', 310, 2, (180, 184, 193))

    @staticmethod
    def _center(canvas, text, y, scale, color):
        width = (len(text) * 4 - 1) * scale
        HealthRenderer._text(canvas, text, WINDOW_WIDTH / 2 - width / 2, y, scale=scale, color=color)
