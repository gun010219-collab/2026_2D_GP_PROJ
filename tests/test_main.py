"""Loop control tests with a fake canvas; these do not verify Windows GUI."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main


class WindowLoopTests(unittest.TestCase):
    def make_canvas(self):
        canvas = Mock()
        canvas.SDL_QUIT = 256
        canvas.SDL_KEYDOWN = 768
        canvas.SDLK_ESCAPE = 27
        canvas.SDLK_F11 = 1073741892
        canvas.SDL_MOUSEBUTTONDOWN = 1025
        canvas.SDL_BUTTON_LEFT = 1
        return canvas

    def run_with_canvas(self, canvas):
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings'), patch.object(main, 'SettingsRenderer'):
            main.main()

    def test_escape_and_close_release_resources_on_repeated_runs(self):
        for kind, key in [(768, 27), (256, None), (768, 27)]:
            with self.subTest(kind=kind):
                canvas = self.make_canvas()
                canvas.get_events.return_value = [SimpleNamespace(type=kind, key=key)]
                self.run_with_canvas(canvas)
                canvas.open_canvas.assert_called_once_with(1440, 900)
                canvas.close_canvas.assert_called_once_with()
                canvas.draw_rectangle.assert_not_called()

    def test_render_frame_is_paced_and_title_restored(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [[], [SimpleNamespace(type=256)]]
        with patch.object(main, 'sleep') as sleeper:
            self.run_with_canvas(canvas)
        self.assertGreaterEqual(canvas.draw_rectangle.call_count, 100)
        canvas.update_canvas.assert_called_once_with()
        sleeper.assert_called_once()
        self.assertGreaterEqual(sleeper.call_args.args[0], 0)
        canvas.SDL_SetWindowTitle.assert_called_with(canvas.window, b'CHECKMATE')
        canvas.close_canvas.assert_called_once_with()

    def test_render_failure_still_releases_resources(self):
        canvas = self.make_canvas()
        canvas.get_events.return_value = []
        canvas.SDL_RenderClear.side_effect = RuntimeError('render failure')
        with self.assertRaisesRegex(RuntimeError, 'render failure'):
            self.run_with_canvas(canvas)
        canvas.close_canvas.assert_called_once_with()

    def test_menu_escape_is_consumed_before_normal_escape_exit(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=768, key=27)],
            [SimpleNamespace(type=768, key=27)],
        ]
        self.run_with_canvas(canvas)
        self.assertEqual(canvas.update_canvas.call_count, 2)
        canvas.close_canvas.assert_called_once_with()

    def test_f11_and_menu_click_use_same_display_toggle(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [
            [SimpleNamespace(type=768, key=1073741892)],
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=1025, button=1, x=720, y=427)],
            [SimpleNamespace(type=256)],
        ]
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
                patch.object(main, 'DisplaySettings') as display, \
                patch.object(main, 'SettingsRenderer'):
            main.main()
        self.assertEqual(display.return_value.toggle.call_count, 2)
        canvas.open_canvas.assert_called_once_with(1440, 900)

    def test_x_exits_while_menu_is_open(self):
        canvas = self.make_canvas()
        canvas.get_events.side_effect = [
            [SimpleNamespace(type=1025, button=1, x=1295, y=41)],
            [SimpleNamespace(type=256)],
        ]
        self.run_with_canvas(canvas)
        canvas.close_canvas.assert_called_once_with()

    def test_x_is_not_lost_in_same_batch_as_f11(self):
        canvas = self.make_canvas()
        canvas.get_events.return_value = [SimpleNamespace(type=768, key=1073741892),
                                         SimpleNamespace(type=256)]
        self.run_with_canvas(canvas)
        canvas.update_canvas.assert_not_called()
        canvas.close_canvas.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
