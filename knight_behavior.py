"""Pure Knight landing candidates/selection; no time, HP, SDL or animation."""
from board import in_bounds


# Clockwise from upper-right. The PDF defines the set, not its tie order.
KNIGHT_STEPS = ((1, 2), (2, 1), (2, -1), (1, -2),
                (-1, -2), (-2, -1), (-2, 1), (-1, 2))


def landing_candidates(origin, occupied):
    """Jump over intermediate pieces; only the landing cell can block a jump.

    occupied contains other active enemies, not the player. A player-occupied
    landing is an attack target; resolution never lands on top of the player.
    """
    col, row = origin
    return tuple((col + dx, row + dy) for dx, dy in KNIGHT_STEPS
                 if in_bounds(col + dx, row + dy) and (col + dx, row + dy) not in occupied)


def choose_landing(origin, player_cell, occupied):
    """Nearest player distance first, stable offset order on ties; no retarget."""
    candidates = landing_candidates(origin, occupied)
    return min(candidates, key=lambda cell: abs(cell[0] - player_cell[0])
               + abs(cell[1] - player_cell[1])) if candidates else None
