
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

MARTIAL_TIMINGS = {
    'pawn': (75, 125, 106, 204),
    'rook': (65, 135, 100, 320),
    'knight': (65, 135, 100, 310),
}
CASTER_TIMINGS = {
    'bishop': (98, 182, 120, 400),
    'queen': (104, 176, 140, 400),
    'king_melee': (108, 172, 135, 395),
    'king_pulse': (90, 210, 185, 465),
}
GROUPS = {
    'martial': ('enemies', 'manifest_player_only.json', MARTIAL_TIMINGS),
    'caster': ('enemies_caster', 'manifest_martial.json', CASTER_TIMINGS),
}
ATTACK_KINDS = {'pawn':'pawn_contact', 'queen':'queen_diagonal', 'king_pulse':'king_pulse'}


def regular_cells(width, height, columns=4, rows=3):
    return [(round(col*width/columns),round(row*height/rows),
             round((col+1)*width/columns),round((row+1)*height/rows))
            for row in range(rows) for col in range(columns)]


def largest_pose(pixels):
    """Keep a single connected figure when a weapon crosses the printed cell grid."""
    width=len(pixels[0])//4
    height=len(pixels)
    unvisited={y*width+x for y,row in enumerate(pixels)
               for x,alpha in enumerate(row[3::4]) if alpha>=12}
    largest=[]
    while unvisited:
        first=unvisited.pop()
        component=[first]
        for current in component:
            y,x=divmod(current,width)
            for cy in range(max(0,y-1),min(height,y+2)):
                for cx in range(max(0,x-1),min(width,x+2)):
                    other=cy*width+cx
                    if other in unvisited:
                        unvisited.remove(other)
                        component.append(other)
        if len(component)>len(largest):
            largest=component
    masked=[bytearray(width*4) for _ in range(height)]
    for index in largest:
        y,x=divmod(index,width)
        start=x*4
        masked[y][start:start+4]=pixels[y][start:start+4]
    return tuple(bytes(row) for row in masked)


def trim(pixels):
    left,top,right,bottom = bounds(pixels,1)
    x,y = min(left,FOOT[0])-1,min(top,FOOT[1])-1
    rect=(x,y,max(right,FOOT[0]+1)+1,max(bottom,FOOT[1]+1)+1)
    return crop(pixels,rect), [FOOT[0]-x,FOOT[1]-y]


def save_json(path, data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def prepare(sprite_root, output, *, group='martial'):
    folder, base, timings = GROUPS[group]
    scope = tuple(f'ch{chapter}_{mode}' for chapter in range(1,6) for mode in timings)
    enemy_root = sprite_root/folder
    recipes=json.loads((enemy_root/'recipes.json').read_text(encoding='utf-8'))
    if set(recipes)!=set(scope):
        raise ValueError(f'Expected {len(scope)} {group} sprite recipes')
    manifest=json.loads((sprite_root/base).read_text(encoding='utf-8'))
    base_clip_count=len(manifest['clips'])
    evidence={}
    output.mkdir(parents=True)
    pages=output/folder
    pages.mkdir()
    with TemporaryDirectory(prefix='checkmate-enemy-atlas-') as temp_name:
        temp=Path(temp_name)
        for name in scope:
            item=recipes[name]
            mode=name.split('_',1)[1]
            kind=mode.split('_',1)[0]
            directional=group=='martial' or mode=='king_melee'
            chapter=int(name[2])
            source=enemy_root/'sheets'/f'{name}.png'
            reference=ROOT/item['reference']
            sources={source:item['source_sha256'],reference:item['reference_sha256'],
                     **{ROOT/path:digest for path,digest in item.get('supporting_references',{}).items()}}
            for path,digest in sources.items():
                if sha256(path.read_bytes()).hexdigest()!=digest:
                    raise ValueError(f'Sprite source hash mismatch: {path}')
            sheet=read(source)
            columns, rows = (4,3) if directional else (2,2)
            width, height = len(sheet[0])//4,len(sheet)
            cells=item.get('cells',regular_cells(width,height,columns,rows))
            directions=item['directions']
            expected=({'up','down','right'},{'up','down','left'}) if directional else ({'neutral'},)
            if (len(cells)!=columns*rows or len(directions)!=(3 if directional else 1)
                    or set(directions) not in expected
                    or any(not (0<=x0<x1<=width and 0<=y0<y1<=height) for x0,y0,x1,y1 in cells)):
                raise ValueError(f'Invalid sheet recipe: {name}')
            poses=[crop(sheet,rectangle) for rectangle in cells]
            for index in item.get('isolate',()):
                poses[index-1]=largest_pose(poses[index-1])
            ref_bounds=bounds(read(reference),96)
            ref_height=ref_bounds[3]-ref_bounds[1]
            guards=[bounds(poses[row*4],96) for row in range(len(directions))]
            source_height=median(guard[3]-guard[1] for guard in guards)
            scale=float(item.get('scale',ref_height/source_height))
            author=pages/'frames'/name
            author.mkdir(parents=True)
            clips=[]
            record=evidence[name]=dict(scale=scale,reference_alpha_height=ref_height,frames=[])
            for row,facing in enumerate(directions):
                frames=[]
                for column,duration in enumerate(timings[mode]):
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
                          impact=2,attack_kind=ATTACK_KINDS.get(mode,'basic'),frames=frames)
                if kind in ('rook','knight'):
                    clip['contact']=3
                clips.append(clip)
                if facing in ('left','right'):
                    clips.append(dict(clip, facing='left' if facing=='right' else 'right',flip_x=True))
            spec=temp/f'{name}.json'
            save_json(spec,dict(purpose='production',columns=columns,clips=clips))
            packed=build(spec,temp/name)
            page=json.loads(packed.read_text(encoding='utf-8'))
            out_file=pages/f'{name}.png'
            copyfile(packed.parent/'atlas.png',out_file)
            manifest['atlases'][name]=dict(page['atlases']['actors'],file=f'{folder}/{name}.png')
            manifest['clips'].extend(dict(clip,atlas=name) for clip in page['clips'])
            record['atlas_bytes']=out_file.stat().st_size
            record['atlas_sha256']=sha256(out_file.read_bytes()).hexdigest()
    manifest_file=output/'manifest.json'
    save_json(manifest_file,manifest)
    SpriteCatalog.read(manifest_file)
    counts=Counter(clip['design'] for clip in manifest['clips'][base_clip_count:])
    expected={'pawn':20,'rook':20,'knight':20} if group=='martial' else {'bishop':5,'queen':5,'king':25}
    if counts!=expected:
        raise ValueError(f'Wrong clip counts for {group}: {counts}')
    save_json(pages/'frames.json',evidence)
    return manifest_file


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--group', choices=GROUPS, default='martial')
    args=parser.parse_args()
    print(prepare(args.source,args.output,group=args.group))
