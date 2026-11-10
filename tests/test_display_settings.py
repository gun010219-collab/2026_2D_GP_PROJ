import unittest
from unittest.mock import Mock

from display_settings import DisplaySettings, logical_mouse_to_canvas


class FakeSDL:
    SDL_WINDOW_FULLSCREEN = 1
    SDL_WINDOW_FULLSCREEN_DESKTOP = 4097

    def __init__(self):
        self.window = object()
        self.renderer = object()
        self.flags = 0
        self.bounds = (120, 80, 1440, 900)
        self.fail = False
        self.SDL_SetHint = Mock()
        self.SDL_RenderSetLogicalSize = Mock(return_value=0)
        self.SDL_GetError = Mock(return_value=b'test SDL error')
        self.calls = []

    def SDL_GetWindowFlags(self, window):
        return self.flags

    def SDL_GetWindowPosition(self, window, x, y):
        x._obj.value, y._obj.value = self.bounds[:2]

    def SDL_GetWindowSize(self, window, w, h):
        w._obj.value, h._obj.value = self.bounds[2:]

    def SDL_SetWindowFullscreen(self, window, flags):
        self.calls.append(flags)
        if self.fail:
            return -1
        self.flags = flags
        self.bounds = (0, 0, 1920, 1080) if flags else (0, 0, 1440, 900)
        return 0

    def SDL_SetWindowSize(self, window, w, h):
        self.bounds = (*self.bounds[:2], w, h)

    def SDL_SetWindowPosition(self, window, x, y):
        self.bounds = (x, y, *self.bounds[2:])


class DisplayTests(unittest.TestCase):
    def test_repeated_toggle_restores_bounds(self):
        c = FakeSDL()
        display = DisplaySettings(c)
        for _ in range(5):
            self.assertTrue(display.toggle())
            self.assertTrue(display.fullscreen)
            self.assertTrue(display.toggle())
            self.assertFalse(display.fullscreen)
            self.assertEqual(c.bounds, (120, 80, 1440, 900))
        self.assertEqual(c.calls, [4097, 0] * 5)

    def test_failed_enter_and_exit_show_actual_flags(self):
        c = FakeSDL()
        display = DisplaySettings(c)
        for flags in (0, 4097):
            c.flags = flags
            c.fail = True
            with self.assertLogs('display_settings', level='ERROR'):
                self.assertFalse(display.toggle())
            self.assertEqual(display.fullscreen, bool(flags))
            self.assertIn('test SDL error', display.error)

    def test_recovery_clears_error(self):
        c = FakeSDL()
        display = DisplaySettings(c)
        c.fail = True
        with self.assertLogs('display_settings', level='ERROR'):
            display.toggle()
        c.fail = False
        self.assertTrue(display.toggle())
        self.assertEqual(display.error, '')

    def test_state_is_not_cached(self):
        c = FakeSDL()
        display = DisplaySettings(c)
        c.flags = 4097
        self.assertTrue(display.fullscreen)
        c.flags = 0
        self.assertFalse(display.fullscreen)

    def test_logical_size_failure_is_fatal(self):
        c = FakeSDL()
        c.SDL_RenderSetLogicalSize.return_value = -1
        with self.assertRaisesRegex(RuntimeError, 'logical rendering'):
            DisplaySettings(c)

    def test_success_return_without_changed_flags_is_error(self):
        c = FakeSDL()
        c.SDL_SetWindowFullscreen = Mock(return_value=0)
        display = DisplaySettings(c)
        with self.assertLogs('display_settings', level='ERROR'):
            self.assertFalse(display.toggle())
        self.assertFalse(display.fullscreen)

    def test_mouse_origin_edges_and_bars(self):
        self.assertEqual(logical_mouse_to_canvas(0, 0), (0, 899))
        self.assertEqual(logical_mouse_to_canvas(1439, 899), (1439, 0))
        for point in [(-1, 200), (1440, 200), (200, -1), (200, 900), (float('nan'), 0)]:
            self.assertIsNone(logical_mouse_to_canvas(*point))
