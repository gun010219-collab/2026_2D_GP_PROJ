"""Projected facing and strike cues read the logical player and attack snapshot."""
from dataclasses import dataclass
from functools import lru_cache

from arena_art_common import CAMERA
from board import in_bounds
from combat import AttackEvent
from player import DIRECTIONS


@dataclass(frozen=True)
class Aim:
    origin: tuple[int, int]
    facing: str
    target: tuple[int, int] | None
    strike: AttackEvent | None


def player_aim(game):
    player = game.player
    dx,dy = DIRECTIONS[player.facing]
    target = player.col+dx,player.row+dy
    return Aim(player.position,player.facing,target if in_bounds(*target) else None,
               game.combat.active_attack)


@lru_cache(maxsize=800)
def arrow(cell,facing,*,strike=False):
    col,row = cell
    dx,dy = DIRECTIONS[facing]
    # Keep the live chevron in the tile's front margin, away from the ring.
    x,y = (col+.5,row+.5) if strike else (col+.23,row+.14)
    def point(forward,side):
        return CAMERA.project(x+dx*forward-dy*side,y+dy*forward+dx*side)
    tip = point(.13,0)
    return ((point(-.09,0),tip),(point(.018,.075),tip),(tip,point(.018,-.075)),
            (point(-.025,.075),point(.086,0)),(point(.086,0),point(-.025,-.075)))


@lru_cache(maxsize=200)
def corners(cell,active):
    col,row = cell
    indices = (0,1,2,3) if active else (0,2)
    points = ((.16,.17,1,1),(.84,.17,-1,1),(.84,.83,-1,-1),(.16,.83,1,-1))
    length = .19 if active else .12
    lines = []
    for i in indices:
        x,y,dx,dy = points[i]
        corner = CAMERA.project(col+x,row+y)
        lines.extend(((corner,CAMERA.project(col+x+dx*length,row+y)),
                      (corner,CAMERA.project(col+x,row+y+dy*length))))
    return tuple(lines)


def draw_aim(canvas,aim):
    def lines(segments,color):
        for start,end in segments:
            canvas.draw_line(*start,*end,*color)

    strike = aim.strike
    if aim.target is not None and (strike is None or strike.target_cell != aim.target):
        lines(corners(aim.target,False),(182,151,80))
    if strike is not None:
        lines(corners(strike.target_cell,True),(255,225,149))
        lines(arrow(strike.target_cell,strike.facing,strike=True),(255,239,181))
    lines(arrow(aim.origin,aim.facing),(250,206,102))
