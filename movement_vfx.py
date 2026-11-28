"""Local movement echoes using the player's existing mesh texture."""
import ctypes
from math import hypot

from arena_art_common import ArenaArtError
from combat_vfx import MAX_EFFECTS, MAX_PARTICLES
from config import BOARD_BOTTOM, BOARD_LEFT, TILE_SIZE


def fits_budget(manager, fast):
    elements = 5 if fast else 2
    return (len(manager.effects) < MAX_EFFECTS
            and sum(effect.particles for effect in manager.effects) + elements <= MAX_PARTICLES)


def draw(canvas, texture, layout, trail):
    import sdl2 as s

    origin, target, progress, fade, fast = trail

    def at(portion):
        x = origin[0] + (target[0] - origin[0]) * portion
        y = origin[1] + (target[1] - origin[1]) * portion
        return layout((x-BOARD_LEFT)/TILE_SIZE-.5, (y-BOARD_BOTTOM)/TILE_SIZE-.5)

    echoes = ((.30, 132), (.78, 73)) if fast else ((.56, 100),)
    vertices = (s.SDL_Vertex * (6 * len(echoes)))()
    for i, (lag, strength) in enumerate(reversed(echoes)):
        pose = at(progress * (1 - lag))
        cx, cy = pose['center']
        size = pose['height']
        half = size * .5
        color = s.SDL_Color(166, 219, 255, round(strength * fade**.66))
        for j, (u, v) in enumerate(((0, 0), (1, 0), (0, 1), (0, 1), (1, 0), (1, 1))):
            vertices[i * 6 + j] = s.SDL_Vertex(
                s.SDL_FPoint(cx-half+size*u, 899-cy-half+size*v), color, s.SDL_FPoint(u, v))
    renderer = canvas.renderer
    if s.SDL_RenderGeometry(renderer, texture, vertices, len(vertices), None, 0):
        raise ArenaArtError('Could not draw movement echoes')

    sx, sy = at(0)['foot']
    ex, ey = at(1)['foot']
    length = hypot(ex-sx, ey-sy)
    if length < 1:
        return
    dx, dy = (ex-sx)/length, (ey-sy)/length
    lines = ((-10, 5, .86), (11, 11, .68), (-7, 23, .56)) if fast else ((-8, 8, .72),)
    wind = (s.SDL_Vertex * (3 * len(lines)))()
    for i, (offset, height, length_fraction) in enumerate(lines):
        x = sx + dx*length*progress - dy*offset
        y = sy + dy*length*progress + dx*offset + height
        tail = length * progress * length_fraction
        bright = s.SDL_Color(179, 232, 255, round((180 if fast else 133) * fade**.64))
        clear = s.SDL_Color(179, 232, 255, 0)
        wind[i*3] = s.SDL_Vertex(s.SDL_FPoint(x-dx*tail, 899-y+dy*tail), clear, s.SDL_FPoint())
        wind[i*3+1] = s.SDL_Vertex(s.SDL_FPoint(x-dy*2.5, 899-y-dx*2.5), bright, s.SDL_FPoint())
        wind[i*3+2] = s.SDL_Vertex(s.SDL_FPoint(x+dy*2.5, 899-y+dx*2.5), clear, s.SDL_FPoint())

    previous = ctypes.c_int()
    if s.SDL_GetRenderDrawBlendMode(renderer, ctypes.byref(previous)):
        raise ArenaArtError('Could not read movement blend mode')
    if s.SDL_SetRenderDrawBlendMode(renderer, s.SDL_BLENDMODE_BLEND):
        raise ArenaArtError('Could not set movement blend mode')
    try:
        if s.SDL_RenderGeometry(renderer, None, wind, len(wind), None, 0):
            raise ArenaArtError('Could not draw movement wind')
    finally:
        s.SDL_SetRenderDrawBlendMode(renderer, previous.value)
