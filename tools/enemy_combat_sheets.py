
"""Normalize referenced enemy sprite sheets and build one atlas page per design."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile
from statistics import median
from tempfile import TemporaryDirectory

from build_sprite_atlas import ROOT, SpriteCatalog, build
from player_combat_sheets import FOOT, bounds, crop, normalize, read, write

TIMINGS = {
    'pawn': (75, 125, 106, 204),
    'rook': (65, 135, 100, 320),
    'knight': (65, 135, 100, 310),
}
SCOPE = tuple(f'ch{chapter}_{kind}' for chapter in range(1,6) for kind in TIMINGS)


def regular_cells(width, height):
    return [(round(col*width/4),round(row*height/3),round((col+1)*width/4),round((row+1)*height/3))
            for row in range(3) for col in range(4)]


def trim(pixels):
    left,top,right,bottom = bounds(pixels,1)
    x,y = min(left,FOOT[0])-1,min(top,FOOT[1])-1
    rect=(x,y,max(right,FOOT[0]+1)+1,max(bottom,FOOT[1]+1)+1)
    return crop(pixels,rect), [FOOT[0]-x,FOOT[1]-y]


def save_json(path, data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def prepare(sprite_root, output):
    enemy_root = sprite_root/'enemies'
    recipes=json.loads((enemy_root/'recipes.json').read_text(encoding='utf-8'))
    if set(recipes)!=set(SCOPE):
        raise ValueError('Expected exactly the 15 R7-A3E-4 designs')
    manifest=json.loads((sprite_root/'manifest_player_only.json').read_text(encoding='utf-8'))
    evidence={}
    output.mkdir(parents=True)
    pages=output/'enemies'
    pages.mkdir()
    with TemporaryDirectory(prefix='checkmate-enemy-atlas-') as temp_name:
        temp=Path(temp_name)
        for name in SCOPE:
            item=recipes[name]
            kind=name.split('_')[1]
            chapter=int(name[2])
            source=enemy_root/'sheets'/f'{name}.png'
            reference=ROOT/item['reference']
            for path,key in ((source,'source_sha256'),(reference,'reference_sha256')):
                if sha256(path.read_bytes()).hexdigest()!=item[key]:
                    raise ValueError(f'Sprite source hash mismatch: {path}')
            sheet=read(source)
            cells=item.get('cells',regular_cells(len(sheet[0])//4,len(sheet)))
            directions=item['directions']
            if (len(cells)!=12 or len(directions)!=3 or any(s not in ('left','right','up','down') for s in directions)
                    or len(set(directions))!=3 or not set(directions) & {'right','left'}):
                raise ValueError(f'Invalid 4×3 sheet recipe: {name}')
            poses=[crop(sheet,rectangle) for rectangle in cells]
            ref_bounds=bounds(read(reference),96)
            ref_height=ref_bounds[3]-ref_bounds[1]
            guards=[bounds(poses[i],96) for i in (0,4,8)]
            source_height=median(guard[3]-guard[1] for guard in guards)
            scale=float(item.get('scale',ref_height/source_height))
            author=pages/'frames'/name
            author.mkdir(parents=True)
            clips=[]
            record=evidence[name]=dict(scale=scale,reference_alpha_height=ref_height,frames=[])
            for row,facing in enumerate(directions):
                frames=[]
                for column,duration in enumerate(TIMINGS[kind]):
                    i=row*4+column
                    try:
                        pixels,foot,source_box=normalize(poses[i],scale,item.get('feet',{}).get(str(i+1)))
                    except ValueError as exc:
                        raise ValueError(f'{name}, row {row+1} pose {column+1}: {exc}') from exc
                    file=author/f'{facing}_{column+1}.png'
                    write(file,pixels)
                    record['frames'].append(dict(file=file.relative_to(pages).as_posix(),
                        sha256=sha256(file.read_bytes()).hexdigest(), source_cell=cells[i],
                        source_alpha=source_box, source_foot=foot, anchor=FOOT, alpha=bounds(pixels,1)))
                    cropped,crop_foot=trim(pixels)
                    runtime=temp/f'{name}_{facing}_{column+1}.png'
                    write(runtime,cropped)
                    frames.append(dict(file=runtime.name,foot=crop_foot,ms=duration))
                clip=dict(chapter=chapter,design=kind,action='attack',facing=facing,reference_height=256,
                          impact=2,attack_kind='pawn_contact' if kind=='pawn' else 'basic',frames=frames)
                if kind in ('rook','knight'):
                    clip['contact']=3
                clips.append(clip)
                if facing in ('left','right'):
                    clips.append(dict(clip, facing='left' if facing=='right' else 'right',flip_x=True))
            spec=temp/f'{name}.json'
            save_json(spec,dict(purpose='production',columns=4,clips=clips))
            packed=build(spec,temp/name)
            page=json.loads(packed.read_text(encoding='utf-8'))
            out_file=pages/f'{name}.png'
            copyfile(packed.parent/'atlas.png',out_file)
            manifest['atlases'][name]=dict(page['atlases']['actors'],file=f'enemies/{name}.png')
            manifest['clips'].extend(dict(clip,atlas=name) for clip in page['clips'])
            record['atlas_bytes']=out_file.stat().st_size
            record['atlas_sha256']=sha256(out_file.read_bytes()).hexdigest()
    manifest_file=output/'manifest.json'
    save_json(manifest_file,manifest)
    SpriteCatalog.read(manifest_file)
    counts=Counter(clip['design'] for clip in manifest['clips'])
    assert counts=={'player':8,'pawn':20,'rook':20,'knight':20},counts
    save_json(pages/'frames.json',evidence)
    return manifest_file


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    print(prepare(args.source,args.output))
