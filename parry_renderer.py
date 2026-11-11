"""Separate temporary input-window and actual-result feedback; read-only."""
from config import TILE_SIZE, cell_center
from health_renderer import HealthRenderer


class ParryRenderer:
    """Input-relative window preview, never an actual success indicator."""
    def draw(self, canvas, player, parry, tick):
        state = parry.state_at(tick)
        if state == 'inactive':
            return
        x, y = cell_center(player.col, player.row)
        unit = TILE_SIZE / 84
        # Hollow rings leave attack-warning cells and the player center visible.
        for radius, color in ((39, (13, 24, 36)), (37, (91, 174, 218)),
                              (35, (205, 222, 231))):
            canvas.draw_circle(x, y, round(radius * unit), *color)
        if state == 'perfect_window':
            # These gold marks mean timing availability, not PERFECT/SUCCESS.
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                canvas.draw_line(x + dx * 34 * unit, y + dy * 34 * unit,
                                 x + dx * 39 * unit, y + dy * 39 * unit,
                                 232, 199, 112)


class ParryResultRenderer:
    """Display only the immutable adjudicated result, for 18 combat ticks.

    The caller hides results for a dead player, whose combat clock is frozen.
    No attack, binding, damage, stun or reward is changed by rendering.
    """
    FEEDBACK_TICKS = 18  # Temporary readability choice, not a combat window.
    NORMAL = (127, 208, 250)
    PERFECT = (255, 226, 116)
    NEUTRAL = (193, 195, 203)

    def draw(self, canvas, result, tick):
        if (result is None or result.status not in ('normal', 'perfect', 'failed', 'unbound')
                or not 0 <= tick - result.tick < self.FEEDBACK_TICKS):
            return
        labels = {'normal': 'PARRY SUCCESS', 'perfect': 'PERFECT PARRY',
                  'failed': 'PARRY FAILED', 'unbound': 'NO LINK'}
        color = (self.PERFECT if result.status == 'perfect' else
                 self.NORMAL if result.status == 'normal' else self.NEUTRAL)
        canvas.draw_rectangle(30, 652, 270, 690, 17, 22, 27, filled=True)
        HealthRenderer._text(canvas, labels[result.status], 44, 663, scale=3, color=color)
        if not result.successful:
            return
        x, y = cell_center(*result.player_cell)
        unit = TILE_SIZE / 84
        if result.status == 'normal':
            # Success corners differ from the circular input-window preview.
            for sx in (-1, 1):
                for sy in (-1, 1):
                    px, py = x + sx * 31 * unit, y + sy * 31 * unit
                    canvas.draw_line(px, py, px - sx * 9 * unit, py, *color)
                    canvas.draw_line(px, py, px, py - sy * 9 * unit, *color)
        else:
            # A brighter inner ring and eight short rays identify actual perfect
            # success. Every endpoint stays within the resolved player's cell.
            canvas.draw_circle(x, y, round(31 * unit), *color)
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                diagonal_scale = .71 if dx and dy else 1
                canvas.draw_line(x + dx * 28 * unit * diagonal_scale,
                                 y + dy * 28 * unit * diagonal_scale,
                                 x + dx * 38 * unit * diagonal_scale,
                                 y + dy * 38 * unit * diagonal_scale, *color)
