import unittest
from unittest.mock import Mock

from frame_timing import FramePacer
from sdl_input import poll_ready_events


class ReleasePacingTests(unittest.TestCase):
    def test_wake_latency_is_repaid_once_and_long_stalls_begin_a_fresh_period(self):
        pacer=FramePacer(180)
        step=1/180
        self.assertAlmostEqual(pacer.remaining(.002,1.),step-.002)
        self.assertAlmostEqual(pacer.remaining(.002,1.+step+.0004),step-.0024)
        self.assertEqual(pacer.remaining(.020,1.+2*step),0)
        self.assertAlmostEqual(pacer.remaining(.002,1.15),step-.002)
        self.assertAlmostEqual(pacer.remaining(.002,1.15+step),step-.002)

    def test_idle_poll_pumps_focus_and_preserves_the_original_input_batch(self):
        canvas=Mock(SDL_FIRSTEVENT=0,SDL_LASTEVENT=65535)
        canvas.SDL_HasEvents.side_effect=(0,1)
        result=poll_ready_events(canvas)
        self.assertEqual(tuple(result),())
        canvas.get_events.assert_not_called()
        canvas.print_fps.assert_called_once_with()
        self.assertIs(poll_ready_events(canvas),canvas.get_events.return_value)
        canvas.get_events.assert_called_once_with()
        self.assertEqual(canvas.SDL_PumpEvents.call_count,2)
        canvas.SDL_HasEvents.assert_called_with(0,65535)
