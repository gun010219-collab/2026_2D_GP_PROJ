"""Real SDL dummy-driver regression: no Windows GUI is opened or verified."""
import os
import subprocess
import sys
import textwrap
import unittest


class SDLMouseMappingTests(unittest.TestCase):
    def test_scaled_letterboxed_events_are_transformed_once(self):
        script = textwrap.dedent('''
            import ctypes
            import sdl2 as s
            from display_settings import DisplaySettings, logical_mouse_to_canvas
            from settings_menu import SETTINGS_BUTTON
            from settings_menu import SettingsMenu
            from settings_renderer import SettingsRenderer
            from pico2d import pico2d as canvas
            from player import load_stage1_player
            from player_renderer import PlayerRenderer
            from combat import Combat
            from attack_renderer import AttackRenderer
            from parry import Parry
            from parry_renderer import ParryRenderer
            from types import SimpleNamespace
            assert s.SDL_Init(s.SDL_INIT_VIDEO) == 0
            try:
                for width, height in [(1440,900),(1920,1080),(1280,1024),(2880,1800)]:
                    window = s.SDL_CreateWindow(b'test', 0, 0, width, height, s.SDL_WINDOW_HIDDEN)
                    renderer = s.SDL_CreateRenderer(window, -1, s.SDL_RENDERER_SOFTWARE)
                    assert window and renderer
                    try:
                        adapter = SimpleNamespace(**{name: getattr(s, name) for name in dir(s)})
                        adapter.window, adapter.renderer = window, renderer
                        DisplaySettings(adapter)
                        scale = min(width / 1440, height / 900)
                        ox, oy = (width-1440*scale)/2, (height-900*scale)/2
                        def click(px, py):
                            s.SDL_FlushEvents(s.SDL_FIRSTEVENT, s.SDL_LASTEVENT)
                            event = s.SDL_Event()
                            event.type = s.SDL_MOUSEBUTTONDOWN
                            event.button.windowID = s.SDL_GetWindowID(window)
                            event.button.button = s.SDL_BUTTON_LEFT
                            event.button.x, event.button.y = int(px), int(py)
                            assert s.SDL_PushEvent(ctypes.byref(event)) == 1
                            out = s.SDL_Event()
                            while s.SDL_PollEvent(ctypes.byref(out)):
                                if out.type == s.SDL_MOUSEBUTTONDOWN:
                                    return logical_mouse_to_canvas(out.button.x, out.button.y)
                            raise AssertionError('missing mouse event')
                        x = SETTINGS_BUTTON.left + SETTINGS_BUTTON.width/2
                        y = SETTINGS_BUTTON.bottom + SETTINGS_BUTTON.height/2
                        point = click(ox + x*scale, oy + (899-y)*scale)
                        assert SETTINGS_BUTTON.contains(point), (width,height,point)
                        assert abs(point[0]-x) <= 2 and abs(point[1]-y) <= 2
                        if ox > 2:
                            assert click(0, height/2) is None
                        if oy > 2:
                            assert click(width/2, 0) is None
                        # Exercise the actual installed Pico2D/TTF draw path offscreen.
                        canvas.window, canvas.renderer = window, renderer
                        canvas.canvas_width, canvas.canvas_height = 1440, 900
                        assert canvas.TTF_Init() == 0
                        ui = SettingsRenderer(canvas)
                        try:
                            AttackRenderer().draw(canvas, Combat().request_attack(load_stage1_player()))
                            PlayerRenderer().draw(canvas, load_stage1_player())
                            parry = Parry()
                            parry.request(0)
                            for tick in (0, 8, 18):
                                ParryRenderer().draw(canvas, load_stage1_player(), parry, tick)
                            menu = SettingsMenu()
                            ui.draw(menu, SimpleNamespace(fullscreen=False, error=''))
                            menu.is_open = True
                            for state in (False, True):
                                ui.draw(menu, SimpleNamespace(fullscreen=state, error='test'))
                            canvas.update_canvas()
                            # Installed Pico2D filters repeat KEYDOWN and retains KEYUP.
                            s.SDL_FlushEvents(s.SDL_FIRSTEVENT, s.SDL_LASTEVENT)
                            for kind, repeat in [(s.SDL_KEYDOWN, 0), (s.SDL_KEYDOWN, 1), (s.SDL_KEYUP, 0)]:
                                event = s.SDL_Event()
                                event.type = kind
                                event.key.windowID = s.SDL_GetWindowID(window)
                                event.key.keysym.sym = s.SDLK_UP
                                event.key.repeat = repeat
                                assert s.SDL_PushEvent(ctypes.byref(event)) == 1
                            keys = canvas.get_events()
                            assert [(e.type, e.key) for e in keys] == [(s.SDL_KEYDOWN,s.SDLK_UP),(s.SDL_KEYUP,s.SDLK_UP)]
                            for kind, repeat in [(s.SDL_KEYDOWN, 0), (s.SDL_KEYDOWN, 1), (s.SDL_KEYUP, 0)]:
                                event = s.SDL_Event()
                                event.type = kind
                                event.key.windowID = s.SDL_GetWindowID(window)
                                event.key.keysym.sym = s.SDLK_SPACE
                                event.key.repeat = repeat
                                assert s.SDL_PushEvent(ctypes.byref(event)) == 1
                            keys = canvas.get_events()
                            assert [(e.type, e.key) for e in keys] == [(s.SDL_KEYDOWN,s.SDLK_SPACE),(s.SDL_KEYUP,s.SDLK_SPACE)]
                            for shift in (s.SDLK_LSHIFT, s.SDLK_RSHIFT):
                                for kind, repeat in [(s.SDL_KEYDOWN, 0), (s.SDL_KEYDOWN, 1), (s.SDL_KEYUP, 0)]:
                                    event = s.SDL_Event()
                                    event.type = kind
                                    event.key.windowID = s.SDL_GetWindowID(window)
                                    event.key.keysym.sym = shift
                                    event.key.repeat = repeat
                                    assert s.SDL_PushEvent(ctypes.byref(event)) == 1
                                keys = canvas.get_events()
                                assert [(e.type, e.key) for e in keys] == [(s.SDL_KEYDOWN,shift),(s.SDL_KEYUP,shift)]
                        finally:
                            ui.close()
                            canvas.TTF_Quit()
                    finally:
                        s.SDL_DestroyRenderer(renderer)
                        s.SDL_DestroyWindow(window)
            finally:
                s.SDL_Quit()
        ''')
        result = subprocess.run([sys.executable, '-c', script],
                                env={**os.environ, 'SDL_VIDEODRIVER': 'dummy'},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
