"""Approved CHECKMATE screen geometry; independent of rendering libraries."""

WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
WINDOW_TITLE = 'CHECKMATE'

BOARD_SIZE = 10
TILE_SIZE = 75
BOARD_LEFT = 75
BOARD_BOTTOM = 75
BOARD_PIXEL_SIZE = BOARD_SIZE * TILE_SIZE

HUD_LEFT = 900
HUD_BOTTOM = 75
HUD_WIDTH = 465
HUD_HEIGHT = 750

FIXED_TIME_STEP = 1.0 / 60.0


def cell_center(col: int, row: int) -> tuple[float, float]:
    """Return a cell's canvas center; row zero is the bottom row."""
    if type(col) is not int or type(row) is not int:
        raise TypeError('Cell coordinates must be integers')
    if not (0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE):
        raise ValueError('Cell coordinates must be between 0 and 9')
    return (BOARD_LEFT + (col + 0.5) * TILE_SIZE,
            BOARD_BOTTOM + (row + 0.5) * TILE_SIZE)
