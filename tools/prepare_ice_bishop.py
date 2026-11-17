"""D3A only: reuse approved D1 normalization without rewriting old Ice assets."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.prepare_chapter3_units import normalized


def prepare(folder=ROOT/'assets/chapter3_units'):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init, IMG_Quit, IMG_INIT_PNG
    folder = Path(folder); source = folder/'source/bishop.png'; original = source.read_bytes()
    if s.SDL_Init(0): raise OSError('SDL initialization failed')
    old_hint = s.SDL_GetHint(s.SDL_HINT_RENDER_SCALE_QUALITY)
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG: raise OSError('PNG initialization failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        encoded,before,after,dimensions = normalized(source)
        row = dict(name='bishop',source='source/bishop.png',file='bishop.png',
                   source_size=before['size'],source_alpha_bbox=before['alpha_bbox'],
                   source_alpha_nonzero_bbox=before['alpha_nonzero_bbox'],
                   source_transparent_pixels=before['transparent_pixels'],
                   source_safety_margin_fraction=before['safety_margin_fraction'],
                   source_bytes=len(original),source_sha256=hashlib.sha256(original).hexdigest(),
                   **after,normalized_dimensions=dimensions,rgba_bytes=256*256*4,
                   file_bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest(),
                   foot_anchor=[128,after['alpha_bbox'][3]],
                   anchor_note='alpha-bottom static candidate; inspect boot soles; not live Stage12',
                   target_front_visible_height=84,hp_offset_candidate=10)
        manifest = dict(task='Task 5-D3A',status='Static Ice Bishop candidate; user design approval pending; no live Stage12 renderer',
                        generator='OpenAI built-in image_gen; exact model not exposed',
                        normalization='Unchanged tools.prepare_chapter3_units.normalized: alpha>5 bbox, uniform max220px SDL linear premultiplied resize, straight RGBA256 padding',
                        alpha_bbox_threshold=5,assets=[row])
        outputs={'bishop.png':encoded,'bishop_manifest.json':(json.dumps(manifest,indent=2)+'\n').encode()}
        for name,data in outputs.items():
            p=folder/name
            if p.exists() and p.read_bytes()!=data: raise ValueError('Preserve conflicting output: '+name)
        if source.read_bytes()!=original: raise ValueError('Source changed during preparation')
        created=[]
        try:
            for name,data in outputs.items():
                p=folder/name
                if not p.exists():
                    stream=p.open('xb');created.append(p)
                    with stream:stream.write(data)
        except BaseException:
            for p in created:p.unlink(missing_ok=True)
            raise
        return manifest
    finally:
        if old_hint is None:s.SDL_ResetHint(s.SDL_HINT_RENDER_SCALE_QUALITY)
        else:s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,old_hint)
        IMG_Quit();s.SDL_Quit()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',type=Path,default=ROOT/'assets/chapter3_units')
    print(json.dumps(prepare(parser.parse_args().folder),indent=2))
