"""Temporary supported-enemy silhouettes; no combat mutation or resources."""
from config import TILE_SIZE, cell_center
from render_motion import display_center


class EnemyRenderer:
    positions = None  # Optional read-only pixel snapshot, supplied by main.

    def draw(self, canvas, enemies):
        unit = TILE_SIZE / 84
        for enemy in enemies:
            if not enemy.active:
                continue
            x, y = display_center(enemy, self.positions)
            logical_x, logical_y = cell_center(*enemy.position)
            if (x, y) != (logical_x, logical_y):
                canvas.draw_rectangle(logical_x-4, logical_y-4, logical_x+4, logical_y+4, 132, 190, 214)
            if enemy.kind == 'queen':
                # Wide low crown, distinct from King's tall central cross.
                for l,b,r,t in ((-19,-17,19,5),(-25,5,25,12),(-24,12,-17,22),
                                (-10,12,-4,20),(4,12,10,20),(17,12,24,22),(-24,-25,24,-19)):
                    canvas.draw_rectangle(x+l*unit,y+b*unit,x+r*unit,y+t*unit,218,207,239,filled=True)
                canvas.draw_rectangle(x-10*unit,y-15*unit,x+10*unit,y+2*unit,57,48,77,filled=True)
                continue
            if enemy.kind == 'king':
                # Wide royal crown with a taller central cross, distinct from Rook.
                for left, bottom, right, top in (
                        (-18, -17, 18, 10), (-20, 8, 20, 16), (-20, 14, -13, 22),
                        (13, 14, 20, 22), (-4, 14, 4, 27), (-9, 20, 9, 24),
                        (-25, -25, 25, -19)):
                    canvas.draw_rectangle(x + left * unit, y + bottom * unit,
                                          x + right * unit, y + top * unit,
                                          222, 192, 123, filled=True)
                canvas.draw_rectangle(x - 12 * unit, y - 16 * unit, x + 12 * unit, y + 5 * unit,
                                      45, 38, 53, filled=True)
                canvas.draw_rectangle(x - 3 * unit, y - 2 * unit, x + 3 * unit, y + 4 * unit,
                                      186, 78, 86, filled=True)
                continue
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
