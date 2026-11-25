"""Single-texture combat VFX batches. UVs refer to the authored 4×2 atlas."""
from math import cos, hypot, sin
from pathlib import Path
from struct import Struct

import sdl2 as s

from arena_art_common import ArenaArtError

ATLAS = Path(__file__).parent / 'assets' / 'vfx' / 'combat_atlas.png'
TILES = ('halo', 'flare', 'ribbon', 'smoke', 'ripple', 'runes', 'crystal', 'ember')
UVS = {name: (((i%4)*64+.5)/256, ((i//4)*64+.5)/128,
              ((i%4+1)*64-.5)/256, ((i//4+1)*64-.5)/128)
       for i,name in enumerate(TILES)}
_VERTEX = Struct('=ff4Bff')
_TRIANGLES = (0,1,2,2,1,3)


class VFXAtlas:
    def __init__(self):
        self.image = None
        self.canvas = None
        self.vertices = (s.SDL_Vertex * 1152)()
        self.count = 0
        self.failed = False

    def open(self, canvas):
        if self.failed:
            return False
        if self.image is None:
            self.canvas = canvas
            self.image = canvas.load_image(str(ATLAS))
            if (self.image.w,self.image.h) != (256,128):
                raise ArenaArtError('Invalid VFX atlas dimensions')
            if s.SDL_SetTextureBlendMode(self.image.texture,s.SDL_BLENDMODE_BLEND):
                raise ArenaArtError('Cannot apply VFX atlas alpha blending')
        return True

    def close(self):
        self.count = 0
        if self.image is not None:
            self.canvas.SDL_DestroyTexture(self.image.texture)
            self.image.texture = None
            self.image = None
        self.canvas = None

    def flush(self):
        count, self.count = self.count, 0
        if count and s.SDL_RenderGeometry(self.canvas.renderer,self.image.texture,
                                         self.vertices,count,None,0):
            raise ArenaArtError(s.SDL_GetError().decode())

    def quad(self, tile, a, b, half_width, rgb, alpha):
        opacity = min(255,round(alpha*255))
        dx,dy = b[0]-a[0],b[1]-a[1]
        length = hypot(dx,dy)
        if opacity <= 0 or length < .01 or self.count == len(self.vertices):
            return
        nx,ny = -dy*half_width/length,dx*half_width/length
        u,v,U,V = UVS[tile]
        corners = ((a[0]+nx,a[1]+ny,u,v),(a[0]-nx,a[1]-ny,u,V),
                   (b[0]+nx,b[1]+ny,U,v),(b[0]-nx,b[1]-ny,U,V))
        offset = self.count*_VERTEX.size
        for index in _TRIANGLES:
            x,y,tx,ty = corners[index]
            _VERTEX.pack_into(self.vertices,offset,x,899-y,*rgb,opacity,tx,ty)
            offset += _VERTEX.size
        self.count += 6

    def stamp(self, tile, x, y, size, aspect, rgb, alpha, *, angle=0):
        dx,dy = size*cos(angle),size*sin(angle)
        self.quad(tile,(x-dx,y-dy),(x+dx,y+dy),size*aspect,rgb,alpha)
