"""Continuous UV mesh for actor poses. Original sprite pixels stay in one texture."""
import ctypes
from dataclasses import dataclass
from functools import lru_cache
from math import pi, sin

from actor_animation import State
from arena_art_common import ArenaArtError


@dataclass(frozen=True)
class Deformation:
    lean: float = 0.
    rise: float = 0.
    gear: float = 0.
    cloth: float = 0.
    core: float = 0.
    squash: float = 0.
    opacity: float = 1.


# Tempo, armor response, loose material response, and localized tint.
MATERIAL = {
    1: (1.0, 1.0, .92, (255, 223, 173)),
    2: (.86, .86, 1.28, (201, 255, 170)),
    3: (.92, 1.18, .66, (188, 231, 255)),
    4: (.77, 1.24, .47, (255, 190, 143)),
    5: (.94, .96, 1.39, (255, 179, 208)),
}


def idle(kind, time):
    wave = lambda period, offset=0: sin((time / period + offset) * 2*pi)
    if kind == 'player':
        return Deformation(1.5*wave(2.5), 1.8*wave(2.1), 2.3*wave(2.1,.28), 2.7*wave(2.9,.15))
    if kind == 'pawn':
        return Deformation(.8*wave(1.5), .8*wave(1.18), 2.4*wave(1.18,.29), .45*wave(1.5))
    if kind == 'rook':
        return Deformation(2.6*wave(4.1), .5*wave(4.1), 2.0*wave(4.1,.28), .2)
    if kind == 'knight':
        return Deformation(.5*wave(2.9), .6*wave(2.9), 3.1*wave(2.55), 2.3*wave(2.55,.28))
    if kind == 'bishop':
        return Deformation(.45*wave(3.9), .65*wave(3.9), 1.7*wave(3.9,.12), 2.3*wave(3.25), (1+wave(2.1))*.5)
    if kind == 'queen':
        return Deformation(1.25*wave(4.45), .85*wave(4.45), 1.75*wave(4.45,.32), 3.65*wave(3.7,.12), (1+wave(3.1))*.5)
    return Deformation(1.8*wave(6.3), 1.65*wave(5.7), 2.8*wave(5.7,.14), .8*wave(6.3,.23), (1+wave(3.8))*.5)


# Windup and release amplitudes for the existing combat action of each kind.
ACTION = {
    'player': (5., 8., 6.), 'pawn': (4., 7., 7.), 'rook': (8., 10., 4.),
    'knight': (6., 6., 9.), 'bishop': (1., 1., 9.), 'queen': (3., 4., 10.), 'king': (7., 8., 7.),
}


def deformation(kind, chapter, pose):
    tempo, armor, cloth, _ = MATERIAL[chapter]
    state, phase = pose.state, pose.phase
    side = pose.direction
    if state is State.IDLE:
        rest = idle(kind, phase*tempo)
        return Deformation(rest.lean*armor, rest.rise, rest.gear*armor, rest.cloth*cloth, rest.core)
    if state is State.MOVE:
        step = sin(phase * (19 if kind in ('player','pawn') else 12)*tempo)
        return Deformation(side*(2.8 if kind in ('rook','king') else 2.1),
                           1.1*step, armor*step*2.2, cloth*sin(phase*15)*2)
    charge, launch, action = ACTION[kind]
    if state is State.WINDUP:
        power = min(1., max(0., phase))
        pulse = pose.attack_kind == 'king_pulse'
        return Deformation(-side*charge*power, -3*power, action*power*armor, cloth*power*2,
                           power if kind in ('bishop','queen','king') else 0., .10*power if pulse else .035*power)
    if state is State.ATTACK:
        power = (1-phase)**2
        pulse = pose.attack_kind == 'king_pulse'
        return Deformation(0 if pulse else side*launch*power, (8 if pulse else 3)*power,
                           side*action*power*armor, -3*power*cloth, power if kind in ('bishop','queen','king') else 0.)
    if state is State.HIT:
        strength = min(9, 3.5+pose.amount*.7)*(1-phase)
        return Deformation(-strength*side, -strength*.35, strength*.35, strength*.25, squash=.035*(1-phase))
    if state is State.STUN:
        return Deformation(2.0*sin(phase*13), -3, sin(phase*10)*3, .5, squash=.075)
    if state is State.DEATH:
        fall = phase**2 if kind == 'king' else 1-(1-phase)**2
        return Deformation(-14*fall, -7*fall, -4*fall, 4*fall, squash=.66*fall,
                           opacity=max(0., 1-fall**1.6))
    power = .78 if state is State.PARRY_READY else 1-phase
    magnitude = {State.PARRY_READY: 4., State.PARRY_NORMAL: 6.,
                 State.PARRY_PERFECT: 9., State.PARRY_FAILED: -5.}[state]
    return Deformation(-side*magnitude*power*.65, -2*power, magnitude*power, 2*power*cloth,
                       power if state is State.PARRY_PERFECT else 0., .03*power)


# x is sprite-local, y increases toward the feet. Independently weighted
# equipment and cloth share vertices with the torso and never leave cut seams.
GEAR_X = {'player': .28, 'pawn': .30, 'rook': .72, 'knight': .70,
          'bishop': .33, 'queen': .35, 'king': .64}
GEAR_Y = {'player': .47, 'pawn': .44, 'rook': .43, 'knight': .27,
          'bishop': .31, 'queen': .32, 'king': .32}
COLS = 5
ROWS = 6
UV = tuple((col/COLS,row/ROWS) for row in range(ROWS+1) for col in range(COLS+1))
INDICES = tuple(i for r in range(ROWS) for c in range(COLS) for j in (r*(COLS+1)+c,)
                for i in (j,j+1,j+COLS+1,j+1,j+COLS+2,j+COLS+1))
SDL_INDICES = (ctypes.c_int*len(INDICES))(*INDICES)


def weights(kind, chapter, u, v):
    gear_x = .30 if kind == 'knight' and chapter in (1, 2, 3) else GEAR_X[kind]
    gear = max(0., 1-abs(u-gear_x)/.42) * max(0., 1-abs(v-GEAR_Y[kind])/.49)
    cloth = min(1., abs(u-.5)*2.5) * max(0., 1-abs(v-.66)/.47)
    core = max(0., 1-abs(u-.50)*3.2-abs(v-.40)*3.0)
    if kind == 'bishop':
        core = max(gear*.65, core*.7)
    if kind in ('pawn', 'player'):
        # Shield response on the opposite side is smaller and counter-phased.
        gear -= .55*max(0., 1-abs(u-(1-gear_x))/.24)*max(0., 1-abs(v-.53)/.33)
    return gear, cloth, core


@lru_cache(maxsize=128)
def weighted_vertices(kind, chapter, foot_row):
    points = ((u, foot_row if v == (ROWS-1)/ROWS else v) for u,v in UV)
    return tuple((u,v,*weights(kind,chapter,u,v)) for u,v in points)


def draw_actor(canvas, texture, kind, chapter, layout, pose):
    import sdl2 as s

    effect = deformation(kind, chapter, pose)
    tint = MATERIAL[chapter][3]
    size = layout['height']
    anchor_x = layout['foot'][0]
    ground = layout['foot'][1] + layout.get('elevation', 0.)
    top_of_square = layout['center'][1] + size/2
    strength = size/100

    def point(u,v,gear,cloth):
        y = top_of_square-v*size
        # Pin a band containing both foot contacts; weight higher parts smoothly.
        height = max(0., min(1., (y-ground)/(.78*size)))
        pin = min(1., height*5)
        x = anchor_x + (u-.5)*size + strength*(
            effect.lean*height + pin*(effect.gear*gear + effect.cloth*cloth*(u-.5)*2))
        y = y - max(0., y-ground)*effect.squash + strength*(
            effect.rise*height + effect.gear*gear*pin*(.43 if kind == 'knight' else .16))
        return x, y

    verts = (s.SDL_Vertex * len(UV))()
    alpha = round(effect.opacity*255)
    foot_row = round((top_of_square-ground)/size*256)/256
    for i, (u,v,gear,cloth,core) in enumerate(weighted_vertices(kind,chapter,foot_row)):
        x,y = point(u,v,gear,cloth)
        color = effect.core*core*.72
        verts[i].position = s.SDL_FPoint(x,899-y)
        verts[i].tex_coord = s.SDL_FPoint(u,v)
        verts[i].color = s.SDL_Color(*(round(255+(channel-255)*color) for channel in tint),alpha)
    if s.SDL_RenderGeometry(canvas.renderer, texture, verts, len(verts), SDL_INDICES, len(INDICES)):
        raise ArenaArtError('SDL actor mesh failed: ' + s.SDL_GetError().decode())
    top_v = (top_of_square-layout['top'])/size
    gear,cloth,_ = weights(kind,chapter,.5,top_v)
    return point(.5,top_v,gear,cloth)
