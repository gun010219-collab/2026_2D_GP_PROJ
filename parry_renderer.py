"""Temporary defensive availability halo; never indicates parry success."""
from config import TILE_SIZE, cell_center


class ParryRenderer:
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
