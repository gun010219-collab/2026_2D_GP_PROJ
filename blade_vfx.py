"""Player blade ribbons and contact fragments, in the combat mesh's local coordinates."""
from math import atan2, cos, pi, sin

from combat_vfx import SAMPLES


STEEL = (104, 163, 215)
SILVER = (211, 235, 255)
WHITE = (255, 250, 225)
GOLD = (245, 194, 107)


def ribbon(radius, width, sweep, offset, lean=0):
    """Two tapered edges. Author each profile once, rotate it with the live swing."""
    points = []
    for i in range(15):
        u = i / 14
        angle = (u - .54) * sweep + offset
        outer = radius + lean * u
        inner = outer - width * sin(pi * u) ** .8
        points.append((cos(angle)*outer, sin(angle)*outer, cos(angle)*inner, sin(angle)*inner))
    return tuple(points)


EDGE = ribbon(46, 9, 2.23, .03)
BEVEL = ribbon(47, 2.1, 2.32, .02)
ECHO = ribbon(34, 4.2, 1.96, -.42, 4)
WAKE = ribbon(33, 7, 1.86, -.70, 3)
FAN = ribbon(26, 6, 1.72, -.38, 6)
FILIGREE = ribbon(43, 1.6, 2.80, -.24)

# Outer bevel, delayed blue echo, then the three nested facets of the royal blade.
LAYERS = {
    2: ((EDGE, STEEL, .88), (BEVEL, SILVER, 1)),
    3: ((WAKE, STEEL, .43), (ECHO, SILVER, .92), (EDGE, STEEL, .96), (BEVEL, WHITE, 1)),
    4: ((FAN, SILVER, .76), (ECHO, STEEL, .91), (EDGE, SILVER, 1), (BEVEL, WHITE, 1)),
    5: ((FAN, GOLD, .95), (WAKE, STEEL, .58), (ECHO, WHITE, .96),
        (EDGE, GOLD, 1), (FILIGREE, SILVER, .98), (BEVEL, WHITE, 1)),
}


def tint(rgb, opacity):
    return (*rgb, round(255 * opacity))


def swing(mesh, origin, target, tier, t):
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    x, y = origin[0] + .36*dx, origin[1] + .36*dy + 18
    heading = atan2(dy, dx) - .35 + 1.12*t
    for profile, metal, opacity in LAYERS[tier]:
        # The afterimage lags the blade and dissolves first.
        ghost = profile is WAKE
        angle = heading - (.48*t if ghost else 0)
        c, s = cos(angle), sin(angle)
        color = bytes(tint(metal, opacity * (1-t*t) * (1-t if ghost else 1)))
        last = None
        for a,b,i,j in profile:
            outer = (x+c*a-s*b, y+.83*(s*a+c*b))
            inner = (x+c*i-s*j, y+.83*(s*i+c*j))
            if last:
                mesh.ribbon_quad(last[0], last[1], outer, inner, color)
            last = outer, inner


# Open crown above a pointed escutcheon; its negative spaces keep the target visible.
CREST = ((-10,4),(-13,15),(-6,10),(0,19),(6,10),(13,15),(10,4),
         (-10,4),(-8,-2),(0,-8),(8,-2),(10,4))


def contact(mesh, fx, x, y, age, t):
    tier = fx.blade_tier
    fade = 1-t
    if tier >= 4:
        # Two broken arcs around the contact, well inside the target cell.
        radius = 6 + 27 * (1-fade*fade)
        wave = tint(GOLD if tier == 5 else SILVER, .82*fade*fade)
        for angle in (.25, pi+.25):
            mesh.arc(x, y, radius, .55, angle+.5*t, 2.36, 2.5*fade+.4, wave, 9)
    if tier == 5:
        size = .68 + .32*min(1., t*5)
        cy = y + 9 + 9*t
        points = [(x+a*size, cy+b*size) for a,b in CREST]
        for a,b in zip(points,points[1:]):
            mesh.stroke(a,b,2.2,tint(GOLD, fade))
        mesh.tri((x-2,cy+6),(x,cy+12),(x+2,cy+6),tint(WHITE, fade))
    for index in range(fx.particles):
        dx,dy,speed,width = SAMPLES[(fx.seed+index) % len(SAMPLES)]
        distance = 4 + speed*age*(1-.42*t)
        px,py = x+dx*distance, y+dy*distance*.75-48*age*age
        length = width*(2.7 if tier < 4 else 3.9)*fade
        tip = px+dx*length, py+dy*length
        tail = px-dx*length, py-dy*length
        edge = (px-dy*width*.6, py+dx*width*.6)
        mesh.tri(tail,edge,tip,tint(GOLD if tier == 5 else STEEL, fade))
        mesh.tri(tail,(px+dy*width*.5,py-dx*width*.5),tip,tint(WHITE if tier >= 4 else SILVER, fade))
        if tier == 3:
            mesh.stroke(tail,(tail[0]-dx*length*1.6,tail[1]-dy*length*1.6),
                        width, tint(STEEL, .52*fade), 0)
