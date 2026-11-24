"""Prepare Chapter 4/5 artwork with the existing 220px alpha normalization."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.prepare_chapter3_units import metrics, normalized

DIRECTORY = ROOT / 'assets/late_chapter_units'
TARGETS = {
    'pawn': ['spear', 'shield'],
    'rook': ['shoulder armor', 'shield'],
    'knight': ['head', 'mane', 'hooves'],
    'bishop': ['staff', 'robes'],
    'queen': ['scepter', 'mantle'],
    'king': ['fists', 'shoulder armor', 'core'],
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inspect_png(path):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load

    image = IMG_Load(str(path).encode('utf-8'))
    if not image:
        raise OSError(f'Cannot read PNG {path}')
    rgba = s.SDL_ConvertSurfaceFormat(image, s.SDL_PIXELFORMAT_RGBA32, 0)
    try:
        if not rgba:
            raise OSError(f'Cannot measure PNG {path}')
        return metrics(rgba)
    finally:
        if rgba:
            s.SDL_FreeSurface(rgba)
        s.SDL_FreeSurface(image)


def prepare():
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init, IMG_INIT_PNG, IMG_Quit

    if s.SDL_Init(0):
        raise OSError('Cannot initialize SDL')
    rows = []
    prompts = json.loads((DIRECTORY / 'prompts.json').read_bytes())
    try:
        IMG_Init(IMG_INIT_PNG)
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY, b'1')
        for chapter in (4, 5):
            for kind, moving in TARGETS.items():
                name = f'ch{chapter}_{kind}.png'
                if kind == 'king':
                    out = ROOT / 'assets/character_concepts' / name
                    source = out.parent / 'source' / name
                    before, after = inspect_png(source), inspect_png(out)
                    encoded = out.read_bytes()
                    origin = 'B1C existing original and prepared PNG'
                else:
                    source = DIRECTORY / 'source' / name
                    out = DIRECTORY / name
                    # Keep tight source framing as provenance. The runtime sprite gets
                    # its own transparent padding from the shared normalization.
                    encoded, before, after, _ = normalized(source, minimum_source_margin=0)
                    if out.exists() and out.read_bytes() != encoded:
                        raise ValueError(f'Prepared output already exists with different bytes: {out}')
                    if not out.exists():
                        out.write_bytes(encoded)
                    origin = 'Built-in image_gen / R2'
                box = after['alpha_bbox']
                rows.append(dict(chapter=chapter, kind=kind, origin=origin,
                                 source=source.relative_to(ROOT).as_posix(), source_sha256=sha(source.read_bytes()),
                                 input=before, file=out.relative_to(ROOT).as_posix(), sha256=sha(encoded),
                                 prepared=after, feet=[128, box[3]], moving_parts=moving,
                                 generation=prompts.get(name.removesuffix('.png'))))
                print(chapter, kind, box, flush=True)
    finally:
        IMG_Quit()
        s.SDL_Quit()
    (DIRECTORY / 'manifest.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    prepare()
