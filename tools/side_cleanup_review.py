"""R6 front-central relief cleanup; R5 alignment, rails and Chapter1 remain.

1..5 theme, 6..8 Cleanup A/B/C, 9 C/Mode1, Q/W/E cues,
A/S/D/F/H/P scene, B previous R5-C, G grid, L/R/T Pulse/input/resolution,
F11/SETTINGS, ESC exit. Frozen review only.
"""
import argparse
import ctypes
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from time import sleep
import weakref

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.aligned_board_review import AlignedRenderer
from tools.ornate_board_review import CAMERA,pulse_phase,parry_window_scene
from tools.highend_board_review import resolved_pulse_scene
from tools.themed_arena_review import THEMES,LABELS,review_text
from tools.stage5_camera_review import polygon,outline
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS,open_preview,capture_png
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer

ASSETS=ROOT/'assets/side_cleanup'
AFFECTED=THEMES[1:]
# Front central bay only, bottom-left logical canvas coordinates. Its top is
# drawn before the deck, so the gameplay surface still owns every inside pixel.
BAY=(622,14,848,134)
FRONT_REGION=(545,5,925,134)
DECK_Y=CAMERA.corners[0][1]


def panel_layout(record,choice):
    l,t,r,b=record['alpha_bounds'];w,h=r-l,b-t
    maxw,maxh,top=((365,121,128),(340,112,120),(365,121,131.5))[choice]
    scale=min(maxw/w,maxh/h);ow,oh=w*scale,h*scale
    opaque=(735-ow/2,top-oh,735+ow/2,top)
    left=opaque[0]-l*scale;bottom=opaque[1]-(256-b)*scale
    return dict(opaque=opaque,image=(left+256*scale,bottom+128*scale,512*scale,256*scale),
                uniform_scale=scale,deck_clearance=DECK_Y-top)


def clip_parts(box=BAY):
    l,b,r,t=box;top=899-t;bottom=899-b
    return ((0,0,1440,top),(0,bottom,1440,900-bottom),(0,top,l,bottom-top),(r,top,1440-r,bottom-top))


def prepare(directory):
    """Native alpha crop/pad/resize only; generated originals are retained."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_Load,IMG_SavePNG,IMG_INIT_PNG
    from tools.prepare_stage5_art import alpha_bounds
    records=[];s.SDL_Init(0);IMG_Init(IMG_INIT_PNG)
    try:
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        for theme in AFFECTED:
            source=directory/'source'/(theme+('_facade.png' if theme in ('frozen','gothic') else '_panel.png'))
            a=IMG_Load(str(source).encode('utf-8'))
            if not a:raise FileNotFoundError(source)
            image=s.SDL_ConvertSurfaceFormat(a,s.SDL_PIXELFORMAT_RGBA32,0);s.SDL_FreeSurface(a)
            if not image:raise RuntimeError('RGBA conversion')
            target=renderer=texture=None
            try:
                (l,t,r,b),clear=alpha_bounds(image)
                if not clear:raise ValueError('True-alpha relief required')
                target=s.SDL_CreateRGBSurfaceWithFormat(0,512,256,32,s.SDL_PIXELFORMAT_RGBA32)
                if not target:raise RuntimeError('Surface failed')
                renderer=s.SDL_CreateSoftwareRenderer(target)
                if not renderer:raise RuntimeError('Renderer failed')
                texture=s.SDL_CreateTextureFromSurface(renderer,image)
                if not texture:raise RuntimeError('Texture failed')
                scale=min(476/(r-l),220/(b-t));w,h=round((r-l)*scale),round((b-t)*scale)
                src=s.SDL_Rect(l,t,r-l,b-t);dest=s.SDL_Rect((512-w)//2,(256-h)//2,w,h)
                s.SDL_SetTextureBlendMode(texture,s.SDL_BLENDMODE_NONE)
                s.SDL_SetRenderDrawColor(renderer,0,0,0,0);s.SDL_RenderClear(renderer)
                if s.SDL_RenderCopy(renderer,texture,ctypes.byref(src),ctypes.byref(dest))!=0:raise RuntimeError('Panel resize failed')
                s.SDL_RenderPresent(renderer);path=directory/(theme+'_panel.png')
                if IMG_SavePNG(target,str(path).encode('utf-8'))!=0:raise RuntimeError('Panel save failed')
                bounds,clear=alpha_bounds(target)
                records.append(dict(theme=theme,source=source.name,size=[512,256],source_size=[image.contents.w,image.contents.h],alpha_bounds=bounds,
                    transparent_pixels=clear,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
            finally:
                if texture:s.SDL_DestroyTexture(texture)
                if renderer:s.SDL_DestroyRenderer(renderer)
                if target:s.SDL_FreeSurface(target)
                s.SDL_FreeSurface(image)
    finally:IMG_Quit();s.SDL_Quit()
    (directory/'asset_manifest.json').write_text(json.dumps(dict(status='R6 front bay cleanup pending approval',
        source_scope='New complete front relief derivatives; all R5 alignment and other art reused',assets=records),indent=2)+'\n')


class FacadeLayer:
    """Clip the old truncated relief on the frame layer, not on combat/HUD."""
    def __init__(self,owner,image):self.owner=weakref.ref(owner);self.image=image

    def draw(self,*args):
        owner=self.owner()
        if owner.show_original:return self.image.draw(*args)
        import sdl2 as s
        c=owner.c;enabled=s.SDL_RenderIsClipEnabled(c.renderer);old=s.SDL_Rect()
        s.SDL_RenderGetClipRect(c.renderer,ctypes.byref(old))
        try:
            for rect in clip_parts():
                part=s.SDL_Rect(*rect)
                if enabled:
                    intersection=s.SDL_Rect()
                    if not s.SDL_IntersectRect(ctypes.byref(part),ctypes.byref(old),ctypes.byref(intersection)):continue
                    part=intersection
                if s.SDL_RenderSetClipRect(c.renderer,ctypes.byref(part))!=0:raise RuntimeError('Front bay clip failed')
                self.image.draw(*args)
        finally:s.SDL_RenderSetClipRect(c.renderer,ctypes.byref(old) if enabled else None)
        owner.draw_front_bay()


class SideCleanupRenderer(AlignedRenderer):
    def __init__(self,c,assets=ASSETS):
        super().__init__(c);self.show_original=False;self.cleanup_choice=2;self.front_layout=None
        try:
            self.panel_records={r['theme']:r for r in json.loads((assets/'asset_manifest.json').read_text())['assets']}
            for theme in AFFECTED:
                p=assets/(theme+'_panel.png')
                if not p.is_file():raise FileNotFoundError(p)
                self.images['panel_'+theme]=c.load_image(str(p))
                c.SDL_SetTextureColorMod(self.images['panel_'+theme].texture,210,210,210)
                key='align_'+theme+'_c';self.images[key]=FacadeLayer(self,self.images[key])
        except Exception:self.close();raise

    def draw_front_bay(self):
        c=self.c;theme=THEMES[self.theme];choice=self.cleanup_choice
        layout=panel_layout(self.panel_records[theme],choice);self.front_layout=layout
        # A proper central facade bay replaces the clipped older medallion.
        # Its shallow header stays below the deck; it never paints on a tile.
        l,b,r,t=BAY
        # A non-figurative material bed replaces the entire old crest. Reusing
        # neighbouring facade art would also copy its figurative motifs here.
        # The small exposed header is a shallow underside course, not a black
        # picture-frame backdrop. Its material is the existing chapter stone.
        tint=((0,0,0),(163,151,112),(190,208,220),(132,116,100),(148,141,157))[self.theme]
        polygon(c,((l,b),(r,b),(r,t),(l,t)),(*tint,255),texture=self.images['polish_'+theme+'_light'].texture)
        if choice==2:
            # Underside seam follows the existing horizontal facade course.
            c.draw_line(l,129,r,129,100,96,86)
        else:
            c.draw_line(l,128,r,128,88,86,80)
        self.images['panel_'+theme].draw(*layout['image'])

    def board(self,cam,grid):
        choice=self.variant;comparison=self.compare
        self.cleanup_choice=choice;self.front_layout=None
        self.show_original=comparison or self.theme==0
        # Always use R5 Fix-C. Cleanup selections NEVER choose another alignment.
        self.variant=2;self.compare=False
        try:super().board(cam,grid)
        finally:self.variant=choice;self.compare=comparison;self.show_original=False

    def controls(self,scene,cam,probe,roster):
        c=self.c;c.draw_rectangle(25,290,240,505,12,18,26,filled=True)
        labels=('A TOP LINE','B LOWER RELIEF','C FRONT BAY')
        rows=((LABELS[self.theme],480),('PRIOR R5 C' if self.compare else 'CLEAN '+labels[self.variant],458),
              ('MODE '+str(self.mode)+' FRAME CUE ONLY',436),('1 TO 5 THEME 6 TO 8 FIX',414),('Q W E CUES 9 BEST',392),
              ('A S D F H P SCENE',370),('B OLD G GRID L R T',348),('F11 DISPLAY ESC EXIT',326),
              (self.cue.kind.upper().replace('_',' '),304))
        for text,y in rows:review_text(c,text,30,y,scale=2)
        result=scene.game.resolver.last_parry_result
        if result and result.successful and 0<=scene.game.combat.tick-result.tick<18:
            c.draw_rectangle(25,508,278,529,12,18,26,filled=True)
            review_text(c,'PERFECT PARRY' if result.status=='perfect' else 'PARRY SUCCESS',30,514,scale=2)


def review_extras(out):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load,IMG_SavePNG
    def compose(name,size,items):
        target=s.SDL_CreateRGBSurfaceWithFormat(0,*size,32,s.SDL_PIXELFORMAT_RGBA32)
        if not target:raise RuntimeError('Comparison surface failed')
        renderer=None
        try:
            renderer=s.SDL_CreateSoftwareRenderer(target)
            if not renderer:raise RuntimeError('Comparison renderer failed')
            for source,crop,dest in items:
                image=IMG_Load(str(out/source).encode('utf-8'))
                if not image:raise FileNotFoundError(source)
                texture=s.SDL_CreateTextureFromSurface(renderer,image);s.SDL_FreeSurface(image)
                if not texture:raise RuntimeError('Comparison texture failed')
                try:
                    src=None if crop is None else s.SDL_Rect(*crop);dst=s.SDL_Rect(*dest)
                    if s.SDL_RenderCopy(renderer,texture,None if src is None else ctypes.byref(src),ctypes.byref(dst))!=0:raise RuntimeError('Comparison copy failed')
                finally:s.SDL_DestroyTexture(texture)
            s.SDL_RenderPresent(renderer)
            if IMG_SavePNG(target,str(out/name).encode('utf-8'))!=0:raise RuntimeError('Comparison save failed')
        finally:
            if renderer:s.SDL_DestroyRenderer(renderer)
            s.SDL_FreeSurface(target)
    compose('cleanup_comparison_sheet.png',(1440,1500),[(theme+'_'+v+'_normal.png',None,(i*480,j*300,480,300))
        for j,theme in enumerate(THEMES) for i,v in enumerate('abc')])
    for theme in THEMES:
        for label,source in (('before','prior_R5_'+theme+'_normal.png'),('after',theme+'_c_normal.png')):
            compose(theme+'_front_'+label+'.png',(1080,435),[(source,(555,748,360,145),(0,0,1080,435))])
            compose(theme+'_joints_'+label+'.png',(540,435),[(source,(560,748,90,145),(0,0,270,435)),(source,(820,748,90,145),(270,0,270,435))])


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=SideCleanupRenderer(c,args.assets)
        scenes=[make_scene(n) for n in SCENARIOS];phases=[pulse_phase(t) for t in (10,60,110)]
        window=parry_window_scene();resolved=resolved_pulse_scene();all_scenes=scenes+phases+[window,resolved]
        before=[snapshot(s) for s in all_scenes]
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
            def save(name,scene):
                renderer.draw(scene);settings.draw(menu,display);capture_png(c,out/(name+'.png'));c.update_canvas()
                records.append(dict(file=name+'.png',scenario=scene.name,theme=renderer.theme,variant=renderer.variant,mode=renderer.mode,
                    compare=renderer.compare,cue=asdict(renderer.cue),warning_cells=renderer.warning_cells,bounds=renderer.bounds,
                    cue_segments=renderer.cue_segments,rim_quads=renderer.rim_quads,tile_quads=renderer.tile_quads,
                    front_layout=renderer.front_layout,replacement_box=FRONT_REGION if renderer.front_layout else None,
                    upper_clip_box=BAY if renderer.front_layout else None))
            for theme,name in enumerate(THEMES):
                renderer.theme=theme
                for variant,v in enumerate('abc'):
                    renderer.variant=variant;save(name+'_'+v+'_normal',scenes[0])
                renderer.variant=2
                if theme:
                    for scene in (scenes[2],scenes[3],scenes[4],scenes[5]):save(name+'_c_'+scene.name,scene)
            renderer.theme=1
            for mode in range(3):
                renderer.mode=mode
                for scene in scenes:save('forest_mode_'+str(mode)+'_'+scene.name,scene)
            for mode in (1,2):
                renderer.mode=mode;save('forest_window_mode_'+str(mode),window)
            renderer.mode=1
            for scene in phases+[resolved]:save(scene.name,scene)
            renderer.compare=True
            for theme,name in enumerate(THEMES):
                renderer.theme=theme;save('prior_R5_'+name+'_normal',scenes[0])
            renderer.theme=1;save('prior_R5_pulse',scenes[-1])
            assert before==[snapshot(s) for s in all_scenes]
            review_extras(out)
            (out/'review_manifest.json').write_text(json.dumps(dict(status='R6 central front cleanup pending approval',
                size=[1440,900],camera=CAMERA.corners,textures_loaded=len(renderer.images),recommended=dict(variant=2,mode=1),
                clarification='User identified front-central medallion/relief; lateral rails and Chapter1 retained',
                scenes=before,captures=records,comparison_sheet='cleanup_comparison_sheet.png'),indent=2)+'\n')
            print('Captured 61 scenes + cleanup sheet + 20 front/joint crops; combat unchanged');return
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
    parser.add_argument('--fine',action='store_true',help='R6c Chapter4/5 Fine A/B/C; B compares R6b-C')
    options=parser.parse_args()
    if options.fine:
        if options.prepare:parser.error('--fine reuses R6b assets; --prepare is not needed')
        from tools.front_crest_fine_review import run as run_fine
        run_fine(options)
    elif options.prepare:prepare(options.assets)
    else:run(options)
