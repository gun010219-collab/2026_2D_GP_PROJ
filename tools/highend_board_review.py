"""R3 sculpted altar shells, frozen Stage5 review. Live renderers are untouched.

1..5 theme, 6..8 R1/R2/R3, 9 R3/Mode1, Q/W/E cues,
A/S/D/F/H/P scene, B previous R2, G grid, L Pulse time, R parry window,
T resolved Pulse, F11/SETTINGS, ESC exit.
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
from tools.arena_projection import ArenaCamera
from tools.ornate_board_review import OrnateRenderer,CAMERA,cue_for,pulse_phase,parry_window_scene
from tools.themed_arena_review import THEMES,LABELS,review_text
from tools.stage5_camera_review import polygon,outline
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS,open_preview,capture_png
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from board import is_light_tile

ASSETS=ROOT/'assets/highend_board'
PROFILES=('REGAL MONUMENT','ORNATE RELIC','GRAND ARENA')
# Front-left, front-right, back-right, back-left in source-normalized y-down.
# These are the opening calibration, not game cells or gameplay parameters.
OPENING=((214/1536,552/1024),(1325/1536,552/1024),(1204/1536,135/1024),(333/1536,135/1024))


def project_art(x,y,opening=OPENING):
    """Align the source opening to B+12; fit only exterior art into margins.

    Source front relief was illustrated tall for detail. Its vertical display
    scale is reduced separately from the top. This is a 2D layer fit, not 3D.
    """
    source=ArenaCamera('SOURCE OPENING',tuple((u,1-v) for u,v in opening),0,1)
    u,v=source.inverse(x,1-y)
    if u<0:u*=.65
    elif u>10:u=10+(u-10)*.65
    if v<0:v*=.22
    elif v>10:v=10+(v-10)*.50
    return CAMERA.project(u,v)


def prepare(directory):
    """Native SDL render-layer calibration/resize, retain every original PNG."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_Load,IMG_SavePNG,IMG_INIT_PNG
    from tools.prepare_stage5_art import alpha_bounds
    records=[]
    if s.SDL_Init(0)!=0:raise RuntimeError('SDL init failed')
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG:raise RuntimeError('PNG init failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        # Dense piecewise mesh is baked once; the viewer only draws one PNG.
        nx,ny=96,64
        vertices=(s.SDL_Vertex*((nx+1)*(ny+1)))()
        for j in range(ny+1):
            for i in range(nx+1):
                x,y=project_art(i/nx,j/ny);v=vertices[j*(nx+1)+i]
                v.position=s.SDL_FPoint(x,899-y);v.color=s.SDL_Color(255,255,255,255)
                v.tex_coord=s.SDL_FPoint(i/nx,j/ny)
        indices=[]
        for j in range(ny):
            for i in range(nx):
                a=j*(nx+1)+i;b=a+1;d=a+nx+1;e=d+1
                indices.extend((a,b,e,a,e,d))
        ix=(ctypes.c_int*len(indices))(*indices)
        for theme in THEMES:
            for variant in range(1,4):
                name=f'{theme}_r{variant}';path=directory/'source'/(name+'.png')
                loaded=IMG_Load(str(path).encode('utf-8'))
                if not loaded:raise FileNotFoundError(path)
                source=s.SDL_ConvertSurfaceFormat(loaded,s.SDL_PIXELFORMAT_RGBA32,0);s.SDL_FreeSurface(loaded)
                if not source:raise RuntimeError('RGBA conversion')
                target=renderer=tex=None
                try:
                    source_bounds,source_clear=alpha_bounds(source)
                    if not source_clear:raise ValueError('Transparent shell required: '+name)
                    target=s.SDL_CreateRGBSurfaceWithFormat(0,1440,900,32,s.SDL_PIXELFORMAT_RGBA32)
                    if not target:raise RuntimeError('Surface failed')
                    renderer=s.SDL_CreateSoftwareRenderer(target)
                    if not renderer:raise RuntimeError('Renderer failed')
                    tex=s.SDL_CreateTextureFromSurface(renderer,source)
                    if not tex:raise RuntimeError('Texture failed')
                    s.SDL_SetTextureBlendMode(tex,s.SDL_BLENDMODE_NONE)
                    s.SDL_SetRenderDrawColor(renderer,0,0,0,0);s.SDL_RenderClear(renderer)
                    if s.SDL_RenderGeometry(renderer,tex,vertices,len(vertices),ix,len(indices))!=0:
                        raise RuntimeError(s.SDL_GetError().decode())
                    s.SDL_RenderPresent(renderer);dest=directory/(name+'.png')
                    if IMG_SavePNG(target,str(dest).encode('utf-8'))!=0:raise RuntimeError('Save failed')
                    bounds,clear=alpha_bounds(target)
                    records.append(dict(name=name,size=[1440,900],source_size=[source.contents.w,source.contents.h],
                        source_alpha_bounds=source_bounds,source_transparent_pixels=source_clear,
                        alpha_bounds=bounds,transparent_pixels=clear,opening=OPENING,
                        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
                finally:
                    if tex:s.SDL_DestroyTexture(tex)
                    if renderer:s.SDL_DestroyRenderer(renderer)
                    if target:s.SDL_FreeSurface(target)
                    s.SDL_FreeSurface(source)
    finally:IMG_Quit();s.SDL_Quit()
    (directory/'asset_manifest.json').write_text(json.dumps(dict(status='R3 sculptural shell review drafts',
        method='SDL piecewise exterior fitting; logical opening unchanged',assets=records),indent=2)+'\n')


def resolved_pulse_scene():
    scene=pulse_phase(110);scene.name='pulse_resolved'
    record=next(r for r in scene.game.encounter.ledger._records.values()
                if r.state=='telegraph' and r.event.attack_kind=='king_pulse')
    scene.game.advance(record.event.hit_tick-scene.game.combat.tick)
    return scene


def contact_sheet(directory):
    """Mechanical 5x3 arrangement of actual captures, no art repainting."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load,IMG_SavePNG
    target=s.SDL_CreateRGBSurfaceWithFormat(0,1440,1500,32,s.SDL_PIXELFORMAT_RGBA32)
    if not target:raise RuntimeError('Contact surface failed')
    renderer=None
    try:
        renderer=s.SDL_CreateSoftwareRenderer(target)
        if not renderer:raise RuntimeError('Contact renderer failed')
        for row,theme in enumerate(THEMES):
            for col in range(3):
                image=IMG_Load(str(directory/f'{theme}_r{col+1}_normal.png').encode('utf-8'))
                if not image:raise RuntimeError('Contact source failed')
                texture=s.SDL_CreateTextureFromSurface(renderer,image);s.SDL_FreeSurface(image)
                if not texture:raise RuntimeError('Contact texture failed')
                try:
                    dest=s.SDL_Rect(col*480,row*300,480,300)
                    if s.SDL_RenderCopy(renderer,texture,None,ctypes.byref(dest))!=0:raise RuntimeError('Contact copy failed')
                finally:s.SDL_DestroyTexture(texture)
        s.SDL_RenderPresent(renderer)
        if IMG_SavePNG(target,str(directory/'chapter_variant_sheet.png').encode('utf-8'))!=0:raise RuntimeError('Contact save failed')
    finally:
        if renderer:s.SDL_DestroyRenderer(renderer)
        s.SDL_FreeSurface(target)


class HighendRenderer(OrnateRenderer):
    def __init__(self,c,assets=ASSETS):
        super().__init__(c)
        try:
            for theme in THEMES:
                for variant in range(1,4):
                    name=f'{theme}_r{variant}';p=assets/(name+'.png')
                    if not p.is_file():raise FileNotFoundError(p)
                    self.images[name]=c.load_image(str(p))
        except Exception:self.close();raise

    def line(self,cam,a,b,color,*,cue=False):
        if cue and not self.compare:
            def inset(p):
                return tuple(v*.35 if v<0 else 10+(v-10)*.35 if v>10 else v for v in p)
            a,b=inset(a),inset(b)
        super().line(cam,a,b,color,cue=cue)

    def board(self,cam,grid):
        self.decor_segments=[];self.cue_segments=[];self.decor_quads=[]
        if self.compare:
            # Compare the previous R2 C, not its still older Q comparison.
            self.compare=False;variant=self.variant
            try:
                self.variant=2
                # Keep old cue rail coordinates on the previous board.
                self._old_cues=True
                super().board(cam,grid)
            finally:self.compare=True;self.variant=variant;self._old_cues=False
            return
        c=self.c
        self.images['arena_'+THEMES[self.theme]].draw(720,450,1440,900)
        self.images[f'{THEMES[self.theme]}_r{self.variant+1}'].draw(720,450,1440,900)
        # A true-alpha sculptural boss retains its proportions independently
        # of the shallow fascia. Existing chapter crests remain unmodified.
        self.images['seal_'+THEMES[self.theme]].draw(735,72,104,104)
        # Exact same original 100 textures. Art never replaces cell geometry.
        for col in range(10):
            for row in range(10):
                pts=cam.tile(col,row)
                polygon(c,pts,texture=self.images['tile_light' if is_light_tile(col,row) else 'tile_dark'].texture)
                if grid:outline(c,pts,(113,121,126))
        # A quiet continuous recess integrates information into the inner lip.
        for quad in (((0,-.025),(10,-.025),(10,-.12),(0,-.12)),
                     ((10.025,0),(10.12,0),(10.12,10),(10.025,10)),
                     ((0,10.025),(10,10.025),(10,10.12),(0,10.12)),
                     ((-.12,0),(-.025,0),(-.025,10),(-.12,10))):
            self.decor_quads.append(quad)
            polygon(c,tuple(cam.project(*p) for p in quad),(25,29,35,255))
        outline(c,tuple(cam.project(u,v) for u,v in ((0,0),(10,0),(10,10),(0,10))),(20,24,31))
        self.draw_cue(cam)

    def draw_cue(self,cam):
        if getattr(self,'_old_cues',False):
            # line() normally compresses the new cue rail. B must retain R2.
            previous=self.compare;self.compare=True
            try:super().draw_cue(cam)
            finally:self.compare=previous
        else:super().draw_cue(cam)

    def controls(self,scene,cam,probe,roster):
        c=self.c;c.draw_rectangle(25,290,240,505,12,18,26,filled=True)
        rows=((LABELS[self.theme],480),('PRIOR R2 C' if self.compare else 'R'+str(self.variant+1)+' '+PROFILES[self.variant],458),
              ('MODE '+str(self.mode)+'  FRAME CUE ONLY',436),('1 TO 5 THEME 6 TO 8 ART',414),
              ('Q W E CUES 9 BEST',392),('A S D F H P SCENE',370),('B OLD G GRID L R T',348),
              ('F11 DISPLAY ESC EXIT',326),(self.cue.kind.upper().replace('_',' '),304))
        for label,y in rows:review_text(c,label,30,y,scale=2)
        result=scene.game.resolver.last_parry_result
        if result and result.successful and 0<=scene.game.combat.tick-result.tick<18:
            c.draw_rectangle(25,508,278,529,12,18,26,filled=True)
            review_text(c,'PERFECT PARRY' if result.status=='perfect' else 'PARRY SUCCESS',30,514,scale=2)


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=HighendRenderer(c,args.assets)
        scenes=[make_scene(n) for n in SCENARIOS]
        phases=[pulse_phase(t) for t in (10,60,110)];window=parry_window_scene();resolved=resolved_pulse_scene()
        all_scenes=scenes+phases+[window,resolved];before=[snapshot(s) for s in all_scenes]
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
            def save(name,scene):
                renderer.draw(scene);settings.draw(menu,display);capture_png(c,out/(name+'.png'));c.update_canvas()
                records.append(dict(file=name+'.png',theme=renderer.theme,variant=renderer.variant,mode=renderer.mode,
                    compare=renderer.compare,cue=asdict(renderer.cue),warning_cells=renderer.warning_cells,bounds=renderer.bounds,
                    cue_segments=renderer.cue_segments,decor_quads=renderer.decor_quads))
            renderer.mode=1
            for theme,name in enumerate(THEMES):
                renderer.theme=theme
                for variant in range(3):
                    renderer.variant=variant;save(f'{name}_r{variant+1}_normal',scenes[0])
                renderer.variant=2
                for scene in (scenes[2],scenes[-1]):save(name+'_r3_'+scene.name,scene)
            renderer.theme=0
            for mode in range(3):
                renderer.mode=mode
                for scene in scenes:save('royal_mode_'+str(mode)+'_'+scene.name,scene)
            for mode in (1,2):
                renderer.mode=mode;save('royal_window_mode_'+str(mode),window)
            renderer.mode=1
            for scene in phases+[resolved]:save(scene.name,scene)
            renderer.compare=True
            for scene in (scenes[0],scenes[-1]):save('prior_R2_'+scene.name,scene)
            assert before==[snapshot(s) for s in all_scenes]
            contact_sheet(out)
            (out/'review_manifest.json').write_text(json.dumps(dict(status='R3 pending design approval',
                size=[1440,900],camera=CAMERA.corners,textures_loaded=len(renderer.images),recommended=dict(variant=2,mode=1),
                contact_sheet='chapter_variant_sheet.png',scenes=before,captures=records),indent=2)+'\n')
            print('Captured 51 scenes + one chapter/variant sheet; combat unchanged');return
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
