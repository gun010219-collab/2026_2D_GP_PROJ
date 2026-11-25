"""Tick-synchronous risk overlay and read-only Left Alt input guidance."""
from array import array
from ctypes import c_float, c_int, c_uint16, byref
from dataclasses import dataclass
from math import cos, sin, tau
from struct import Struct

import sdl2 as s

from arena_art_common import CAMERA, ArenaArtError
from enemy_attack import EnemyAttackEvent
from health_renderer import HealthRenderer
from parry_resolution import grade_for_delta


@dataclass(frozen=True)
class Risk:
    attack: EnemyAttackEvent
    progress: float
    grade: str | None
    opacity: float


@dataclass(frozen=True)
class TimingRing:
    attack_key: tuple
    ticks_left: int
    radius: float


@dataclass(frozen=True)
class ParryHint:
    status: str
    tick: int
    target: tuple | None = None
    ring: TimingRing | None = None


def risk_at(event, tick):
    if not event.telegraph_start_tick <= tick < event.hit_tick:
        return None
    delta = event.hit_tick - tick
    progress = (tick - event.telegraph_start_tick) / (event.hit_tick - event.telegraph_start_tick)
    grade = grade_for_delta(delta)
    pulse = event.attack_kind == 'king_pulse'
    if grade is None:
        ramp = progress**1.75
        opacity = .05 + .285*ramp if pulse else .04 + .40*ramp
    else:
        opacity = .65 + .13*(7-delta)/6 if grade=='perfect' else .45 + .18*(18-delta)/10
        if pulse:
            opacity = .08 + .58*opacity
    return Risk(event,progress,grade,opacity)


def warning_frame(game, *, blocked=False, held=False):
    """Return one live warning per cell and the candidate for the next fresh input."""
    if not game.playing:
        return {},None
    resolver, tick = game.resolver, game.combat.tick
    attacks = sorted(resolver.live_telegraphs(tick),key=lambda e:(e.hit_tick,e.attack_id,e.key))
    cells = {}
    for attack in attacks:
        risk = risk_at(attack,tick)
        for cell in attack.target_cells:
            cells.setdefault(cell,risk)
    cell = game.player.position
    if blocked or cell not in cells:
        return cells,None

    # main queues input on a settled frame. The next fresh tick is the
    # earliest edge that can bind, even if display refresh is much faster.
    input_tick = tick + (game.encounter.tick == tick)
    threat = cells[cell].attack
    target = resolver.parry_target(input_tick,telegraphs=attacks)
    # Until an input can link, count down to the earliest actual danger.
    countdown = target or threat
    remaining = countdown.hit_tick - tick
    duration = countdown.hit_tick - countdown.telegraph_start_tick
    ring = TimingRing(countdown.key,remaining,.23+.35*remaining/duration)
    if held:
        return cells,ParryHint('release',input_tick,ring=ring)
    if not game.parry.can_request(input_tick):
        return cells,ParryHint('cooldown',input_tick,ring=ring)
    if target:
        if target.hit_tick < resolver.player_invulnerable_until_tick:
            return cells,ParryHint('immune',input_tick,ring=ring)
        return cells,ParryHint(grade_for_delta(target.hit_tick-input_tick),input_tick,target.key,ring)
    delta = threat.hit_tick - input_tick
    status = 'impact' if delta == 0 else 'wait' if grade_for_delta(delta) is None else 'no_link'
    return cells,ParryHint(status,input_tick,ring=ring)


def _quad(x0,y0,x1,y1):
    return ((x0,y0),(x1,y0),(x1,y1),(x0,y1))


_RING = tuple((cos(tau*i/32),sin(tau*i/32)) for i in range(32))
_POINT = Struct('=ff')


class WarningGeometry:
    """Keep projected coordinates and topology fixed. Upload one tinted batch."""
    def __init__(self):
        xy, self.groups = [], {}
        for row in range(10):
            for col in range(10):
                self.groups[col,row] = self._tile(xy,col,row)
        self.ring_centers = {}
        for col,row in self.groups:
            x,y = CAMERA.project(col+.5,row+.30)
            right,_ = CAMERA.project(col+1.5,row+.30)
            _,above = CAMERA.project(col+.5,row+1.30)
            self.ring_centers[col,row] = x,899-y,right-x,(above-y)*.54
        self.ring_start = len(xy)//2
        self.ring_indices = array('H')
        for i in range(len(_RING)):
            a,b = self.ring_start+2*i,self.ring_start+2*((i+1)%len(_RING))
            self.ring_indices.extend((a,b,a+1,a+1,b,b+1))
        xy.extend((0.,)*(len(_RING)*4))
        self.vertex_count = len(xy)//2
        self.xy = (c_float*len(xy))(*xy)
        self.rgba = bytearray(self.vertex_count*4)
        self.colors = (s.SDL_Color*self.vertex_count).from_buffer(self.rgba)

    @staticmethod
    def _tile(xy,col,row):
        def group(points,indices):
            base = len(xy)//2
            for x,y in points:
                px,py = CAMERA.project(col+x,row+y)
                xy.extend((px,899-py))
            return base,len(points),array('H',(base+i for i in indices))

        triangles = (0,1,2,0,2,3)
        outside = _quad(.036,.036,.964,.964)
        inside = _quad(.073,.073,.927,.927)
        fill = group(outside,triangles)
        rim_indices = tuple(i for a,b in ((0,1),(1,2),(2,3),(3,0))
                            for i in (a,b,b+4,a,b+4,a+4))
        rim = group(outside+inside,rim_indices)
        marks = []
        for corner in range(4):
            x,y = outside[corner]
            sx,sy = (1 if x < .5 else -1),(1 if y < .5 else -1)
            # Six positions form an L that stays within the projected tile.
            marks.extend((x+sx*u,y+sy*v) for u,v in
                         ((0,0),(.23,0),(.23,.057),(.057,.057),(.057,.23),(0,.23)))
        corners = group(marks,(offset+i for offset in range(0,24,6)
                               for i in (0,1,2,0,2,3,0,3,4,0,4,5)))
        aim = group(((.09,.31),(.16,.41),(.09,.51),(.84,.41),(.91,.31),(.91,.51)),
                    (0,1,2,3,4,5))
        return fill,rim,corners,aim

    def paint_ring(self, cell, hint):
        x,y,sx,sy = self.ring_centers[cell]
        radius = hint.ring.radius
        inner = radius - (.065 if hint.status=='perfect' else .045)
        offset = self.ring_start*_POINT.size
        for dx,dy in _RING:
            _POINT.pack_into(self.xy,offset,x+dx*sx*radius,y-dy*sy*radius)
            _POINT.pack_into(self.xy,offset+_POINT.size,x+dx*sx*inner,y-dy*sy*inner)
            offset += 2*_POINT.size
        light = {'perfect':(255,245,216,255),'normal':(183,230,255,242)}.get(
            hint.status,(250,146,158,228))
        pair = bytes((*light,26,11,15,245))
        self.rgba[self.ring_start*4:] = pair*len(_RING)

    def draw(self, canvas, cells, player_cell, hint):
        indices = array('H')
        color_cache = {}

        def paint(group,color):
            start,count,index = group
            self.rgba[start*4:(start+count)*4] = color*count
            indices.extend(index)

        for cell,risk in cells.items():
            fill,rim,corners,_ = self.groups[cell]
            lookup = risk.attack.key
            if lookup not in color_cache:
                pulse = risk.attack.attack_kind=='king_pulse'
                if risk.grade=='perfect':
                    border = (250,209,132,164 if pulse else 230)
                elif risk.grade=='normal':
                    border = (255,125,130,190 if pulse else 220)
                else:
                    border = (241,96,111,round(90+80*risk.progress**1.75))
                corner = (255,245,216,222 if pulse else 255)
                color_cache[lookup] = (bytes((196,28,49,round(risk.opacity*255))),bytes(border),bytes(corner))
            surface,border,accent = color_cache[lookup]
            paint(fill,surface)
            paint(rim,border)
            if risk.grade == 'perfect':
                paint(corners,accent)
        if hint and hint.target:
            paint(self.groups[player_cell][3],bytes(HINTS[hint.status][1]) + b'\xff')
        if hint and hint.ring:
            self.paint_ring(player_cell,hint)
            indices.extend(self.ring_indices)

        renderer = canvas.renderer
        blend = c_int()
        if s.SDL_GetRenderDrawBlendMode(renderer,byref(blend)):
            raise ArenaArtError('Unable to read telegraph blend mode')
        if s.SDL_SetRenderDrawBlendMode(renderer,s.SDL_BLENDMODE_BLEND):
            raise ArenaArtError('Unable to set telegraph blend mode')
        raw = (c_uint16*len(indices)).from_buffer(indices)
        try:
            if s.SDL_RenderGeometryRaw(renderer,None,self.xy,8,self.colors,4,None,0,
                                       self.vertex_count,raw,len(indices),2):
                raise ArenaArtError(s.SDL_GetError().decode())
        finally:
            s.SDL_SetRenderDrawBlendMode(renderer,blend.value)


HINTS = {
    'wait': ('WAIT FOR PARRY',(254,170,174)),
    'normal': ('L ALT  NORMAL',(183,230,255)),
    'perfect': ('L ALT  PERFECT',(255,237,175)),
    'cooldown': ('PARRY COOLDOWN',(185,183,185)),
    'release': ('RELEASE L ALT',(185,183,185)),
    'no_link': ('NO PARRY LINK',(254,170,174)),
    'impact': ('IMPACT NEXT TICK',(254,170,174)),
    'immune': ('IMMUNE AT IMPACT',(185,183,185)),
}


class TelegraphRenderer:
    def __init__(self):
        self.geometry = None
        self.failed = False
        self.blocked = self.held = False

    def draw(self, canvas, game):
        cells,hint = warning_frame(game,blocked=self.blocked,held=self.held)
        if cells:
            if self.geometry is None:
                self.geometry = WarningGeometry()
            self.geometry.draw(canvas,cells,game.player.position,hint)
            if hint and hint.target and hint.status=='perfect':
                x,y = CAMERA.project(game.player.col+.5,game.player.row+.30)
                canvas.draw_rectangle(x-17,y-25,x+17,y-11,24,14,18,filled=True)
                HealthRenderer._text(canvas,'ALT',x-11,y-23,color=HINTS['perfect'][1])
        return cells,hint

    def draw_hint(self, canvas, hint):
        if hint:
            text,color = HINTS[hint.status]
            HealthRenderer._text(canvas,'NEXT INPUT',44,744)
            HealthRenderer._text(canvas,text,44,724,color=color)
