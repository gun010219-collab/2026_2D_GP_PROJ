"""R7-A2 enemy effects. Geometry reads presentation receipts only."""
from dataclasses import dataclass
from functools import lru_cache
from math import atan2, cos, hypot, pi, sin, tau

from arena_art_common import CAMERA
from combat_vfx import SAMPLES

ENEMY_STRIKES = frozenset(('pawn_thrust','rook_strike','knight_strike','bishop_cast',
                          'queen_fire','king_strike','king_pulse'))


@dataclass(frozen=True)
class Style:
    color: tuple
    edge: tuple
    shadow: tuple
    material: str
    gravity: float
    drag: float


STYLES = {
    1: Style((248,179,44),(255,249,193),(116,64,14),'metal',190,.22),
    2: Style((58,232,120),(206,255,185),(14,72,38),'vine',40,.58),
    3: Style((52,129,255),(218,250,255),(24,48,146),'frost',150,.19),
    4: Style((253,65,55),(255,217,151),(109,13,25),'lava',-96,.44),
    5: Style((177,93,255),(237,211,255),(22,8,38),'void',-28,.64),
}


CRIMSON = (120,11,22)
LAYERED_STYLES = {**STYLES, 5: Style((237,24,43),(255,208,208),(8,8,10),'curse',-28,.64)}


def tint(rgb, alpha):
    return (*rgb,max(0,min(255,round(alpha*255))))


def beam_segments(origin, cells):
    """Group contiguous ledger cells by ray; return exact board-parametric ends."""
    rays = {}
    for col,row in cells:
        dx,dy = col-origin[0],row-origin[1]
        step = ((dx>0)-(dx<0),(dy>0)-(dy<0))
        if step == (0,0):
            continue
        distance = max(abs(dx),abs(dy))
        rays.setdefault(step,[]).append(distance)
    paths = []
    for (dx,dy), distances in rays.items():
        first = last = None
        for distance in sorted(distances):
            if last is not None and distance != last+1:
                paths.append((dx,dy,first,last))
                first = None
            first = distance if first is None else first
            last = distance
        paths.append((dx,dy,first,last))
    return tuple(paths)


@lru_cache(maxsize=128)
def projected_beams(origin,cells):
    x,y = origin[0]+.5,origin[1]+.5
    return tuple((CAMERA.project(x+dx*(first-.33),y+dy*(first-.33)),
                  CAMERA.project(x+dx*(last+.34),y+dy*(last+.34)))
                 for dx,dy,first,last in beam_segments(origin,cells))


@lru_cache(maxsize=128)
def wave_cells(origin,cells):
    return tuple((hypot(x-origin[0],y-origin[1]),*CAMERA.center(x,y)) for x,y in cells)


@lru_cache(maxsize=100)
def center(cell):
    return CAMERA.center(*cell)


def shard(mesh,a,b,end_width,color):
    """One tapered triangle around a direction vector."""
    dx,dy = b[0]-a[0],b[1]-a[1]
    length = max(.01,hypot(dx,dy))
    px,py = -dy/length*end_width,dx/length*end_width
    mesh.tri((a[0]+px,a[1]+py),(a[0]-px,a[1]-py),b,color)


def sigil(mesh,x,y,r,turn,style,opacity):
    mesh.arc(x,y,r,.47,0,tau,2,tint(style.shadow,opacity),segments=16)
    mat = style.material
    for i in range(6 if mat=='vine' else 4):
        count = 6 if mat=='vine' else 4
        angle = turn+i*tau/count
        dx,dy = cos(angle),sin(angle)*.47
        a = x+r*dx,y+r*dy
        b = x+(r+8)*dx,y+(r+8)*dy
        color = tint(style.edge,opacity*.91)
        if mat=='metal':
            shard(mesh,a,b,4,color)
        elif mat=='vine':
            mesh.arc(*a,6,.66,angle-pi*.4,pi*1.2,2,color,segments=5)
        elif mat=='frost':
            mesh.stroke(a,b,2,color,0)
            mesh.stroke(b,(a[0]-dy*5,a[1]+dx*5),2,tint(style.color,opacity))
        elif mat=='lava':
            center_rx,center_ry = (a[0]+b[0])*.5,(a[1]+b[1])*.5
            mesh.stroke(a,(center_rx-dy*7,center_ry+dx*5),3,tint(style.color,opacity),2)
            mesh.stroke((center_rx-dy*7,center_ry+dx*5),b,2,color,0)
        else:
            mesh.arc(*a,8,.48,angle-pi*.36,pi*.8,3,tint(style.color,opacity),segments=4)
            shard(mesh,a,b,3,color)


def lightning(mesh,a,b,style,phase,fade,side):
    dx,dy = b[0]-a[0],b[1]-a[1]
    length = max(1,hypot(dx,dy))
    nx,ny = -dy/length*side,dx/length*side
    previous = a
    for i,offset in enumerate((9,-6,12,0),1):
        part = i*.25
        jag = offset*(.82+.18*sin(phase*16+i*2))
        point = a[0]+dx*part+nx*jag,a[1]+dy*part+ny*jag
        mesh.stroke(previous,point,7,tint(style.shadow,.84*fade),5)
        mesh.stroke(previous,point,3.15,tint(style.color,.89*fade),1.5)
        if i in (1,3):
            fork = point[0]+nx*10+dx*.10,point[1]+ny*10+dy*.10
            mesh.stroke(point,fork,1.6,tint(CRIMSON,fade),0)
        previous = point


def vein(mesh,a,b,style,age,opacity,side=1):
    dx,dy = b[0]-a[0],b[1]-a[1]
    length = max(.01,hypot(dx,dy))
    nx,ny = -dy/length*side,dx/length*side
    mat = style.material
    if mat=='metal':
        shard(mesh,(a[0]+nx*6,a[1]+ny*6),b,2,tint(style.edge,opacity*.8))
        return
    if mat == 'curse':
        lightning(mesh,a,b,style,age,opacity,side)
        return
    bends = {'vine':(7,11,4),'frost':(5,-4,8),'lava':(8,-6,4),'void':(12,8,17)}[mat]
    previous = a
    for i,bend in enumerate(bends,1):
        part = i*.245
        drift = sin(age*11+part*3)*3 if mat in ('vine','void') else 0
        point = a[0]+dx*part+nx*(bend+drift),a[1]+dy*part+ny*(bend+drift)
        mesh.stroke(previous,point,3 if mat=='void' else 2,tint(style.color,opacity),1)
        if mat in ('vine','frost') and i!=2:
            shard(mesh,point,(point[0]+nx*7,point[1]+ny*7),2,tint(style.edge,opacity*.64))
        previous = point
    mesh.stroke(previous,b,2,tint(style.edge,opacity*.65),0)


_RING = tuple((cos(i*tau/24),sin(i*tau/24)) for i in range(25))


@lru_cache(maxsize=512)
def projected_wave(origin,radius):
    x,y = origin[0]+.5,origin[1]+.5
    last = None
    segments = []
    for dx,dy in _RING:
        col,row = x+dx*radius,y+dy*radius
        # Keep the decorative ribbon inside the board; outside arcs disappear.
        point = CAMERA.project(col,row) if .13<col<9.87 and .13<row<9.87 else None
        if last and point:
            segments.append((last,point))
        last = point
    return tuple(segments)


def pulse_front(mesh,origin,radius,style,fade):
    shadow = tint(style.shadow,.56*fade)
    core = tint(style.color,.70*fade)
    edge = tint(style.edge,.77*fade)
    for a,b in projected_wave(origin,radius):
        mesh.stroke(a,b,12 if style.material=='curse' else 9,shadow)
        mesh.stroke(a,b,4,core)
        mesh.stroke(a,b,1.5,edge)


def strike(mesh,fx,age,t,style):
    name = fx.name
    x,y = center(fx.origin)
    tx,ty = center(fx.cell)
    fade = 1-t
    edge = tint(style.edge,fade)
    color = tint(style.color,fade*.78)
    shadow = tint(style.shadow,fade*.70)
    if name=='queen_fire':
        for a,b in projected_beams(fx.origin,fx.cells):
            mesh.stroke(a,b,3+15*fade,tint(style.shadow,fade*.57),2+9*fade)
            mesh.stroke(a,b,2+8*fade,tint(style.color,fade*.77),2+6*fade)
            mesh.stroke(a,b,1+3.5*fade,edge,1+2.4*fade)
            if fade>.32:
                vein(mesh,a,b,style,age,.43*fade)
        return
    if name in ('bishop_cast','king_pulse'):
        radius = t*14
        # Pixel markings stay inside their actual targeted cells, behind the warning.
        pulse = name=='king_pulse'
        if pulse and len(fx.cells)==100:
            pulse_front(mesh,fx.origin,.25+radius,style,fade)
        for distance,cx,cy in wave_cells(fx.origin,fx.cells):
            energy = 1-abs(distance-radius)/(2.22 if pulse else 1.92)
            if energy <= 0:
                continue
            size = 6+(15 if pulse else 11)*energy
            mesh.tri((cx-size,cy-3),(cx,cy+size*.34),(cx+size,cy-3),
                     tint(style.shadow,.32*energy))
            if pulse:
                if style.material == 'curse':
                    mid = cx+size*.21,cy+size*.20
                    mesh.stroke((cx-size,cy-4),mid,6,tint(style.shadow,.78*energy),5)
                    mesh.stroke(mid,(cx+size,cy-2),4,tint(style.color,.86*energy),0)
                    mesh.stroke((cx-size,cy-4),mid,2,tint(style.edge,.86*energy),2)
                else:
                    mesh.stroke((cx-size,cy-1),(cx+size,cy+2),4,tint(style.color,.73*energy))
                    mesh.stroke((cx-size*.55,cy+3),(cx+size*.62,cy+5),2,tint(style.edge,energy))
            else:
                mesh.stroke((cx-size,cy),(cx,cy+size*.38),3,tint(style.color,.82*energy))
                mesh.stroke((cx,cy+size*.38),(cx+size,cy),2,tint(style.edge,energy))
        sigil(mesh,x,y,(17+52*t if pulse else 17+37*t),age*2,style,.74*fade)
        return
    dx,dy = tx-x,ty-y
    angle = atan2(dy,dx)
    ux,uy = cos(angle),sin(angle)
    lift = 15 if name=='rook_strike' else 20
    base = x,y+lift
    if name=='pawn_thrust':
        extension = .91+.09*sin(pi*t)
        tip = x+dx*extension,y+lift+dy*extension
        neck = tip[0]-ux*19,tip[1]-uy*19
        mesh.stroke(base,neck,8*fade,shadow,5)
        mesh.stroke(base,neck,4.2*fade,color,4)
        shard(mesh,neck,tip,5.7*fade,edge)
        mesh.stroke((base[0]+ux*9,base[1]+uy*9),tip,1.75,edge,0)
        vein(mesh,base,tip,style,age,.51*fade)
    elif name=='rook_strike':
        reach = min(55,hypot(dx,dy))
        # The dense launch wedge is fixed to the first leg; the moving trail
        # derives independently from the authenticated attack_move receipt.
        tip = x+ux*reach,y+lift+uy*reach
        shard(mesh,base,tip,12*fade,shadow)
        for side in (-1,1):
            start = x-uy*side*8,y+lift+ux*side*8
            mesh.stroke(start,tip,4.8*fade,color,0)
        vein(mesh,base,tip,style,age,.52*fade)
    elif name=='knight_strike':
        end = x+dx*.47,y+lift+dy*.47+17
        vein(mesh,base,end,style,age,.66*fade)
        mesh.arc(x,y+lift,18+13*t,.76,angle+.45,-1.35,4.4*fade,edge,segments=9)
    else:
        for offset,width,span in ((0,13,1.75),(.12,5,1.54)):
            mesh.arc((x+tx)*.5,(y+ty)*.5+14,24+15*t,.72,angle-.95+offset,span,
                     width*fade,shadow if not offset else color,segments=14)
        mesh.arc(tx,ty,15+42*t,.48,angle+pi*.3,tau*.73,4.2*fade,edge,segments=14)


def travel(mesh,fx,x,y,lift,t,style):
    ox,oy = center(fx.origin)
    tx,ty = center(fx.cell)
    head = x,y+lift+11
    fade = 1-t
    if fx.name=='rook_impact':
        tail = x-(tx-ox)*.23,y+6-(ty-oy)*.23
        mesh.stroke(tail,head,13*fade,tint(style.shadow,fade*.65),2)
        mesh.stroke(tail,head,5*fade,tint(style.color,fade*.85),1)
        vein(mesh,tail,head,style,t,.56*fade)
    else:
        # The endpoint follows RenderMotion's same ground and 18px lift.
        # Two lagged points build a visible arc with no separate flight clock.
        back = x-(tx-ox)*.19,y-(ty-oy)*.19+lift*.62+5
        middle = (back[0]+x)*.5,(back[1]+head[1])*.5+5
        mesh.stroke(back,middle,3,tint(style.color,fade*.59),6)
        mesh.stroke(middle,head,7,tint(style.edge,fade*.72),1)
        vein(mesh,back,head,style,t,.5*fade,-1)


def impact(mesh,fx,age,t,style):
    x,y = center(fx.cell)
    boss = fx.name=='boss_death'
    radius = (17 if boss else 15)+age*(142 if boss else 158)
    sigil(mesh,x,y,min(104 if boss else 80,radius),age*1.4,style,.86*(1-t))
    if boss or fx.name=='rook_impact':
        mesh.arc(x,y,radius*.72,.48,age,tau*.88,4,tint(style.color,.46*(1-t)),segments=16)


def particles(mesh,fx,style,x,y,age,t):
    fade = max(0.,1-t)
    mat = style.material
    for i in range(fx.particles):
        dx,dy,speed,size = SAMPLES[(fx.seed+i)%len(SAMPLES)]
        distance = speed*age*(1-style.drag*t)*(1.28 if fx.name in ('boss_death','king_pulse') else 1.14)
        px = x+dx*distance
        py = y+dy*distance*.74-style.gravity*age*age/2
        a = tint(style.edge,fade**.9)
        b = tint(style.color,fade**1.2)
        if mat=='metal':
            shard(mesh,(px,py),(px+dx*size*5,py+dy*size*5),size*.8,a)
        elif mat=='vine':
            px += sin(t*9+i)*6
            mesh.tri((px-2*size,py),(px,py+size*2),(px+2*size,py-size),b)
            mesh.stroke((px-2*size,py),(px,py+size),1,a)
        elif mat=='frost':
            shard(mesh,(px,py),(px+dx*size*5,py+dy*size*5),size,a)
            shard(mesh,(px,py),(px-dx*size*2,py-dy*size*2),size,b)
        elif mat=='lava':
            shard(mesh,(px,py),(px-dx*size,py+size*(2+t)),size*(1.2-t),b)
            mesh.stroke((px,py),(px-dx*size*.4,py+size*2),1,a,0)
        else:
            dark = tint(style.shadow,.55*fade)
            mesh.tri((px-size*2,py),(px,py+size*3),(px+size*2,py-size),dark)
            mesh.stroke((px-size*1.5,py),(px+dx*size,py+size*3),2,b,.5)
