"""R5 measured frame registration. Frozen review, no live-game changes.

1..5 theme, 6..8 Fix A/B/C, 9 C/Mode1, Q/W/E cues,
A/S/D/F/H/P scenes, B original R4-C, G grid, L/R/T Pulse/input/resolution,
F11/SETTINGS, ESC exit.
"""
import argparse
import ctypes
from dataclasses import asdict
import hashlib
import json
from math import atan2,cos,sin,hypot
from pathlib import Path
import statistics
import sys
from time import sleep

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.arena_projection import ArenaCamera
from tools.polished_board_review import PolishedRenderer
from tools.ornate_board_review import CAMERA,pulse_phase,parry_window_scene
from tools.highend_board_review import resolved_pulse_scene
from tools.themed_arena_review import THEMES,LABELS,review_text
from tools.stage5_camera_review import polygon,outline
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS,open_preview,capture_png
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from board import is_light_tile

ASSETS=ROOT/'assets/aligned_board'
PROFILES=('A PROJECTION','B MITERED SEAT','C CORNER ALIGN')


def fit_line(points):
    """Robust least-squares y=a*x+b, rejecting isolated ornaments."""
    current=list(points)
    for _ in range(3):
        mx=statistics.mean(x for x,y in current);my=statistics.mean(y for x,y in current)
        a=sum((x-mx)*(y-my) for x,y in current)/sum((x-mx)**2 for x,y in current);b=my-a*mx
        errors=[abs(y-a*x-b) for x,y in current]
        threshold=max(2,statistics.median(errors)*3)
        kept=[p for p in current if abs(p[1]-a*p[0]-b)<=threshold]
        if len(kept)<6 or kept==current:break
        current=kept
    return a,b,current,max(abs(y-a*x-b) for x,y in current)


def survey_frame(path):
    """Measure the actual dark empty opening in the existing R4 PNG."""
    import sdl2 as s
    from sdl2.sdlimage import IMG_Load
    image=IMG_Load(str(path).encode('utf-8'))
    if not image:raise FileNotFoundError(path)
    rgba=s.SDL_ConvertSurfaceFormat(image,s.SDL_PIXELFORMAT_RGBA32,0);s.SDL_FreeSurface(image)
    if not rgba:raise RuntimeError('RGBA conversion failed')
    try:
        pitch=rgba.contents.pitch;data=ctypes.string_at(rgba.contents.pixels,pitch*900)
    finally:s.SDL_FreeSurface(rgba)
    def dark(x,y):
        k=y*pitch+x*4;r,g,b,a=data[k:k+4]
        return a>220 and max(r,g,b)<80 and max(r,g,b)-min(r,g,b)<18
    left=[];right=[];top=[];bottom=[]
    for y in range(230,641,15):
        l=r=735
        if not dark(l,y):continue
        while l>0 and dark(l,y):l-=1
        while r<1439 and dark(r,y):r+=1
        left.append((y,l+.5));right.append((y,r-.5))
    for x in tuple(range(470,621,15))+tuple(range(850,1001,15)):
        t=b=420
        if not dark(x,t):continue
        while t>0 and dark(x,t):t-=1
        while b<899 and dark(x,b):b+=1
        top.append((x,t+.5));bottom.append((x,b-.5))
    lines=[fit_line(p) for p in (left,right,top,bottom)]
    if any(len(v[2])<6 or v[3]>3 for v in lines):raise ValueError('Opening edge survey requires review: '+str(path))
    def intersect(vertical,horizontal):
        av,bv=vertical[:2];ah,bh=horizontal[:2]
        y=(ah*bv+bh)/(1-ah*av);return av*y+bv,899-y
    quad=(intersect(lines[0],lines[3]),intersect(lines[1],lines[3]),
          intersect(lines[1],lines[2]),intersect(lines[0],lines[2]))
    source=ArenaCamera('MEASURED R4',quad,0,1)
    return source,dict(corners=quad,lines=[dict(a=a,b=b,points=p,max_residual=e) for a,b,p,e in lines]),data,pitch


def edge_angles(source):
    # Front/right/back/left; both cameras use the same winding.
    angles=[]
    for i in range(4):
        a,b=source.corners[i],source.corners[(i+1)%4]
        p,q=CAMERA.corners[i],CAMERA.corners[(i+1)%4]
        angles.append(atan2(q[1]-p[1],q[0]-p[0])-atan2(b[1]-a[1],b[0]-a[0]))
    # Small registration angles; unwrap the +/-pi discontinuity.
    return tuple(atan2(sin(t),cos(t)) for t in angles)


def registered_point(source,x,y,variant,gain):
    """Exact boundary registration, exterior-only uniform size compensation.

    A: projective baseline; B: translated offsets (rigid corner quadrants);
    C: offsets rotate with the edge, smoothly meeting rigid corner rotations.
    """
    u,v=source.inverse(x,y);cu=max(0,min(10,u));cv=max(0,min(10,v))
    target=CAMERA.project(cu,cv)
    if 0<=u<=10 and 0<=v<=10:return CAMERA.project(u,v)
    anchor=source.project(cu,cv)
    if variant==0:
        p=CAMERA.project(u,v);dx,dy=p[0]-target[0],p[1]-target[1]
    else:
        dx,dy=x-anchor[0],y-anchor[1]
        if variant==2:
            angles=edge_angles(source)
            corners=tuple((angles[i-1]+angles[i])/2 for i in range(4))
            if u<0 and v<0:theta=corners[0]
            elif u>10 and v<0:theta=corners[1]
            elif u>10 and v>10:theta=corners[2]
            elif u<0 and v>10:theta=corners[3]
            else:
                side,t=(0,cu/10) if v<0 else (1,cv/10) if u>10 else (2,1-cu/10) if v>10 else (3,1-cv/10)
                edge=angles[side]
                near=min(1,t*5);near=near*near*(3-2*near)
                far=min(1,(1-t)*5);far=far*far*(3-2*far)
                theta=edge+(corners[side]-edge)*(1-near)+(corners[(side+1)%4]-edge)*(1-far)
            dx,dy=dx*cos(theta)-dy*sin(theta),dx*sin(theta)+dy*cos(theta)
    return target[0]+gain*dx,target[1]+gain*dy


def exterior_gain(source,data,pitch):
    # One scalar per theme, shared by A/B/C. Keep the entire nontrivial alpha
    # silhouette in the viewport; never squeeze just the vertical direction.
    gain=.97
    for py in range(0,900,8):
        for px in range(0,1440,8):
            if data[py*pitch+px*4+3]<24:continue
            x,y=px,899-py;u,v=source.inverse(x,y)
            if 0<=u<=10 and 0<=v<=10:continue
            anchor=CAMERA.project(max(0,min(10,u)),max(0,min(10,v)))
            for variant in range(3):
                p=registered_point(source,x,y,variant,1)
                for a,b,low,high in zip(anchor,p,(16,16),(1424,884)):
                    delta=b-a
                    if delta>0:gain=min(gain,(high-a)/delta)
                    elif delta<0:gain=min(gain,(low-a)/delta)
    if not .45<gain<=1:raise ValueError('Exterior cannot fit naturally: '+str(gain))
    return gain*.985


def clip_polygon(points):
    """Clip source geometry, leaving texture UVs within native SDL bounds."""
    result=list(points)
    for axis,bound,greater in ((0,0,True),(0,1440,False),(1,0,True),(1,900,False)):
        old=result;result=[]
        if not old:break
        for p,q in zip(old,old[1:]+old[:1]):
            pin=p[axis]>=bound if greater else p[axis]<=bound
            qin=q[axis]>=bound if greater else q[axis]<=bound
            if pin:result.append(p)
            if pin!=qin:
                t=(bound-p[axis])/(q[axis]-p[axis]);result.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
    return result


def prepare(directory):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_Load,IMG_SavePNG,IMG_INIT_PNG
    from tools.prepare_stage5_art import alpha_bounds
    directory.mkdir(parents=True,exist_ok=True);records=[]
    s.SDL_Init(0);IMG_Init(IMG_INIT_PNG)
    try:
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        for theme in THEMES:
            path=ROOT/'assets/polished_board'/(theme+'_frame.png')
            source,survey,data,pitch=survey_frame(path);gain=exterior_gain(source,data,pitch)
            # The parametric mesh includes 0/10 exactly. No triangle straddles
            # the opening, so its four rendered edges are exact straight lines.
            values=[-6+i*.25 for i in range(89)]
            patches=[]
            for u,un in zip(values,values[1:]):
                for v,vn in zip(values,values[1:]):
                    if 0<=u and un<=10 and 0<=v and vn<=10:continue
                    q=[(p[0],899-p[1]) for p in (source.project(u,v),source.project(un,v),source.project(un,vn),source.project(u,vn))]
                    p=clip_polygon(q)
                    if len(p)>=3:patches.append(p)
            loaded=IMG_Load(str(path).encode('utf-8'))
            if not loaded:raise FileNotFoundError(path)
            try:
                for variant in range(3):
                    target=s.SDL_CreateRGBSurfaceWithFormat(0,1440,900,32,s.SDL_PIXELFORMAT_RGBA32)
                    if not target:raise RuntimeError('Surface failed')
                    renderer=texture=None
                    try:
                        renderer=s.SDL_CreateSoftwareRenderer(target)
                        if not renderer:raise RuntimeError('Renderer failed')
                        texture=s.SDL_CreateTextureFromSurface(renderer,loaded)
                        if not texture:raise RuntimeError('Texture failed')
                        s.SDL_SetTextureBlendMode(texture,s.SDL_BLENDMODE_NONE)
                        s.SDL_SetRenderDrawColor(renderer,0,0,0,0);s.SDL_RenderClear(renderer)
                        verts=[];indices=[]
                        for p in patches:
                            start=len(verts)
                            for x,y in p:
                                dx,dy=registered_point(source,x,899-y,variant,gain)
                                verts.append((dx,899-dy,x/1440,y/900))
                            for i in range(1,len(p)-1):indices.extend((start,start+i,start+i+1))
                        vertices=(s.SDL_Vertex*len(verts))()
                        for i,(x,y,u,v) in enumerate(verts):
                            vertices[i].position=s.SDL_FPoint(x,y);vertices[i].color=s.SDL_Color(255,255,255,255)
                            vertices[i].tex_coord=s.SDL_FPoint(max(0,min(1,u)),max(0,min(1,v)))
                        ix=(ctypes.c_int*len(indices))(*indices)
                        if s.SDL_RenderGeometry(renderer,texture,vertices,len(vertices),ix,len(indices))!=0:raise RuntimeError(s.SDL_GetError().decode())
                        s.SDL_RenderPresent(renderer);name=f'{theme}_{"abc"[variant]}';dest=directory/(name+'.png')
                        if IMG_SavePNG(target,str(dest).encode('utf-8'))!=0:raise RuntimeError('Save failed')
                        bounds,clear=alpha_bounds(target)
                        records.append(dict(name=name,size=[1440,900],source=path.relative_to(ROOT).as_posix(),
                            source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                            survey=survey,target_opening=CAMERA.corners,exterior_uniform_gain=gain,alpha_bounds=bounds,transparent_pixels=clear))
                    finally:
                        if texture:s.SDL_DestroyTexture(texture)
                        if renderer:s.SDL_DestroyRenderer(renderer)
                        s.SDL_FreeSurface(target)
            finally:s.SDL_FreeSurface(loaded)
    finally:IMG_Quit();s.SDL_Quit()
    (directory/'asset_manifest.json').write_text(json.dumps(dict(status='R5 measured registration review pending approval',assets=records),indent=2)+'\n')


class AlignedRenderer(PolishedRenderer):
    def __init__(self,c,assets=ASSETS):
        super().__init__(c)
        self.rim_quads=[]
        try:
            self.aligned_records={r['name']:r for r in json.loads((assets/'asset_manifest.json').read_text())['assets']}
            for theme in THEMES:
                for v in 'abc':
                    path=assets/(theme+'_'+v+'.png')
                    if not path.is_file():raise FileNotFoundError(path)
                    self.images['align_'+theme+'_'+v]=c.load_image(str(path))
        except Exception:self.close();raise

    def board(self,cam,grid):
        self.decor_segments=[];self.cue_segments=[];self.decor_quads=[];self.tile_quads=[];self.rim_quads=[]
        if self.compare:
            variant=self.variant;self.compare=False
            try:self.variant=2;super().board(cam,grid)
            finally:self.variant=variant;self.compare=True
            return
        c=self.c;theme=THEMES[self.theme]
        self.images['arena_'+theme].draw(720,450,1440,900)
        self.images['align_'+theme+'_'+'abc'[self.variant]].draw(720,450,1440,900)
        # All sides have a fixed width in the SAME logical projection. There
        # is no aperture-sized cover rectangle or independently widened rear.
        pad=(.16,.10,.12)[self.variant]
        outer=((-pad,-pad),(10+pad,-pad),(10+pad,10+pad),(-pad,10+pad))
        inner=((0,0),(10,0),(10,10),(0,10))
        levels=(0,1) if self.variant==0 else (0,.18,.82,1)
        for n,(lo,hi) in enumerate(zip(levels,levels[1:])):
            def lerp(t):return tuple((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for a,b in zip(outer,inner))
            a,b=lerp(lo),lerp(hi)
            for side in range(4):
                nxt=(side+1)%4;quad=(a[side],a[nxt],b[nxt],b[side]);self.rim_quads.append(quad)
                gain=(1,) if self.variant==0 else (.76,1,1.10)
                value=min(255,round(200*gain[n]*(1.05 if side in (2,3) else .94)))
                polygon(c,tuple(cam.project(*p) for p in quad),(value,value,value,255),texture=self.images['polish_'+theme+'_light'].texture)
        for col in range(10):
            for row in range(10):
                pts=cam.tile(col,row);self.tile_quads.append(pts)
                key='polish_'+theme+('_light' if is_light_tile(col,row) else '_dark')
                polygon(c,pts,texture=self.images[key].texture)
                if grid:outline(c,pts,(113,121,126))
        # R4-C's internal tile picture is unchanged; only exterior joints move.
        from tools.polished_board_review import TONES
        outline(c,cam.corners,tuple(round(v*.72) for v in TONES[self.theme]))
        self.draw_cue(cam)

    def controls(self,scene,cam,probe,roster):
        c=self.c;c.draw_rectangle(25,290,240,505,12,18,26,filled=True)
        labels=('A PLANAR FIT','B MITER FIT','C FULL ALIGN')
        rows=((LABELS[self.theme],480),('PRIOR R4 C' if self.compare else 'FIX '+labels[self.variant],458),
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
    compose('fix_comparison_sheet.png',(1440,1500),[(theme+'_'+v+'_normal.png',None,(i*480,j*300,480,300))
        for j,theme in enumerate(THEMES) for i,v in enumerate('abc')])
    corners=((320,95,220,180),(1000,95,220,180),(205,705,220,180),(1075,705,220,180))
    for theme in THEMES:
        for label,source in (('before','prior_R4_'+theme+'_normal.png'),('after',theme+'_c_normal.png')):
            compose(theme+'_corners_'+label+'.png',(880,720),[(source,rect,((i%2)*440,(i//2)*360,440,360)) for i,rect in enumerate(corners)])
            compose(theme+'_rear_'+label+'.png',(1300,180),[(source,(410,125,650,90),(0,0,1300,180))])


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise RuntimeError('SDL preview unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=AlignedRenderer(c,args.assets)
        scenes=[make_scene(n) for n in SCENARIOS];phases=[pulse_phase(t) for t in (10,60,110)]
        window=parry_window_scene();resolved=resolved_pulse_scene();all_scenes=scenes+phases+[window,resolved]
        before=[snapshot(s) for s in all_scenes]
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
            def save(name,scene):
                renderer.draw(scene);settings.draw(menu,display);capture_png(c,out/(name+'.png'));c.update_canvas()
                records.append(dict(file=name+'.png',scenario=scene.name,theme=renderer.theme,variant=renderer.variant,mode=renderer.mode,
                    compare=renderer.compare,cue=asdict(renderer.cue),warning_cells=renderer.warning_cells,bounds=renderer.bounds,
                    cue_segments=renderer.cue_segments,rim_quads=renderer.rim_quads,tile_quads=renderer.tile_quads))
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
                renderer.theme=theme;save('prior_R4_'+name+'_normal',scenes[0])
            renderer.theme=0;save('prior_R4_pulse',scenes[-1])
            assert before==[snapshot(s) for s in all_scenes]
            review_extras(out)
            (out/'review_manifest.json').write_text(json.dumps(dict(status='R5 alignment review pending approval',
                size=[1440,900],camera=CAMERA.corners,textures_loaded=len(renderer.images),recommended=dict(variant=2,mode=1),
                scenes=before,captures=records,comparison_sheet='fix_comparison_sheet.png'),indent=2)+'\n')
            print('Captured 55 scenes + fix sheet + 20 corner/rear comparisons; combat unchanged');return
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
