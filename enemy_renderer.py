"""Temporary supported-enemy silhouettes; no combat mutation or resources."""
from config import TILE_SIZE, cell_center


class EnemyRenderer:
    def draw(self, canvas, enemies):
        unit = TILE_SIZE / 84
        for enemy in enemies:
            if not enemy.active:
                continue
            x, y = cell_center(enemy.col, enemy.row)
            if enemy.kind == 'bishop':
                # Narrow priest/miter silhouette, split crown and diagonal notch.
                for left, bottom, right, top in (
                        (-12, -18, 12, 4), (-10, 4, 10, 16),
                        (-8, 16, -2, 25), (2, 16, 8, 25), (-22, -25, 22, -19)):
                    canvas.draw_rectangle(x + left * unit, y + bottom * unit,
                                          x + right * unit, y + top * unit,
                                          214, 207, 185, filled=True)
                canvas.draw_rectangle(x - 7 * unit, y - 17 * unit, x + 7 * unit, y + 3 * unit,
                                      54, 48, 67, filled=True)
                canvas.draw_line(x - 4 * unit, y + 7 * unit, x + 5 * unit, y + 16 * unit, 62, 48, 69)
                continue
            if enemy.kind == 'knight':
                # Bent neck, forward muzzle and one ear; keep the HP label
                # above y+30 and the warning cell's outer border unobstructed.
                for left, bottom, right, top in (
                        (-15, -16, 10, -5), (-12, -8, 1, 16), (-9, 11, 16, 23),
                        (9, 7, 22, 16), (-10, 21, -3, 27), (-17, 0, -12, 18),
                        (-23, -25, 23, -18)):
                    canvas.draw_rectangle(x + left * unit, y + bottom * unit,
                                          x + right * unit, y + top * unit,
                                          205, 208, 216, filled=True)
                canvas.draw_rectangle(x - 8 * unit, y - 14 * unit, x - 2 * unit, y + 10 * unit,
                                      58, 54, 68, filled=True)
                canvas.draw_rectangle(x + 8 * unit, y + 16 * unit, x + 10 * unit, y + 18 * unit,
                                      33, 38, 48, filled=True)
                continue
            if enemy.kind == 'rook':
                # Broad tower and three crenellations, distinct from the round Pawn.
                canvas.draw_rectangle(x - 19 * unit, y - 18 * unit,
                                      x + 19 * unit, y + 13 * unit, 205, 199, 187, filled=True)
                canvas.draw_rectangle(x - 15 * unit, y - 17 * unit,
                                      x + 15 * unit, y + 10 * unit, 57, 53, 69, filled=True)
                for offset in (-18, -4, 10):
                    canvas.draw_rectangle(x + offset * unit, y + 11 * unit,
                                          x + (offset + 8) * unit, y + 24 * unit,
                                          205, 199, 187, filled=True)
                canvas.draw_rectangle(x - 24 * unit, y - 25 * unit,
                                      x + 24 * unit, y - 19 * unit, 205, 194, 172, filled=True)
                canvas.draw_line(x - 9 * unit, y - 2 * unit, x + 9 * unit, y - 2 * unit,
                                 162, 151, 203)
                continue
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
