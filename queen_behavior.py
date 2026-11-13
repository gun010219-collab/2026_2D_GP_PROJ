"""Deterministic Queen geometry only; no clock, damage or rendering."""
from board import in_bounds
from config import QUEEN_MOVE_MAX_CELLS

MOVE_STEPS = ((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1))
RAY_STEPS = ((1,1),(1,-1),(-1,-1),(-1,1))


def diagonal_targets(origin, player_cell, occupied=()):
    blocked = set(occupied) | {player_cell}
    cells = []
    for dx,dy in RAY_STEPS:
        x,y = origin
        while in_bounds(x+dx,y+dy):
            x,y = x+dx,y+dy
            cells.append((x,y))
            if (x,y) in blocked:
                break
    return tuple(cells)


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
    return min(candidates,key=lambda c:(player_cell not in diagonal_targets(c,player_cell,occupied),
               abs(c[0]-player_cell[0])+abs(c[1]-player_cell[1]))) if candidates else origin
