"""Combat geometry and optional atlas layers in the approved B+12 projection."""
import ctypes
import logging
from functools import lru_cache
from math import atan2, cos, hypot, pi, sin, tau
from struct import Struct

import sdl2 as s

from arena_art_common import ArenaArtError, CAMERA
from combat_vfx import MATERIALS, SAMPLES
from config import MOTION_SECONDS
import attack_vfx
import layered_attack_vfx
from vfx_atlas import VFXAtlas


@lru_cache(maxsize=100)
def center(cell):
    return CAMERA.center(*cell)


def ray_ends(origin, cells):
    """First and last *actual* target on each published ray, in ledger order."""
    rays = {}
    for cell in cells:
        dx, dy = cell[0] - origin[0], cell[1] - origin[1]
        step = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))
        if step != (0, 0):
            first, _ = rays.get(step, (cell, cell))
            rays[step] = first, cell
    return rays.values()


_VERTEX = Struct('=ff4B8x')  # SDL_Vertex with unused texture coordinates


class Mesh:
    """Reusable triangle buffer, flushed in painter order once per layer/chunk."""
    def __init__(self):
        self.vertices = (s.SDL_Vertex * 3072)()
        self.count = 0
        self.renderer = None

    def flush(self):
        count, self.count = self.count, 0
        if count and s.SDL_RenderGeometry(self.renderer, None, self.vertices, count, None, 0):
            raise ArenaArtError(s.SDL_GetError().decode())

    def tri(self, a, b, c, color):
        if self.count == len(self.vertices):
            self.flush()
        offset = self.count * _VERTEX.size
        for x, y in (a, b, c):
            _VERTEX.pack_into(self.vertices, offset, x, 899-y, *color)
            offset += _VERTEX.size
        self.count += 3

    def stroke(self, a, b, width, color, tip=None):
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = hypot(dx, dy)
        if length < .01:
            return
        nx, ny = -dy/length*.5, dx/length*.5
        end = width if tip is None else tip
        p, q = (a[0]+nx*width, a[1]+ny*width), (a[0]-nx*width, a[1]-ny*width)
        r, t = (b[0]+nx*end, b[1]+ny*end), (b[0]-nx*end, b[1]-ny*end)
        self.tri(p, q, r, color)
        self.tri(r, q, t, color)

    def arc(self, x, y, radius, aspect, start, sweep, width, color, segments=18):
        last = (x + cos(start)*radius, y + sin(start)*radius*aspect)
        for i in range(1, segments+1):
            angle = start + sweep*i/segments
            point = (x+cos(angle)*radius, y+sin(angle)*radius*aspect)
            self.stroke(last, point, width, color)
            last = point


def rgba(rgb, opacity):
    return (*rgb, max(0, min(255, round(255*opacity))))


def glint(mesh, x, y, size, color):
    for dx, dy, stretch in ((1,0,1),(-1,0,1),(0,1,1.45),(0,-1,.85)):
        mesh.stroke((x,y), (x+size*dx*stretch,y+size*dy*stretch), max(1,size*.34), color, 0)


def strike(mesh, fx, t, mat):
    x,y = center(fx.origin)
    tx,ty = center(fx.cell)
    angle = atan2(ty-y,tx-x)
    color, edge = rgba(mat.color, .78*(1-t)), rgba(mat.edge, 1-t*t)
    if fx.name == 'player_swing':
        # A tapered crescent, sweeping toward the single locked front cell.
        x += (tx-x)*.36
        y += (ty-y)*.36+18
        for radius, offset, weight, tint in ((41,-.20,3,color),(46,0,6,edge),(48,.04,1,color)):
            last = None
            for i in range(15):
                u = i/14
                a = angle - 1.15 + .8*t + 1.9*u + offset
                point = (x+radius*cos(a), y+radius*.83*sin(a))
                if last:
                    mesh.stroke(last,point,max(.3,weight*sin(pi*u)**.6),tint)
                last = point
    elif fx.name in ('pawn_thrust','knight_strike','king_strike','rook_strike'):
        reach = min(42, hypot(tx-x,ty-y)) if fx.name == 'rook_strike' else hypot(tx-x,ty-y)
        tip = (x+cos(angle)*reach*(.65+.35*sin(pi*t)), y+18+sin(angle)*reach*(.65+.35*sin(pi*t)))
        mesh.stroke((x,y+18),tip,9 if fx.name=='king_strike' else 5,color,0)
        mesh.stroke((x+cos(angle)*10,y+18+sin(angle)*10),tip,2,edge,0)
        if fx.name == 'king_strike':
            mesh.arc(tx,ty,9+32*t,.44,0,tau,3,color)
    elif fx.name == 'queen_fire':
        for near,far in ray_ends(fx.origin,fx.cells):
            a,b = center(near),center(far)
            start = ((x+a[0])*.5,(y+a[1])*.5)
            end = (b[0]+(a[0]-x)*.33,b[1]+(a[1]-y)*.33)
            mesh.stroke(start,end,10*(1-t)+2,rgba(mat.color,.46*(1-t)),4*(1-t))
            mesh.stroke(start,end,3*(1-t)+.8,edge,1)
    elif fx.name in ('bishop_cast','king_pulse'):
        # Only authorized cells participate in the ground wave.
        radius = t*14
        for cell in fx.cells:
            distance = hypot(cell[0]-fx.origin[0],cell[1]-fx.origin[1])
            pulse = max(0.,1-abs(distance-radius)/2)
            if pulse:
                cx,cy = center(cell)
                size = 5+13*pulse
                mesh.stroke((cx-size,cy),(cx,cy+size*.41),2,rgba(mat.edge,pulse*.81))
                mesh.stroke((cx,cy+size*.41),(cx+size,cy),2,rgba(mat.color,pulse*.92))
        mesh.arc(x,y,11+45*t,.46,0,tau,3,color)


def debris(mesh, fx, mat, x, y, age, t):
    alpha = (1-t)**(.65 if mat.fragment=='ember' else 1.2)
    silver = fx.name=='parry_normal'
    gold = fx.name=='parry_perfect'
    for i in range(fx.particles):
        dx,dy,speed,size = SAMPLES[(fx.seed+i)%len(SAMPLES)]
        distance = speed*age*(1-mat.drag*t)*(1.45 if gold else 1)
        px, py = x+dx*distance, y+dy*distance*.78-mat.gravity*age*age/2
        rgb = (181,230,255) if silver else (255,224,134) if gold else (mat.edge if i%3 else mat.color)
        tint = rgba(rgb, alpha)
        if mat.fragment == 'leaf' and not (silver or gold):
            px += sin(t*tau+i)*7*t
            mesh.tri((px-2*size,py),(px,py+size),(px+2*size,py+sin(i+t*8)*size),tint)
        elif mat.fragment == 'ember' and not (silver or gold):
            mesh.stroke((px,py),(px+sin(i+t*7)*size,py+size*(2+t)),size*(1-t)+1,tint,0)
        elif mat.fragment == 'iron' and not (silver or gold):
            mesh.tri((px-size,py),(px,py+size*1.5),(px+size,py-size),tint)
        else:
            length = size*(4 if mat.fragment=='crystal' or gold else 2.6)
            mesh.stroke((px,py),(px-dx*length,py-dy*length),size,tint,0)


class VFXRenderer:
    def __init__(self, manager):
        self.manager = manager
        self.mesh = Mesh()
        self.atlas = VFXAtlas() if manager.layered else None

    def close(self):
        if self.atlas is not None:
            self.atlas.close()

    def draw_atlas(self, layer, canvas, game, layouts, style):
        atlas = self.atlas
        if atlas is None or atlas.failed or layer == 'labels':
            return
        try:
            if not atlas.open(canvas):
                return
            manager = self.manager
            tick = game.combat.tick
            for attack, origin, kind in manager.charges.values():
                amount = (tick-attack.start_tick)/(attack.hit_tick-attack.start_tick)
                pulse = attack.attack_kind=='king_pulse'
                if layer == 'ground':
                    x,y = center(origin)
                    layered_attack_vfx.charge(atlas,layer,x,y,kind,pulse,amount,style)
                elif layouts:
                    body = layouts.get(attack.source_entity_instance_id)
                    if body and kind in ('bishop','queen','king'):
                        x,y = body['center']
                        x += body['height']*.22 if kind=='bishop' else 0
                        layered_attack_vfx.charge(atlas,layer,x,y+5,kind,pulse,amount,style)
                        if pulse:
                            atlas.stamp('flare',x,body['top']-6,12+13*amount,.85,
                                        style.edge,.72,angle=amount)
            for fx in manager.effects:
                age = max(0.,manager.time-fx.start)
                t = min(1.,age/fx.duration)
                layered_attack_vfx.draw(atlas,layer,fx,age,t,style,manager.time)
            atlas.flush()
        except (ArenaArtError,OSError):
            atlas.close()
            atlas.failed = True
            logging.getLogger(__name__).warning('Combat VFX atlas unavailable; using combat geometry',
                                               exc_info=True)

    def fail(self):
        self.manager.failed = True
        self.manager.effects.clear()
        self.manager.charges.clear()
        logging.getLogger(__name__).warning('Combat VFX unavailable for current session', exc_info=True)

    def draw(self, layer, canvas, game, layouts=None):
        manager = self.manager
        if manager.failed or not (manager.effects or manager.charges):
            return
        mesh = self.mesh
        mesh.renderer, mesh.count = canvas.renderer, 0
        blend = ctypes.c_int()
        changed = False
        try:
            if s.SDL_GetRenderDrawBlendMode(canvas.renderer, ctypes.byref(blend)):
                raise ArenaArtError('Cannot read VFX blend mode')
            if blend.value != s.SDL_BLENDMODE_BLEND:
                if s.SDL_SetRenderDrawBlendMode(canvas.renderer,s.SDL_BLENDMODE_BLEND):
                    raise ArenaArtError('Cannot apply VFX alpha blending')
                changed = True
            mat = MATERIALS[game.chapter]
            styles = attack_vfx.LAYERED_STYLES if manager.layered else attack_vfx.STYLES
            style = styles[game.chapter] if manager.renewed else None
            self.draw_atlas(layer,canvas,game,layouts,style)
            if layer in ('ground','front'):
                for attack, origin, kind in manager.charges.values():
                    portion = (game.combat.tick-attack.start_tick)/(attack.hit_tick-attack.start_tick)
                    x,y = center(origin)
                    radius = (26 if attack.attack_kind=='king_pulse' else 18)*(1-.55*portion)
                    if layer == 'ground':
                        if style and kind in ('bishop','queen','king'):
                            attack_vfx.sigil(mesh,x,y,radius*(1.35 if kind=='bishop' else 1.28),
                                             pi*portion,style,.65)
                        else:
                            mesh.arc(x,y,radius,.43,pi*portion,tau*.8,2,rgba(style.color if style else mat.color,.7))
                    elif kind in ('queen','bishop','king') and layouts:
                        body = layouts.get(attack.source_entity_instance_id)
                        if body:
                            cx,cy = body['center']
                            offset = .22*body['height'] if kind=='bishop' else 0
                            glint(mesh,cx+offset,cy+5,(3+9*portion)*(1.32 if style else 1),
                                  rgba(style.edge if style else mat.edge,.82))
                            if attack.attack_kind=='king_pulse':
                                glint(mesh,cx,body['top']-5,(3+6*portion)*(1.35 if style else 1),
                                      rgba(style.color if style else mat.color,.9))
            effects = manager.effects
            if style and layer=='front':
                effects = sorted(effects,key=lambda fx:fx.name.startswith('parry_'))
            for fx in effects:
                age = max(0.,manager.time-fx.start)
                t = min(1.,age/fx.duration)
                self.effect(layer,fx,age,t,mat,style)
            mesh.flush()
        except (ArenaArtError,OSError):
            mesh.count = 0
            self.fail()
        finally:
            if changed and s.SDL_SetRenderDrawBlendMode(canvas.renderer,blend.value):
                self.fail()

    def effect(self,layer,fx,age,t,mat,style=None):
        mesh = self.mesh
        x,y = center(fx.cell)
        ox,oy = center(fx.origin)
        name = fx.name
        if layer == 'labels':
            if fx.amount:
                damage_number(mesh,fx.amount,x+21,y+42+19*t,rgba(mat.edge,1-t*t))
            return
        if name in ('bishop_cast','king_pulse','queen_fire'):
            if layer=='ground':
                if style:
                    attack_vfx.strike(mesh,fx,age,t,style)
                else:
                    strike(mesh,fx,t,mat)
            x,y = ox,oy
        elif layer == 'ground':
            if name in ('rook_impact','knight_land','boss_death'):
                delay = MOTION_SECONDS if name != 'boss_death' and fx.cell != fx.origin else 0
                after_land = self.manager.time-fx.landed if fx.landed is not None else age-delay
                if style:
                    if name=='boss_death' or fx.landed is not None:
                        attack_vfx.impact(mesh,fx,after_land,t,style)
                elif fx.travel_pose is None and after_land >= 0:
                    mesh.arc(x,y,12+after_land*115,.45,0,tau,3,rgba(mat.edge,1-t))
            return
        elif name in ('player_swing','pawn_thrust','rook_strike','knight_strike','king_strike'):
            if style and name in attack_vfx.ENEMY_STRIKES:
                attack_vfx.strike(mesh,fx,age,t,style)
            else:
                strike(mesh,fx,t,mat)
        elif name in ('rook_impact','knight_land'):
            u = min(1.,age/MOTION_SECONDS) if fx.origin != fx.cell else 1.
            eased = u*u*(3-2*u)
            lx,ly = ox+(x-ox)*eased,oy+(y-oy)*eased
            if fx.landed is None and (fx.travel_pose is not None or u < 1):
                lift = 18*sin(pi*u) if name=='knight_land' else 0
                if fx.travel_pose is not None:
                    col,row,lift = fx.travel_pose
                    lx,ly = CAMERA.project(col,row)
                if style:
                    if fx.travel_pose is not None:
                        attack_vfx.travel(mesh,fx,lx,ly,lift,u,style)
                    return
                mesh.stroke((lx-(x-ox)*.13,ly+lift+10-(y-oy)*.13),(lx,ly+lift+10),5,
                            rgba(mat.edge,.53*(1-u)),1)
                return
            if style and fx.landed is None:
                return
            if fx.landed is not None:
                age = self.manager.time-fx.landed
            elif fx.origin != fx.cell:
                age -= MOTION_SECONDS
        elif name.startswith('parry_'):
            gold = name=='parry_perfect'
            dx,dy = ox-x,oy-y
            length = max(1,hypot(dx,dy))
            x,y = x+dx/length*12,y+20+dy/length*9
            if gold:
                # Recoil belongs to the contact glint, never to the world viewport.
                kick_x, kick_y = self.manager.shake()
                x, y = x+kick_x, y+kick_y
            color = (255,221,126) if gold else (158,223,246)
            for i in range(3 if gold else 1):
                r = 8+(54 if gold else 29)*max(0,t-i*.10)
                mesh.arc(x,y,r,.79,0,tau,3-i*.75,rgba(color,(1-t)*(.85-i*.15)))
            glint(mesh,x,y,(25 if gold else 13)*(1-t),rgba((255,252,223),1-t))
        elif name in ('player_hit','player_hurt'):
            y += 23
            tint = (255,129,122) if name=='player_hurt' else (255,242,186)
            glint(mesh,x,y,21*(1-t)**2,rgba(tint,1-t))
            if name=='player_hurt' and t < .45:
                for edge,sign in ((8,1),(1432,-1)):
                    mesh.stroke((edge,373),(edge+sign*5,450),3,rgba(tint,.65-t))
                    mesh.stroke((edge+sign*5,450),(edge,527),3,rgba(tint,.65-t))
        elif name.endswith('_death'):
            y += 15
            if name=='boss_death':
                if style:
                    attack_vfx.vein(mesh,(x,y-6),(x,y+72*(1-t)),style,age,.85*(1-t))
                    glint(mesh,x,y+15,41*(1-t),rgba(style.edge,1-t))
                else:
                    mesh.arc(x,y,15+75*t,.57,0,tau,4,rgba(mat.color,1-t))
                    glint(mesh,x,y+15,29*(1-t),rgba(mat.edge,1-t))
        if layer=='front':
            if style and (name in attack_vfx.ENEMY_STRIKES or name in ('rook_impact','knight_land','boss_death')
                          or (name=='player_hurt' and fx.source_kind=='pawn')):
                attack_vfx.particles(mesh,fx,style,x,y,age,t)
            else:
                debris(mesh,fx,mat,x,y,age,t)


# Seven-segment digits with a dark under-stroke stay legible on ice and basalt.
_DIGITS = ('abcdef','bc','abdeg','abcdg','bcfg','acdfg','acdefg','abc','abcdefg','abcdfg')
_SEGMENTS = dict(a=(0,10,6,10), b=(6,10,6,5), c=(6,5,6,0), d=(0,0,6,0),
                 e=(0,5,0,0), f=(0,10,0,5), g=(0,5,6,5))


def damage_number(mesh, amount, x, y, color):
    for width,tint in ((4,(27,19,27,color[3])),(2,color)):
        mesh.stroke((x-7,y+5),(x-2,y+5),width,tint)
        for i,ch in enumerate(str(amount)):
            for segment in _DIGITS[int(ch)]:
                a,b,c,d = _SEGMENTS[segment]
                mesh.stroke((x+i*9+a,y+b),(x+i*9+c,y+d),width,tint)
