"""Short hidden native SDL run with real perf_counter and the real render limiter."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class FrameTelemetrySDLTests(unittest.TestCase):
    def test_real_clock_dummy_renderer_reports_measurements_and_closes(self):
        script=textwrap.dedent('''
            import time,ctypes
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as c
            import main
            started=time.perf_counter();closed=[]
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0 and c.TTF_Init()==0
                c.window=s.SDL_CreateWindow(b'Frame telemetry',0,0,w,h,s.SDL_WINDOW_HIDDEN)
                c.renderer=s.SDL_CreateRenderer(c.window,-1,s.SDL_RENDERER_SOFTWARE)
                c.canvas_width,c.canvas_height=w,h
            def close_window():
                s.SDL_DestroyRenderer(c.renderer);s.SDL_DestroyWindow(c.window)
                c.TTF_Quit();s.SDL_Quit();closed.append(True)
            def poll():
                if time.perf_counter()-started>1.25:
                    e=s.SDL_Event();e.type=s.SDL_QUIT;s.SDL_PushEvent(ctypes.byref(e))
                return [] if time.perf_counter()-started<=1.25 else c_get()
            c_get=c.get_events
            g=main._new_game()
            with patch.object(c,'open_canvas',side_effect=open_window),patch.object(c,'close_canvas',side_effect=close_window), \\
                 patch.object(c,'get_events',side_effect=poll),patch.object(c,'SDL_GetWindowFlags',return_value=s.SDL_WINDOW_INPUT_FOCUS), \\
                 patch.object(main,'_new_game',return_value=g):
                main.main()
            assert closed==[True] and 30<=g.combat.tick<=85,g.combat.tick
        ''')
        r=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).resolve().parents[1],
                         env={**os.environ,'SDL_VIDEODRIVER':'dummy','CHECKMATE_FRAME_STATS':'1'},capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('CHECKMATE RENDERER',r.stdout);self.assertIn('active_sim_hz=',r.stdout)
        self.assertIn('p99_ms=',r.stdout)
        print(r.stdout)
