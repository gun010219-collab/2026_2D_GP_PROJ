"""Temporary target-cell slash feedback; no hit/damage claims or textures."""
from board import tile_bounds


class AttackRenderer:
    def draw(self, canvas, attack):
        if attack is None:
            return
        left, bottom, right, top = tile_bounds(*attack.target_cell)
        # Every effect pixel stays within the exact logical target cell.
        canvas.draw_rectangle(left, bottom, right - 1, top - 1, 19, 31, 46)
        canvas.draw_rectangle(left + 2, bottom + 2, right - 3, top - 3, 228, 191, 104)
        canvas.draw_rectangle(left + 4, bottom + 4, right - 5, top - 5, 95, 176, 216)
        w, h = right - left, top - bottom
        # Short parallel ivory/gold slashes, a range marker rather than a HIT flash.
        for offset in (-2, 0, 2):
            canvas.draw_line(left + w * 0.22, bottom + h * 0.23 + offset,
                             left + w * 0.76, bottom + h * 0.77 + offset,
                             241, 228, 187)
