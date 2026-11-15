"""Technical PNG crop/pad/linear resize only; no semantic art edits or new dependencies."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import sdl2 as s
from sdl2.sdlimage import IMG_Init, IMG_Quit, IMG_Load, IMG_SavePNG, IMG_INIT_PNG

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
 'player':'exec-4705a4a3-7cf7-4e67-a79a-6db5b51e8ce0.png',
 'pawn':'exec-30327780-3993-4df6-a873-d335e584322b.png',
 'rook':'exec-51cef84f-2027-4bf0-8429-332dafe91bd8.png',
 'king':'exec-76971367-714f-41d7-a20a-1888fa7b1f2d.png',
 'tile_light':'exec-08921f75-00ee-41e6-82da-f4737728093d.png',
 'tile_dark':'exec-874aaec4-114b-439a-ac1c-886dcf4bf992.png',
 'background':'exec-bba9807f-15f2-4c90-aedc-22a9ee5857b5.png'
}

def alpha_bounds(surface):
    w,h=surface.contents.w,surface.contents.h
    buf=ctypes.string_at(surface.contents.pixels,surface.contents.pitch*h)
    xs=[];ys=[];transparent=0
    for y in range(h):
        row=buf[y*surface.contents.pitch:y*surface.contents.pitch+w*4]
        opaque=[x for x in range(w) if row[x*4+3]>5]
        transparent+=sum(row[x*4+3]==0 for x in range(w))
        if opaque:xs.extend((opaque[0],opaque[-1]));ys.append(y)
    if not xs:raise ValueError('Empty image')
    return (min(xs),min(ys),max(xs)+1,max(ys)+1),transparent

def prepare(source, output):
    output.mkdir(parents=True,exist_ok=True)
    source_dir=output/'source';source_dir.mkdir(exist_ok=True)
    manifest=[]
    if s.SDL_Init(s.SDL_INIT_VIDEO)!=0:raise RuntimeError('SDL initialization failed')
    s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG:raise RuntimeError('PNG initialization failed')
        for name,filename in NAMES.items():
            original=source/filename
            if not original.exists():original=source/(name+'.png')
            copy=source_dir/(name+'.png')
            if not copy.exists():shutil.copy2(original,copy)
            elif copy.read_bytes()!=original.read_bytes():raise ValueError('Existing source differs: '+str(copy))
            loaded=IMG_Load(str(copy).encode('utf-8'))
            if not loaded:raise RuntimeError('PNG load failed')
            rgba=s.SDL_ConvertSurfaceFormat(loaded,s.SDL_PIXELFORMAT_RGBA32,0)
            s.SDL_FreeSurface(loaded)
            if not rgba:raise RuntimeError('RGBA conversion failed')
            try:
                bbox,clear=alpha_bounds(rgba);w,h=rgba.contents.w,rgba.contents.h
                sprite=name in ('player','pawn','rook','king')
                if sprite and not clear:raise ValueError('Sprite has no true transparency')
                width,height=(1440,900) if name=='background' else (256,256)
                target=renderer=tex=None
                try:
                    target=s.SDL_CreateRGBSurfaceWithFormat(0,width,height,32,s.SDL_PIXELFORMAT_RGBA32)
                    if not target:raise RuntimeError('SDL resize surface failure')
                    renderer=s.SDL_CreateSoftwareRenderer(target)
                    if not renderer:raise RuntimeError('SDL resize renderer failure')
                    tex=s.SDL_CreateTextureFromSurface(renderer,rgba)
                    if not tex:raise RuntimeError('SDL resize texture failure')
                    s.SDL_SetTextureBlendMode(tex,s.SDL_BLENDMODE_NONE)
                    s.SDL_SetRenderDrawColor(renderer,0,0,0,0);s.SDL_RenderClear(renderer)
                    if sprite:
                        x,y,r,b=bbox;bw,bh=r-x,b-y;scale=220/max(bw,bh)
                        dw,dh=round(bw*scale),round(bh*scale)
                        src=s.SDL_Rect(x,y,bw,bh);dst=s.SDL_Rect((width-dw)//2,(height-dh)//2,dw,dh)
                    else:src=s.SDL_Rect(0,0,w,h);dst=s.SDL_Rect(0,0,width,height)
                    if s.SDL_RenderCopy(renderer,tex,ctypes.byref(src),ctypes.byref(dst))!=0:raise RuntimeError('Resize failed')
                    s.SDL_RenderPresent(renderer)
                    path=output/(name+'.png')
                    if IMG_SavePNG(target,str(path).encode('utf-8'))!=0:raise RuntimeError('Save failed')
                    out_bounds,out_clear=alpha_bounds(target)
                    manifest.append(dict(name=name,source='source/'+name+'.png',source_size=[w,h],
                        source_alpha_bbox=bbox,source_transparent_pixels=clear,
                        file=name+'.png',size=[width,height],alpha_bbox=out_bounds,
                        transparent_pixels=out_clear,rgba_bytes=width*height*4,file_bytes=path.stat().st_size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        source_sha256=hashlib.sha256(copy.read_bytes()).hexdigest()))
                finally:
                    if tex:s.SDL_DestroyTexture(tex)
                    if renderer:s.SDL_DestroyRenderer(renderer)
                    if target:s.SDL_FreeSurface(target)
            finally:s.SDL_FreeSurface(rgba)
    finally:IMG_Quit();s.SDL_Quit()
    (output/'asset_manifest.json').write_text(json.dumps(dict(
        status='AI design approval drafts; not final production art',
        operation='SDL linear crop/pad/resize; alpha preserved; no content repainting',
        assets=manifest),indent=2)+'\n',encoding='utf-8')
    print('Prepared7 PNG samples; RGBA allocation',sum(x['rgba_bytes'] for x in manifest),'bytes')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'assets/art_samples/stage5')
    args=parser.parse_args();prepare(args.source,args.output)
