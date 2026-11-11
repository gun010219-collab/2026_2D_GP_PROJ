"""Pure Rook geometry/selection. Time, HP, ledgers and rendering live elsewhere."""
from board import in_bounds
from config import ROOK_MOVE_MAX_CELLS


# Stable tie order shared with Pawn; movement length is Rook-specific.
ROOK_STEPS = ((0, 1), (0, -1), (-1, 0), (1, 0))


def attack_path(origin, player_cell, occupied):
    """Straight path excluding origin, including the booked player cell.

    The 3-cell limit is for repositioning, not the PDF's dash. A blocked line
    cannot start an attack. No wall terrain exists in the current board model.
    """
    col, row = origin
    pc, pr = player_cell
    if origin == player_cell or (col != pc and row != pr):
        return ()
    dx = (pc > col) - (pc < col)
    dy = (pr > row) - (pr < row)
    cells = []
    while (col, row) != player_cell:
        col, row = col + dx, row + dy
        if not in_bounds(col, row) or (col, row) in occupied:
            return ()
        cells.append((col, row))
    return tuple(cells)


def choose_move(origin, player_cell, occupied):
    """Select a clear alignment first, then nearest; ties keep direction/order.

    This is a deterministic technical policy for the PDF's unspecified choice
    of reposition cell. It deliberately differs from Pawn's 1-cell pursuit.
    Every intermediate cell must be free, including the player cell.
    """
    candidates = []
    for dx, dy in ROOK_STEPS:
        for distance in range(1, ROOK_MOVE_MAX_CELLS + 1):
            cell = origin[0] + dx * distance, origin[1] + dy * distance
            if not in_bounds(*cell) or cell in occupied or cell == player_cell:
                break
            candidates.append(cell)
    if not candidates:
        return origin
    return min(candidates, key=lambda cell: (
        not bool(attack_path(cell, player_cell, occupied)),
        abs(cell[0] - player_cell[0]) + abs(cell[1] - player_cell[1])))
