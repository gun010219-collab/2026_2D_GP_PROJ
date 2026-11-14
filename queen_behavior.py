"""Deterministic Queen geometry only; no clock, damage or rendering."""
from board import in_bounds
from config import QUEEN_MOVE_MAX_CELLS

MOVE_STEPS = ((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1))
RAY_STEPS = MOVE_STEPS


def queen_ray_targets(origin):
    """N/NE/E/SE/S/SW/W/NW, piercing to the board edge; origin excluded."""
    if not isinstance(origin, (tuple, list)) or len(origin) != 2 or not in_bounds(*origin):
        raise ValueError('Queen origin must be an integer board cell')
    cells = []
    for dx, dy in RAY_STEPS:
        x, y = origin
        while in_bounds(x + dx, y + dy):
            x, y = x + dx, y + dy
            cells.append((x, y))
    return tuple(cells)


def diagonal_targets(origin, player_cell=None, occupied=()):
    """Compatibility alias: Task2-G replaces the legacy four blocked diagonals."""
    return queen_ray_targets(origin)


def reposition_candidates(origin, player_cell, occupied=()):
    blocked = set(occupied) | {player_cell}
    cells = []
    for dx,dy in MOVE_STEPS:
        for distance in range(1,QUEEN_MOVE_MAX_CELLS+1):
            cell = origin[0]+dx*distance,origin[1]+dy*distance
            if not in_bounds(*cell) or cell in blocked:
                break
            cells.append(cell)
    return tuple(cells)


def choose_reposition(origin, player_cell, occupied=()):
    occupied = set(occupied) - {origin}
    candidates = reposition_candidates(origin,player_cell,occupied)
    return min(candidates,key=lambda c:(player_cell not in queen_ray_targets(c),
               abs(c[0]-player_cell[0])+abs(c[1]-player_cell[1]))) if candidates else origin
