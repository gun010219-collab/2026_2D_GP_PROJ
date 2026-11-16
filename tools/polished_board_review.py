"""R4 natural Grand Arena, themed tops and fitted joints. Frozen review only.

1..5 theme, 6..8 A/B/C, 9 C/Mode1, Q/W/E cue strength,
A/S/D/F/H/P scene, B original R3, G grid, L Pulse phase, R input window,
T resolved Pulse, F11/SETTINGS, ESC exit. No live game renderer is replaced.
"""
import argparse
import ctypes
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from time import sleep

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.highend_board_review import HighendRenderer,resolved_pulse_scene
from tools.ornate_board_review import CAMERA,pulse_phase,parry_window_scene
from tools.themed_arena_review import THEMES,LABELS,review_text
from tools.stage5_camera_review import polygon,outline
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS,open_preview,capture_png
from board import is_light_tile
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer

ASSETS=ROOT/'assets/polished_board'
PROFILES=('A NATURAL','B THEMED TOP','C FITTED RIM')
# Source opening survey in normalized image coordinates (top-left origin).
# Only the seat adapts to this survey; the sculptural image is NEVER warped.
OPENING=((315/1586,794/992),(1274/1586,794/992),(1140/1586,166/992),(448/1586,166/992))
TONES=((138,124,98),(106,117,91),(133,161,177),(110,103,95),(109,104,119))


def uniform_fit(width,height,bounds):
    """One scale for both axes; fit opaque art in the fixed viewport."""
    l,t,r,b=bounds
    scale=min(1260/(r-l),850/(b-t),.94)
    x=735-(l+r)*scale/2
    y=min(472-(.43*height)*scale,888-b*scale)
    y=max(y,30-t*scale)
    return scale,x,y


def seat_bounds(opening,padding):
    coords=[CAMERA.inverse(x,899-y) for x,y in opening]
    return (min(-padding,min(u for u,v in coords)-.08),
            min(-padding,min(v for u,v in coords)-.08),
            max(10+padding,max(u for u,v in coords)+.08),
            max(10+padding,max(v for u,v in coords)+.08))


def seat_corners(bounds):
    l,b,r,t=bounds
    return ((l,b),(r,b),(r,t),(l,t))


def blend_corners(outer,t):
    inner=((0,0),(10,0),(10,10),(0,10))
    return tuple((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for a,b in zip(outer,inner))


def prepare(directory):
    """Native uniform frame fit and mechanical light/dark atlas extraction."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_Load,IMG_SavePNG,IMG_INIT_PNG
    from tools.prepare_stage5_art import alpha_bounds
    records=[]
    if s.SDL_Init(0)!=0:raise RuntimeError('SDL init failed')
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG:raise RuntimeError('PNG init failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        for theme in THEMES:
            for kind in ('frame','tiles'):
                path=directory/'source'/(theme+'_'+kind+'.png');loaded=IMG_Load(str(path).encode('utf-8'))
                if not loaded:raise FileNotFoundError(path)
                source=s.SDL_ConvertSurfaceFormat(loaded,s.SDL_PIXELFORMAT_RGBA32,0);s.SDL_FreeSurface(loaded)
                if not source:raise RuntimeError('RGBA conversion')
                try:
                    w,h=source.contents.w,source.contents.h
                    bounds,clear=alpha_bounds(source)
                    if kind=='frame' and not clear:raise ValueError('Frame must have true alpha')
                    parts=(('frame',None),) if kind=='frame' else (('light',0),('dark',1))
                    for suffix,index in parts:
                        size=(1440,900) if kind=='frame' else (128,128)
                        target=s.SDL_CreateRGBSurfaceWithFormat(0,*size,32,s.SDL_PIXELFORMAT_RGBA32)
                        if not target:raise RuntimeError('Surface failed')
                        renderer=texture=None
                        try:
                            renderer=s.SDL_CreateSoftwareRenderer(target)
                            if not renderer:raise RuntimeError('Renderer failed')
                            texture=s.SDL_CreateTextureFromSurface(renderer,source)
                            if not texture:raise RuntimeError('Texture failed')
                            s.SDL_SetTextureBlendMode(texture,s.SDL_BLENDMODE_NONE)
                            s.SDL_SetRenderDrawColor(renderer,0,0,0,0);s.SDL_RenderClear(renderer)
                            name=theme+'_'+suffix;extra={}
                            if kind=='frame':
                                scale,x,y=uniform_fit(w,h,bounds)
                                dest=s.SDL_FRect(x,y,w*scale,h*scale)
                                if s.SDL_RenderCopyF(renderer,texture,None,ctypes.byref(dest))!=0:raise RuntimeError('Frame copy failed')
                                extra=dict(uniform_scale=scale,offset=[x,y],opening=[[x+u*w*scale,y+v*h*scale] for u,v in OPENING])
                            else:
                                side=min(w//2,h);region=s.SDL_Rect(index*(w//2)+(w//2-side)//2,(h-side)//2,side,side)
                                # Bake a restrained material pass over the old
                                # light/dark tile. This preserves value contrast
                                # without adding a second per-frame tile draw.
                                base_path=ROOT/'assets/art_samples/stage5_r2'/('tile_light.png' if index==0 else 'tile_dark.png')
                                base=IMG_Load(str(base_path).encode('utf-8'))
                                if not base:raise FileNotFoundError(base_path)
                                base_tex=s.SDL_CreateTextureFromSurface(renderer,base);s.SDL_FreeSurface(base)
                                if not base_tex:raise RuntimeError('Base tile failed')
                                try:
                                    if s.SDL_RenderCopy(renderer,base_tex,None,None)!=0:raise RuntimeError('Base tile copy failed')
                                finally:s.SDL_DestroyTexture(base_tex)
                                s.SDL_SetTextureBlendMode(texture,s.SDL_BLENDMODE_BLEND)
                                s.SDL_SetTextureColorMod(texture,235,235,235);s.SDL_SetTextureAlphaMod(texture,180)
                                if s.SDL_RenderCopy(renderer,texture,ctypes.byref(region),None)!=0:raise RuntimeError('Tile copy failed')
                                extra=dict(source_rect=[region.x,region.y,region.w,region.h],material_alpha=180,material_rgb_gain=235,
                                    base_source=base_path.relative_to(ROOT).as_posix(),base_sha256=hashlib.sha256(base_path.read_bytes()).hexdigest())
                            s.SDL_RenderPresent(renderer);dest_path=directory/(name+'.png')
                            if IMG_SavePNG(target,str(dest_path).encode('utf-8'))!=0:raise RuntimeError('PNG save failed')
                            alpha,transparent=alpha_bounds(target)
                            records.append(dict(name=name,size=size,source=path.name,source_size=[w,h],alpha_bounds=alpha,
                                transparent_pixels=transparent,sha256=hashlib.sha256(dest_path.read_bytes()).hexdigest(),
                                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),**extra))
                        finally:
                            if texture:s.SDL_DestroyTexture(texture)
                            if renderer:s.SDL_DestroyRenderer(renderer)
                            s.SDL_FreeSurface(target)
                finally:s.SDL_FreeSurface(source)
    finally:IMG_Quit();s.SDL_Quit()
    (directory/'asset_manifest.json').write_text(json.dumps(dict(status='R4 polishing review pending approval',
        frame_method='One uniform scale plus translation; no homography, axis stretch or exterior compression',assets=records),indent=2)+'\n')


class PolishedRenderer(HighendRenderer):
    def __init__(self,c,assets=ASSETS):
        super().__init__(c)
        self.prior=False
        self.tile_quads=[];self.seat=None
        try:
            self.asset_records={r['name']:r for r in json.loads((assets/'asset_manifest.json').read_text())['assets']}
            for theme in THEMES:
                for suffix in ('frame','light','dark'):
                    name=theme+'_'+suffix;p=assets/(name+'.png')
                    if not p.is_file():raise FileNotFoundError(p)
                    self.images['polish_'+name]=c.load_image(str(p))
        except Exception:self.close();raise

    def board(self,cam,grid):
        self.decor_segments=[];self.cue_segments=[];self.decor_quads=[];self.tile_quads=[];self.seat=None
        if self.compare:
            variant=self.variant;self.compare=False;self.prior=True
            try:self.variant=2;super().board(cam,grid)
            finally:self.variant=variant;self.compare=True;self.prior=False
            return
        c=self.c;theme=THEMES[self.theme]
        self.images['arena_'+theme].draw(720,450,1440,900)
        self.images['polish_'+theme+'_frame'].draw(720,450,1440,900)
        bounds=seat_bounds(self.asset_records[theme+'_frame']['opening'],.20 if self.variant==2 else .12)
        self.seat=bounds;outer=seat_corners(bounds);tone=TONES[self.theme]
        # Solid structural substrate closes the entire surveyed aperture. The
        # visible outside bands are material, not a black empty cue channel.
        polygon(c,tuple(cam.project(*p) for p in outer),(*tone,255))
        levels=(0,.12,.82,1) if self.variant==2 else (0,.10,.92,1)
        for n,(lo,hi) in enumerate(zip(levels,levels[1:])):
            a,b=blend_corners(outer,lo),blend_corners(outer,hi)
            for side in range(4):
                nxt=(side+1)%4;quad=(a[side],a[nxt],b[nxt],b[side]);self.decor_quads.append(quad)
                gain=(.74,1.0,1.10)[n]*(1.05 if side in (2,3) else .94)
                value=min(255,round(200*gain))
                polygon(c,tuple(cam.project(*p) for p in quad),(value,value,value,255),texture=self.images['polish_'+theme+'_light'].texture)
        for col in range(10):
            for row in range(10):
                light=is_light_tile(col,row)
                key=('tile_light' if light else 'tile_dark') if self.variant==0 else 'polish_'+theme+('_light' if light else '_dark')
                pts=cam.tile(col,row);self.tile_quads.append(pts)
                polygon(c,pts,texture=self.images[key].texture)
                if grid:outline(c,pts,(113,121,126))
        # A hairline material edge, not the old wide dark 'gap'.
        outline(c,tuple(cam.project(u,v) for u,v in ((0,0),(10,0),(10,10),(0,10))),tuple(round(v*.72) for v in tone))
        self.draw_cue(cam)

    def controls(self,scene,cam,probe,roster):
        c=self.c;c.draw_rectangle(25,290,240,505,12,18,26,filled=True)
        rows=((LABELS[self.theme],480),('PRIOR R3 GRAND ARENA' if self.compare else 'R3 '+PROFILES[self.variant],458),
              ('MODE '+str(self.mode)+' FRAME CUE ONLY',436),('1 TO 5 THEME 6 TO 8 FIT',414),('Q W E CUES 9 BEST',392),
              ('A S D F H P SCENE',370),('B OLD G GRID L R T',348),('F11 DISPLAY ESC EXIT',326),
              (self.cue.kind.upper().replace('_',' '),304))
        for text,y in rows:review_text(c,text,30,y,scale=2)
        result=scene.game.resolver.last_parry_result
        if result and result.successful and 0<=scene.game.combat.tick-result.tick<18:
            c.draw_rectangle(25,508,278,529,12,18,26,filled=True)
            review_text(c,'PERFECT PARRY' if result.status=='perfect' else 'PARRY SUCCESS',30,514,scale=2)


def review_extras(out):
    """Mechanical comparison sheet and enlarged actual corner crops."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load,IMG_SavePNG
    def compose(dest,size,items):
        target=s.SDL_CreateRGBSurfaceWithFormat(0,*size,32,s.SDL_PIXELFORMAT_RGBA32)
        if not target:raise RuntimeError('Comparison surface failed')
        renderer=None
        try:
            renderer=s.SDL_CreateSoftwareRenderer(target)
            if not renderer:raise RuntimeError('Comparison renderer failed')
            for source,src,dst in items:
                image=IMG_Load(str(source).encode('utf-8'))
                if not image:raise FileNotFoundError(source)
                texture=s.SDL_CreateTextureFromSurface(renderer,image);s.SDL_FreeSurface(image)
                if not texture:raise RuntimeError('Comparison texture failed')
                try:
                    crop=None if src is None else s.SDL_Rect(*src);d=s.SDL_Rect(*dst)
                    if s.SDL_RenderCopy(renderer,texture,None if crop is None else ctypes.byref(crop),ctypes.byref(d))!=0:raise RuntimeError('Comparison copy failed')
                finally:s.SDL_DestroyTexture(texture)
            s.SDL_RenderPresent(renderer)
            if IMG_SavePNG(target,str(out/dest).encode('utf-8'))!=0:raise RuntimeError('Comparison save failed')
        finally:
            if renderer:s.SDL_DestroyRenderer(renderer)
            s.SDL_FreeSurface(target)
    compose('chapter_polish_sheet.png',(1440,1500),[(out/f'{theme}_{v}_normal.png',None,(col*480,row*300,480,300))
        for row,theme in enumerate(THEMES) for col,v in enumerate('abc')])
    for theme in THEMES:
        for label,source in (('before',f'prior_R3_{theme}_normal.png'),('after',f'{theme}_c_normal.png')):
            compose(theme+'_joint_'+label+'.png',(660,480),[(out/source,(320,115,220,160),(0,0,660,480))])


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=PolishedRenderer(c,args.assets)
        scenes=[make_scene(n) for n in SCENARIOS];phases=[pulse_phase(t) for t in (10,60,110)]
        window=parry_window_scene();resolved=resolved_pulse_scene();all_scenes=scenes+phases+[window,resolved]
        before=[snapshot(s) for s in all_scenes]
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
            def save(name,scene):
                renderer.draw(scene);settings.draw(menu,display);capture_png(c,out/(name+'.png'));c.update_canvas()
                records.append(dict(file=name+'.png',scenario=scene.name,theme=renderer.theme,variant=renderer.variant,mode=renderer.mode,
                    compare=renderer.compare,cue=asdict(renderer.cue),warning_cells=renderer.warning_cells,bounds=renderer.bounds,
                    cue_segments=renderer.cue_segments,seat=renderer.seat,seat_quads=renderer.decor_quads,tile_quads=renderer.tile_quads))
            for theme,name in enumerate(THEMES):
                renderer.theme=theme
                for variant,v in enumerate('abc'):
                    renderer.variant=variant;save(name+'_'+v+'_normal',scenes[0])
                renderer.variant=2
                for scene in (scenes[2],scenes[-1]):save(name+'_c_'+scene.name,scene)
            renderer.theme=0
            for mode in range(3):
                renderer.mode=mode
                for scene in scenes:save('royal_mode_'+str(mode)+'_'+scene.name,scene)
            for mode in (1,2):
                renderer.mode=mode;save('royal_window_mode_'+str(mode),window)
            renderer.mode=1
            for scene in phases+[resolved]:save(scene.name,scene)
            renderer.compare=True
            for theme,name in enumerate(THEMES):
                renderer.theme=theme;save('prior_R3_'+name+'_normal',scenes[0])
            renderer.theme=0;save('prior_R3_pulse',scenes[-1])
            assert before==[snapshot(s) for s in all_scenes]
            review_extras(out)
            (out/'review_manifest.json').write_text(json.dumps(dict(status='R4 polish review pending approval',
                size=[1440,900],camera=CAMERA.corners,textures_loaded=len(renderer.images),recommended=dict(variant=2,mode=1),
                scenes=before,captures=records,comparison_sheet='chapter_polish_sheet.png'),indent=2)+'\n')
            print('Captured 55 scenes + chapter sheet + 10 joint crops; combat unchanged');return
        active=0;extra=None;phase_index=0;grid=False;probe=None;running=True
        keys=(c.SDLK_a,c.SDLK_s,c.SDLK_d,c.SDLK_f,c.SDLK_h,c.SDLK_p)
        while running:
            for e in c.get_events():
                if e.type==c.SDL_QUIT:running=False
                elif e.type==c.SDL_KEYDOWN:
                    if getattr(e,'repeat',False):continue
                    if e.key==c.SDLK_ESCAPE:
                        if menu.is_open:menu.is_open=False
                        else:running=False
                    elif e.key==c.SDLK_F11:display.toggle()
                    elif not menu.is_open:
                        if c.SDLK_1<=e.key<=c.SDLK_5:renderer.theme=e.key-c.SDLK_1
                        elif c.SDLK_6<=e.key<=c.SDLK_8:renderer.variant=e.key-c.SDLK_6
                        elif e.key==c.SDLK_9:renderer.variant=2;renderer.mode=1;renderer.compare=False
                        elif e.key in (c.SDLK_q,c.SDLK_w,c.SDLK_e):renderer.mode=(c.SDLK_q,c.SDLK_w,c.SDLK_e).index(e.key)
                        elif e.key in keys:active=keys.index(e.key);extra=None
                        elif e.key==c.SDLK_l:extra=phases[phase_index];phase_index=(phase_index+1)%3
                        elif e.key==c.SDLK_r:extra=window
                        elif e.key==c.SDLK_t:extra=resolved
                        elif e.key==c.SDLK_g:grid=not grid
                        elif e.key==c.SDLK_b:renderer.compare=not renderer.compare
                elif e.type==c.SDL_MOUSEBUTTONDOWN and e.button==c.SDL_BUTTON_LEFT:
                    point=logical_mouse_to_canvas(e.x,e.y);opened=menu.is_open;action=menu.click(point)
                    if action=='toggle_fullscreen':display.toggle()
                    elif not opened and not menu.is_open and point is not None:probe=CAMERA.pick(*point)
            renderer.draw(extra if extra is not None else scenes[active],grid=grid,probe=probe)
            settings.draw(menu,display);c.update_canvas();sleep(1/180)
        assert before==[snapshot(s) for s in all_scenes]
    finally:
        if settings is not None:settings.close()
        if renderer is not None:renderer.close()
        c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,default=ASSETS)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--capture-dir',type=Path)
    options=parser.parse_args()
    if options.prepare:prepare(options.assets)
    else:run(options)
