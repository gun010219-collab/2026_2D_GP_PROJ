"""Incremental mechanical Bishop crop/pad; retain all approved Pawn/Rook bytes."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import sdl2 as s
from sdl2.sdlimage import IMG_Init, IMG_Quit, IMG_Load, IMG_SavePNG, IMG_INIT_PNG
from tools.prepare_stage5_art import alpha_bounds


def prepare(folder):
    src = folder / 'source/bishop.png'
    manifest_path = folder / 'asset_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    prior = {r['name']: r for r in manifest['assets']}
    for row in prior.values():
        for name, digest in ((row['file'], row['sha256']), (row['source'], row['source_sha256'])):
            if hashlib.sha256((folder/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Existing unit changed: ' + name)
    for row in json.loads((folder/'knight_manifest.json').read_text(encoding='utf-8'))['assets']:
        for name, digest in ((row['file'], row['sha256']), (row['source'], row['source_sha256'])):
            if hashlib.sha256((folder/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Existing Knight changed: ' + name)
    if s.SDL_Init(s.SDL_INIT_VIDEO):
        raise RuntimeError('SDL video initialization')
    original = rgba = target = renderer = tex = None
    try:
        if not IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG:
            raise RuntimeError('PNG initialization')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY, b'1')
        original = IMG_Load(str(src).encode('utf-8'))
        if not original:
            raise OSError('Cannot load Bishop source')
        rgba = s.SDL_ConvertSurfaceFormat(original, s.SDL_PIXELFORMAT_RGBA32, 0)
        if not rgba:
            raise OSError('Cannot convert Bishop source')
        bbox, clear = alpha_bounds(rgba)
        if not clear:
            raise ValueError('True alpha transparency required')
        x, y, right, bottom = bbox
        bw, bh = right-x, bottom-y
        scale = 220/max(bw, bh)
        dw, dh = round(bw*scale), round(bh*scale)
        target = s.SDL_CreateRGBSurfaceWithFormat(0, 256, 256, 32, s.SDL_PIXELFORMAT_RGBA32)
        if not target:
            raise OSError('Cannot allocate output')
        renderer = s.SDL_CreateSoftwareRenderer(target)
        tex = s.SDL_CreateTextureFromSurface(renderer, rgba) if renderer else None
        if not tex:
            raise OSError('Cannot create resizing texture')
        s.SDL_SetTextureBlendMode(tex, s.SDL_BLENDMODE_NONE)
        s.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
        s.SDL_RenderClear(renderer)
        crop = s.SDL_Rect(x, y, bw, bh)
        dst = s.SDL_Rect((256-dw)//2, (256-dh)//2, dw, dh)
        if s.SDL_RenderCopy(renderer, tex, ctypes.byref(crop), ctypes.byref(dst)):
            raise OSError('Bishop resize failed')
        s.SDL_RenderPresent(renderer)
        with tempfile.TemporaryDirectory() as d:
            png = Path(d)/'bishop.png'
            if IMG_SavePNG(target, str(png).encode('utf-8')):
                raise OSError('Bishop PNG save failed')
            data = png.read_bytes()
        out = folder/'bishop.png'
        if out.exists() and out.read_bytes() != data:
            raise ValueError('Existing Bishop differs; preserve it before making a new version')
        if not out.exists():
            out.write_bytes(data)
        out_box, out_clear = alpha_bounds(target)
        row = dict(name='bishop', source='source/bishop.png',
                   source_size=[rgba.contents.w, rgba.contents.h], source_alpha_bbox=bbox,
                   source_transparent_pixels=clear, file='bishop.png', size=[256, 256],
                   alpha_bbox=out_box, transparent_pixels=out_clear, rgba_bytes=256*256*4,
                   file_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                   source_sha256=hashlib.sha256(src.read_bytes()).hexdigest())
        # The existing Stage6 manifest is a frozen two-unit contract.
        bishop_manifest = folder/'bishop_manifest.json'
        record = dict(status='C4 live forest Bishop candidate; Windows visual approval pending',
                      operation=manifest['operation'], assets=[row])
        if bishop_manifest.exists():
            if json.loads(bishop_manifest.read_text(encoding='utf-8')) != json.loads(json.dumps(record)):
                raise ValueError('Bishop metadata differs')
        else:
            bishop_manifest.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(row, indent=2))
    finally:
        if tex:
            s.SDL_DestroyTexture(tex)
        if renderer:
            s.SDL_DestroyRenderer(renderer)
        for surface in (target, rgba, original):
            if surface:
                s.SDL_FreeSurface(surface)
        IMG_Quit()
        s.SDL_Quit()


if __name__ == '__main__':
    prepare(ROOT/'assets/chapter2_units')
