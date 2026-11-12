"""Temporary, resource-free outcome overlay; settings are rendered above it."""
from game import GameState
from health_renderer import HealthRenderer
from config import WINDOW_HEIGHT, WINDOW_WIDTH


class GameFlowRenderer:
    def draw(self, canvas, game, error=False):
        if game.playing:
            return
        boundary = game.state is GameState.DEV_BOUNDARY
        clear = boundary or game.state in (GameState.UPGRADE, GameState.STAGE_CLEAR, GameState.BOSS_CLEAR)
        accent = (224, 192, 116) if clear else (196, 112, 107)
        x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        canvas.draw_rectangle(x - 300, y - 165, x + 300, y + 165, *accent, filled=True)
        canvas.draw_rectangle(x - 296, y - 161, x + 296, y + 161, 17, 20, 28, filled=True)
        title = (f'STAGE {game.stage_number} CLEAR' if boundary else 'UPGRADE' if game.state is GameState.UPGRADE else
                 'BOSS CLEAR' if game.state is GameState.BOSS_CLEAR else 'STAGE CLEAR' if clear else 'GAME OVER')
        self._center(canvas, title, 558, 6, accent)
        self._center(canvas, f'CHAPTER {game.chapter} DEVELOPMENT' if boundary else f'STAGE {game.stage_number}',
                     516, 3, (225, 218, 197))
        health = game.player.health
        self._center(canvas, f'HP {health.current_hp}/{health.max_hp}', 475, 4, (231, 230, 220))
        alive = sum(enemy.alive for enemy in game.encounter.enemies)
        label = 'PAWNS' if all(e.kind == 'pawn' for e in game.encounter.enemies) else 'ENEMIES'
        self._center(canvas, f'{label} LEFT {alive}/{len(game.encounter.enemies)}', 439, 3,
                     (202, 204, 209))
        if game.next_stage_number is not None:
            self._center(canvas, f'N TO CHAPTER {game.chapter + 1}', 409, 3, (224, 192, 116))
        if boundary:
            self._center(canvas, f'STAGE {game.stage_number + 1} NOT AVAILABLE', 399, 3, (224, 192, 116))
        restart = ('R TO RESTART' if game.restart_stage_number == game.stage_number
                   else f'R TO STAGE {game.restart_stage_number}')
        if game.restart_stage_number is not None:
            self._center(canvas, restart, 384, 4, (224, 192, 116))
        self._center(canvas, 'ESC TO EXIT', 343, 3, (213, 214, 218))
        self._center(canvas, 'SETTINGS / F11', 310, 2, (180, 184, 193))
        if error:
            self._center(canvas, 'COULD NOT START STAGE  TRY AGAIN', 268, 2, (231, 130, 115))

    def draw_stage_label(self, canvas, game):
        """Small live stage label in the left margin; no outcome panel."""
        if game.playing:
            HealthRenderer._text(canvas, f'STAGE {game.stage_number}', 44, 862, scale=3)
            if game.boss:
                self._draw_boss(canvas, game)

    @staticmethod
    def _draw_boss(canvas, game):
        pulse = game.encounter.pulse
        hp = pulse.king.health
        canvas.draw_rectangle(30, 530, 280, 687, 17, 22, 27, filled=True)
        HealthRenderer._text(canvas, f'KING HP {hp.current_hp}/{hp.max_hp}', 44, 660, scale=3)
        color = (255, 156, 65)
        HealthRenderer._text(canvas, 'CHECKMATE PULSE', 44, 629, color=color)
        labels = {'NORMAL': 'READY' if game.combat.tick >= pulse.next_use_tick else 'RECHARGING',
                  'DRAINING': 'WAITING FOR ATTACKS', 'PULSE_TELEGRAPH': 'PARRY THE PULSE',
                  'PULSE_RESOLUTION': 'RESOLVING', 'CLEANUP': 'CLEANUP'}
        label = labels[pulse.state] if hp.alive else 'KING DEFEATED'
        HealthRenderer._text(canvas, label, 44, 602, color=color)
        if pulse.state == 'PULSE_TELEGRAPH':
            left = max(0, pulse.event.hit_tick - game.combat.tick)
            HealthRenderer._text(canvas, f'HIT IN {left} TICKS', 44, 576)
        elif pulse.state == 'CLEANUP' and pulse.resume_tick is not None:
            HealthRenderer._text(canvas, f'RESUME IN {max(0, pulse.resume_tick-game.combat.tick)}', 44, 576)
        if hp.last_damage_tick is not None and 0 <= game.combat.tick-hp.last_damage_tick < 6:
            HealthRenderer._text(canvas, 'KING HIT', 44, 546, color=HealthRenderer.HIT)

    @staticmethod
    def _center(canvas, text, y, scale, color):
        width = (len(text) * 4 - 1) * scale
        HealthRenderer._text(canvas, text, WINDOW_WIDTH / 2 - width / 2, y, scale=scale, color=color)
