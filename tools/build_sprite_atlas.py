
"""Pack individual RGBA PNGs into a padded sprite atlas and validated runtime manifest."""
import argparse
from contextlib import ExitStack
import ctypes
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sprite_animation import SpriteCatalog, integers

PADDING = 2
PNG_HEADER = b'\x89PNG\r\n\x1a\n'


def rgba_size(path):
    with path.open('rb') as stream:
        header = stream.read(26)
    if len(header) != 26 or header[:8] != PNG_HEADER or header[12:16] != b'IHDR' or header[24:26] != b'\x08\x06':
        raise ValueError(f'Expected an 8-bit RGBA PNG: {path}')
    return struct.unpack('>II', header[16:24])


def visible_top(surface, path):
    data = surface.contents
    if not data.pixels or data.pitch < data.w * 4:
        raise ValueError(f'Invalid RGBA pixel buffer: {path}')
    pixels = ctypes.string_at(data.pixels, data.pitch * data.h)
    rows = [pixels[y * data.pitch + 3:y * data.pitch + data.w * 4:4] for y in range(data.h)]
    if not any(any(row) for row in rows):
        raise ValueError(f'Transparent frame: {path}')
    if any(rows[0]) or any(rows[-1]) or any(row[0] or row[-1] for row in rows):
        raise ValueError(f'Frame has content at its border. Leave room for the weapon and cape: {path}')
    return next(y for y, row in enumerate(rows) if any(row))


def build(source, output):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load, IMG_SavePNG

    data = json.loads(source.read_text(encoding='utf-8'))
    columns = data.get('columns', 4)
    if type(columns) is not int or not 1 <= columns <= 16:
        raise ValueError('columns must be between 1 and 16')
    paths = {frame['file']: (source.parent / frame['file']).resolve()
             for clip in data['clips'] for frame in clip['frames']}
    if not paths:
        raise ValueError('No input frames')
    sizes = {path: rgba_size(path) for path in paths.values()}
    cell_w = max(size[0] for size in sizes.values()) + PADDING * 2
    cell_h = max(size[1] for size in sizes.values()) + PADDING * 2
    columns = min(len(sizes), columns)
    width, height = cell_w * columns, cell_h * ((len(sizes) + columns - 1) // columns)
    if not (1 <= width <= 4096 and 1 <= height <= 4096):
        raise ValueError('Atlas cannot exceed 4096×4096')

    with ExitStack() as stack:
        atlas = s.SDL_CreateRGBSurfaceWithFormat(0, width, height, 32, s.SDL_PIXELFORMAT_RGBA32)
        if not atlas:
            raise OSError(s.SDL_GetError())
        stack.callback(s.SDL_FreeSurface, atlas)
        if s.SDL_FillRect(atlas, None, 0):
            raise OSError(s.SDL_GetError())
        regions = {}
        for index, (path, size) in enumerate(sizes.items()):
            with ExitStack() as frame_stack:
                loaded = IMG_Load(str(path).encode('utf-8'))
                if not loaded:
                    raise OSError(f'Cannot decode {path}: {s.SDL_GetError()}')
                frame_stack.callback(s.SDL_FreeSurface, loaded)
                frame = s.SDL_ConvertSurfaceFormat(loaded, s.SDL_PIXELFORMAT_RGBA32, 0)
                if not frame:
                    raise OSError(s.SDL_GetError())
                frame_stack.callback(s.SDL_FreeSurface, frame)
                if (frame.contents.w, frame.contents.h) != size:
                    raise ValueError(f'Image dimensions do not match the PNG header: {path}')
                top = visible_top(frame, path)
                x, y = index % columns * cell_w + PADDING, index // columns * cell_h + PADDING
                region = s.SDL_Rect(x, y, *size)
                if (s.SDL_SetSurfaceBlendMode(frame, s.SDL_BLENDMODE_NONE)
                        or s.SDL_BlitSurface(frame, None, atlas, ctypes.byref(region))):
                    raise OSError(s.SDL_GetError())
                regions[path] = ([x, y, *size], top)
        clips = []
        for clip in data['clips']:
            frames = []
            for frame in clip['frames']:
                rect, top = regions[paths[frame['file']]]
                frames.append(dict(rect=rect, visible_top=top, foot=integers(frame['foot'], 2),
                                   ms=frame['ms'], offset=integers(frame.get('offset', (0, 0)), 2)))
            clips.append({**clip, 'frames': frames, 'atlas': 'actors'})
        manifest = dict(version=1, purpose=data['purpose'],
                        atlases={'actors': {'file': 'atlas.png', 'size': [width, height]}}, clips=clips)
        SpriteCatalog.parse(manifest, output, allow_test=True)
        output.mkdir(parents=True)
        if IMG_SavePNG(atlas, str(output / 'atlas.png').encode('utf-8')):
            raise OSError(s.SDL_GetError())
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return output / 'manifest.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Source clip JSON with per-frame file, foot and ms')
    parser.add_argument('output', type=Path, help='New output directory')
    args = parser.parse_args()
    print(build(args.source, args.output))
