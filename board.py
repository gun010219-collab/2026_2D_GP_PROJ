"""Pure board geometry. Rectangles use half-open bounds [left, right)."""
from math import isfinite

from config import BOARD_BOTTOM, BOARD_LEFT, BOARD_PIXEL_SIZE, BOARD_SIZE, TILE_SIZE, cell_center


def in_bounds(col: int, row: int) -> bool:
    return (type(col) is int and type(row) is int
            and 0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE)


def tile_bounds(col: int, row: int) -> tuple[int, int, int, int]:
    cell_center(col, row)  # Share the configuration's input validation.
    left, bottom = BOARD_LEFT + col * TILE_SIZE, BOARD_BOTTOM + row * TILE_SIZE
    return left, bottom, left + TILE_SIZE, bottom + TILE_SIZE


def is_light_tile(col: int, row: int) -> bool:
    cell_center(col, row)
    return (col + row) % 2 == 1  # Traditional dark lower-left corner.


def iter_tiles():
    """Yield (col, row) from bottom to top, left to right."""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            yield col, row


def screen_to_cell(x: float, y: float) -> tuple[int, int] | None:
    """Return None outside the board; top and right edges are excluded."""
    if not isfinite(x) or not isfinite(y):
        return None
    if not (BOARD_LEFT <= x < BOARD_LEFT + BOARD_PIXEL_SIZE
            and BOARD_BOTTOM <= y < BOARD_BOTTOM + BOARD_PIXEL_SIZE):
        return None
    return int((x - BOARD_LEFT) // TILE_SIZE), int((y - BOARD_BOTTOM) // TILE_SIZE)
