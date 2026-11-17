"""Static D1 art review only. No StageGame, AI, combat clock, or live art switch."""
import argparse
import ctypes
from dataclasses import dataclass, asdict
import hashlib
import json
from math import cos, sin, pi
from pathlib import Path
import sys
from time import sleep

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_art_common import CAMERA, sprite_layout
from board import is_light_tile
from combat_balance import profile_for
from display_settings import DisplaySettings, logical_mouse_to_canvas
from health_renderer import HealthRenderer
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from stage_manager import StageCatalog
from stage5_art_renderer import polygon, outline
from tools.stage5_art_preview import open_preview, capture_png
from stage6_art_renderer import actor_layout as player_layout

ASSETS = ROOT/'assets/chapter3_units'
TARGET_HEIGHT = {'pawn': 66, 'rook': 78, 'knight': 80}
HP_OFFSET = {'pawn': 8, 'rook': 10, 'knight': 10}
PAGES = ('source_cast', 'silhouettes', 'scale84', 'stage11_static', 'warning_layout', 'alpha_edges')
# Explicit readability overlay. These cells do not come from an attack ledger.
LAYOUT_CELLS = ((2, 4), (3, 4), (4, 4), (7, 4), (3, 6), (6, 6))


@dataclass(frozen=True)
class Actor:
    data_id: str
    kind: str
    col: int
    row: int
    hp: int


def actors():
    d = StageCatalog.load().get_stage(11)
    p = profile_for(d.chapter)
    return (Actor('player', 'player', *d.player_spawn, 3),
            *(Actor(e.data_id, e.kind, e.col, e.row, p.hp(e.kind)) for e in d.enemies))


def candidate_layout(kind, u, v, records):
    if kind == 'player':
        return player_layout(kind, u, v)
    alpha = {k: (r['alpha_bbox'][1], r['alpha_bbox'][3]) for k, r in records.items()}
    sizes = {k: TARGET_HEIGHT[k]*256/(r['alpha_bbox'][3]-r['alpha_bbox'][1])/(CAMERA.sprite_scale*1.10)
             for k, r in records.items()}
    return sprite_layout(kind, u, v, sizes, {}, HP_OFFSET, alpha)


class Review:
    def __init__(self, canvas, folder=ASSETS):
        self.c = canvas; self.folder = Path(folder); self.images = {}; self.layout_rows = []
        self.records = {r['name']: r for r in json.loads((self.folder/'asset_manifest.json').read_text())['assets']}
        self.roster = actors()
        self.paths = {'background': ROOT/'assets/themed_arena/frozen.png',
                      'frame': ROOT/'assets/aligned_board/frozen_c.png',
                      'light': ROOT/'assets/polished_board/frozen_light.png',
                      'dark': ROOT/'assets/polished_board/frozen_dark.png',
                      'player': ROOT/'assets/character_concepts/player.png'}
        for kind in TARGET_HEIGHT:
            self.paths[kind] = self.folder/(kind+'.png')
            self.paths[kind+'_source'] = self.folder/'source'/(kind+'.png')
        try:
            for key, path in self.paths.items():
                if not path.is_file(): raise FileNotFoundError(path)
                self.images[key] = canvas.load_image(str(path))
        except BaseException:
            self.close()
            raise

    def close(self):
        for image in self.images.values():
            if image.texture:
                self.c.SDL_DestroyTexture(image.texture)
                image.texture = None
        self.images.clear()

    def image(self, key, x, y, w, h, silhouette=False):
        import sdl2 as s
        texture = self.images[key].texture
        if silhouette and s.SDL_SetTextureColorMod(texture, 0, 0, 0):
            raise OSError('Silhouette modulation failed')
        try:
            dst = s.SDL_FRect(x-w/2, 899-y-h/2, w, h)
            if s.SDL_RenderCopyF(self.c.renderer, texture, None, ctypes.byref(dst)):
                raise OSError('Static image draw failed')
        finally:
            if silhouette: s.SDL_SetTextureColorMod(texture, 255, 255, 255)

    def text(self, text, x, y, scale=2, color=(210,224,234)):
        # The shipped compact HUD alphabet lacks Z. Add it locally for FROZEN,
        # without editing or mutating the approved shared glyph dictionary.
        for index,char in enumerate(text):
            left=x+index*4*scale
            local={'Z':('111','001','010','100','111'), '-':('000','000','111','000','000')}
            if char not in local:
                HealthRenderer._text(self.c,char,left,y,scale=scale,color=color)
                continue
            for row,bits in enumerate(local[char]):
                for col,bit in enumerate(bits):
                    if bit=='1':
                        px=left+col*scale;py=y+(4-row)*scale
                        self.c.draw_rectangle(px,py,px+scale-1,py+scale-1,*color,filled=True)

    def actor(self, a, layout):
        x, y = layout['foot']; h = layout['height']
        polygon(self.c, tuple((x+3+cos(i*pi/4)*h*.20, y-2+sin(i*pi/4)*3) for i in range(8)),
                (24,28,36,255))
        self.image(a.kind, x, layout['center'][1], h, h)
        label = str(a.hp)+'/'+str(a.hp); width=len(label)*8
        hp = layout['hp_y']
        self.c.draw_rectangle(x-width/2-3, hp-3, x+width/2+3, hp+13, 12,19,25, filled=True)
        self.text(label,x-width/2,hp,color=HealthRenderer.HEALTH)
        self.layout_rows.append(dict(id=a.data_id, kind=a.kind, **layout))

    def board(self, grid):
        self.image('background',720,450,1440,900)
        self.image('frame',720,450,1440,900)
        # Same camera and top/frame opening as the existing live pipeline.
        outer=tuple(CAMERA.project(u,v) for u,v in ((-.12,-.12),(10.12,-.12),(10.12,10.12),(-.12,10.12)))
        polygon(self.c,outer,texture=self.images['light'].texture)
        for col in range(10):
            for row in range(10):
                tile=CAMERA.tile(col,row)
                polygon(self.c,tile,texture=self.images['light' if is_light_tile(col,row) else 'dark'].texture)
                if grid: outline(self.c,tile,(89,119,142))

    def draw(self, page, grid=False):
        if not 0 <= page < len(PAGES): raise ValueError('Unknown review page')
        c=self.c; self.layout_rows=[]
        c.SDL_SetRenderDrawColor(c.renderer,20,28,40,255); c.SDL_RenderClear(c.renderer)
        if page in (0,1):
            self.text('FROZEN PALACE - '+('SOURCE ART' if page==0 else 'ACTUAL ALPHA SILHOUETTES'),40,848,4)
            for i,kind in enumerate(TARGET_HEIGHT):
                x=240+i*480; r=self.records[kind]
                if page==1:c.draw_rectangle(x-215,190,x+215,750,207,218,226,filled=True)
                # Both views fit the same measured source silhouette to a 400x500 box.
                l,t,right,b=r['source_alpha_bbox']; sw,sh=r['source_size']
                gain=min(400/(right-l),500/(b-t))
                if page==0:
                    w,h=sw*gain,sh*gain
                    cx=x+(sw/2-(l+right)/2)*gain; cy=215+(b-sh/2)*gain
                    self.image(kind+'_source',cx,cy,w,h)
                else:
                    # Prepared alpha is mechanically derived from this source; no invented silhouette.
                    l,t,right,b=r['alpha_bbox']; gain=min(400/(right-l),500/(b-t))
                    self.image(kind,x+(128-(l+right)/2)*gain,215+(b-128)*gain,256*gain,256*gain,True)
                self.text('ICE '+kind.upper(),x-100,155,4)
                self.text('FULL BODY - FIT TO 400 X 500',x-185,115,2)
        elif page==2:
            self.text('84PX CELLS - CANDIDATE DISPLAY SIZES',40,848,4)
            for x,label in ((440,'LIGHT'),(650,'DARK'),(860,'WARNING'),(1090,'SILHOUETTE')):
                self.text(label,x-45,770,2)
            for i,kind in enumerate(('player',*TARGET_HEIGHT)):
                y=678-i*160
                self.text(kind.upper(),95,y,3)
                layout=candidate_layout(kind,0,0,self.records)
                a=Actor(kind,kind,0,0,3 if kind=='player' else profile_for(3).hp(kind))
                for x,tile in ((440,'light'),(650,'dark'),(860,'light'),(1090,'light')):
                    self.image(tile,x,y,84,84)
                    c.draw_rectangle(x-42,y-42,x+42,y+42,90,116,140)
                    if x==860:
                        c.draw_rectangle(x-40,y-40,x+40,y+40,239,88,109)
                        for dx in (-28,-7,14):c.draw_line(x+dx,y-35,x+dx+10,y-25,239,88,109)
                    h=layout['height'];foot=y-35
                    center=foot+(layout['center'][1]-layout['foot'][1])
                    self.image(kind,x,center,h,h,x==1090)
                    if x!=1090:
                        hp=foot+layout['hp_y']-layout['foot'][1]
                        self.text(str(a.hp)+'/'+str(a.hp),x-12,hp)
                r=self.records.get(kind)
                box=r['alpha_bbox'] if r else (41,18,215,238)
                self.text(str(round(h*(box[2]-box[0])/256))+' X '+str(round(h*(box[3]-box[1])/256))+' PX',
                          1220,y,2)
            self.text('NEIGHBORS',95,65,3)
            for i,kind in enumerate(('pawn','rook','knight','player')):
                x=440+i*84;y=70
                self.image('light' if i%2==0 else 'dark',x,y,84,84)
                c.draw_rectangle(x-42,y-42,x+42,y+42,90,116,140)
                layout=candidate_layout(kind,0,0,self.records);h=layout['height'];foot=y-35
                self.image(kind,x,foot+layout['center'][1]-layout['foot'][1],h,h)
            self.text('WARNING COLUMN IS A GEOMETRY STUDY',820,80,2)
            self.text('NO ATTACK OR DAMAGE',820,50,2)
        elif page in (3,4):
            self.board(grid)
            if page==4:
                for cell in LAYOUT_CELLS:
                    outline(c,CAMERA.tile(*cell),(239,88,109))
                    col,row=cell
                    for t in (.15,.35,.55,.75):
                        c.draw_line(*CAMERA.project(col+t,row+.12),*CAMERA.project(col+t+.12,row+.24),239,88,109)
            for a in sorted(self.roster,key=lambda a:(-a.row,a.col,a.data_id)):
                self.actor(a,candidate_layout(a.kind,a.col,a.row,self.records))
            c.draw_rectangle(12,715,285,890,12,19,25,filled=True)
            self.text('STAGE 11 STATIC',24,862,3)
            self.text('ART CANDIDATES ONLY',24,827,2)
            self.text('ROOK2 KNIGHT2 PAWN1',24,800,2)
            self.text('REFERENCE ENEMY HP67',24,773,2)
            self.text('NO AI OR COMBAT CLOCK',24,744,2)
            c.draw_rectangle(15,25,1375,60,12,19,25,filled=True)
            self.text('STATIC WARNING OVERLAY - NO LEDGER OR DAMAGE' if page==4 else
                      'ORIGINAL STAGE11 SPAWNS - NOT A LIVE RENDERER',28,38,2)
        else:
            self.text('ALPHA EDGE CHECK - SAME PNG ON FOUR BACKGROUNDS',30,848,3)
            colors=((240,240,240),(25,31,43),(190,60,145),(72,100,123))
            for j,color in enumerate(colors):
                x=190+j*350
                for i,kind in enumerate(TARGET_HEIGHT):
                    y=645-i*230
                    c.draw_rectangle(x-145,y-100,x+145,y+100,*color,filled=True)
                    self.image(kind,x,y,220,220)
            self.text('SOURCE ALPHA IS PRESERVED - CHECK FRINGES AT VIEWER 100 PERCENT',30,54,2)
        self.text('1 SOURCE  2 SILHOUETTE  3 84PX  4 SPAWNS  5 OVERLAY  6 ALPHA  G GRID',30,8,2)


def capture(canvas, review, output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    records=[]
    roster=review.roster
    for page,name in enumerate(PAGES):
        review.draw(page,grid=page in (3,4))
        path=output/(name+'.png')
        capture_png(canvas,path)
        if review.roster != roster: raise AssertionError('Review mutated the static roster')
        records.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            actors=review.layout_rows))
    result=dict(status='D1 static design review; no live Stage11 renderer or attack simulation',
                camera_corners=CAMERA.corners,reference_roster=[asdict(a) for a in roster],
                target_front_height=TARGET_HEIGHT,warning_overlay=list(LAYOUT_CELLS),
                warning_note='Hand-selected geometry study, not ledger events or damage',
                assets={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in review.paths.values()},captures=records)
    (output/'review_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Captured',len(records),'static design pages; textures',len(review.images))
    return result


def run(args):
    from pico2d import pico2d as c
    review=None;display=None
    try:
        open_preview(c,capture=bool(args.capture_dir))
        if not c.window or not c.renderer: raise OSError('Review window unavailable')
        c.hide_lattice()
        review=Review(c)
        if args.capture_dir:return capture(c,review,args.capture_dir)
        display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        c.SDL_SetWindowTitle(c.window,b'CHECKMATE D1 - STATIC ART REVIEW')
        page=0;grid=False;running=True
        while running:
            for event in c.get_events():
                if event.type==c.SDL_QUIT:running=False
                elif event.type==c.SDL_KEYDOWN and not getattr(event,'repeat',False):
                    if event.key==c.SDLK_ESCAPE:
                        if menu.is_open:menu.is_open=False
                        else:running=False
                    elif event.key==c.SDLK_F11:display.toggle()
                    elif not menu.is_open:
                        if c.SDLK_1<=event.key<=c.SDLK_6:page=event.key-c.SDLK_1
                        elif event.key==c.SDLK_g:grid=not grid
                elif event.type==c.SDL_MOUSEBUTTONDOWN and event.button==1:
                    action=menu.click(logical_mouse_to_canvas(event.x,event.y))
                    if action=='toggle_fullscreen':display.toggle()
                    elif action=='exit':running=False
            review.draw(page,grid);settings.draw(menu,display);c.update_canvas();sleep(1/180)
    finally:
        if review is not None:review.close()
        if c.window:c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir',type=Path)
    run(parser.parse_args())
