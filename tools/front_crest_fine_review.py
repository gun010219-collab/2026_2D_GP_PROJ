"""R6c: Chapter4/5 local finishing, R6b-C preserved for Chapter1/2/3.

Use tools/side_cleanup_review.py --fine (same controls; B compares R6b-C).
This frozen inspection tool never updates game simulation or main rendering.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from time import sleep

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.side_cleanup_review import (ASSETS,THEMES,LABELS,CAMERA,BAY,FRONT_REGION,
    DECK_Y,SideCleanupRenderer,panel_layout,polygon,review_text)
from tools.ornate_board_review import pulse_phase,parry_window_scene
from tools.highend_board_review import resolved_pulse_scene
from tools.stage5_art_preview import (make_scene,snapshot,SCENARIOS,open_preview,capture_png)
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer

OUTPUT=ROOT/'assets/front_crest_fine'
TARGETS=(3,4)
SPECS=((4,1.0),(2,.96),(7,.94))  # drop from R6b-C, uniform silhouette scale


def fine_layout(record,choice):
    """Keep complete alpha silhouette; reserve a visible underside joint."""
    base=panel_layout(record,2);drop,gain=SPECS[choice]
    l,b,r,t=base['opaque'];cx=(l+r)/2;top=t-drop
    w,h=(r-l)*gain,(t-b)*gain;scale=base['uniform_scale']*gain
    opaque=(cx-w/2,top-h,cx+w/2,top)
    x0,y0,x1,y1=record['alpha_bounds']
    left=opaque[0]-x0*scale;bottom=opaque[1]-(256-y1)*scale
    return dict(opaque=opaque,image=(left+256*scale,bottom+128*scale,512*scale,256*scale),
        uniform_scale=scale,deck_clearance=DECK_Y-top,drop=drop,gain=gain)


class FineRenderer(SideCleanupRenderer):
    def __init__(self,c,assets=ASSETS):
        super().__init__(c,assets);self.theme=3;self.fine_choice=2;self.use_fine=False
        self.separator_quads=[]

    def board(self,cam,grid):
        choice=self.variant;comparison=self.compare
        self.separator_quads=[];self.fine_choice=choice
        self.use_fine=self.theme in TARGETS and not comparison
        # B always means R6b Cleanup-C, not the older R5 comparison path.
        # Chapters1..3 also use the unchanged R6b-C, for every Fine selection.
        self.variant=2;self.compare=False
        try:super().board(cam,grid)
        finally:self.variant=choice;self.compare=comparison;self.use_fine=False

    def draw_front_bay(self):
        if not self.use_fine:return super().draw_front_bay()
        c=self.c;theme=THEMES[self.theme]
        self.front_layout=fine_layout(self.panel_records[theme],self.fine_choice)
        l,b,r,t=BAY
        tint=((132,116,100) if self.theme==3 else (148,141,157))
        polygon(c,((l,b),(r,b),(r,t),(l,t)),(*tint,255),texture=self.images['polish_'+theme+'_light'].texture)
        self.images['panel_'+theme].draw(*self.front_layout['image'])

    def draw_cue(self,cam):
        # Draw after the existing top bevel and BEFORE all cue lines. Therefore
        # the joint cannot occlude the danger/parry/Pulse frame information.
        if self.use_fine and self.fine_choice in (1,2):
            c=self.c;theme=THEMES[self.theme];l,b,r,t=self.front_layout['opaque']
            bottom=130 if self.fine_choice==1 else 125
            bands=(((l,132),(r,132),(r-1,131),(l+1,131)),
                   ((l+1,131),(r-1,131),(r-1,bottom),(l+1,bottom)))
            light,dark=(((226,211,188),(180,164,144)) if self.theme==3 else ((217,209,227),(177,170,190)))
            for quad,color in zip(bands,(light,dark)):
                self.separator_quads.append(quad)
                polygon(c,quad,(*color,255),texture=self.images['polish_'+theme+'_light'].texture)
        return super().draw_cue(cam)

    def controls(self,scene,cam,probe,roster):
        # Preserve real success feedback and all original HUD outside the help.
        super().controls(scene,cam,probe,roster)
        c=self.c;c.draw_rectangle(25,290,240,505,12,18,26,filled=True)
        label=('FINE A LOWER','FINE B SEAM','FINE C COMBINED')[self.variant]
        if self.compare:label='PRIOR R6B C'
        elif self.theme not in TARGETS:label='R6B C UNCHANGED'
        rows=((LABELS[self.theme],480),(label,458),('MODE '+str(self.mode)+' FRAME CUE ONLY',436),
              ('1 TO 5 THEME 6 TO 8 FINE',414),('9 BEST Q W E CUES',392),('A S D F H P SCENE',370),
              ('B R6B G GRID L R T',348),('F11 DISPLAY ESC EXIT',326),
              (self.cue.kind.upper().replace('_',' '),304))
        for text,y in rows:review_text(c,text,30,y,scale=2)


def compose_reviews(out):
    """Native screenshot crops only; old assets/captures are never overwritten."""
    import ctypes
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load,IMG_SavePNG
    def compose(name,size,items):
        surface=s.SDL_CreateRGBSurfaceWithFormat(0,*size,32,s.SDL_PIXELFORMAT_RGBA32)
        if not surface:raise RuntimeError('Comparison surface failed')
        renderer=None
        try:
            renderer=s.SDL_CreateSoftwareRenderer(surface)
            if not renderer:raise RuntimeError('Comparison renderer failed')
            for source,crop,dest in items:
                a=IMG_Load(str(out/source).encode('utf-8'))
                if not a:raise FileNotFoundError(source)
                tex=s.SDL_CreateTextureFromSurface(renderer,a);s.SDL_FreeSurface(a)
                if not tex:raise RuntimeError('Comparison texture failed')
                try:
                    src=None if crop is None else s.SDL_Rect(*crop);dst=s.SDL_Rect(*dest)
                    if s.SDL_RenderCopy(renderer,tex,None if src is None else ctypes.byref(src),ctypes.byref(dst))!=0:raise RuntimeError('Comparison copy failed')
                finally:s.SDL_DestroyTexture(tex)
            s.SDL_RenderPresent(renderer)
            if IMG_SavePNG(surface,str(out/name).encode('utf-8'))!=0:raise RuntimeError('Comparison save failed')
        finally:
            if renderer:s.SDL_DestroyRenderer(renderer)
            s.SDL_FreeSurface(surface)
    compose('fine_comparison_sheet.png',(1440,600),[(t+'_'+v+'_normal.png',None,(i*480,j*300,480,300))
        for j,t in enumerate(('volcanic','gothic')) for i,v in enumerate('abc')])
    compose('before_after_sheet.png',(1440,900),[(name,None,(i*720,j*450,720,450))
        for j,t in enumerate(('volcanic','gothic')) for i,name in enumerate(('before_'+t+'_normal.png',t+'_c_normal.png'))])
    for t in ('volcanic','gothic'):
        for label,name in (('before','before_'+t+'_normal.png'),('after',t+'_c_normal.png')):
            compose(t+'_front_'+label+'.png',(1200,435),[(name,(535,748,400,145),(0,0,1200,435))])
            compose(t+'_top_'+label+'.png',(1200,180),[(name,(535,750,400,60),(0,0,1200,180))])


def capture(c,renderer,settings,menu,display,args,scenes):
    out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
    before=[snapshot(scene) for scene in scenes]
    def save(name,scene):
        renderer.draw(scene);settings.draw(menu,display);capture_png(c,out/(name+'.png'));c.update_canvas()
        records.append(dict(file=name+'.png',scenario=scene.name,theme=renderer.theme,variant=renderer.variant,
            mode=renderer.mode,compare=renderer.compare,cue=asdict(renderer.cue),warning_cells=renderer.warning_cells,
            tile_quads=renderer.tile_quads,rim_quads=renderer.rim_quads,cue_segments=renderer.cue_segments,
            front_layout=renderer.front_layout,separator_quads=renderer.separator_quads))
    renderer.mode=1
    for theme,t in enumerate(THEMES):
        renderer.theme=theme
        for variant,v in enumerate('abc'):
            renderer.variant=variant;save(t+'_'+v+'_normal',scenes[0])
    for theme in TARGETS:
        renderer.theme=theme;renderer.variant=2;t=THEMES[theme]
        for scene in scenes[1:]:save(t+'_c_'+scene.name,scene)
        renderer.compare=True
        for scene in scenes:save('before_'+t+'_'+scene.name,scene)
        renderer.compare=False
        for mode in (0,2):
            renderer.mode=mode;save(t+'_mode_'+str(mode)+'_pulse',scenes[5])
        renderer.mode=1
    if before!=[snapshot(scene) for scene in scenes]:raise AssertionError('Review changed combat')
    compose_reviews(out)
    used=['tools/front_crest_fine_review.py','assets/side_cleanup/asset_manifest.json']
    used+=['assets/side_cleanup/'+t+'_panel.png' for t in THEMES[1:]]
    (out/'review_manifest.json').write_text(json.dumps(dict(status='R6c local finishing pending design approval',
        camera=CAMERA.corners,region=FRONT_REGION,targets=TARGETS,recommended=dict(variant=2,mode=1),
        textures_loaded=len(renderer.images),scenes=before,captures=records,
        input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in used}),indent=2)+'\n')
    print('Captured 61 scenes + 2 sheets + 8 front/top crops; R6b files retained')


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=FineRenderer(c,args.assets)
        scenes=[make_scene(n) for n in SCENARIOS]+[pulse_phase(t) for t in (10,60,110)]+[parry_window_scene(),resolved_pulse_scene()]
        before=[snapshot(s) for s in scenes]
        if args.capture_dir:return capture(c,renderer,settings,menu,display,args,scenes)
        active=0;phase=0;grid=False;probe=None;running=True
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
                        elif e.key in keys:active=keys.index(e.key)
                        elif e.key==c.SDLK_l:active=6+phase;phase=(phase+1)%3
                        elif e.key==c.SDLK_r:active=9
                        elif e.key==c.SDLK_t:active=10
                        elif e.key==c.SDLK_g:grid=not grid
                        elif e.key==c.SDLK_b:renderer.compare=not renderer.compare
                elif e.type==c.SDL_MOUSEBUTTONDOWN and e.button==c.SDL_BUTTON_LEFT:
                    point=logical_mouse_to_canvas(e.x,e.y);opened=menu.is_open;action=menu.click(point)
                    if action=='toggle_fullscreen':display.toggle()
                    elif not opened and not menu.is_open and point is not None:probe=CAMERA.pick(*point)
            renderer.draw(scenes[active],grid=grid,probe=probe);settings.draw(menu,display);c.update_canvas();sleep(1/180)
        if before!=[snapshot(s) for s in scenes]:raise AssertionError('Review changed combat')
    finally:
        if settings is not None:settings.close()
        if renderer is not None:renderer.close()
        c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,default=ASSETS)
    parser.add_argument('--capture-dir',type=Path)
    run(parser.parse_args())
