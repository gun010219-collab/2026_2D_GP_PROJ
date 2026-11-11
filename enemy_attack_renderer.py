"""Exact enemy telegraph cells; queried ledger state never consumes attacks."""
from board import tile_bounds


class EnemyAttackRenderer:
    def draw(self, canvas, ledger):
        for event in ledger.telegraphs:
            for col, row in event.target_cells:
                left, bottom, right, top = tile_bounds(col, row)
                canvas.draw_rectangle(left, bottom, right - 1, top - 1, 47, 14, 25)
                canvas.draw_rectangle(left + 2, bottom + 2, right - 3, top - 3, 231, 87, 111)
                # Dashed in-cell stripes distinguish danger from gold attacks/blue defense.
                for offset in range(10, right - left - 8, 14):
                    canvas.draw_line(left + offset, bottom + 10,
                                     left + offset + 6, bottom + 16, 209, 104, 120)
