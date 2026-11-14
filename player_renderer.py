"""Temporary procedural silver/blue player marker, replaceable by sprites."""
from config import TILE_SIZE, cell_center
from render_motion import display_center
from player import DIRECTIONS


class PlayerRenderer:
    positions = None  # Optional read-only pixel snapshot, supplied by main.

    def draw(self, canvas, player):
        x, y = display_center(player, self.positions)
        logical_x, logical_y = cell_center(*player.position)
        if (x, y) != (logical_x, logical_y):
            canvas.draw_rectangle(logical_x-4, logical_y-4, logical_x+4, logical_y+4, 132, 190, 214)
        unit = TILE_SIZE / 84
        r = round(28 * unit)
        # Dark outline + cyan rim remain legible on both marble tile values.
        canvas.draw_circle(x, y, r, 12, 19, 29, filled=True)
        canvas.draw_circle(x, y, r - 3, 86, 164, 206, filled=True)
        canvas.draw_circle(x, y, r - 6, 32, 48, 68, filled=True)
        canvas.draw_rectangle(x - 15 * unit, y - 18 * unit, x + 15 * unit, y + 5 * unit,
                              218, 225, 223, filled=True)
        canvas.draw_circle(x, y + 9 * unit, round(12 * unit), 238, 235, 217, filled=True)
        canvas.draw_line(x - 7 * unit, y + 9 * unit, x + 7 * unit, y + 9 * unit, 33, 57, 77)
        canvas.draw_line(x, y - 14 * unit, x, y + 1 * unit, 171, 140, 75)
        # A three-sided arrow outside the rim identifies facing, not an attack area.
        dx, dy = DIRECTIONS[player.facing]
        tip = x + dx * 36 * unit, y + dy * 36 * unit
        base = x + dx * 28 * unit, y + dy * 28 * unit
        a = base[0] - dy * 5 * unit, base[1] + dx * 5 * unit
        b = base[0] + dy * 5 * unit, base[1] - dx * 5 * unit
        for start, end in ((a, tip), (tip, b), (b, a)):
            canvas.draw_line(*start, *end, 232, 199, 112)
