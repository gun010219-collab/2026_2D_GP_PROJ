"""A/B/C projected arena prototype, read-only frozen Stage5 combat snapshots.

1/2/3 camera, 4..9 scene, G grid, B old screen, F11 fullscreen,
T six-piece compatibility study, mouse tile probe, SETTINGS, ESC exit.
"""
import argparse
import ctypes
import gc
import json
from pathlib import Path
import sys
from time import sleep
from math import cos,sin,pi

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.arena_projection import CAMERAS
from tools.stage5_art_preview import make_scene,snapshot,SCENARIOS,open_preview,capture_png,SampleRenderer
from tools.character_art_review import SIZES
from health_renderer import HealthRenderer
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from board import is_light_tile

OUT=ROOT/'assets/camera_review'


def polygon(c,points,color=(255,255,255,255),texture=None):
    """Native SDL textured geometry, each board tile separately projected."""
    import sdl2 as s
    vertices=(s.SDL_Vertex*len(points))()
    uv=((0,1),(1,1),(1,0),(0,0))
    for i,(x,y) in enumerate(points):
        vertices[i].position=s.SDL_FPoint(x,899-y)
        vertices[i].color=s.SDL_Color(*color)
        vertices[i].tex_coord=s.SDL_FPoint(*uv[i%4])
    indices=[]
    for i in range(1,len(points)-1):indices.extend((0,i,i+1))
    arr=(ctypes.c_int*len(indices))(*indices)
    if s.SDL_RenderGeometry(c.renderer,texture,vertices,len(points),arr,len(indices))!=0:
        raise RuntimeError('SDL geometry unavailable: '+s.SDL_GetError().decode())


def outline(c,points,color):
    for a,b in zip(points,points[1:]+points[:1]):c.draw_line(*a,*b,*color)


class CameraRenderer:
    def __init__(self,c):
        self.c=c;self.images={};self.original=SampleRenderer(c)
        self.bounds=[];self.order=[];self.warning_cells=[]
        paths={k:ROOT/'assets/character_concepts'/(('player' if k=='player' else 'ch1_'+k)+'.png')
               for k in ('player','pawn','rook','king','knight','bishop','queen')}
        paths.update({k:ROOT/'assets/art_samples/stage5_r2'/(k+'.png') for k in ('tile_light','tile_dark','background')})
        try:
            for k,p in paths.items():self.images[k]=c.load_image(str(p))
        except Exception:self.close();raise

    def close(self):self.images.clear();gc.collect()

    def board(self,cam,grid):
        c=self.c
        self.images['background'].draw(720,450,1440,900)
        # Royal floor: receding joints and a low-contrast horizon leave a
        # separate architectural layer behind the independent board slab.
        horizon=755
        for y in range(0,horizon,6):
            u=y/horizon;c.draw_rectangle(0,y,1439,y+6,round(13+u*18),round(17+u*16),round(24+u*15),filled=True)
        for x in range(-1800,3300,240):c.draw_line(720+(x-720)*.16,horizon,x,0,49,47,45)
        for y in (45,125,240,390,565,700):
            if y<horizon:c.draw_line(0,y,1439,y,41,42,44)
        top=tuple(cam.project(u,v) for u,v in ((-.18,-.18),(10.18,-.18),(10.18,10.18),(-.18,10.18)))
        for spread,color in ((15,(12,15,20,255)),(7,(7,10,15,255))):
            shadow=tuple((720+(x-720)*(1+spread/600),y-cam.thickness-8) for x,y in top)
            polygon(c,shadow,color)
        for i in (0,1,3):
            j=(i+1)%4;a,b=top[i],top[j]
            polygon(c,(a,b,(b[0],b[1]-cam.thickness),(a[0],a[1]-cam.thickness)),
                    ((67,54,38,255) if i==0 else (31,32,37,255)))
        polygon(c,top,(151,123,74,255));outline(c,top,(220,192,130))
        for col in range(10):
            for row in range(10):
                points=cam.tile(col,row)
                polygon(c,points,texture=self.images['tile_light' if is_light_tile(col,row) else 'tile_dark'].texture)
                if grid:outline(c,points,(114,113,103))
        # Bevel between the metal lip and playable top; no perspective image
        # of an entire screen is ever transformed.
        outline(c,tuple(cam.project(u,v) for u,v in ((0,0),(10,0),(10,10),(0,10))),(18,21,27))

    def mark(self,cam,cell,color,*,hatch=False):
        points=cam.tile(*cell);outline(self.c,points,color)
        if hatch:
            col,row=cell
            for t in (.15,.35,.55,.75):
                a=cam.project(col+t,row+.12);b=cam.project(col+t+.12,row+.24)
                self.c.draw_line(*a,*b,*color)

    def draw(self,scene,cam,*,grid=False,original=False,probe=None,roster=False):
        c=self.c;g=scene.game;self.bounds=[];self.order=[];self.warning_cells=[]
        if original:
            self.original.draw(scene);self.controls(scene,cam,probe,roster);return
        self.board(cam,grid)
        for record in g.encounter.ledger._records.values():
            if record.state!='telegraph':continue
            ev=record.event
            pulse=ev.attack_kind=='king_pulse'
            for cell in ev.target_cells:
                self.warning_cells.append(tuple(cell));self.mark(cam,cell,(241,144,62) if pulse else (239,88,109),hatch=True)
        if scene.player_attack is not None:self.mark(cam,scene.player_attack.target_cell,(237,207,113),hatch=True)
        if probe is not None:self.mark(cam,probe,(100,216,239))
        actors=[(e.kind,e.position,e.health.current_hp,e.health.max_hp,e.data_id) for e in g.encounter.enemies if e.active]
        actors.append(('player',g.player.position,g.player.health.current_hp,g.player.health.max_hp,'player'))
        if roster:
            actors=[(k,(i+2,5),None,None,k) for i,k in enumerate(('pawn','rook','knight','bishop','queen','king'))]
            actors.append(('player',(5,2),None,None,'player'))
        # Smaller screen y is nearer: far actors first, deterministic tie break.
        actors.sort(key=lambda a:(-cam.center(*a[1])[1],cam.center(*a[1])[0],a[4]))
        labels=[]
        for kind,cell,hp,max_hp,key in actors:
            # Near-quarter foot point stays inside its logical cell and leaves
            # room for a rear-row actor's head/HP in the unchanged A viewport.
            x,y=cam.project(cell[0]+.5,cell[1]+.25);depth=cell[1]/10
            height=SIZES[kind]*cam.sprite_scale*(1 if cam is CAMERAS[0] else 1.10-.23*depth)
            # Alpha bottom is 18/256. Keep the foot at the projected cell center.
            center_y=y+height*(.5-18/256)
            foot=tuple((x+4+cos(i*pi/4)*height*.24,y-2+sin(i*pi/4)*4) for i in range(8))
            polygon(c,foot,(24,25,29,255))
            self.images[kind].draw(x,center_y,height,height)
            top=center_y+height*110/256
            self.bounds.append(dict(id=key,cell=cell,box=(x-height/2,y,x+height/2,top),foot=(x,y)))
            self.order.append(key)
            if hp is not None:labels.append((f'{hp}/{max_hp}',x,top+5))
            if kind=='player':
                dx,dy={'up':(0,1),'down':(0,-1),'left':(-1,0),'right':(1,0)}[g.player.facing]
                a=cam.project(cell[0]+.5,cell[1]+.5);b=cam.project(cell[0]+.5+dx*.32,cell[1]+.5+dy*.32)
                c.draw_line(*a,*b,101,201,244)
        # Labels follow sprites so a front actor does not hide a rear HP label.
        for text,x,y in labels:
            width=len(text)*8;c.draw_rectangle(x-width/2-3,y-3,x+width/2+3,y+13,12,19,25,filled=True)
            HealthRenderer._text(c,text,x-width/2,y,scale=2,color=(147,220,166))
        result=g.resolver.last_parry_result
        if not roster and result and result.successful and 0<=g.combat.tick-result.tick<18:
            color=(255,221,113) if result.status=='perfect' else (112,207,246)
            pts=cam.tile(*result.player_cell);outline(c,pts,color)
            if result.status=='perfect':
                x,y=cam.center(*result.player_cell)
                for dx,dy in ((0,1),(1,0),(0,-1),(-1,0)):
                    c.draw_line(x+dx*10,y+dy*10,x+dx*23,y+dy*23,*color)
        self.original.health.draw(c,g.player,(),g.combat.tick,g.combat.pending_attack_bonus)
        self.original.flow.draw_stage_label(c,g)
        self.controls(scene,cam,probe,roster)

    def controls(self,scene,cam,probe,roster):
        self.c.draw_rectangle(25,290,278,505,12,18,26,filled=True)
        for label,y in ((cam.name,480),(scene.name.upper().replace('_',' '),457),
                        ('1 TO 3 CAMERA',425),('4 TO 9 SCENE',403),('G GRID  B OLD',381),
                        ('T CAST  F11 DISPLAY',359),('ESC EXIT',337)):
            HealthRenderer._text(self.c,label,30,y,scale=2)
        result=scene.game.resolver.last_parry_result
        if not roster and result and result.successful and 0<=scene.game.combat.tick-result.tick<18:
            HealthRenderer._text(self.c,'PERFECT PARRY' if result.status=='perfect' else 'PARRY SUCCESS',30,514,scale=2,
                                 color=(255,221,113) if result.status=='perfect' else (112,207,246))
        if roster:HealthRenderer._text(self.c,'CAST STUDY',30,310,scale=2)
        elif probe is not None:HealthRenderer._text(self.c,f'CELL {probe[0]} {probe[1]}',30,310,scale=2)


def run(args):
    from pico2d import pico2d as c
    renderer=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.renderer or not c.window:raise RuntimeError('Preview SDL unavailable')
        c.hide_lattice();display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        renderer=CameraRenderer(c);scenes=[make_scene(n) for n in SCENARIOS]
        before=[snapshot(s) for s in scenes]
        if args.capture_dir:
            out=args.capture_dir;out.mkdir(parents=True,exist_ok=True);records=[]
            for i,cam in enumerate(CAMERAS):
                for scene in scenes:
                    renderer.draw(scene,cam);settings.draw(menu,display)
                    filename=f'{"ABC"[i]}_{scene.name}.png';capture_png(c,out/filename);c.update_canvas()
                    records.append(dict(file=filename,order=renderer.order,bounds=renderer.bounds,warning_cells=renderer.warning_cells))
                renderer.draw(scenes[0],cam,grid=True,roster=True);settings.draw(menu,display)
                capture_png(c,out/(f'{"ABC"[i]}_cast.png'));c.update_canvas()
            assert before==[snapshot(s) for s in scenes]
            (out/'camera_manifest.json').write_text(json.dumps(dict(status='Prototype pending user camera approval',
                size=[1440,900],logical_board=[10,10],textures_loaded=len(renderer.images),cameras=[dict(name=a.name,corners=a.corners,thickness=a.thickness) for a in CAMERAS],
                scenes=before,captures=records),indent=2)+'\n')
            print('Captured A/B/C x 6 real scenes plus 3 cast studies; combat unchanged');return
        active=0;mode=1;grid=False;old=False;roster=False;probe=None;running=True
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
                        if c.SDLK_1<=e.key<=c.SDLK_3:mode=e.key-c.SDLK_1;probe=None
                        elif c.SDLK_4<=e.key<=c.SDLK_9:active=e.key-c.SDLK_4
                        elif e.key==c.SDLK_g:grid=not grid
                        elif e.key==c.SDLK_b:old=not old
                        elif e.key==c.SDLK_t:roster=not roster
                elif e.type==c.SDL_MOUSEBUTTONDOWN and e.button==c.SDL_BUTTON_LEFT:
                    point=logical_mouse_to_canvas(e.x,e.y)
                    was_open=menu.is_open;action=menu.click(point)
                    if action=='toggle_fullscreen':display.toggle()
                    elif not was_open and not menu.is_open and point is not None and not old:probe=CAMERAS[mode].pick(*point)
            renderer.draw(scenes[active],CAMERAS[mode],grid=grid,original=old,probe=probe,roster=roster)
            settings.draw(menu,display);c.update_canvas();sleep(1/180)
        assert before==[snapshot(s) for s in scenes]
    finally:
        if settings is not None:settings.close()
        if renderer is not None:renderer.close()
        c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir',type=Path)
    run(parser.parse_args())
