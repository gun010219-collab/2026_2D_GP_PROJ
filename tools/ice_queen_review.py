"""D4A static Ice Queen inspection, no live Stage13 combat or renderer switch."""
import argparse
from dataclasses import asdict
import hashlib
import json
from math import cos,sin,pi
from pathlib import Path
import sys
from time import sleep

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from arena_art_common import CAMERA,sprite_layout
from combat_balance import profile_for
from display_settings import DisplaySettings,logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from stage_manager import StageCatalog
from stage12_art_renderer import actor_layout as approved_layout
from stage5_art_renderer import polygon,outline
from queen_behavior import queen_ray_targets
from tools.chapter3_art_review import Actor
from tools.ice_bishop_review import Review as BishopReview
from tools.stage5_art_preview import open_preview,capture_png

ASSETS=ROOT/'assets/chapter3_units'
KINDS=('pawn','rook','knight','bishop','queen')
PAGES=('queen_source','ice_cast','front_back_84','stage13_static','queen_ray_reference','alpha_edges')


def actors():
    d=StageCatalog.load().get_stage(13);p=profile_for(d.chapter)
    return (Actor('player','player',*d.player_spawn,3),
            *(Actor(e.data_id,e.kind,e.col,e.row,p.hp(e.kind)) for e in d.enemies))


def candidate_layout(kind,u,v,records):
    if kind!='queen':return approved_layout(kind,u,v)
    r=records['queen'];top,bottom=r['alpha_bbox'][1::2]
    size=r['target_front_visible_height']*256/(bottom-top)/(CAMERA.sprite_scale*1.10)
    return sprite_layout(kind,u,v,{'queen':size},{},{'queen':r['hp_offset_candidate']},{'queen':(top,bottom)})


def visible_bounds(layout,record):
    left,top,right,bottom=record['alpha_bbox'];x,y=layout['center'];h=layout['height']
    return (x+(left-128)*h/256,y+(128-bottom)*h/256,
            x+(right-128)*h/256,y+(128-top)*h/256)


class Review(BishopReview):
    def __init__(self,canvas,folder=ASSETS):
        self.c=canvas;self.folder=Path(folder);self.images={};self.layout_rows=[]
        rows=[]
        for name in ('asset_manifest.json','bishop_manifest.json','queen_manifest.json'):
            rows.extend(json.loads((self.folder/name).read_text())['assets'])
        self.records={r['name']:r for r in rows};self.roster=actors()
        self.paths={'background':ROOT/'assets/themed_arena/frozen.png',
                    'frame':ROOT/'assets/aligned_board/frozen_c.png',
                    'light':ROOT/'assets/polished_board/frozen_light.png',
                    'dark':ROOT/'assets/polished_board/frozen_dark.png',
                    'player':ROOT/'assets/character_concepts/player.png'}
        for k in KINDS:
            self.paths[k]=self.folder/(k+'.png');self.paths[k+'_source']=self.folder/'source'/(k+'.png')
        try:
            for key,p in self.paths.items():
                if not p.is_file():raise FileNotFoundError(p)
                image=canvas.load_image(str(p));self.images[key]=image
                if not image.texture:raise OSError('Static texture failed: '+key)
        except BaseException:self.close();raise

    def label(self,a,layout):
        x=layout['foot'][0];y=layout['hp_y'];text=str(a.hp)+'/'+str(a.hp);width=len(text)*8
        self.c.draw_rectangle(x-width/2-3,y-3,x+width/2+3,y+13,12,19,25,filled=True)
        self.text(text,x-width/2,y,color=(130,203,153))

    def body(self,a,layout):
        x,y=layout['foot'];h=layout['height']
        polygon(self.c,tuple((x+3+cos(i*pi/4)*h*.20,y-2+sin(i*pi/4)*3) for i in range(8)),(24,28,36,255))
        self.image(a.kind,x,layout['center'][1],h,h)
        self.layout_rows.append(dict(id=a.data_id,kind=a.kind,**layout))

    def draw(self,page,grid=False):
        if not 0<=page<len(PAGES):raise ValueError('Unknown Queen page')
        c=self.c;self.layout_rows=[];c.SDL_SetRenderDrawColor(c.renderer,20,28,40,255);c.SDL_RenderClear(c.renderer)
        if page==0:
            self.text('ICE QUEEN - ORIGINAL SOURCE AND RGBA256 CANDIDATE',25,848,3)
            c.draw_rectangle(40,160,655,795,34,47,64,filled=True);self.source('queen',350,180,560,590)
            self.text('SELECTED SOURCE - FULL CROWN CAPE SCEPTER BOOTS',70,115,2)
            for x,label,size in ((850,'RGBA256',330),(1210,'ALPHA SILHOUETTE',330)):
                c.draw_rectangle(x-155,345,x+155,730,208,221,232,filled=True)
                self.image('queen',x,535,size,size,x==1210);self.text(label,x-100,285,2)
            self.image('queen',850,150,256,256)
            self.text('BOTTOM VIEW IS PREPARED 1X',1030,110,2)
        elif page==1:
            self.text('FROZEN PALACE - FIVE ORIGINAL DESIGNS',25,848,4)
            for i,k in enumerate(KINDS):
                x=145+i*285;self.source(k,x,260,230,490)
                self.text('ICE '+k.upper(),x-86,205,3);self.text('SOURCE FIT - NOT GAME SCALE',x-127,165,2)
                layout=candidate_layout(k,0,0,self.records);h=layout['height']
                self.image('light',x,72,84,84);self.image(k,x,37+layout['center'][1]-layout['foot'][1],h,h)
        elif page==2:
            self.text('84PX SWATCH - FRONT V0 AND REAR V9',25,848,4)
            for x,label in ((430,'FRONT LIGHT'),(640,'FRONT DARK'),(850,'REAR LIGHT'),(1060,'REAR DARK')):self.text(label,x-65,785,2)
            for i,k in enumerate(KINDS):
                y=685-i*135;self.text(k.upper(),55,y,3)
                for x,key,v in ((430,'light',0),(640,'dark',0),(850,'light',9),(1060,'dark',9)):
                    self.image(key,x,y,84,84);c.draw_rectangle(x-42,y-42,x+42,y+42,89,119,142)
                    l=candidate_layout(k,0,v,self.records);h=l['height'];foot=y-35
                    self.image(k,x,foot+l['center'][1]-l['foot'][1],h,h)
                    hp=foot+l['hp_y']-l['foot'][1];text=str(profile_for(3).hp(k))+'/'+str(profile_for(3).hp(k));w=len(text)*8
                    c.draw_rectangle(x-w/2-3,hp-3,x+w/2+3,hp+13,12,19,25,filled=True);self.text(text,x-w/2,hp)
                r=self.records[k];left,top,right,bottom=r['alpha_bbox'];h=candidate_layout(k,0,0,self.records)['height']
                self.text(str(round(h*(right-left)/256))+' X '+str(round(h*(bottom-top)/256)),1220,y,2)
            self.text('SWATCH84 - SHARED B12 DEPTH - STATIC SIZE CANDIDATES ONLY',25,32,2)
        elif page in (3,4):
            self.board(grid);queen=next(a for a in self.roster if a.kind=='queen');rays=queen_ray_targets((queen.col,queen.row))
            if page==4:
                for col,row in rays:
                    outline(c,CAMERA.tile(col,row),(239,88,109))
                    for t in (.15,.4,.65):c.draw_line(*CAMERA.project(col+t,row+.12),*CAMERA.project(col+t+.12,row+.24),239,88,109)
            labels=[]
            for a in sorted(self.roster,key=lambda a:(-a.row,a.col,a.data_id)):
                l=candidate_layout(a.kind,a.col,a.row,self.records);self.body(a,l);labels.append((a,l))
            # Same two-pass HP policy as the live common renderer: cape cannot paint over a prior label.
            for a,l in labels:self.label(a,l)
            c.draw_rectangle(10,708,290,890,12,19,25,filled=True)
            for text,y in [('STAGE13 STATIC',862),('QUEEN1 KNIGHT1 PAWN3',830),('ENEMY HP58',798),('NO AI LEDGER DAMAGE',766),('USER DESIGN PENDING',734)]:self.text(text,22,y,2)
            c.draw_rectangle(15,15,1420,65,12,19,25,filled=True)
            self.text('EIGHT RAYS '+str(len(rays))+' CELLS - ORIGIN EXCLUDED - STATIC GEOMETRY NOT LIVE EVENTS' if page==4 else
                      'ORIGINAL STAGE13 SPAWNS - LABELS AFTER BODIES - NO LIVE RENDERER',28,38,2)
        else:
            self.text('QUEEN ALPHA - SAME PNG ON FOUR BACKGROUNDS',25,848,4)
            for i,color in enumerate(((245,245,245),(15,22,31),(195,65,145),(78,107,128))):
                x=190+i*350;c.draw_rectangle(x-150,280,x+150,720,*color,filled=True)
                self.image('queen',x,510,340,340);self.text(('LIGHT','DARK','MAGENTA','BLUE GREY')[i],x-70,235,2)
            self.text('INSPECT ALL CROWN CAPE SCEPTER AND BOOT TIPS - NO EDGE CROP OR BLACK MATTE',25,125,2)
            self.text('ALPHA AND SOURCE HASHES IN QUEEN MANIFEST - NOT A LIVE COMBAT TEST',25,80,2)
        self.text('1 SOURCE 2 CAST 3 FRONT REAR 4 STAGE13 5 RAYS 6 ALPHA G GRID F11 ESC',25,5,2)


def capture(canvas,review,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rows=[];roster=review.roster
    for page,name in enumerate(PAGES):
        review.draw(page,grid=page in (3,4));p=output/(name+'.png');capture_png(canvas,p)
        if review.roster!=roster:raise AssertionError('Static roster changed')
        rows.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actors=review.layout_rows))
    queen=next(a for a in roster if a.kind=='queen')
    manifest=dict(status='D4A static Queen candidate; user design GUI pending; no live Stage13 combat or renderer',
                  camera_corners=CAMERA.corners,roster=[asdict(a) for a in roster],
                  queen_rays=queen_ray_targets((queen.col,queen.row)),
                  warning_note='Pure queen_behavior geometry at original spawn; no ledger, damage, parry, AI clock or reposition simulated. Origin excluded.',
                  player_hp_note='Static reference HP3, not a simulated carried build or receipt',
                  assets={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in review.paths.values()},captures=rows)
    (output/'review_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('CAPTURED',len(rows),'STATIC Queen pages;',len(review.images),'textures; no live Stage13')
    return manifest


def run(args):
    from pico2d import pico2d as c
    review=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise OSError('Static Queen window unavailable')
        c.hide_lattice();review=Review(c)
        if args.capture_dir:return capture(c,review,args.capture_dir)
        display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        c.SDL_SetWindowTitle(c.window,b'CHECKMATE D4A - STATIC ICE QUEEN REVIEW')
        page=0;grid=False;running=True
        while running:
            for e in c.get_events():
                if e.type==c.SDL_QUIT:running=False
                elif e.type==c.SDL_KEYDOWN and not getattr(e,'repeat',False):
                    if e.key==c.SDLK_ESCAPE:
                        if menu.is_open:menu.is_open=False
                        else:running=False
                    elif e.key==c.SDLK_F11:display.toggle()
                    elif not menu.is_open:
                        if c.SDLK_1<=e.key<=c.SDLK_6:page=e.key-c.SDLK_1
                        elif e.key==c.SDLK_g:grid=not grid
                elif e.type==c.SDL_MOUSEBUTTONDOWN and e.button==1:
                    action=menu.click(logical_mouse_to_canvas(e.x,e.y))
                    if action=='toggle_fullscreen':display.toggle()
                    elif action=='exit':running=False
            review.draw(page,grid);settings.draw(menu,display);c.update_canvas();sleep(1/180)
    finally:
        if settings is not None:settings.close()
        if review is not None:review.close()
        if c.window:c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture-dir',type=Path);run(p.parse_args())
