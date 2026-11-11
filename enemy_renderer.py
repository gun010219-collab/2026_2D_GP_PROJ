"""Temporary dark royal Pawn silhouettes; no health or hit feedback."""
from config import TILE_SIZE, cell_center


class EnemyRenderer:
    def draw(self, canvas, enemies):
        unit = TILE_SIZE / 84
        for enemy in enemies:
            if not enemy.active:
                continue
            x, y = cell_center(enemy.col, enemy.row)
            # Light outer silhouette on dark squares; dark inset on light squares.
            canvas.draw_circle(x, y + 16 * unit, round(13 * unit), 205, 199, 187, filled=True)
            canvas.draw_circle(x, y + 16 * unit, round(10 * unit), 69, 48, 54, filled=True)
            canvas.draw_rectangle(x - 11 * unit, y - 12 * unit, x + 11 * unit, y + 5 * unit,
                                  194, 184, 166, filled=True)
            canvas.draw_rectangle(x - 8 * unit, y - 12 * unit, x + 8 * unit, y + 5 * unit,
                                  65, 43, 50, filled=True)
            canvas.draw_rectangle(x - 23 * unit, y - 25 * unit, x + 23 * unit, y - 16 * unit,
                                  205, 194, 172, filled=True)
            canvas.draw_rectangle(x - 20 * unit, y - 22 * unit, x + 20 * unit, y - 18 * unit,
                                  72, 48, 54, filled=True)
            canvas.draw_line(x - 5 * unit, y + 16 * unit, x + 5 * unit, y + 16 * unit,
                             225, 109, 116)
