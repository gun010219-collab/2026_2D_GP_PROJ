"""Standalone character concept/84px review. Never imported by the live game.

1 silhouette study, 2 royal cast, 3 five Kings, 4 scale/adjacency,
5..9 authentic Stage5 snapshots, B original/art, ESC exit.
"""
import argparse
import ctypes
import gc
import hashlib
import json
from pathlib import Path
import sys
from time import sleep
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.stage5_art_preview import (SampleRenderer, make_scene, snapshot,
    open_preview, capture_png)
from health_renderer import HealthRenderer
from config import cell_center

ASSETS=ROOT/'assets/character_concepts'
KINDS=('pawn','rook','knight','bishop','queen','king')
NAMES=tuple('ch1_'+k for k in KINDS)+('player',)+tuple('ch'+str(i)+'_king' for i in range(2,6))
SIZES=dict(pawn=60,rook=72,knight=72,bishop=72,queen=74,king=78,player=72)


def prepare(directory):
    """Only technical alpha crop/pad/resize; source originals remain untouched."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_Load,IMG_SavePNG,IMG_INIT_PNG
    from tools.prepare_stage5_art import alpha_bounds
    if s.SDL_Init(s.SDL_INIT_VIDEO)!=0:raise RuntimeError('SDL initialization failed')
    records=[]
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG:raise RuntimeError('PNG initialization failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        for name in NAMES:
            src=directory/'source'/(name+'.png')
            loaded=IMG_Load(str(src).encode('utf-8'))
            if not loaded:raise RuntimeError('Missing source: '+str(src))
            rgba=s.SDL_ConvertSurfaceFormat(loaded,s.SDL_PIXELFORMAT_RGBA32,0)
            s.SDL_FreeSurface(loaded)
            if not rgba:raise RuntimeError('RGBA conversion failed')
            target=renderer=texture=None
            try:
                bounds,transparent=alpha_bounds(rgba)
                if not transparent:raise ValueError('Expected true transparency: '+name)
                target=s.SDL_CreateRGBSurfaceWithFormat(0,256,256,32,s.SDL_PIXELFORMAT_RGBA32)
                if not target:raise RuntimeError('Surface allocation failed')
                renderer=s.SDL_CreateSoftwareRenderer(target)
                if not renderer:raise RuntimeError('Renderer allocation failed')
                texture=s.SDL_CreateTextureFromSurface(renderer,rgba)
                if not texture:raise RuntimeError('Texture allocation failed')
                x,y,r,b=bounds;scale=220/max(r-x,b-y)
                w,h=round((r-x)*scale),round((b-y)*scale)
                crop=s.SDL_Rect(x,y,r-x,b-y);dest=s.SDL_Rect((256-w)//2,(256-h)//2,w,h)
                s.SDL_SetTextureBlendMode(texture,s.SDL_BLENDMODE_NONE)
                s.SDL_SetRenderDrawColor(renderer,0,0,0,0);s.SDL_RenderClear(renderer)
                if s.SDL_RenderCopy(renderer,texture,ctypes.byref(crop),ctypes.byref(dest))!=0:raise RuntimeError('Resize failed')
                s.SDL_RenderPresent(renderer)
                out=directory/(name+'.png')
                if IMG_SavePNG(target,str(out).encode('utf-8'))!=0:raise RuntimeError('PNG save failed')
                box,clear=alpha_bounds(target)
                records.append(dict(name=name,size=[256,256],alpha_bbox=box,transparent_pixels=clear,
                    source_size=[rgba.contents.w,rgba.contents.h],source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                    sha256=hashlib.sha256(out.read_bytes()).hexdigest(),rgba_bytes=256*256*4))
            finally:
                if texture:s.SDL_DestroyTexture(texture)
                if renderer:s.SDL_DestroyRenderer(renderer)
                if target:s.SDL_FreeSurface(target)
                s.SDL_FreeSurface(rgba)
    finally:IMG_Quit();s.SDL_Quit()
    (directory/'asset_manifest.json').write_text(json.dumps(dict(status='Concepts pending design/camera approval',assets=records),indent=2)+'\n')


class ConceptStage5(SampleRenderer):
    def sprite(self,kind,cell):
        x,y=cell_center(*cell)
        self.resources.images[kind].draw(x,y-5,SIZES[kind],SIZES[kind])

    def draw(self,scene,*,art=False):
        super().draw(scene,art=art)
        # This gallery has a different page map from the preserved Stage5 tool.
        self.canvas.draw_rectangle(25,290,275,390,11,17,26,filled=True)
        for label,y in (('1 TO 9 PAGES',367),('B COMPARE',345),('ESC EXIT',323),('NOT LIVE GAMEPLAY',301)):
            HealthRenderer._text(self.canvas,label,30,y,scale=2)


def draw_gallery(c,images,page):
    text=HealthRenderer._text
    c.draw_rectangle(0,0,1439,899,11,17,26,filled=True)
    labels=('ROYAL SILHOUETTES','ROYAL CHARACTER CONCEPTS','FIVE CHAPTER KINGS','84PX SCALE AND NEIGHBORS')
    text(c,labels[page],35,850,scale=4)
    text(c,'CONCEPT REVIEW  CAMERA NOT FINAL  1 TO 9 PAGES  B COMPARE  ESC EXIT',35,810,scale=2)
    names=tuple('ch'+str(i)+'_king' for i in range(1,6)) if page==2 else tuple('ch1_'+k for k in KINDS)
    if page==3:names=('player',)+tuple('ch1_'+k for k in KINDS)
    step=1380/len(names)
    for i,name in enumerate(names):
        x=35+step*(i+.5);pic=images[name];kind=name.split('_')[-1]
        text(c,name.upper().replace('_',' '),x-65,760,scale=2)
        if page!=3:
            if page==0:c.SDL_SetTextureColorMod(pic.texture,0,0,0)
            c.draw_rectangle(x-step/2+8,430,x+step/2-8,735,146,149,150,filled=True) if page==0 else None
            try:pic.draw(x,580,min(step-10,260),min(step-10,260))
            finally:c.SDL_SetTextureColorMod(pic.texture,255,255,255)
        for y,tile in ((345,'tile_light'),(225,'tile_dark')):
            images[tile].draw(x,y,84,84)
            pic.draw(x,y-5,SIZES[kind],SIZES[kind])
            c.draw_rectangle(x-42,y-42,x+41,y+41,160,126,71)
        if page==3:
            # Adjacent 84px cells and a cell-exact warning pattern: layout study,
            # not an enemy event or invented combat outcome.
            x=426+i*84;y=550
            images['tile_dark' if i%2 else 'tile_light'].draw(x,y,84,84)
            pic.draw(x,y-5,SIZES[kind],SIZES[kind])
            c.draw_rectangle(x-40,y-40,x+40,y+40,229,85,103)
            c.draw_line(x-32,y-31,x-24,y-23,229,85,103)
    if page==3:text(c,'LAYOUT STUDY ONLY  REAL HP AND ATTACK EVENTS ON PAGES 5 TO 9',35,680,scale=2)
    text(c,'TOP: CONCEPT   BELOW: REAL 84PX LIGHT AND DARK CELLS',35,105,scale=2)


def run(args):
    from pico2d import pico2d as c
    images={};renderer=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.renderer or not c.window:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice()
        c.SDL_SetWindowTitle(c.window,b'CHECKMATE CHARACTER CONCEPT REVIEW - NOT LIVE GAMEPLAY')
        paths={n:args.assets/(n+'.png') for n in NAMES}
        paths.update({n:ROOT/'assets/art_samples/stage5_r2'/(n+'.png') for n in ('tile_light','tile_dark','background')})
        for n,path in paths.items():
            if not path.is_file():raise FileNotFoundError(path)
        for n,path in paths.items():images[n]=c.load_image(str(path))
        stage_images={k:images['ch1_'+k] for k in ('pawn','rook','king')}
        stage_images.update({k:images[k] for k in ('player','tile_light','tile_dark','background')})
        renderer=ConceptStage5(c,SimpleNamespace(images=stage_images))
        scene_names=('normal','enemy_warning','parry_normal','parry_perfect','pulse')
        scenes=[make_scene(n) for n in scene_names];before=[snapshot(s) for s in scenes]
        def draw(page,art=True):
            if page<4:draw_gallery(c,images,page)
            else:renderer.draw(scenes[page-4],art=art)
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True)
            filenames=('ch1_silhouettes','ch1_cast','king_comparison','scale84')+scene_names
            for page,name in enumerate(filenames):
                for _ in range(3):draw(page)
                capture_png(c,out/(name+'.png'));c.update_canvas()
            assert before==[snapshot(s) for s in scenes]
            (out/'review_manifest.json').write_text(json.dumps(dict(width=1440,height=900,tile=84,
                textures_loaded=len(images),sizes=SIZES,scenes=before,files=[n+'.png' for n in filenames]),indent=2)+'\n')
            print('Captured 9 concept/84px/real Stage5 snapshots; combat unchanged')
            return
        page=0;art=True;running=True
        while running:
            for e in c.get_events():
                if e.type==c.SDL_QUIT:running=False
                elif e.type==c.SDL_KEYDOWN:
                    if e.key==c.SDLK_ESCAPE:running=False
                    elif c.SDLK_1<=e.key<=c.SDLK_9:page=e.key-c.SDLK_1
                    elif e.key==c.SDLK_b:art=not art
            draw(page,art);c.update_canvas();sleep(1/180)
        assert before==[snapshot(s) for s in scenes]
    finally:
        if renderer is not None:renderer.resources.images.clear()
        images.clear();gc.collect();c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,default=ASSETS)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--capture-dir',type=Path)
    options=parser.parse_args()
    if options.prepare:prepare(options.assets)
    else:run(options)
