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
        self._center(canvas, f'STAGE {game.stage_number}', 516, 3, (225, 218, 197))
        health = game.player.health
        self._center(canvas, f'HP {health.current_hp}/{health.max_hp}', 475, 4, (231, 230, 220))
        alive = sum(enemy.alive for enemy in game.encounter.enemies)
        label = 'PAWNS' if all(e.kind == 'pawn' for e in game.encounter.enemies) else 'ENEMIES'
        self._center(canvas, f'{label} LEFT {alive}/{len(game.encounter.enemies)}', 439, 3,
                     (202, 204, 209))
        if game.next_stage_number is not None:
            self._center(canvas, 'N TO CONTINUE', 409, 3, (224, 192, 116))
        restart = ('R TO RESTART' if game.restart_stage_number == game.stage_number
                   else f'R TO STAGE {game.restart_stage_number}')
        self._center(canvas, restart, 384, 4, (224, 192, 116))
        self._center(canvas, 'ESC TO EXIT', 343, 3, (213, 214, 218))
        self._center(canvas, 'SETTINGS / F11', 310, 2, (180, 184, 193))

    def draw_stage_label(self, canvas, game):
        """Small live stage label in the left margin; no outcome panel."""
        if game.playing:
            HealthRenderer._text(canvas, f'STAGE {game.stage_number}', 44, 862, scale=3)

    @staticmethod
    def _center(canvas, text, y, scale, color):
        width = (len(text) * 4 - 1) * scale
        HealthRenderer._text(canvas, text, WINDOW_WIDTH / 2 - width / 2, y, scale=scale, color=color)
