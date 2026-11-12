"""Approved King one-step pursuit and adjacent single-cell melee geometry."""
from board import in_bounds


# Stable candidate order; min() preserves this order on equal distances.
KING_STEPS = ((0, 1), (0, -1), (-1, 0), (1, 0),
              (-1, 1), (1, 1), (-1, -1), (1, -1))


def move_candidates(origin, player_cell, occupied):
    col, row = origin
    return tuple((col + dx, row + dy) for dx, dy in KING_STEPS
                 if in_bounds(col + dx, row + dy)
                 and (col + dx, row + dy) != player_cell
                 and (col + dx, row + dy) not in occupied)


def choose_move(origin, player_cell, occupied):
    """Prefer the nearest legal cell in Chebyshev distance, then fixed order.

    All blocked means stay and retry at the next movement action. This is a
    deterministic greedy policy, not a guarantee of finding a shortest path.
    """
    candidates = move_candidates(origin, player_cell, occupied)
    return min(candidates, key=lambda p: max(abs(p[0] - player_cell[0]),
                                           abs(p[1] - player_cell[1]))) if candidates else origin


def melee_target(origin, player_cell):
    distance = max(abs(origin[0] - player_cell[0]), abs(origin[1] - player_cell[1]))
    return tuple(player_cell) if distance == 1 and in_bounds(*player_cell) else None
