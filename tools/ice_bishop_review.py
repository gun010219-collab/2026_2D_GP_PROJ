"""D3A static art inspection. No StageGame, live ledger, AI or parry simulation."""
import argparse
from dataclasses import asdict
import hashlib
import json
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
from stage11_art_renderer import actor_layout as approved_layout
from stage5_art_renderer import outline
from tools.chapter3_art_review import Review as D1Review,Actor
from tools.stage5_art_preview import open_preview,capture_png

ASSETS=ROOT/'assets/chapter3_units'
KINDS=('pawn','rook','knight','bishop')
PAGES=('bishop_source','ice_cast','front_back_84','stage12_static','warning_reference','alpha_edges')
TARGET_HEIGHT=84
HP_OFFSET=10
# Hand-selected visual references only: never consumed by a live renderer.
COLOR_CELLS=tuple((c,r) for c in range(10) for r in range(10) if (c+r)%2==0)
ROOK_CELLS=tuple((c,4) for c in range(3,9))
DIAGONAL_GUIDE=tuple((c,r) for c in range(10) for r in range(10) if abs(c-2)==abs(r-8))


def actors():
    d=StageCatalog.load().get_stage(12);p=profile_for(d.chapter)
    return (Actor('player','player',*d.player_spawn,3),
            *(Actor(e.data_id,e.kind,e.col,e.row,p.hp(e.kind)) for e in d.enemies))


def candidate_layout(kind,u,v,records):
    if kind!='bishop':return approved_layout(kind,u,v)
    top,bottom=records['bishop']['alpha_bbox'][1::2]
    size=TARGET_HEIGHT*256/(bottom-top)/(CAMERA.sprite_scale*1.10)
    return sprite_layout(kind,u,v,{'bishop':size},{},{'bishop':HP_OFFSET},{'bishop':(top,bottom)})


class Review(D1Review):
    def __init__(self,canvas,folder=ASSETS):
        self.c=canvas;self.folder=Path(folder);self.images={};self.layout_rows=[]
        old=json.loads((self.folder/'asset_manifest.json').read_text())['assets']
        bishop=json.loads((self.folder/'bishop_manifest.json').read_text())['assets']
        self.records={r['name']:r for r in (*old,*bishop)}
        self.roster=actors()
        self.paths={'background':ROOT/'assets/themed_arena/frozen.png',
                    'frame':ROOT/'assets/aligned_board/frozen_c.png',
                    'light':ROOT/'assets/polished_board/frozen_light.png',
                    'dark':ROOT/'assets/polished_board/frozen_dark.png',
                    'player':ROOT/'assets/character_concepts/player.png'}
        for k in KINDS:
            self.paths[k]=self.folder/(k+'.png')
            self.paths[k+'_source']=self.folder/'source'/(k+'.png')
        try:
            for key,p in self.paths.items():
                if not p.is_file():raise FileNotFoundError(p)
                image=canvas.load_image(str(p));self.images[key]=image
                if not image.texture:raise OSError('Static texture creation failed: '+key)
        except BaseException:
            self.close();raise

    def source(self,kind,x,foot,max_width=270,max_height=520):
        row=self.records[kind];left,top,right,bottom=row['source_alpha_bbox']
        sw,sh=row['source_size'];gain=min(max_width/(right-left),max_height/(bottom-top))
        self.image(kind+'_source',x+(sw/2-(left+right)/2)*gain,
                   foot+(bottom-sh/2)*gain,sw*gain,sh*gain)

    def draw(self,page,grid=False):
        if not 0<=page<len(PAGES):raise ValueError('Unknown Bishop review page')
        c=self.c;self.layout_rows=[]
        c.SDL_SetRenderDrawColor(c.renderer,20,28,40,255);c.SDL_RenderClear(c.renderer)
        if page==0:
            self.text('ICE BISHOP - SOURCE AND RGBA256 CANDIDATE',30,848,4)
            c.draw_rectangle(120,170,550,790,37,49,64,filled=True)
            self.source('bishop',335,185,350,580)
            self.text('SELECTED SOURCE 1024 X 1536',160,115,2)
            self.text('FULL CROWN STAFF AND BOOTS',165,85,2)
            for x,label,size in ((820,'PREPARED 2X',512),(1190,'SILHOUETTE',300)):
                c.draw_rectangle(x-165,340,x+165,760,202,217,229,filled=True)
                self.image('bishop',x,550,size,size,label=='SILHOUETTE')
                self.text(label,x-90,285,3)
            self.image('bishop',1190,160,256,256)
            self.text('PREPARED 1X - TRANSPARENT',950,30,2)
        elif page==1:
            self.text('FROZEN PALACE - FOUR ORIGINAL ICE DESIGNS',30,848,4)
            for i,k in enumerate(KINDS):
                x=185+i*355
                self.source(k,x,235,260,500)
                self.text('ICE '+k.upper(),x-90,180,3)
                self.text('SOURCE FIT - NOT GAME SCALE',x-145,135,2)
                layout=candidate_layout(k,0,0,self.records);h=layout['height']
                self.image('light',x,70,84,84)
                self.image(k,x,35+layout['center'][1]-layout['foot'][1],h,h)
        elif page==2:
            self.text('84PX SWATCH - FRONT V0 AND REAR V9',30,848,4)
            for x,label in ((440,'FRONT LIGHT'),(650,'FRONT DARK'),(860,'REAR LIGHT'),(1070,'REAR DARK')):
                self.text(label,x-62,780,2)
            for i,k in enumerate(KINDS):
                y=665-i*165;self.text(k.upper(),60,y,3)
                for x,key,v in ((440,'light',0),(650,'dark',0),(860,'light',9),(1070,'dark',9)):
                    self.image(key,x,y,84,84);c.draw_rectangle(x-42,y-42,x+42,y+42,89,119,142)
                    layout=candidate_layout(k,0,v,self.records);h=layout['height'];foot=y-35
                    self.image(k,x,foot+layout['center'][1]-layout['foot'][1],h,h)
                    hp=foot+layout['hp_y']-layout['foot'][1]
                    label=str(profile_for(3).hp(k))+'/'+str(profile_for(3).hp(k));width=len(label)*8
                    c.draw_rectangle(x-width/2-3,hp-3,x+width/2+3,hp+13,12,19,25,filled=True)
                    self.text(label,x-width/2,hp)
                l,t,r,b=self.records[k]['alpha_bbox'];front=candidate_layout(k,0,0,self.records)['height']
                self.text(str(round(front*(r-l)/256))+' X '+str(round(front*(b-t)/256)),1220,y,2)
            self.text('SWATCHES ARE 84PX - SPRITES USE SHARED B12 DEPTH SCALE - NOT COMBAT',35,35,2)
        elif page in (3,4):
            self.board(grid)
            if page==4:
                for col,row in COLOR_CELLS:
                    outline(c,CAMERA.tile(col,row),(239,88,109))
                    for t in (.15,.4,.65):
                        c.draw_line(*CAMERA.project(col+t,row+.12),*CAMERA.project(col+t+.12,row+.24),239,88,109)
                for cell in ROOK_CELLS:outline(c,CAMERA.tile(*cell),(237,177,93))
                for cell in DIAGONAL_GUIDE:
                    x,y=CAMERA.center(*cell);c.draw_line(x-5,y-5,x+5,y+5,103,168,222)
            # Same stable ground row/col ordering, no simulated movement/lift.
            for a in sorted(self.roster,key=lambda a:(-a.row,a.col,a.data_id)):
                self.actor(a,candidate_layout(a.kind,a.col,a.row,self.records))
            c.draw_rectangle(10,708,285,890,12,19,25,filled=True)
            for text,y in [('STAGE12 STATIC',860),('BISHOP2 ROOK1 PAWN2',826),('ENEMY HP60',795),
                           ('NO AI LEDGER PARRY',764),('USER DESIGN PENDING',733)]:self.text(text,22,y,2)
            c.draw_rectangle(15,15,1420,65,12,19,25,filled=True)
            self.text('COLOR50 AND ROOK LINE ARE STATIC REFERENCES - BLUE DIAGONAL GUIDE IS NOT DAMAGE' if page==4 else
                      'ORIGINAL STAGE12 SPAWNS - SHARED BISHOP TEXTURE - NO LIVE RENDERER',28,38,2)
        else:
            self.text('ALPHA EDGES - SAME UNMODIFIED RGBA ON FOUR COLORS',30,848,3)
            for i,color in enumerate(((245,245,245),(15,22,31),(195,65,145),(78,107,128))):
                x=190+i*350;c.draw_rectangle(x-150,260,x+150,770,*color,filled=True)
                self.image('bishop',x,510,500,500)
                self.text(('LIGHT','DARK','MAGENTA','BLUE GREY')[i],x-70,220,2)
            self.text('CHECK CROWN TIPS STAFF TIP BOTH BOOTS - NO BLACK MATTE OR EDGE CROP',30,125,2)
            self.text('ALPHA BBOX AND SHA IN BISHOP MANIFEST - NOT A DYNAMIC HP OR PARRY TEST',30,80,2)
        self.text('1 SOURCE 2 CAST 3 FRONT REAR 4 STAGE12 5 GUIDES 6 ALPHA G GRID F11 ESC',25,5,2)


def capture(canvas,review,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rows=[];roster=review.roster
    for page,name in enumerate(PAGES):
        review.draw(page,grid=page in (3,4));p=output/(name+'.png');capture_png(canvas,p)
        if review.roster!=roster:raise AssertionError('Static roster changed')
        rows.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actors=review.layout_rows))
    manifest=dict(status='D3A static Ice Bishop design candidate; user GUI pending; no live Stage12 or combat validation',
                  camera_corners=CAMERA.corners,roster=[asdict(a) for a in roster],target_bishop_front_height=TARGET_HEIGHT,
                  warning_note='Hand-selected color50 and Rook line geometry only; blue diagonal axis is NOT an attack. Current Bishop AI uses stationary color50. No ledger/parry/damage simulation.',
                  color_reference=COLOR_CELLS,rook_reference=ROOK_CELLS,diagonal_guide=DIAGONAL_GUIDE,
                  assets={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in review.paths.values()},captures=rows)
    (output/'review_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('CAPTURED',len(rows),'STATIC pages;',len(review.images),'textures; no live Stage12')
    return manifest


def run(args):
    from pico2d import pico2d as c
    review=settings=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise OSError('Static review SDL window unavailable')
        c.hide_lattice();review=Review(c)
        if args.capture_dir:return capture(c,review,args.capture_dir)
        display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        c.SDL_SetWindowTitle(c.window,b'CHECKMATE D3A - STATIC ICE BISHOP REVIEW')
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
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir',type=Path)
    run(parser.parse_args())
