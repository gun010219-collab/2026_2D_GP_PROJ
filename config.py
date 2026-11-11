"""Approved CHECKMATE screen geometry; independent of rendering libraries."""

WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
WINDOW_TITLE = 'CHECKMATE'

BOARD_SIZE = 10
TILE_SIZE = 84
BOARD_LEFT = 300
BOARD_BOTTOM = 30
BOARD_PIXEL_SIZE = BOARD_SIZE * TILE_SIZE
BOARD_RIGHT = BOARD_LEFT + BOARD_PIXEL_SIZE
BOARD_TOP = BOARD_BOTTOM + BOARD_PIXEL_SIZE

FIXED_TIME_STEP = 1.0 / 60.0

# Task 1-C implementation baselines, not final combat balance.
ATTACK_COOLDOWN_SECONDS = 0.6
ATTACK_EFFECT_SECONDS = 0.15  # Temporary visual feedback, independent of cooldown.
MAX_SIMULATION_STEPS_PER_FRAME = 8

# Task 1-D temporary input-relative parry windows, not success adjudication.
PARRY_WINDOW_SECONDS = 0.30
PERFECT_PARRY_WINDOW_SECONDS = 0.12  # Ceil to 8 ticks (~0.133s) at 60Hz.
PARRY_COOLDOWN_SECONDS = 1.0  # Initial PDF baseline, not final balance.

# Pawn timings from game design PDF p.11; initial implementation baselines.
PAWN_MOVE_INTERVAL_SECONDS = 2.20
PAWN_TELEGRAPH_SECONDS = 0.65
PAWN_RECOVERY_SECONDS = 0.90

# Task 1-F initial PDF baselines, not final approved combat balance.
# Game design PDF p.6 (player/damage/invulnerability), p.11 (Pawn HP).
PLAYER_INITIAL_HP = 3
PAWN_INITIAL_HP = 2
PLAYER_ATTACK_DAMAGE = 1
PAWN_ATTACK_DAMAGE = 1
PLAYER_HIT_INVULNERABILITY_SECONDS = 0.80  # 48 shared combat ticks.


def cell_center(col: int, row: int) -> tuple[float, float]:
    """Return a cell's canvas center; row zero is the bottom row."""
    if type(col) is not int or type(row) is not int:
        raise TypeError('Cell coordinates must be integers')
    if not (0 <= col < BOARD_SIZE and 0 <= row < BOARD_SIZE):
        raise ValueError('Cell coordinates must be between 0 and 9')
    return (BOARD_LEFT + (col + 0.5) * TILE_SIZE,
            BOARD_BOTTOM + (row + 0.5) * TILE_SIZE)
