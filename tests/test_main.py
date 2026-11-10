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
        return canvas

    def run_with_canvas(self, canvas):
        with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}):
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
        canvas.clear_canvas.side_effect = RuntimeError('render failure')
        with self.assertRaisesRegex(RuntimeError, 'render failure'):
            self.run_with_canvas(canvas)
        canvas.close_canvas.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
