"""Release title, chapter selection, ending and credits for the shared canvas."""
from dataclasses import dataclass
import ctypes
import os
from pathlib import Path

from chapter_themes import get_theme
from health_renderer import HealthRenderer
from settings_menu import Rect
from ui_theme import DIM as UI_DIM, ROSE, SILVER, PALE, current as current_ui

THEMES = ('royal','forest','frozen','volcanic','gothic')
CHAPTERS = tuple(get_theme(chapter).name.upper() for chapter in range(1,6))
ROOT = Path(__file__).resolve().parent
GOLD = (223,194,130)
LIGHT = (237,232,216)
DIM = (128,129,139)


@dataclass(frozen=True)
class Button:
    action: str | int
    label: str
    rect: Rect
    enabled: bool = True


def buttons(screen, data, replay=False):
    if screen == 'main':
        rows = [('new','NEW GAME',True),('continue','CONTINUE',data.continue_chapter is not None),
                ('chapters','CHAPTER SELECT',True),('settings','SETTINGS',True),('exit','EXIT',True)]
        return tuple(Button(a,label,Rect(567,490-i*72,416,63),enabled)
                     for i,(a,label,enabled) in enumerate(rows))
    if screen == 'chapters':
        cards = tuple(Button(i,name,Rect(128,611-(i-1)*105,540,87),i in data.unlocked)
                      for i,name in enumerate(CHAPTERS,1))
        return (*cards,Button('main','MAIN MENU',Rect(128,63,540,54)))
    if screen == 'ending':
        rows = [('credits','CREDITS'),('replay','REPLAY FINAL BOSS'),('main','MAIN MENU')] if replay else (
            ('credits','CREDITS'),('main','MAIN MENU'))
        width = 276
        x = (1440-(width*len(rows)+24*(len(rows)-1)))//2
        return tuple(Button(a,label,Rect(x+i*(width+24),179,width,57))
                     for i,(a,label) in enumerate(rows))
    return (Button('ending','RETURN',Rect(539,120,362,56)),)


class FrontInput:
    def __init__(self):
        self.selected = 0
        self.preview = None

    def action(self, canvas, event, items, point):
        enabled = [i for i,item in enumerate(items) if item.enabled]
        if self.selected not in enabled:
            self.selected = enabled[0]
        if event.type == canvas.SDL_MOUSEBUTTONDOWN and event.button == canvas.SDL_BUTTON_LEFT:
            for i,item in enumerate(items):
                if item.rect.contains(point):
                    if isinstance(item.action,int):
                        self.preview = i
                    if item.enabled:
                        self.selected = i
                        return item.action
                    break
        if event.type != canvas.SDL_KEYDOWN or getattr(event,'repeat',False):
            return None
        if event.key in (canvas.SDLK_UP,canvas.SDLK_DOWN,canvas.SDLK_LEFT,canvas.SDLK_RIGHT):
            step = -1 if event.key in (canvas.SDLK_UP,canvas.SDLK_LEFT) else 1
            self.selected = enabled[(enabled.index(self.selected)+step)%len(enabled)]
            self.preview = None
        elif event.key == canvas.SDLK_RETURN and self.preview is None:
            return items[self.selected].action
        return None


class FrontRenderer:
    def __init__(self,canvas,ui):
        self.c, self.ui = canvas, ui
        self.images = {}
        try:
            art = {theme:ROOT/'assets'/'themed_arena'/(theme+'.png') for theme in THEMES}
            if not current_ui(canvas):
                art.update(player=ROOT/'assets'/'character_concepts'/'player.png',
                           king=ROOT/'assets'/'character_concepts'/'ch1_king.png')
            for name,path in art.items():
                try:
                    self.images[name] = canvas.load_image(str(path))
                except OSError:
                    pass
            if current_ui(canvas):
                return
            fonts = Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
            for file,size,labels in (
                ('georgia.ttf',80,('CHECKMATE',)),
                ('georgia.ttf',64,('CHECKMATE',)),
                ('georgia.ttf',48,('CHAPTER SELECT','CREDITS')),
                ('segoeui.ttf',24,('NEW GAME','CONTINUE','CHAPTER SELECT','SETTINGS','EXIT',
                                  'MAIN MENU','REPLAY FINAL BOSS','CREDITS',*CHAPTERS)),
                ('segoeui.ttf',22,('CAMPAIGN COMPLETE','ALL FIVE CHAPTERS CLEARED',
                                  'CHAPTER CHECKPOINTS ARE SAVED AT THE START OF EACH CHAPTER',
                                  'MOVE  ARROWS     ATTACK  LEFT CTRL     PARRY  LEFT ALT',
                                  'UPGRADE  1 / 2 / 3     DISPLAY  F11     TITLE  ESC',
                                  'TUK GAME ENGINEERING',
                                  'GAME DESIGN AND PRODUCTION  /  CHECKMATE PROJECT',
                                  'IMPLEMENTATION AND TESTING  /  PROJECT WITH CODEX',
                                  'ART  /  PROJECT DIRECTION AND AI-ASSISTED ILLUSTRATION',
                                  'AUDIO  /  ORIGINAL PROJECT COMPOSITION AND SYNTHESIS',
                                  'RUNTIME  /  PYTHON, PICO2D, SDL2 AND SDL_MIXER')),
            ):
                font = canvas.load_font(str(fonts/file),size)
                try:
                    for label in labels:
                        ui._cache_text(font,label, key=('front',size,label))
                finally:
                    canvas.TTF_CloseFont(font.font)
        except BaseException:
            self.close()
            raise

    def title(self,label,x,y,size=80):
        self.ui._label(('front',size,label),x,y)

    def fill(self,rect,color):
        self.ui._rect(rect,color)

    def image(self,theme,rect):
        image = self.images.get(theme)
        if image is None:
            return
        c = self.c
        dest = c.SDL_Rect(rect.left,900-rect.bottom-rect.height,rect.width,rect.height)
        c.SDL_RenderCopy(c.renderer,image.texture,None,ctypes.byref(dest))

    def backdrop(self,theme):
        c = self.c
        view = Rect(0,0,1440,900)
        self.fill(view,(11,13,22))
        self.image(theme,view)
        blend = ctypes.c_int()
        c.SDL_GetRenderDrawBlendMode(c.renderer,ctypes.byref(blend))
        c.SDL_SetRenderDrawBlendMode(c.renderer,c.SDL_BLENDMODE_BLEND)
        try:
            self.ui._rect(view,(8,10,16),187)
        finally:
            c.SDL_SetRenderDrawBlendMode(c.renderer,blend.value)

    def button(self,item,active):
        rect = item.rect
        color = GOLD if active else (91,73,45) if item.enabled else (55,55,62)
        self.fill(rect,color)
        self.fill(Rect(rect.left+1,rect.bottom+1,rect.width-2,rect.height-2),
                  (56,43,25) if active else (19,21,30))
        if active:
            self.fill(Rect(rect.left,rect.bottom,4,rect.height),GOLD)
        if not item.enabled:
            self.small(item.label,rect.left+rect.width//2,rect.bottom+rect.height//2-5,color=DIM)
        else:
            key = ('front',24,item.label)
            self.ui._label(key if key in self.ui.textures else item.label,
                           rect.left+rect.width//2,rect.bottom+rect.height//2)

    def small(self,text,x,y,scale=2,color=LIGHT):
        HealthRenderer._text(self.c,text,x-(len(text)*4-1)*scale/2,y,scale=scale,color=color)

    def draw_screen(self,screen,data,notice,selection,ending=None,replay=False):
        theme = current_ui(self.c)
        if theme:
            self._draw_themed(theme,screen,data,notice,selection,ending,replay)
            return
        items = buttons(screen,data,replay)
        if screen == 'main':
            self.backdrop('royal')
            self.fill(Rect(79,154,478,624),(17,19,27))
            self.fill(Rect(79,151,478,3),GOLD)
            self.title('CHECKMATE',318,701,64)
            self.title('TUK GAME ENGINEERING',318,640,22)
            self.fill(Rect(625,265,716,451),(106,83,46))
            self.image('royal',Rect(629,269,708,443))
            self.image('king',Rect(978,360,278,278))
            self.image('player',Rect(744,318,230,230))
            self.title('MOVE  ARROWS     ATTACK  LEFT CTRL     PARRY  LEFT ALT',983,217,22)
            self.title('UPGRADE  1 / 2 / 3     DISPLAY  F11     TITLE  ESC',983,181,22)
            self.small('NEW GAME SETS THE ACTIVE CHECKPOINT TO CHAPTER 1',295,584)
            target = data.continue_chapter
            self.small(f'CONTINUE STARTS CHAPTER {target}' if target else 'CONTINUE UNAVAILABLE',
                       295,561,color=GOLD if target else DIM)
            for i,item in enumerate(items):
                self.button(item,selection==i)
            if data.final_clear:
                self.small('CAMPAIGN COMPLETE',318,172,color=GOLD)
        elif screen == 'chapters':
            current = min(selection,4)
            self.backdrop(THEMES[current])
            self.title('CHAPTER SELECT',399,787,48)
            self.fill(Rect(725,226,622,390),(119,92,49))
            self.image(THEMES[current],Rect(729,230,614,382))
            self.title(CHAPTERS[current],1036,670,24)
            self.title('CHAPTER CHECKPOINTS ARE SAVED AT THE START OF EACH CHAPTER',1036,180,22)
            for i,item in enumerate(items):
                if i==5:
                    self.button(item,selection==i)
                    continue
                rect = item.rect
                self.fill(rect,GOLD if selection==i else (93,73,43))
                self.fill(Rect(rect.left+1,rect.bottom+1,rect.width-2,rect.height-2),(19,21,30))
                self.image(THEMES[i],Rect(rect.left+6,rect.bottom+6,119,75))
                self.title(item.label,rect.left+329,rect.bottom+56,24)
                status = (f'STAGE {i*5+1}  /  ENTRY ATTACK +{data.entry_attack[i]}' if item.enabled
                          else f'LOCKED  /  DEFEAT THE STAGE {i*5} BOSS')
                self.small(status,rect.left+329,rect.bottom+21,color=GOLD if item.enabled else DIM)
        else:
            self.backdrop('gothic')
            self.fill(Rect(296,268,848,458),(19,21,30))
            self.fill(Rect(296,268,848,2),GOLD)
            if screen=='ending':
                self.title('CHECKMATE',720,633)
                self.title('CAMPAIGN COMPLETE',720,540,22)
                self.title('ALL FIVE CHAPTERS CLEARED',720,493,22)
                if ending:
                    self.small(f'FINAL STAGE 25  /  HP {ending.hp}/{ending.max_hp}',720,413,3)
                    self.small(f'FINISH TICK {ending.tick}   /   ATTACK LEVEL {ending.attack_level}',720,364)
            else:
                self.title('CREDITS',720,636,48)
                for i,label in enumerate(('GAME DESIGN AND PRODUCTION  /  CHECKMATE PROJECT',
                                          'IMPLEMENTATION AND TESTING  /  PROJECT WITH CODEX',
                                          'ART  /  PROJECT DIRECTION AND AI-ASSISTED ILLUSTRATION',
                                          'AUDIO  /  ORIGINAL PROJECT COMPOSITION AND SYNTHESIS',
                                          'RUNTIME  /  PYTHON, PICO2D, SDL2 AND SDL_MIXER')):
                    self.title(label,720,552-i*49,22)
            for i,item in enumerate(items):
                self.button(item,selection==i)
        if notice:
            self.fill(Rect(100,12,1240,34),(29,21,23))
            self.small(notice,720,24,color=(247,178,144))

    def _draw_themed(self,theme,screen,data,notice,selection,ending,replay):
        theme.sprite('cathedral',Rect(0,0,1440,900),fit='cover')
        items = buttons(screen,data,replay)
        pointer = theme.pointer()
        hovered = next((i for i,item in enumerate(items) if item.rect.contains(pointer)),None)
        active = selection if hovered is None else hovered
        if screen == 'main':
            theme.sprite('wordmark',Rect(294,570,968,265))
            for i,(item,icon) in enumerate(zip(items,('knight','crown','book','gear','power'))):
                theme.button(item.rect,item.label,active=i==active,enabled=item.enabled,
                             icon=icon,decorated=True)
            theme.rule(775,178,310)
            if data.final_clear:
                theme.text('CAMPAIGN COMPLETE',775,153,size=18,color=PALE)
        elif screen == 'chapters':
            current_index = min(selection if hovered is None else hovered,4)
            theme.text('CHAPTER SELECT',398,790,size=54,display=True)
            theme.rule(398,750,268)
            for i,item in enumerate(items[:5]):
                box = item.rect
                theme.panel(box,active=i==active,muted=not item.enabled)
                image = self.images.get(THEMES[i])
                if image:
                    theme.image(image,Rect(box.left+10,box.bottom+9,112,69))
                x = box.left+140
                color = SILVER if item.enabled else UI_DIM
                theme.text(item.label,x,box.bottom+55,size=26,display=True,align='left',color=color)
                status = (f'Stage {i*5+1}  /  Entry attack +{data.entry_attack[i]}' if item.enabled
                          else f'Locked  /  Defeat the Stage {i*5} boss')
                theme.text(status,x,box.bottom+27,size=20,align='left',color=PALE if item.enabled else UI_DIM)
            theme.button(items[-1].rect,items[-1].label,active=active==5)
            theme.panel(Rect(725,193,620,466))
            preview = self.images.get(THEMES[current_index])
            if preview:
                theme.image(preview,Rect(740,251,590,348))
            theme.text(CHAPTERS[current_index],1035,625,size=29,display=True)
            theme.text('Checkpoints are saved at each chapter entrance.',1035,222,size=20,color=PALE)
        else:
            theme.panel(Rect(288,262,864,503))
            theme.rule(720,686,358)
            if screen == 'ending':
                theme.text('CHECKMATE',720,628,size=68,display=True)
                theme.text('CAMPAIGN COMPLETE',720,546,size=34,display=True,color=ROSE)
                theme.text('All five chapters cleared',720,492,size=25,color=PALE)
                if ending:
                    theme.text(f'Final stage 25  /  HP {ending.hp}/{ending.max_hp}',720,424,size=23)
                    theme.text(f'Finish tick {ending.tick}  /  Attack level {ending.attack_level}',
                               720,383,size=20,color=PALE)
            else:
                theme.text('CREDITS',720,631,size=54,display=True)
                for i,(role,credit) in enumerate((
                    ('GAME DESIGN & PRODUCTION','CHECKMATE Project · TUK Game Engineering'),
                    ('IMPLEMENTATION & TESTING','CHECKMATE Project with Codex'),
                    ('VISUAL ART','Project direction and AI-assisted illustration'),
                    ('AUDIO','Original project composition and synthesis'),
                    ('TYPE & RUNTIME','Cinzel · Source Sans 3 · Python · Pico2D · SDL2'),
                )):
                    y = 548-i*49
                    theme.text(role,720,y,size=19,display=True,color=ROSE)
                    theme.text(credit,720,y-23,size=19,color=PALE)
            for i,item in enumerate(items):
                theme.button(item.rect,item.label,active=i==active)
        if notice:
            theme.panel(Rect(100,11,1240,36))
            theme.text(notice,720,29,size=20,color=ROSE,width=1180)

    def close(self):
        for image in self.images.values():
            if image.texture:
                self.c.SDL_DestroyTexture(image.texture)
                image.texture = None
        self.images.clear()
