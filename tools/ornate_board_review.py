"""Decorated B+12 board and truthful, optional perimeter cues. Frozen review only.

1..5 theme, 6..8 variant, 9 recommended C/Mode1, Q/W/E cue0/1/2,
A/S/D/F/H/P scene, L real Pulse phase, R active parry window,
G grid, B prior Q board, F11/ESC.
"""
import argparse
import ctypes
from dataclasses import asdict,dataclass
import hashlib
import json
from math import cos,pi
from pathlib import Path
import sys
from time import sleep

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.themed_arena_review import ThemedRenderer,THEMES,LABELS,SIZE_CAMERAS,review_text
from tools.stage5_camera_review import CameraRenderer,polygon,outline
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS,open_preview,capture_png
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from health_renderer import HealthRenderer

ASSETS=ROOT/'assets/ornate_board'
CAMERA=SIZE_CAMERAS[2]


@dataclass(frozen=True)
class FrameCue:
    kind: str
    ready: bool
    active_window: bool
    progress: float=0.0


def cue_for(scene):
    """Read authentic clock/result/ledger only. Never request/consume an action."""
    g=scene.game;t=g.combat.tick
    if not g.playing or not g.player.health.alive:return FrameCue('quiet',False,False)
    active=g.parry.active_at(t);ready=t>=g.parry.next_parry_tick and not active
    result=g.resolver.last_parry_result
    if result and result.successful and 0<=t-result.tick<18:
        return FrameCue('perfect_success' if result.status=='perfect' else 'parry_success',ready,active)
    events=[r.event for r in g.encounter.ledger._records.values() if r.state=='telegraph']
    pulse=next((e for e in events if e.attack_kind=='king_pulse'),None)
    if pulse is not None:return FrameCue('pulse',ready,active,max(0,min(1,(t-pulse.start_tick)/(pulse.hit_tick-pulse.start_tick))))
    if active:return FrameCue('parry_window',False,True)
    if events:return FrameCue('danger',ready,False)
    if scene.player_attack is not None:return FrameCue('player_attack',ready,False)
    return FrameCue('ready' if ready else 'quiet',ready,False)


def pulse_phase(offset):
    import main
    from tools.stage5_art_preview import Scene
    g=main._new_stage_game(5)
    while g.encounter.pulse.event is None and g.playing and g.combat.tick<900:g.advance()
    if g.encounter.pulse.event is None:raise RuntimeError('No genuine Pulse')
    g.advance(offset)
    return Scene('pulse_phase_'+str(offset),g)


def parry_window_scene():
    scene=make_scene('enemy_warning');scene.name='parry_window'
    g=scene.game;event=next(e.current_attack for e in g.encounter.enemies if e.kind=='rook')
    g.advance(event.hit_tick-18-g.combat.tick)
    g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(2)
    return scene


def rail(side,t,offset):
    return ((t*10,-offset),(10+offset,t*10),((1-t)*10,10+offset),(-offset,(1-t)*10))[side]


def prepare(directory):
    """Transparent PNG alpha crop/pad/resize only; retain generated originals."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_Load,IMG_SavePNG,IMG_INIT_PNG
    from tools.prepare_stage5_art import alpha_bounds
    if s.SDL_Init(s.SDL_INIT_VIDEO)!=0:raise RuntimeError('SDL init failed')
    records=[]
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG:raise RuntimeError('PNG init failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        for name in THEMES:
            source=directory/'source'/(name+'.png');loaded=IMG_Load(str(source).encode('utf-8'))
            if not loaded:raise FileNotFoundError(source)
            src=s.SDL_ConvertSurfaceFormat(loaded,s.SDL_PIXELFORMAT_RGBA32,0);s.SDL_FreeSurface(loaded)
            if not src:raise RuntimeError('RGBA conversion failed')
            target=renderer=tex=None
            try:
                (l,t,r,b),clear=alpha_bounds(src)
                if not clear:raise ValueError('Expected transparent medallion')
                target=s.SDL_CreateRGBSurfaceWithFormat(0,256,256,32,s.SDL_PIXELFORMAT_RGBA32)
                if not target:raise RuntimeError('Surface failed')
                renderer=s.SDL_CreateSoftwareRenderer(target)
                if not renderer:raise RuntimeError('Renderer failed')
                tex=s.SDL_CreateTextureFromSurface(renderer,src)
                if not tex:raise RuntimeError('Texture failed')
                ratio=220/max(r-l,b-t);w,h=round((r-l)*ratio),round((b-t)*ratio)
                a=s.SDL_Rect(l,t,r-l,b-t);d=s.SDL_Rect((256-w)//2,(256-h)//2,w,h)
                s.SDL_SetTextureBlendMode(tex,s.SDL_BLENDMODE_NONE)
                s.SDL_SetRenderDrawColor(renderer,0,0,0,0);s.SDL_RenderClear(renderer)
                if s.SDL_RenderCopy(renderer,tex,ctypes.byref(a),ctypes.byref(d))!=0:raise RuntimeError('Resize failed')
                s.SDL_RenderPresent(renderer);dest=directory/(name+'.png')
                if IMG_SavePNG(target,str(dest).encode('utf-8'))!=0:raise RuntimeError('PNG save failed')
                bbox,clear=alpha_bounds(target)
                records.append(dict(name=name,size=[256,256],alpha_bbox=bbox,transparent_pixels=clear,
                    source_size=[src.contents.w,src.contents.h],sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
            finally:
                if tex:s.SDL_DestroyTexture(tex)
                if renderer:s.SDL_DestroyRenderer(renderer)
                if target:s.SDL_FreeSurface(target)
                s.SDL_FreeSurface(src)
    finally:IMG_Quit();s.SDL_Quit()
    (directory/'asset_manifest.json').write_text(json.dumps(dict(status='Decorative hardware drafts',assets=records),indent=2)+'\n')


class OrnateRenderer(ThemedRenderer):
    variant=2
    mode=1
    cue=FrameCue('quiet',False,False)

    def __init__(self,c,assets=ASSETS):
        super().__init__(c)
        self.decor_segments=[];self.cue_segments=[];self.decor_quads=[]
        try:
            for name in THEMES:
                p=assets/(name+'.png')
                if not p.is_file():raise FileNotFoundError(p)
                self.images['seal_'+name]=c.load_image(str(p))
        except Exception:self.close();raise

    def line(self,cam,a,b,color,*,cue=False):
        (self.cue_segments if cue else self.decor_segments).append((a,b))
        self.c.draw_line(*cam.project(*a),*cam.project(*b),*color)

    def board(self,cam,grid):
        self.decor_segments=[];self.cue_segments=[];self.decor_quads=[]
        if self.compare:
            self.compare=False
            try:super().board(cam,grid)
            finally:self.compare=True
            return
        super().board(cam,grid)
        c=self.c
        accents=((191,158,92),(135,151,98),(173,201,214),(182,126,85),(158,139,163))
        bright=accents[self.theme];dark=tuple(round(v*.39) for v in bright)
        # Empty/recessed outer lane in C; all rails stay strictly outside tiles.
        for side in range(4):
            for off,col in ((.035,dark),(.055,bright),(.235,dark),(.30,bright)):
                self.line(cam,rail(side,0,off),rail(side,1,off),col)
            if self.variant==2:
                for off in (.255,.27,.285):self.line(cam,rail(side,0,off),rail(side,1,off),(35,38,43))
            count=8 if self.variant==0 else 24
            for i in range(count):
                t=(i+.5)/count
                a,b,m=rail(side,t-.009,.13),rail(side,t+.009,.13),rail(side,t,.20)
                lo=rail(side,t,.07)
                if self.variant==0:
                    self.line(cam,a,m,bright);self.line(cam,m,b,bright)
                elif self.theme==1:  # paired leaf vein with winding root stem
                    self.line(cam,a,m,bright);self.line(cam,m,b,bright)
                    self.line(cam,b,lo,dark);self.line(cam,lo,a,bright)
                    self.line(cam,lo,m,bright)
                elif self.theme==2:  # crystalline chevrons
                    for p,q in ((a,m),(m,b),(a,lo),(lo,b),(lo,m)):self.line(cam,p,q,bright)
                elif self.theme==3:  # riveted angular crack, subdued copper
                    self.line(cam,a,lo,bright);self.line(cam,lo,m,dark);self.line(cam,m,b,bright)
                    x,y=cam.project(*rail(side,t,.22));c.draw_circle(x,y,1,*bright,filled=True)
                elif self.theme==4:  # pointed Gothic arches
                    for p,q in ((rail(side,t-.012,.06),a),(a,m),(m,b),(b,rail(side,t+.012,.06))):self.line(cam,p,q,bright)
                else:
                    for p,q in ((a,m),(m,b),(b,lo),(lo,a)):self.line(cam,p,q,bright)
                    self.line(cam,rail(side,t-.018,.10),rail(side,t+.018,.10),dark)
        # Four top corner mounts are textured quads completely outside 100 cells.
        for u,v in ((-.165,-.165),(10.165,-.165),(10.165,10.165),(-.165,10.165)):
            half=.14
            quad=((u-half,v-half),(u+half,v-half),(u+half,v+half),(u-half,v+half))
            self.decor_quads.append(quad)
            polygon(c,tuple(cam.project(*p) for p in quad),texture=self.images['seal_'+THEMES[self.theme]].texture)
        # Front face recessed relief panels; never draw rear extrusions over tiles.
        if self.variant:
            for i in range(10):
                a=cam.project(i+.15,-.23);b=cam.project(i+.85,-.23)
                q=((a[0],a[1]-12),(b[0],b[1]-12),(b[0],b[1]-31),(a[0],a[1]-31))
                polygon(c,q,(*dark,255));outline(c,q,bright)
                # Chamfered inset and a raised central carving read as relief,
                # rather than a painted rectangle on the front fascia.
                c.draw_line(a[0]+2,a[1]-14,b[0]-2,b[1]-14,*dark)
                c.draw_line(a[0]+2,a[1]-29,b[0]-2,b[1]-29,*bright)
                mx=(a[0]+b[0])/2;my=(a[1]+b[1])/2-21
                outline(c,((mx-9,my),(mx,my+5),(mx+9,my),(mx,my-5)),bright)
            for u in (2.5,7.5):
                px,py=cam.project(u,-.12)
                self.images['seal_'+THEMES[self.theme]].draw(px,py-24,24,24)
        x,y=cam.project(5,-.12);size=32 if self.variant==0 else 44
        self.images['seal_'+THEMES[self.theme]].draw(x,y-24,size,size)
        self.draw_cue(cam)

    def draw_cue(self,cam):
        if self.mode==0:return
        kind=self.cue.kind
        colors={'quiet':(80,84,91),'ready':(92,154,181),'player_attack':(182,164,119),
            'danger':(173,83,99),'parry_window':(126,198,221),'parry_success':(117,199,225),
            'perfect_success':(244,218,145),'pulse':(195,139,78)}
        color=colors[kind]
        if self.mode==1:color=tuple(round(v*.75) for v in color)
        if kind=='quiet':return
        if kind=='ready':
            for side in (0,2):self.line(cam,rail(side,.46,.275),rail(side,.54,.275),color,cue=True)
            return
        for side in range(4):
            if kind in ('parry_success','parry_window','player_attack'):
                intervals=((.14,.32),(.68,.86))
            elif kind=='danger':intervals=((.05,.18),(.30,.43),(.57,.70),(.82,.95))
            else:intervals=((.025,.975),)
            for start,end in intervals:
                self.line(cam,rail(side,start,.27),rail(side,end,.27),color,cue=True)
                if self.mode==2:self.line(cam,rail(side,start,.29),rail(side,end,.29),color,cue=True)
        if kind=='perfect_success':
            for side in range(4):
                for t in (.03,.97):self.line(cam,rail(side,t-.02,.23),rail(side,t+.02,.30),color,cue=True)
        if kind=='pulse':
            # Event progress controls the perimeter runner; no new combat clock.
            side=min(3,int(self.cue.progress*4));t=(self.cue.progress*4)%1
            strength=.65+.35*(1-cos(self.cue.progress*2*pi))/2
            hot=tuple(round(min(255,v*strength+30)) for v in color)
            self.line(cam,rail(side,max(.02,t-.10),.26),rail(side,min(.98,t+.10),.26),hot,cue=True)

    def draw(self,scene,cam=CAMERA,**kwargs):
        self.cue=cue_for(scene)
        CameraRenderer.draw(self,scene,CAMERA,**kwargs)

    def controls(self,scene,cam,probe,roster):
        c=self.c;c.draw_rectangle(25,290,278,505,12,18,26,filled=True)
        rows=((LABELS[self.theme],480),('PRIOR Q BOARD' if self.compare else 'VARIANT '+'ABC'[self.variant]+' MODE '+str(self.mode),458),
            ('1 TO 5 THEME  6 TO 8 ART',435),('Q W E CUES  9 BEST',413),('A S D F H P SCENE',391),
            ('G GRID B PRIOR L R EXTRA',369),('F11 DISPLAY  ESC EXIT',347),('FRAME CUE ONLY',325))
        for label,y in rows:review_text(c,label,30,y,scale=2)
        review_text(c,self.cue.kind.upper().replace('_',' '),30,304,scale=2)
        result=scene.game.resolver.last_parry_result
        if result and result.successful and 0<=scene.game.combat.tick-result.tick<18:
            c.draw_rectangle(25,508,278,529,12,18,26,filled=True)
            HealthRenderer._text(c,'PERFECT PARRY' if result.status=='perfect' else 'PARRY SUCCESS',30,514,scale=2,
                                 color=(255,221,113) if result.status=='perfect' else (112,207,246))


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.renderer or not c.window:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=OrnateRenderer(c,args.assets)
        scenes=[make_scene(n) for n in SCENARIOS]
        phases=[pulse_phase(t) for t in (10,60,110)]
        window=parry_window_scene()
        before=[snapshot(s) for s in scenes+phases+[window]]
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
            def save(name,scene):
                renderer.draw(scene);settings.draw(menu,display);capture_png(c,out/(name+'.png'));c.update_canvas()
                records.append(dict(file=name+'.png',theme=renderer.theme,variant=renderer.variant,mode=renderer.mode,
                    cue=asdict(renderer.cue),warning_cells=renderer.warning_cells,bounds=renderer.bounds,
                    decor_segments=renderer.decor_segments,cue_segments=renderer.cue_segments,decor_quads=renderer.decor_quads))
            for variant in range(3):
                renderer.variant=variant;renderer.mode=0
                save('royal_variant_'+'ABC'[variant],scenes[0])
            renderer.variant=2
            for mode in range(3):
                renderer.mode=mode
                for scene in scenes:save('royal_mode_'+str(mode)+'_'+scene.name,scene)
            for mode in (1,2):
                renderer.mode=mode;save('royal_window_mode_'+str(mode),window)
            renderer.mode=1
            for theme,name in enumerate(THEMES):
                renderer.theme=theme
                for scene in (scenes[0],scenes[-1]):save(name+'_recommended_'+scene.name,scene)
            renderer.theme=0;renderer.mode=2
            for scene in phases:save(scene.name,scene)
            renderer.compare=True;save('prior_Q',scenes[0])
            assert before==[snapshot(s) for s in scenes+phases+[window]]
            (out/'review_manifest.json').write_text(json.dumps(dict(status='Ornate board review pending approval',
                size=[1440,900],camera=CAMERA.corners,recommended=dict(variant=2,mode=1),textures_loaded=len(renderer.images),
                scenes=before,captures=records),indent=2)+'\n')
            print('Captured 37 ornament/cue/theme/real input and Pulse phase PNGs; combat unchanged');return
        active=0;grid=False;probe=None;phase=None;phase_index=0;running=True
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
                        elif e.key in (c.SDLK_a,c.SDLK_s,c.SDLK_d,c.SDLK_f,c.SDLK_h,c.SDLK_p):
                            active=(c.SDLK_a,c.SDLK_s,c.SDLK_d,c.SDLK_f,c.SDLK_h,c.SDLK_p).index(e.key);phase=None
                        elif e.key==c.SDLK_l:phase=phases[phase_index];phase_index=(phase_index+1)%3
                        elif e.key==c.SDLK_r:phase=window
                        elif e.key==c.SDLK_g:grid=not grid
                        elif e.key==c.SDLK_b:renderer.compare=not renderer.compare
                elif e.type==c.SDL_MOUSEBUTTONDOWN and e.button==c.SDL_BUTTON_LEFT:
                    point=logical_mouse_to_canvas(e.x,e.y);opened=menu.is_open;action=menu.click(point)
                    if action=='toggle_fullscreen':display.toggle()
                    elif not opened and not menu.is_open and point is not None:probe=CAMERA.pick(*point)
            renderer.draw(phase if phase is not None else scenes[active],grid=grid,probe=probe)
            settings.draw(menu,display);c.update_canvas();sleep(1/180)
        assert before==[snapshot(s) for s in scenes+phases+[window]]
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
