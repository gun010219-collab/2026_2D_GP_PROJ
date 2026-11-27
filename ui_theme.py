"""Renderer-owned release UI sprites and bounded SDL_ttf texture cache."""
from collections import OrderedDict
import ctypes as c
from pathlib import Path

from config import WINDOW_HEIGHT
from settings_menu import Rect

ASSETS = Path(__file__).resolve().parent / 'assets' / 'ui'
INK = (17, 13, 19)
STEEL = (135, 117, 128)
SILVER = (241, 234, 237)
PALE = (184, 170, 183)
DIM = (147, 135, 147)
CRIMSON = (211, 63, 88)
ROSE = (255, 162, 173)
TEXT_LIMIT = 320
ICONS = ('knight', 'crown', 'book', 'gear', 'power', 'attack', 'hp', 'move')
SPRITES = ('cathedral', 'wordmark', 'button', 'button_active', 'rule', 'combat_frames', *ICONS)
# The metalwork is fitted to each panel offline. One filtered copy per frame.
COMBAT_REGIONS = {
    'rewards': (0,0,836,550), 'result': (0,552,618,360), 'card': (620,552,240,325),
    'player': (0,914,248,140), 'boss': (250,914,248,156), 'final': (500,914,456,207),
    'badge': (838,0,56,20), 'vitality': (250,1074,208,10),
    'stage': (0,1074,248,45),
}


def current(canvas):
    return getattr(canvas,'__dict__',{}).get('_checkmate_ui')


def fitted_rect(width, height, rect, *, cover=False):
    scale = (max if cover else min)(rect.width / width, rect.height / height)
    w, h = round(width * scale), round(height * scale)
    return Rect(rect.left + (rect.width-w)//2, rect.bottom + (rect.height-h)//2, w, h)


class UITheme:
    def __init__(self, canvas):
        from sdl2 import SDL_ScaleModeLinear, SDL_SetTextureScaleMode

        self.canvas = canvas
        self.fonts = {}
        self.textures = OrderedDict()
        self.sprites = {}
        self.closed = False
        try:
            for name in SPRITES:
                image = canvas.load_image(str(ASSETS/(name+'.png')))
                self.sprites[name] = image
                SDL_SetTextureScaleMode(image.texture,SDL_ScaleModeLinear)
            canvas._checkmate_ui = self
        except BaseException:
            self.close()
            raise

    def _text_texture(self, text, size, display, color):
        key = (text, size, display, color)
        if key in self.textures:
            self.textures.move_to_end(key)
            return self.textures[key]
        canvas = self.canvas
        font_key = (display, size)
        if font_key not in self.fonts:
            name = 'Cinzel.ttf' if display else 'SourceSans3-Regular.ttf'
            self.fonts[font_key] = canvas.load_font(str(ASSETS/'fonts'/name), size).font
        surface = canvas.TTF_RenderUTF8_Blended(
            self.fonts[font_key], text.encode('utf-8'), canvas.SDL_Color(*color,255))
        if not surface:
            raise RuntimeError('Cannot rasterize CHECKMATE UI text')
        try:
            texture = canvas.SDL_CreateTextureFromSurface(canvas.renderer, surface)
            if not texture:
                raise RuntimeError('Cannot create CHECKMATE UI text texture')
            item = texture, surface.contents.w, surface.contents.h
        finally:
            canvas.SDL_FreeSurface(surface)
        self.textures[key] = item
        if len(self.textures) > TEXT_LIMIT:
            _, (old, _, _) = self.textures.popitem(last=False)
            canvas.SDL_DestroyTexture(old)
        return item

    def _copy(self, texture, box):
        rect = self.canvas.SDL_Rect(int(box.left),int(WINDOW_HEIGHT-box.bottom-box.height),
                                    int(box.width),int(box.height))
        self.canvas.SDL_RenderCopy(self.canvas.renderer,texture,None,c.byref(rect))

    def text(self, text, x, y, *, size=22, color=SILVER, display=False, align='center', width=None):
        if not text:
            return
        texture, w, h = self._text_texture(text,size,display,color)
        if width and w > width:
            h = round(h * width / w)
            w = width
        left = x-w/2 if align == 'center' else x-w if align == 'right' else x
        self._copy(texture,Rect(left,y-h/2,w,h))

    def sprite(self, name, box, *, fit='contain'):
        self.image(self.sprites[name],box,fit=fit)

    def image(self, image, box, *, fit='contain'):
        self._copy(image.texture,fitted_rect(image.w,image.h,box,cover=fit=='cover'))

    def fill(self, box, color, alpha=255):
        self.canvas.draw_rectangle(box.left,box.bottom,box.left+box.width-1,
                                   box.bottom+box.height-1,*color,a=alpha,filled=True)

    def panel(self, box, *, active=False, muted=False):
        l,b,w,h = box.left,box.bottom,box.width,box.height
        self.fill(box,CRIMSON if active else (76,65,77) if muted else STEEL)
        self.fill(Rect(l+1,b+1,w-2,h-2),INK)
        self.fill(Rect(l+6,b+6,w-12,h-12),(46,24,36) if active else (29,23,32))
        self.fill(Rect(l+7,b+7,w-14,h-14),(35,17,28) if active else (19,15,23))

    def pointer(self):
        import sdl2 as s
        x,y = c.c_int(),c.c_int()
        logical_x,logical_y = c.c_float(),c.c_float()
        s.SDL_GetMouseState(c.byref(x),c.byref(y))
        s.SDL_RenderWindowToLogical(self.canvas.renderer,x.value,y.value,
                                    c.byref(logical_x),c.byref(logical_y))
        return logical_x.value,WINDOW_HEIGHT-1-logical_y.value

    def combat_frame(self, name, x, y, *, width=None, height=None, tint=None):
        canvas = self.canvas
        left,top,w,h = COMBAT_REGIONS[name]
        source = canvas.SDL_Rect(left,top,w,h)
        dw,dh = w if width is None else width,h if height is None else height
        dest = canvas.SDL_Rect(round(x),round(WINDOW_HEIGHT-y-dh),dw,dh)
        texture = self.sprites['combat_frames'].texture
        if tint:
            canvas.SDL_SetTextureColorMod(texture,*tint)
        try:
            canvas.SDL_RenderCopy(canvas.renderer,texture,c.byref(source),c.byref(dest))
        finally:
            if tint:
                canvas.SDL_SetTextureColorMod(texture,255,255,255)

    def health_bar(self, health, x, y, width, *, segmented=False):
        self.fill(Rect(x,y,width,10),(68,54,63))
        self.fill(Rect(x+1,y+1,width-2,8),(34,23,30))
        filled = round(width*health.current_hp/health.max_hp)
        if filled:
            self.combat_frame('vitality',x,y,width=filled)
        if segmented:
            for i in range(1,health.max_hp):
                self.fill(Rect(x+round(width*i/health.max_hp),y,2,10),INK)

    def rule(self, x, y, width):
        self.sprite('rule',Rect(x-width//2,y-12,width,24))

    def button(self, box, label, *, active=False, enabled=True, icon=None, decorated=False):
        if decorated:
            self.sprite('button_active' if active and enabled else 'button',box)
        else:
            self.panel(box,active=active and enabled,muted=not enabled)
        center = box.bottom+box.height/2
        if icon:
            side = min(38,box.height-14)
            self.sprite(icon,Rect(box.left+48,center-side/2,side,side))
        self.text(label,box.left+box.width/2+(15 if icon else 0),center,
                  size=26 if decorated else 22,color=SILVER if enabled else DIM,
                  display=decorated,width=box.width-(130 if icon else 16))

    def close(self):
        if self.closed:
            return
        self.closed = True
        canvas = self.canvas
        if current(canvas) is self:
            del canvas._checkmate_ui
        for texture,_,_ in self.textures.values():
            canvas.SDL_DestroyTexture(texture)
        for font in self.fonts.values():
            canvas.TTF_CloseFont(font)
        for image in self.sprites.values():
            canvas.SDL_DestroyTexture(image.texture)
            image.texture = None
        self.textures.clear()
        self.fonts.clear()
        self.sprites.clear()
