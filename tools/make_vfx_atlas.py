"""Write the original R7-A2B RGBA atlas and its manifest using the standard library."""
import hashlib
import json
from math import atan2, cos, exp, hypot, sin
from pathlib import Path
from random import Random
from struct import pack
import zlib

ROOT = Path(__file__).resolve().parents[1]
SEED = 72025
TILE = 64
COLUMNS = 4
TILES = ('halo', 'flare', 'ribbon', 'smoke', 'ripple', 'runes', 'crystal', 'ember')
WIDTH, HEIGHT = COLUMNS * TILE, 2 * TILE

_rng = Random(SEED)
_SMOKE = tuple((_rng.uniform(-.6, .6), _rng.uniform(-.6, .6),
                _rng.uniform(6, 19), _rng.uniform(.23, .64)) for _ in range(18))


def opacity(tile, x, y):
    r, angle = hypot(x, y), atan2(y, x)
    outer = max(0., min(1., (1-r)*5))
    if tile == 'halo':
        return outer * exp(-4.3*r*r)
    if tile == 'flare':
        arms = (.13 + .87*cos(2*angle)**12)*exp(-2.7*r)
        return outer * max(exp(-24*r*r), arms)
    if tile == 'ribbon':
        envelope = max(0., 1-x*x)**.65
        return envelope*exp(-(3.7+2*x)*y*y*2.7)*max(0., 1-y*y)
    if tile == 'smoke':
        cloud = sum(power*exp(-tight*((x-cx)**2+(y-cy)**2))
                    for cx, cy, tight, power in _SMOKE)
        folds = .72+.28*sin(17*x+10*y+3*cos(6*y))*cos(9*y-6*x)
        return outer*max(0., cloud-.22)*folds
    if tile == 'ripple':
        return outer*(.84*exp(-98*(r-.67)**2)+.31*exp(-190*(r-.84)**2))
    if tile == 'runes':
        outer_ring = exp(-520*(r-.74)**2)
        marks = cos(9*angle)**24*exp(-172*(r-.53)**2)
        broken_ring = (.36+.64*cos(3*angle)**6)*exp(-370*(r-.40)**2)
        return outer*max(outer_ring, marks, broken_ring)
    if tile == 'crystal':
        branches = cos(3*angle)**24*exp(-1.0*r)
        return outer*max(branches, .74*exp(-42*r*r))
    # Narrow ascending flame with a compact hot base and a curled tail.
    curve = x - .28*sin(4*y)
    return outer*exp(-(6+18*(y+.8)**2)*curve*curve-2*(y+.27)**2)


def chunk(name, data):
    return pack('>I', len(data))+name+data+pack('>I', zlib.crc32(name+data))


def atlas_png():
    pixels = bytearray()
    for row in range(HEIGHT):
        pixels.append(0)
        for col in range(WIDTH):
            tile = TILES[row//TILE*COLUMNS+col//TILE]
            x = (col%TILE-31.5)/29.5
            y = (31.5-row%TILE)/29.5
            alpha = 0 if max(abs(x),abs(y)) >= 1 else opacity(tile, x, y)
            pixels.extend((255,255,255,max(0,min(255,round(alpha*255)))))
    return (b'\x89PNG\r\n\x1a\n'
            +chunk(b'IHDR',pack('>IIBBBBB',WIDTH,HEIGHT,8,6,0,0,0))
            +chunk(b'IDAT',zlib.compress(pixels,9))
            +chunk(b'IEND',b''))


def main():
    output = ROOT/'assets'/'vfx'
    output.mkdir(parents=True,exist_ok=True)
    png = atlas_png()
    (output/'combat_atlas.png').write_bytes(png)
    manifest = dict(file='combat_atlas.png',size=[WIDTH,HEIGHT],tile_size=TILE,
                    format='RGBA8',tiles=TILES,seed=SEED,
                    source='tools/make_vfx_atlas.py',creator='CHECKMATE / Codex',
                    provenance='Original project artwork from mathematical masks; no external inputs',
                    sha256=hashlib.sha256(png).hexdigest())
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
