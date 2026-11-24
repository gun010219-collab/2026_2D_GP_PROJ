"""Mechanical Ice unit preparation; transactional outputs and unchanged originals."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
KINDS = ('pawn', 'rook', 'knight')


def pixels(surface):
    obj = surface.contents
    raw = ctypes.string_at(obj.pixels, obj.pitch * obj.h)
    return b''.join(raw[y * obj.pitch:y * obj.pitch + obj.w * 4] for y in range(obj.h))


def metrics(surface):
    w, h = surface.contents.w, surface.contents.h
    raw = pixels(surface)
    boxes = {}
    for threshold in (0, 5):
        points = [i for i in range(w * h) if raw[i * 4 + 3] > threshold]
        if not points:
            raise ValueError('Empty alpha silhouette')
        xs = [i % w for i in points]; ys = [i // w for i in points]
        boxes[str(threshold)] = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
    partial = [i for i in range(w * h) if 0 < raw[i * 4 + 3] < 255]
    box = boxes['5']
    return dict(size=[w, h], alpha_bbox=box, alpha_nonzero_bbox=boxes['0'],
                transparent_pixels=raw[3::4].count(0), partial_alpha_pixels=len(partial),
                near_black_partial_pixels=sum(max(raw[i*4:i*4+3]) < 8 for i in partial),
                safety_margin_fraction=round(min(box[0]/w, box[1]/h, (w-box[2])/w, (h-box[3])/h), 6))


def set_pixels(surface, raw):
    obj = surface.contents
    for y in range(obj.h):
        row = raw[y * obj.w * 4:(y + 1) * obj.w * 4]
        ctypes.memmove(obj.pixels + y * obj.pitch, bytes(row), len(row))


def normalized(source, *, minimum_source_margin=.05):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load, IMG_SavePNG
    original = rgba = cropped = target = None
    renderer = texture = None
    try:
        header = source.read_bytes()[:26]
        if header[:8] != b'\x89PNG\r\n\x1a\n' or len(header) < 26 or header[24:26] != bytes((8, 6)):
            raise ValueError('Expected an 8-bit RGBA PNG: ' + source.name)
        original = IMG_Load(str(source).encode('utf-8'))
        if not original: raise OSError('PNG load failed: ' + source.name)
        rgba = s.SDL_ConvertSurfaceFormat(original, s.SDL_PIXELFORMAT_RGBA32, 0)
        if not rgba: raise OSError('RGBA conversion failed')
        before = metrics(rgba)
        if max(before['size']) < 1024 or not before['transparent_pixels']:
            raise ValueError('Source needs high resolution and true transparency')
        if before['safety_margin_fraction'] < minimum_source_margin:
            raise ValueError(f'Source alpha falls outside the {minimum_source_margin:.1%} safety margin')
        x, y, right, bottom = before['alpha_bbox']
        bw, bh = right-x, bottom-y
        # RGB is premultiplied only for interpolation, then restored to straight alpha.
        # This avoids dark mattes from transparent black samples in linear filtering.
        data = pixels(rgba); crop = bytearray(bw * bh * 4)
        for cy in range(bh):
            for cx in range(bw):
                a = ((cy+y)*before['size'][0]+cx+x)*4; b = (cy*bw+cx)*4
                alpha = data[a+3]
                crop[b:b+4] = bytes((*((data[a+c]*alpha+127)//255 for c in range(3)), alpha))
        cropped = s.SDL_CreateRGBSurfaceWithFormat(0, bw, bh, 32, s.SDL_PIXELFORMAT_RGBA32)
        if not cropped: raise OSError('Crop allocation failed')
        set_pixels(cropped, crop)
        target = s.SDL_CreateRGBSurfaceWithFormat(0, 256, 256, 32, s.SDL_PIXELFORMAT_RGBA32)
        renderer = s.SDL_CreateSoftwareRenderer(target) if target else None
        texture = s.SDL_CreateTextureFromSurface(renderer, cropped) if renderer else None
        if not texture: raise OSError('Resize allocation failed')
        scale = 220/max(bw, bh); dw, dh = round(bw*scale), round(bh*scale)
        if s.SDL_SetTextureBlendMode(texture, s.SDL_BLENDMODE_NONE):
            raise OSError('Texture blend mode failed')
        s.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
        if s.SDL_RenderClear(renderer): raise OSError('Target clear failed')
        dst = s.SDL_Rect((256-dw)//2, (256-dh)//2, dw, dh)
        if s.SDL_RenderCopy(renderer, texture, None, ctypes.byref(dst)): raise OSError('Resize failed')
        s.SDL_RenderPresent(renderer)
        straight = bytearray(pixels(target))
        for i in range(0, len(straight), 4):
            alpha = straight[i+3]
            for c in range(3):
                straight[i+c] = min(255, (straight[i+c]*255+alpha//2)//alpha) if alpha else 0
        set_pixels(target, straight)
        after = metrics(target)
        with tempfile.TemporaryDirectory(prefix='checkmate_ice_') as temporary:
            png = Path(temporary)/'unit.png'
            if IMG_SavePNG(target, str(png).encode('utf-8')): raise OSError('PNG save failed')
            encoded = png.read_bytes()
        return encoded, before, after, [dw, dh]
    finally:
        if texture: s.SDL_DestroyTexture(texture)
        if renderer: s.SDL_DestroyRenderer(renderer)
        for surface in (target, cropped, rgba, original):
            if surface: s.SDL_FreeSurface(surface)


def prepare(folder):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init, IMG_Quit, IMG_INIT_PNG
    folder = Path(folder)
    originals = {k: (folder/'source'/(k+'.png')).read_bytes() for k in KINDS}
    pending = {}; rows = []
    if s.SDL_Init(0): raise OSError('SDL initialization failed')
    old_hint = s.SDL_GetHint(s.SDL_HINT_RENDER_SCALE_QUALITY)
    try:
        if not IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG: raise OSError('PNG initialization failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY, b'1')
        for kind in KINDS:
            encoded, source, out, dimensions = normalized(folder/'source'/(kind+'.png'))
            pending[kind+'.png'] = encoded
            rows.append(dict(name=kind, source='source/'+kind+'.png', file=kind+'.png',
                             source_size=source['size'], source_alpha_bbox=source['alpha_bbox'],
                             source_alpha_nonzero_bbox=source['alpha_nonzero_bbox'],
                             source_transparent_pixels=source['transparent_pixels'],
                             source_safety_margin_fraction=source['safety_margin_fraction'],
                             source_bytes=len(originals[kind]), source_sha256=hashlib.sha256(originals[kind]).hexdigest(),
                             **out, normalized_dimensions=dimensions, rgba_bytes=256*256*4,
                             file_bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest(),
                             foot_anchor=[128, out['alpha_bbox'][3]], anchor_note='alpha-bottom candidate; inspect actual soles',
                             hp_offset_candidate=8 if kind == 'pawn' else 10))
        record = dict(status='D1 static art candidates; visual approval pending; no live renderer',
                      generator='OpenAI built-in image_gen; exact model not exposed',
                      operation='alpha>5 bbox; uniform max220px SDL linear premultiplied resize; straight RGBA256 padding',
                      alpha_bbox_threshold=5, assets=rows)
        pending['asset_manifest.json'] = (json.dumps(record, indent=2)+'\n').encode('utf-8')
        for name, data in pending.items():
            path = folder/name
            if path.exists() and path.read_bytes() != data:
                raise ValueError('Preserve existing output; contents differ: '+name)
        if any((folder/'source'/(k+'.png')).read_bytes() != data for k, data in originals.items()):
            raise ValueError('A source changed during preparation')
        created = []
        try:
            for name, data in pending.items():
                path = folder/name
                if not path.exists():
                    # Register before writing so an interrupted write can be removed.
                    stream = path.open('xb'); created.append(path)
                    with stream: stream.write(data)
        except BaseException:
            for path in created:
                path.unlink(missing_ok=True)  # Only this invocation's new partial outputs.
            raise
        return record
    finally:
        if old_hint is None: s.SDL_ResetHint(s.SDL_HINT_RENDER_SCALE_QUALITY)
        else: s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY, old_hint)
        IMG_Quit(); s.SDL_Quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=ROOT/'assets/chapter3_units')
    print(json.dumps(prepare(parser.parse_args().folder), indent=2))
