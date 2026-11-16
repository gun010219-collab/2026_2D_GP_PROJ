"""B-only size/theme review; original camera samples and live game stay intact.

1..5 theme, 6..8 size, 9 recommendation, A/S/D/F normal/attack/warning/parry,
H perfect, P Pulse, G grid, B old B, F11/SETTINGS, ESC exit.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys
from time import sleep

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.arena_projection import ArenaCamera,CAMERAS
from tools.stage5_camera_review import CameraRenderer,polygon,outline
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS,open_preview,capture_png
from health_renderer import HealthRenderer
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from board import is_light_tile

ASSETS=ROOT/'assets/themed_arena'
THEMES=('royal','forest','frozen','volcanic','gothic')
LABELS=('ROYAL CHESS','ANCIENT FOREST','FROZEN PALACE','OBSIDIAN CALDERA','GOTHIC THRONE')
SCALES=(1.0,1.06,1.12)
RECOMMENDED=2


def scaled_camera(scale):
    # Uniform display expansion preserves the exact B perspective ratios.
    corners=tuple((735+(x-735)*scale,427.5+(y-427.5)*scale) for x,y in CAMERAS[1].corners)
    return ArenaCamera('B '+str(round((scale-1)*100))+' PERCENT',corners,32*scale,1.10*scale)


SIZE_CAMERAS=tuple(scaled_camera(s) for s in SCALES)


def review_text(canvas,label,x,y,scale=2):
    # The live HUD intentionally has a limited alphabet. Supply Z locally,
    # without changing that module or mutating its shared glyph dictionary.
    for index,char in enumerate(label):
        if char!='Z':HealthRenderer._text(canvas,char,x+index*4*scale,y,scale=scale);continue
        for row,bits in enumerate(('111','001','010','100','111')):
            for col,bit in enumerate(bits):
                if bit=='1':
                    l=x+index*4*scale+col*scale;b=y+(4-row)*scale
                    canvas.draw_rectangle(l,b,l+scale-1,b+scale-1,*HealthRenderer.TEXT,filled=True)


def prepare(directory):
    """Technical opaque PNG resize only; keep high-resolution source files."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_Load,IMG_SavePNG,IMG_INIT_PNG
    if s.SDL_Init(s.SDL_INIT_VIDEO)!=0:raise RuntimeError('SDL init failed')
    records=[]
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG:raise RuntimeError('PNG init failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        for name in THEMES:
            source=directory/'source'/(name+'.png')
            src=IMG_Load(str(source).encode('utf-8'))
            if not src:raise FileNotFoundError(source)
            target=renderer=texture=None
            try:
                target=s.SDL_CreateRGBSurfaceWithFormat(0,1440,900,32,s.SDL_PIXELFORMAT_RGBA32)
                if not target:raise RuntimeError('Surface allocation failed')
                renderer=s.SDL_CreateSoftwareRenderer(target)
                if not renderer:raise RuntimeError('Renderer allocation failed')
                texture=s.SDL_CreateTextureFromSurface(renderer,src)
                if not texture:raise RuntimeError('Texture allocation failed')
                s.SDL_SetTextureBlendMode(texture,s.SDL_BLENDMODE_NONE)
                if s.SDL_RenderCopy(renderer,texture,None,None)!=0:raise RuntimeError('Resize failed')
                s.SDL_RenderPresent(renderer)
                dest=directory/(name+'.png')
                if IMG_SavePNG(target,str(dest).encode('utf-8'))!=0:raise RuntimeError('PNG save failed')
                records.append(dict(name=name,source_size=[src.contents.w,src.contents.h],size=[1440,900],
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),rgba_bytes=1440*900*4))
            finally:
                if texture:s.SDL_DestroyTexture(texture)
                if renderer:s.SDL_DestroyRenderer(renderer)
                if target:s.SDL_FreeSurface(target)
                s.SDL_FreeSurface(src)
    finally:IMG_Quit();s.SDL_Quit()
    (directory/'asset_manifest.json').write_text(json.dumps(dict(status='Background concept drafts',assets=records),indent=2)+'\n')


class ThemedRenderer(CameraRenderer):
    theme=0
    compare=False

    def __init__(self,c,assets=ASSETS):
        super().__init__(c)
        try:
            for name in THEMES:
                path=assets/(name+'.png')
                if not path.is_file():raise FileNotFoundError(path)
                self.images['arena_'+name]=c.load_image(str(path))
                # Non-destructive compositing exposure: architecture remains
                # subordinate to the unchanged characters and warning colors.
                c.SDL_SetTextureColorMod(self.images['arena_'+name].texture,190,190,190)
        except Exception:self.close();raise

    def board(self,cam,grid):
        if self.compare:return super().board(CAMERAS[1],grid)
        c=self.c;theme=self.theme
        self.images['arena_'+THEMES[theme]].draw(720,450,1440,900)
        # A distinct stone/wood/ice platform is assembled below the board.
        palettes=(((130,103,63),(52,42,34)),((102,114,72),(35,46,35)),
                  ((133,170,184),(38,57,74)),((137,98,69),(43,36,38)),((119,105,124),(37,33,45)))
        rim,side=palettes[theme]
        base=tuple(cam.project(u,v) for u,v in ((-.32,-.32),(10.32,-.32),(10.32,10.32),(-.32,10.32)))
        shadow=tuple((735+(x-735)*1.025,y-cam.thickness-20) for x,y in base)
        polygon(c,shadow,(9,13,19,255))
        for i in (0,1,3):
            a,b=base[i],base[(i+1)%4]
            polygon(c,(a,b,(b[0],b[1]-cam.thickness-12),(a[0],a[1]-cam.thickness-12)),(*side,255))
            for upper,lower,gain in ((5,8,.72),(cam.thickness+4,cam.thickness+7,.45)):
                band=tuple(round(v*gain) for v in rim)
                polygon(c,((a[0],a[1]-upper),(b[0],b[1]-upper),(b[0],b[1]-lower),(a[0],a[1]-lower)),(*band,255))
        polygon(c,base,(*tuple(max(0,v-25) for v in rim),255))
        outline(c,base,tuple(min(255,v+20) for v in rim))
        top=tuple(cam.project(u,v) for u,v in ((-.15,-.15),(10.15,-.15),(10.15,10.15),(-.15,10.15)))
        polygon(c,top,(*rim,255));outline(c,top,tuple(min(255,v+55) for v in rim))
        for col in range(10):
            for row in range(10):
                pts=cam.tile(col,row)
                polygon(c,pts,texture=self.images['tile_light' if is_light_tile(col,row) else 'tile_dark'].texture)
                if grid:outline(c,pts,(113,121,126))
        outline(c,tuple(cam.project(u,v) for u,v in ((0,0),(10,0),(10,10),(0,10))),(20,24,31))

    def draw(self,scene,cam,**kwargs):
        return super().draw(scene,CAMERAS[1] if self.compare else cam,**kwargs)

    def controls(self,scene,cam,probe,roster):
        c=self.c;c.draw_rectangle(25,290,278,505,12,18,26,filled=True)
        rows=((LABELS[self.theme],480),('OLD B' if self.compare else cam.name,458),
              ('1 TO 5 THEME',432),('6 TO 8 SIZE  9 BEST',410),('A S D F H P SCENE',388),
              ('G GRID  B OLD',366),('F11 DISPLAY  ESC EXIT',344))
        for text,y in rows:review_text(c,text,30,y,scale=2)
        result=scene.game.resolver.last_parry_result
        if result and result.successful and 0<=scene.game.combat.tick-result.tick<18:
            c.draw_rectangle(25,508,278,529,12,18,26,filled=True)
            HealthRenderer._text(c,'PERFECT PARRY' if result.status=='perfect' else 'PARRY SUCCESS',30,514,scale=2,
                                 color=(255,221,113) if result.status=='perfect' else (112,207,246))
        HealthRenderer._text(c,scene.name.upper().replace('_',' '),30,315,scale=2)


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.renderer or not c.window:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=ThemedRenderer(c,args.assets);scenes=[make_scene(n) for n in SCENARIOS]
        before=[snapshot(s) for s in scenes]
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
            def save(filename,scene,cam):
                renderer.draw(scene,cam);settings.draw(menu,display)
                capture_png(c,out/filename);c.update_canvas()
                records.append(dict(file=filename,bounds=renderer.bounds,order=renderer.order,warning_cells=renderer.warning_cells))
            for size,cam in enumerate(SIZE_CAMERAS):save(f'royal_size_{size}.png',scenes[0],cam)
            renderer.compare=True;save('old_B.png',scenes[0],CAMERAS[1]);renderer.compare=False
            for theme,name in enumerate(THEMES):
                renderer.theme=theme
                for scene in scenes:save(name+'_'+scene.name+'.png',scene,SIZE_CAMERAS[RECOMMENDED])
            assert before==[snapshot(s) for s in scenes]
            (out/'review_manifest.json').write_text(json.dumps(dict(status='B enhancement pending user review',
                size=[1440,900],scales=SCALES,recommended=RECOMMENDED,textures_loaded=len(renderer.images),
                cameras=[dict(corners=c.corners,thickness=c.thickness) for c in SIZE_CAMERAS],scenes=before,captures=records),indent=2)+'\n')
            print('Captured 34 B size/theme/combat PNGs; frozen combat unchanged');return
        active=0;size=RECOMMENDED;grid=False;probe=None;running=True
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
                        elif c.SDLK_6<=e.key<=c.SDLK_8:size=e.key-c.SDLK_6;probe=None
                        elif e.key==c.SDLK_9:size=RECOMMENDED;renderer.compare=False
                        elif e.key in (c.SDLK_a,c.SDLK_s,c.SDLK_d,c.SDLK_f,c.SDLK_h,c.SDLK_p):
                            active=(c.SDLK_a,c.SDLK_s,c.SDLK_d,c.SDLK_f,c.SDLK_h,c.SDLK_p).index(e.key)
                        elif e.key==c.SDLK_g:grid=not grid
                        elif e.key==c.SDLK_b:renderer.compare=not renderer.compare
                elif e.type==c.SDL_MOUSEBUTTONDOWN and e.button==c.SDL_BUTTON_LEFT:
                    point=logical_mouse_to_canvas(e.x,e.y);opened=menu.is_open;action=menu.click(point)
                    if action=='toggle_fullscreen':display.toggle()
                    elif not opened and not menu.is_open and point is not None:
                        probe=(CAMERAS[1] if renderer.compare else SIZE_CAMERAS[size]).pick(*point)
            renderer.draw(scenes[active],SIZE_CAMERAS[size],grid=grid,probe=probe)
            settings.draw(menu,display);c.update_canvas();sleep(1/180)
        assert before==[snapshot(s) for s in scenes]
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
