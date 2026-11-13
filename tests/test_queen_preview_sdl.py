"""Hidden native SDL preview uses the shared main fixed-tick input loop."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class QueenPreviewSDLTests(unittest.TestCase):
    def run_preview(self,parry):
        script=textwrap.dedent('''
            import ctypes,sys
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as c
            from main import run_session
            from tools.queen_preview import PreviewCombat,PreviewFlow,PreviewRenderer
            g=PreviewCombat();now=[0.0];started=[False];frames=[0];done=[False];closed=[]
            poll_real,present_real=c.get_events,c.update_canvas
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0 and c.TTF_Init()==0
                c.window=s.SDL_CreateWindow(b'Queen preview test',0,0,w,h,s.SDL_WINDOW_HIDDEN)
                c.renderer=s.SDL_CreateRenderer(c.window,-1,s.SDL_RENDERER_SOFTWARE)
                c.canvas_width,c.canvas_height=w,h
            def close_window():
                s.SDL_DestroyRenderer(c.renderer);s.SDL_DestroyWindow(c.window)
                c.TTF_Quit();s.SDL_Quit();closed.append(True)
            def poll():
                started[0]=True;s.SDL_FlushEvents(s.SDL_FIRSTEVENT,s.SDL_LASTEVENT)
                if done[0]:
                    e=s.SDL_Event();e.type=s.SDL_QUIT;s.SDL_PushEvent(ctypes.byref(e))
                elif sys.argv[1]=='parry' and g.combat.tick==65:
                    for kind in (s.SDL_KEYDOWN,s.SDL_KEYUP):
                        e=s.SDL_Event();e.type=kind;e.key.keysym.sym=s.SDLK_LSHIFT
                        s.SDL_PushEvent(ctypes.byref(e))
                return poll_real()
            def present():
                if not started[0]:present_real();return
                if g.combat.tick==73:
                    q=g.encounter.enemies[0]
                    assert q.health.current_hp==14
                    if sys.argv[1]=='parry':
                        assert g.player.health.current_hp==3 and g.combat.pending_attack_bonus==2
                        assert g.resolver.last_parry_result.status=='perfect'
                    else:assert g.player.health.current_hp==2
                    done[0]=True
                present_real();now[0]+=1/60;frames[0]+=1;assert frames[0]<90
            with patch.object(c,'open_canvas',side_effect=open_window),patch.object(c,'close_canvas',side_effect=close_window), \\
                 patch.object(c,'get_events',side_effect=poll),patch.object(c,'update_canvas',side_effect=present), \\
                 patch.object(c,'SDL_GetWindowFlags',return_value=s.SDL_WINDOW_INPUT_FOCUS), \\
                 patch('main.perf_counter',side_effect=lambda:now[0]),patch('main.sleep'):
                run_session(g,PreviewFlow(3),game_renderer=PreviewRenderer())
            assert done[0] and closed==[True]
        ''')
        r=subprocess.run([sys.executable,'-c',script,'parry' if parry else 'hit'],
            cwd=Path(__file__).resolve().parents[1],env={**os.environ,'SDL_VIDEODRIVER':'dummy'},
            capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_native_preview_real_queen_damage(self):self.run_preview(False)
    def test_native_preview_real_shift_perfect(self):self.run_preview(True)
