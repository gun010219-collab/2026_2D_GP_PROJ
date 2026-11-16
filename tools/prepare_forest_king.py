"""Normalize the new crown-repaired King only; preserve every existing concept/unit."""
import ctypes
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import sdl2 as s
from sdl2.sdlimage import IMG_Load, IMG_SavePNG, IMG_Init, IMG_Quit, IMG_INIT_PNG
from tools.prepare_stage5_art import alpha_bounds


def prepare(folder):
    for filename in ('asset_manifest.json', 'knight_manifest.json', 'bishop_manifest.json'):
        for row in json.loads((folder/filename).read_text())['assets']:
            for key, digest in (('file', 'sha256'), ('source', 'source_sha256')):
                if hashlib.sha256((folder/row[key]).read_bytes()).hexdigest() != row[digest]:
                    raise ValueError('Existing forest unit changed: '+row[key])
    source = folder/'source/king_c6.png'
    original = rgba = target = renderer = texture = None
    if s.SDL_Init(s.SDL_INIT_VIDEO): raise RuntimeError('SDL initialization')
    try:
        if not IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG: raise RuntimeError('PNG initialization')
        original = IMG_Load(str(source).encode('utf-8'))
        if not original: raise OSError('Cannot load repaired King')
        rgba = s.SDL_ConvertSurfaceFormat(original, s.SDL_PIXELFORMAT_RGBA32, 0)
        if not rgba: raise OSError('Cannot convert repaired King')
        box, clear = alpha_bounds(rgba)
        x, y, right, bottom = box; width, height = rgba.contents.w, rgba.contents.h
        if not clear or not (0 < x < right < width and 0 < y < bottom < height):
            raise ValueError('King must be transparent with a complete silhouette and clear border')
        scale = 220/max(right-x, bottom-y); dw, dh = round((right-x)*scale), round((bottom-y)*scale)
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY, b'1')
        target = s.SDL_CreateRGBSurfaceWithFormat(0, 256, 256, 32, s.SDL_PIXELFORMAT_RGBA32)
        renderer = s.SDL_CreateSoftwareRenderer(target) if target else None
        texture = s.SDL_CreateTextureFromSurface(renderer, rgba) if renderer else None
        if not texture: raise OSError('King resize allocation')
        s.SDL_SetTextureBlendMode(texture, s.SDL_BLENDMODE_NONE)
        s.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0); s.SDL_RenderClear(renderer)
        src = s.SDL_Rect(x, y, right-x, bottom-y); dst = s.SDL_Rect((256-dw)//2, (256-dh)//2, dw, dh)
        if s.SDL_RenderCopy(renderer, texture, ctypes.byref(src), ctypes.byref(dst)): raise OSError('King resize')
        s.SDL_RenderPresent(renderer)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'king.png'
            if IMG_SavePNG(target, str(p).encode('utf-8')): raise OSError('King PNG save')
            data = p.read_bytes()
        out = folder/'king_c6.png'
        if out.exists() and out.read_bytes() != data: raise ValueError('Preserve existing prepared King')
        if not out.exists(): out.write_bytes(data)
        outbox, outclear = alpha_bounds(target)
        record = dict(status='C6 crown-repaired King candidate; user Windows GUI pending',
                      operation='Uniform SDL alpha crop/pad/linear resize; no content repainting',
                      assets=[dict(name='king_c6', source='source/king_c6.png', file='king_c6.png',
                                   source_size=[width, height], source_alpha_bbox=box, source_transparent_pixels=clear,
                                   size=[256, 256], alpha_bbox=outbox, transparent_pixels=outclear,
                                   file_bytes=len(data), rgba_bytes=256*256*4,
                                   source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                   sha256=hashlib.sha256(data).hexdigest())])
        manifest = folder/'king_manifest.json'
        text = json.dumps(record, indent=2)+'\n'
        if manifest.exists() and json.loads(manifest.read_text()) != json.loads(text): raise ValueError('Preserve King metadata')
        if not manifest.exists(): manifest.write_text(text, encoding='utf-8')
        print(text)
    finally:
        if texture: s.SDL_DestroyTexture(texture)
        if renderer: s.SDL_DestroyRenderer(renderer)
        for surface in (target, rgba, original):
            if surface: s.SDL_FreeSurface(surface)
        IMG_Quit(); s.SDL_Quit()


if __name__ == '__main__':
    prepare(ROOT/'assets/chapter2_units')
