
"""Normalize the R7-A3E-2B ImageGen sheets and build cropped runtime atlas pages."""
import argparse
from ctypes import memmove, string_at
from hashlib import sha256
import json
from math import ceil, floor
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

import sdl2 as s
from sdl2.sdlimage import IMG_Load, IMG_SavePNG

from build_sprite_atlas import build, SpriteCatalog

SIZE = 384
FOOT = (192, 302)
PIXEL_BODY_HEIGHT = 195
ATTACK_MS = (66, 67, 83, 84)
PARRY_MS = {
    'parry_ready': (33, 33, 34, 50, 66, 84),
    'parry_normal': (33, 34, 36, 47, 53, 57),
    'parry_perfect': (33, 44, 55, 61, 68, 79),
    'parry_failed': (25, 33, 40, 42, 50, 60),
}
GROUPS = {'attacks': ('left', 'up', 'down'), 'parries': tuple(PARRY_MS)}


def read(path):
    loaded = IMG_Load(str(path).encode('utf-8'))
    if not loaded:
        raise OSError(f'Cannot decode {path}: {s.SDL_GetError()}')
    try:
        surface = s.SDL_ConvertSurfaceFormat(loaded,s.SDL_PIXELFORMAT_RGBA32,0)
        if not surface:
            raise OSError(s.SDL_GetError())
        try:
            image = surface.contents
            data = string_at(image.pixels,image.pitch*image.h)
            return tuple(data[y*image.pitch:y*image.pitch+image.w*4] for y in range(image.h))
        finally:
            s.SDL_FreeSurface(surface)
    finally:
        s.SDL_FreeSurface(loaded)


def write(path, rows):
    width,height = len(rows[0])//4,len(rows)
    surface = s.SDL_CreateRGBSurfaceWithFormat(0,width,height,32,s.SDL_PIXELFORMAT_RGBA32)
    if not surface:
        raise OSError(s.SDL_GetError())
    try:
        image = surface.contents
        for y,row in enumerate(rows):
            memmove(image.pixels+y*image.pitch,row,len(row))
        if IMG_SavePNG(surface,str(path).encode('utf-8')):
            raise OSError(s.SDL_GetError())
    finally:
        s.SDL_FreeSurface(surface)


def bounds(rows, threshold):
    hits = [(y, opaque) for y,row in enumerate(rows)
            if (opaque := [x for x,a in enumerate(row[3::4]) if a>=threshold])]
    if not hits:
        raise ValueError('No visible pixels in pose')
    return min(xs[0] for _,xs in hits), hits[0][0], max(xs[-1] for _,xs in hits)+1, hits[-1][0]+1


def crop(rows, rect):
    x0,y0,x1,y1 = rect
    return tuple(row[x0*4:x1*4] for row in rows[y0:y1])


def normalize(rows, scale, foot_override=None):
    # Generated mattes can contain very faint speckles outside the sprite.
    cutoff = 12
    x0,y0,x1,y1 = box = bounds(rows,cutoff)
    if x0==0 or y0==0 or x1==len(rows[0])//4 or y1==len(rows):
        raise ValueError(f'Pose touches the source cell border: {box}')
    sole_band = rows[max(y0,y1-34):y1]
    ground_left,_,ground_right,_ = bounds(sole_band,96)
    px,py = foot_override or ((ground_left+ground_right)/2,y1-2)
    left,top = (FOOT[0]+(x0-px)*scale,FOOT[1]+(y0-py)*scale)
    right,bottom = (FOOT[0]+(x1-px)*scale,FOOT[1]+(y1-py)*scale)
    if min(left,top)<3 or max(right,bottom)>SIZE-3:
        raise ValueError(f'Pose does not fit {SIZE}: {left:.1f},{top:.1f},{right:.1f},{bottom:.1f}')
    canvas = [bytearray(SIZE*4) for _ in range(SIZE)]
    x_weights = {}
    for x in range(floor(left),ceil(right)):
        sx = (x+.5-FOOT[0])/scale + px-.5
        j = floor(sx)
        x_weights[x] = ((j,1-(sx-j)),(j+1,sx-j))
    for y in range(floor(top),ceil(bottom)):
        sy = (y+.5-FOOT[1])/scale + py-.5
        i = floor(sy)
        y_weights = ((i,1-(sy-i)),(i+1,sy-i))
        for x,weight in x_weights.items():
            alpha = red = green = blue = 0.
            for iy,wy in y_weights:
                if not 0<=iy<len(rows):
                    continue
                row = rows[iy]
                for ix,wx in weight:
                    if not 0<=ix<len(row)//4:
                        continue
                    r,g,b,a = row[ix*4:ix*4+4]
                    if a >= cutoff:
                        opacity = a*wx*wy
                        alpha += opacity
                        red += r*opacity
                        green += g*opacity
                        blue += b*opacity
            if round(alpha):
                canvas[y][x*4:x*4+4] = bytes((round(red/alpha),round(green/alpha),
                                             round(blue/alpha),round(alpha)))
    return tuple(bytes(row) for row in canvas), (px,py), box


def extract(combat, output):
    recipe = json.loads((combat/'recipes.json').read_text(encoding='utf-8'))
    frames = []
    output.mkdir(parents=True)
    for name,entry in recipe.items():
        source = combat/'sheets'/f'{name}.png'
        source_hash = sha256(source.read_bytes()).hexdigest()
        if source_hash != entry['sha256']:
            raise ValueError(f'Source hash mismatch: {source}')
        rows = read(source)
        width,height = len(rows[0])//4,len(rows)
        destination = output/name
        destination.mkdir()
        cols = entry['columns']
        cells = entry.get('cells', [
            (round(i*width/cols),round(j*height/2),round((i+1)*width/cols),round((j+1)*height/2))
            for j in range(2) for i in range(cols)
        ])
        if len(cells)!=2*cols:
            raise ValueError(f'Incorrect cell count for {name}')
        feet = entry.get('feet',{})
        scale = PIXEL_BODY_HEIGHT/entry['body_pixels']
        for index,cell in enumerate(cells,1):
            path = destination/f'{index:02}.png'
            try:
                pixels,foot,box = normalize(crop(rows,cell),scale,feet.get(str(index)))
            except ValueError as exc:
                raise ValueError(f'{name} pose {index}: {exc}') from exc
            write(path,pixels)
            frames.append(dict(frame=path.relative_to(output).as_posix(),cell=cell,source_foot=foot,
                               source_bbox=box,scale=scale,foot=FOOT,alpha_bbox=bounds(pixels,1),
                               sha256=sha256(path.read_bytes()).hexdigest()))
    (output/'frames.json').write_text(json.dumps(frames,indent=2)+'\n',encoding='utf-8')


def pack(sprite_root, output):
    """Retain the 2A page byte-for-byte; add separately packed attack and guard pages."""
    combat = sprite_root/'player'/'combat'
    old = json.loads((sprite_root/'manifest_right_only.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True)
    copyfile(sprite_root/'atlas.png',output/'atlas.png')
    with TemporaryDirectory(prefix='checkmate-cropped-sprites-') as directory:
        temp = Path(directory)
        for category,names in GROUPS.items():
            clips = []
            for name in names:
                attack = name not in PARRY_MS
                first = 5 if attack else 1
                durations = ATTACK_MS if attack else PARRY_MS[name]
                frames = []
                for index,time in enumerate(durations,first):
                    rows = read(combat/'frames'/name/f'{index:02}.png')
                    left,top,right,bottom = bounds(rows,1)
                    # Add an empty pixel and include the anchor even when transparent.
                    rect = (min(left,FOOT[0])-1,min(top,FOOT[1])-1,
                            max(right,FOOT[0]+1)+1,max(bottom,FOOT[1]+1)+1)
                    cropped = temp/f'{name}_{index:02}.png'
                    write(cropped,crop(rows,rect))
                    frames.append(dict(file=cropped.name,foot=[FOOT[0]-rect[0],FOOT[1]-rect[1]],ms=time))
                clips.append(dict(design='player',action='attack' if attack else name,
                                  facing=name if attack else 'neutral',reference_height=256,
                                  impact=0,frames=frames))
            spec = temp/f'{category}.json'
            spec.write_text(json.dumps(dict(purpose='production',columns=4 if category=='attacks' else 6,
                                            clips=clips)),encoding='utf-8')
            result = build(spec,temp/category)
            page = json.loads(result.read_text(encoding='utf-8'))
            filename = f'player_{category}.png'
            copyfile(result.parent/'atlas.png',output/filename)
            old['atlases'][category] = dict(page['atlases']['actors'],file=filename)
            old['clips'].extend(dict(clip,atlas=category) for clip in page['clips'])
    path = output/'manifest.json'
    path.write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
    SpriteCatalog.read(path)
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('extract','pack'))
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    operation = extract if args.command=='extract' else pack
    operation(args.source,args.output)
