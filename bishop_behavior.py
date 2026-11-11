"""PDF p.14 stationary Bishop: all 50 squares of its own board color."""
from board import in_bounds
from config import BOARD_SIZE


def color_targets(origin):
    """Include the source cell; pieces never occlude this board-wide attack."""
    if not isinstance(origin, (tuple, list)) or len(origin) != 2 or not in_bounds(*origin):
        raise ValueError('Bishop origin must be an in-bounds integer cell')
    color = sum(origin) % 2
    return tuple((col, row) for row in range(BOARD_SIZE) for col in range(BOARD_SIZE)
                 if (col + row) % 2 == color)
