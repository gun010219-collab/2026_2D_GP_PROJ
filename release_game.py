"""Own the release window and resources while combat sessions come and go."""
from time import perf_counter, sleep
import os

from campaign_save import start_chapter
from config import WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from display_settings import DisplaySettings, logical_mouse_to_canvas
from frame_timing import FramePacer
from front_menu import FrontInput, FrontRenderer, buttons
from game_audio import AudioManager, MixerAudio
from save_manager import SaveStore, save_path
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer


class ReleaseGame:
    def __init__(self,canvas,path,factory):
        self.canvas, self.factory = canvas, factory
        self.store = SaveStore(path)
        self.menu = SettingsMenu()
        self.menu.audio = self.store.data.audio()
        self.display = DisplaySettings(canvas)
        if self.store.data.fullscreen:
            self.display.toggle()
        self.settings_renderer = self.front = self.audio = None
        self.ending = None
        try:
            self.settings_renderer = SettingsRenderer(canvas)
            self.front = FrontRenderer(canvas,self.settings_renderer)
            if os.environ.get('CHECKMATE_AUDIO','1') == '1':
                backend = MixerAudio.open(canvas)
                if backend is not None:
                    self.audio = AudioManager(backend,self.menu.audio)
        except BaseException:
            self.close()
            raise

    def close(self):
        try:
            if self.audio is not None:
                self.audio.close()
        finally:
            try:
                if self.front is not None:
                    self.front.close()
            finally:
                if self.settings_renderer is not None:
                    self.settings_renderer.close()

    def save_settings(self):
        self.store.settings(self.menu.audio,self.display.fullscreen)
        if self.audio is not None:
            self.audio.apply_settings()

    def front_loop(self,screen,replay):
        c = self.canvas
        self.menu.in_frontend = True
        self.menu.can_return_to_title = False
        keyboard = FrontInput()
        pacer = FramePacer()
        if self.audio is not None:
            self.audio.set_music('ending' if screen in ('ending','credits') else 'menu')
        while True:
            started = perf_counter()
            items = buttons(screen,self.store.data,replay)
            focused = bool(c.SDL_GetWindowFlags(c.window) & c.SDL_WINDOW_INPUT_FOCUS)
            events = c.get_events()
            c.SDL_SetWindowTitle(c.window,WINDOW_TITLE.encode('utf-8'))
            if any(event.type == c.SDL_QUIT for event in events):
                return 'exit'
            for event in events:
                if not focused:
                    continue
                mouse = event.type == c.SDL_MOUSEBUTTONDOWN and event.button == c.SDL_BUTTON_LEFT
                point = logical_mouse_to_canvas(event.x,event.y) if mouse else None
                key = event.key if event.type == c.SDL_KEYDOWN and not getattr(event,'repeat',False) else None
                if key == c.SDLK_F11:
                    self.display.toggle()
                    self.save_settings()
                    break
                if self.menu.is_open:
                    changed = False
                    if key == c.SDLK_ESCAPE:
                        self.menu.key('escape')
                        changed = True
                    elif mouse:
                        action = self.menu.click(point)
                        changed = not self.menu.is_open or action in ('audio_changed','toggle_fullscreen')
                        if action == 'audio_changed':
                            self.save_settings()
                        elif action == 'toggle_fullscreen':
                            self.display.toggle()
                            self.save_settings()
                    if changed and self.audio is not None:
                        self.audio.play('ui_select')
                    break  # A modal/display change cannot activate a menu item in this batch.
                if key == c.SDLK_ESCAPE:
                    return {'main':'exit','chapters':'main','ending':'main','credits':'ending'}[screen]
                action = keyboard.action(c,event,items,point)
                if action is None:
                    continue
                if self.audio is not None:
                    self.audio.play('ui_select')
                if action == 'settings':
                    self.menu.is_open = True
                    break
                return action
            c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
            c.SDL_RenderClear(c.renderer)
            selected = keyboard.selected if keyboard.preview is None else keyboard.preview
            self.front.draw_screen(screen,self.store.data,self.store.notice,selected,self.ending,replay)
            if self.menu.is_open:
                self.settings_renderer.draw(self.menu,self.display)
            c.update_canvas()
            sleep(pacer.remaining(perf_counter()-started))

    def run(self,play):
        screen = 'main'
        retained = None
        try:
            while True:
                action = self.front_loop(screen,retained is not None)
                if action == 'exit':
                    return
                if action in ('chapters','credits','main','ending'):
                    screen = action
                    if screen == 'main' and retained is not None:
                        retained.run.retire()
                        retained = None
                    continue
                if action == 'replay':
                    flow = retained
                    flow.restart(self.factory)
                    retained = None
                else:
                    chapter = 1 if action == 'new' else self.store.data.continue_chapter if action == 'continue' else action
                    flow = start_chapter(self.store,chapter,self.factory)
                self.menu.in_frontend = False
                self.menu.can_return_to_title = True
                destination = play(flow.game,flow,default_art=True,app=self)
                self.menu.is_open = False
                if destination == 'exit':
                    return
                if destination == 'ending':
                    retained = flow
                    screen = 'ending'
                else:
                    screen = 'main'
        finally:
            if retained is not None:
                retained.run.retire()
            self.store.flush()


def launch(factory,play,*,path=None):
    from pico2d import pico2d as canvas

    canvas.open_canvas(WINDOW_WIDTH,WINDOW_HEIGHT)
    try:
        if not canvas.window or not canvas.renderer:
            raise RuntimeError('Pico2D could not create a window and renderer')
        canvas.hide_lattice()
        canvas.SDL_SetWindowTitle(canvas.window,WINDOW_TITLE.encode('utf-8'))
        app = ReleaseGame(canvas,save_path() if path is None else path,factory)
        try:
            app.run(play)
        finally:
            app.close()
    finally:
        canvas.close_canvas()
