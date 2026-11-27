"""Continuous UV mesh for actor poses. Original sprite pixels stay in one texture."""
import ctypes
from dataclasses import dataclass, replace
from functools import lru_cache
from math import cos, pi, radians, sin
from struct import Struct

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
    gear_lift: float = 0.
    spread: float = 0.
    gear_turn: float = 0.
    torso_turn: float = 0.


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


MOVE = {
    'player': (3.2,19,3.0,3.5), 'pawn': (2.8,22,3.8,.8), 'rook': (4.2,11,3.0,.5),
    'knight': (3.0,15,3.6,2.5), 'queen': (2.2,12,1.9,4.1), 'king': (4.3,9,3.2,1.3),
}


# Each tuple holds the charged pose, release, follow-through and follow-through time.
# Offsets are in pixels at a 100px square. Squash stays anchored to ground contact.
ENEMY_ACTION = {
    'pawn': (Deformation(lean=-5,rise=-2,gear=-10,gear_lift=2),
             Deformation(lean=9,rise=2,gear=14,squash=.028),
             Deformation(lean=1,gear=-4,gear_lift=1), .24),
    'rook': (Deformation(lean=-4,rise=-3,gear=-4,squash=.09),
             Deformation(lean=12,rise=-2,gear=8,squash=.045),
             Deformation(lean=-4,rise=-2,gear=-3,squash=.04), .32),
    'knight': (Deformation(lean=-2,rise=-3,gear=-5,gear_lift=-5,squash=.075),
               Deformation(lean=6,rise=3,gear=8,gear_lift=6,cloth=3),
               Deformation(lean=-3,rise=-2,gear=-4,cloth=2,squash=.042), .32),
    'bishop': (Deformation(rise=3,gear=-3,gear_lift=14,cloth=-3,core=.82),
               Deformation(rise=-3,gear=7,gear_lift=-7,cloth=5,core=1.,squash=.045),
               Deformation(rise=1,gear=-3,gear_lift=3,cloth=-4,core=.37), .40),
    'queen': (Deformation(rise=3,gear=-4,gear_lift=8,cloth=8,core=.8,spread=-4),
              Deformation(rise=5,gear=7,gear_lift=-4,cloth=16,core=1.,spread=12),
              Deformation(rise=-3,gear=-2,gear_lift=4,cloth=9,core=.4,squash=.056,spread=-2), .42),
    'king': (Deformation(lean=-7,rise=5,gear=-6,gear_lift=9,cloth=-3,core=.35),
             Deformation(lean=13,rise=-6,gear=10,gear_lift=-7,cloth=7,core=.64,squash=.085),
             Deformation(lean=-4,rise=1,gear=-4,gear_lift=2,cloth=4,squash=.027), .46),
    'king_pulse': (Deformation(rise=-5,gear_lift=7,cloth=-6,core=1.,squash=.08,spread=-14),
                   Deformation(rise=9,gear_lift=4,cloth=17,core=1.,spread=20),
                   Deformation(rise=-5,gear_lift=-4,cloth=8,core=.47,squash=.072,spread=-4), .44),
}

ARRIVAL = {
    'rook': Deformation(lean=-8,rise=-4,gear=-7,gear_lift=-3,squash=.11),
    'knight': Deformation(lean=-4,rise=-5,gear=-5,gear_lift=-8,cloth=5,squash=.12),
}
REST = Deformation()


def enemy_action(kind, chapter, pose):
    profile = 'king_pulse' if pose.attack_kind=='king_pulse' else kind
    charge,release,follow,turn = ENEMY_ACTION[profile]
    phase = min(1.,max(0.,pose.phase))
    if pose.attack_motion=='anticipation':
        a,b,t = REST,charge,phase
    elif pose.attack_motion=='travel':
        a,b,t = release, Deformation(lean=release.lean*.7,gear=release.gear*.8,gear_lift=release.gear_lift*.7,
                                    cloth=release.cloth,squash=release.squash), phase
    else:
        first = ARRIVAL[kind] if pose.attack_motion=='arrival' else release
        a,b,t = (first,follow,phase/turn) if phase<turn else (follow,REST,(phase-turn)/(1-turn))
    t = t*t*(3-2*t)
    _,armor,cloth,_ = MATERIAL[chapter]
    cast = profile in ('bishop','queen','king_pulse')
    hand = (1. if chapter==3 else -1.) if cast else pose.direction
    # Mostly north/south attacks articulate through pitch instead of fake sideways lunges.
    depth = pose.depth_direction
    pitch = 1.-.20*depth
    def mix(name):
        return getattr(a,name)*(1-t)+getattr(b,name)*t
    gear = mix('gear')
    lean = mix('lean')
    return Deformation(lean=lean*pose.direction,rise=mix('rise')*pitch+.32*lean*depth,
                       gear=gear*hand*armor,cloth=mix('cloth')*cloth,core=mix('core'),
                       squash=mix('squash'),gear_lift=(mix('gear_lift')*pitch+.52*gear*depth)*armor,
                       spread=mix('spread'))


PLAYER_SWING = (
    (0., Deformation(lean=-3,rise=-1,gear=-7,gear_lift=4,cloth=-3,squash=.03)),
    (.19, Deformation(lean=11,rise=3,gear=15,gear_lift=-3,cloth=-5)),
    (.46, Deformation(lean=5,rise=-2,gear=9,gear_lift=-5,cloth=12,squash=.035)),
    (.73, Deformation(lean=-1,gear=-3,gear_lift=2,cloth=5)),
    (1., REST),
)
PLAYER_GUARD = {
    State.PARRY_READY: Deformation(lean=-4,rise=-2,gear=-7,gear_lift=3,cloth=2,squash=.035),
    State.PARRY_NORMAL: Deformation(lean=-7,rise=-3,gear=-11,gear_lift=5,cloth=5,squash=.06),
    State.PARRY_PERFECT: Deformation(lean=8,rise=5,gear=-17,gear_lift=10,cloth=15,core=1.,spread=5),
    State.PARRY_FAILED: Deformation(lean=-10,rise=-6,gear=6,gear_lift=-9,cloth=4,squash=.095),
}


def player_action(pose):
    side,depth = pose.direction,pose.depth_direction
    if pose.attack_motion=='swing':
        for (start,a),(end,b) in zip(PLAYER_SWING,PLAYER_SWING[1:]):
            if pose.phase <= end:
                weight = (pose.phase-start)/(end-start)
                break
    else:
        a,b = PLAYER_GUARD[pose.state],REST
        weight = 0. if pose.state is State.PARRY_READY else pose.phase
    weight = weight*weight*(3-2*weight)
    def mix(name):
        return getattr(a,name)*(1-weight)+getattr(b,name)*weight
    gear = mix('gear')
    lean = mix('lean')
    # Longitudinal strokes articulate vertically. The individual sleeve, sword
    # and opposite shield already have signed weights on the original mesh.
    hand = side if side else .32
    return Deformation(lean=lean*side,rise=mix('rise')+.48*lean*depth,
                       gear=gear*hand,gear_lift=mix('gear_lift')+.64*gear*depth,
                       cloth=mix('cloth')*(.85+.18*depth),core=mix('core'),
                       squash=mix('squash'),spread=mix('spread'))


# Weighted local pivots keep the intact texture and ankle anchors.
ATTACK_TURNS = {
    'player': ((-58,-12),(44,17),(22,9)),
    'pawn': ((-38,-11),(28,17),(-12,-6)),
    'rook': ((-19,-14),(24,20),(-16,-10)),
    'knight': ((-30,-13),(35,14),(16,7)),
    'bishop': ((-66,-5),(45,11),(-20,-6)),
    'queen': ((-35,-8),(49,13),(16,-7)),
    'king': ((-68,-13),(38,15),(22,-11)),
    'king_pulse': ((-18,-6),(32,7),(-15,-5)),
}
CONTACT_TURNS = {'rook':(-31,-15),'knight':(-34,-16)}


def articulated_action(kind,chapter,pose):
    profile = 'king_pulse' if pose.attack_kind=='king_pulse' else kind
    charge,release,follow = ATTACK_TURNS[profile]
    phase = pose.phase
    action = pose.attack_motion
    if action=='anticipation':
        steps = ((0.,(0,0)),(1.,charge))
    elif action=='travel':
        steps = ((0.,release),(.66,release),(1.,follow))
    elif action=='swing':
        steps = ((0.,charge),(.19,release),(.35,release),(.61,follow),(1.,(0,0)))
    else:
        first = CONTACT_TURNS[kind] if action=='arrival' else release
        steps = ((0.,first),(.18,first),(.50,follow),(1.,(0,0)))
    for (start,a),(end,b) in zip(steps,steps[1:]):
        if phase<=end:
            t = (phase-start)/(end-start)
            t = t*t*(3-2*t)
            gear,torso = (x+(y-x)*t for x,y in zip(a,b))
            break
    cast = profile in ('bishop','queen','king_pulse')
    sign = (1. if chapter==3 else -1.) if cast else pose.direction or -pose.depth_direction
    base = player_action(pose) if kind=='player' else enemy_action(kind,chapter,pose)
    return replace(base,lean=base.lean*1.22,rise=base.rise*1.27,cloth=base.cloth*1.25,
                   spread=base.spread*1.23,gear_turn=gear*sign,torso_turn=torso*sign)


def deformation(kind, chapter, pose, *, improved=False):
    if pose.articulated:
        return articulated_action(kind,chapter,pose)
    if pose.attack_motion and kind=='player':
        return player_action(pose)
    if pose.attack_motion:
        return enemy_action(kind,chapter,pose)
    tempo, armor, cloth, _ = MATERIAL[chapter]
    state, phase = pose.state, pose.phase
    side = pose.direction
    if state is State.IDLE:
        rest = idle(kind, phase*tempo)
        return Deformation(rest.lean*armor, rest.rise, rest.gear*armor, rest.cloth*cloth, rest.core)
    if state is State.MOVE:
        if improved:
            lean, stride, gear, cloth_lag = MOVE[kind]
            cycle = phase * stride * tempo
            return Deformation(side*lean,.65*sin(cycle),armor*gear*sin(cycle-.75),
                               cloth*cloth_lag*sin(cycle-1.35))
        step = sin(phase * (19 if kind in ('player','pawn') else 12)*tempo)
        return Deformation(side*(2.8 if kind in ('rook','king') else 2.1),
                           1.1*step, armor*step*2.2, cloth*sin(phase*15)*2)
    charge, launch, action = ACTION[kind]
    if state is State.WINDUP:
        power = min(1., max(0., phase))
        if improved:
            power = power*power*(3-2*power)
        pulse = pose.attack_kind == 'king_pulse'
        return Deformation(-side*charge*power, -3*power, action*power*armor, cloth*power*2,
                           power if kind in ('bishop','queen','king') else 0., .10*power if pulse else .035*power)
    if state is State.ATTACK:
        power = (1-phase)**2
        pulse = pose.attack_kind == 'king_pulse'
        if improved:
            settle = sin(pi*phase)*(1-phase)
            return Deformation(0 if pulse else side*launch*power,(8 if pulse else 3)*power,
                               side*action*(power-.27*settle)*armor,(-3*power+4*settle)*cloth,
                               power if kind in ('bishop','queen','king') else 0.)
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
_VERTEX = Struct('=ff4Bff')


def gear_column(kind,chapter,attack):
    if attack and chapter==3 and kind in ('bishop','queen'):
        return .64  # Ice Bishop's staff and Ice Queen's scepter are on the right.
    return .30 if kind=='knight' and chapter in (1,2,3) else GEAR_X[kind]


def weights(kind, chapter, u, v, attack=False):
    gear_x = gear_column(kind,chapter,attack)
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
def weighted_vertices(kind, chapter, foot_row, attack=False):
    points = ((u, foot_row if v == (ROWS-1)/ROWS else v) for u,v in UV)
    return tuple((u,v,*weights(kind,chapter,u,v,attack)) for u,v in points)


def draw_actor(canvas, texture, kind, chapter, layout, pose, *, effect=None):
    import sdl2 as s

    effect = deformation(kind, chapter, pose) if effect is None else effect
    tint = MATERIAL[chapter][3]
    size = layout['height']
    anchor_x = layout['foot'][0]
    ground = layout['foot'][1] + layout.get('elevation', 0.)
    top_of_square = layout['center'][1] + size/2
    strength = size/100
    attack = bool(pose.attack_motion)
    turns = ()
    if effect.gear_turn or effect.torso_turn:
        def turn(pivot_x,pivot_y,angle):
            r = radians(angle)
            return pivot_x,pivot_y,cos(r)-1.,sin(r)
        turns = (turn(.5+(gear_column(kind,chapter,attack)-.5)*.66,.53,effect.gear_turn),
                 turn(.5,.61,effect.torso_turn))

    def point(u,v,gear,cloth):
        y = top_of_square-v*size
        # Pin a band containing both foot contacts; weight higher parts smoothly.
        height = max(0., min(1., (y-ground)/(.78*size)))
        pin = min(1., height*5)
        x = anchor_x + (u-.5)*size + strength*(
            effect.lean*height + pin*(effect.gear*gear + effect.cloth*cloth*(u-.5)*2)
            + effect.spread*(u-.5)*height)
        y = y - max(0., y-ground)*effect.squash + strength*(
            effect.rise*height + effect.gear*gear*pin*(.43 if kind == 'knight' else .16)
            + effect.gear_lift*max(0.,gear)*pin)
        if turns:
            for (pivot_x,pivot_y,c,s),weight in zip(turns,(max(0.,gear)*pin,height)):
                dx,dy = u-pivot_x,pivot_y-v
                x += (c*dx-s*dy)*weight*size
                y += (s*dx+c*dy)*weight*size
        return x, y

    verts = (s.SDL_Vertex * len(UV))()
    alpha = round(effect.opacity*255)
    foot_row = round((top_of_square-ground)/size*256)/256
    for i, (u,v,gear,cloth,core) in enumerate(weighted_vertices(kind,chapter,foot_row,attack)):
        x,y = point(u,v,gear,cloth)
        color = effect.core*core*.72
        if color:
            red,green,blue = (round(255+(channel-255)*color) for channel in tint)
        else:
            red = green = blue = 255
        _VERTEX.pack_into(verts,i*_VERTEX.size,x,899-y,red,green,blue,alpha,u,v)
    if s.SDL_RenderGeometry(canvas.renderer, texture, verts, len(verts), SDL_INDICES, len(INDICES)):
        raise ArenaArtError('SDL actor mesh failed: ' + s.SDL_GetError().decode())
    top_v = (top_of_square-layout['top'])/size
    gear,cloth,_ = weights(kind,chapter,.5,top_v,attack)
    return point(.5,top_v,gear,cloth)
