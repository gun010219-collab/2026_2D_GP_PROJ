"""Real SDL events and Pico2D drawing under dummy video, not desktop GUI QA."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class StageFiveSDLTests(unittest.TestCase):
    def test_native_main_boss_pulse_perfect_clear_restart_and_settings(self):
        script=textwrap.dedent('''
            import ctypes
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from chapter_run import ChapterRun
            run=ChapterRun()
            for number in range(1,4):
                run.select(run.offer_after_clear(number,f"prior-{number}"),("move","move","attack")[number-1])
            from config import FIXED_TIME_STEP
            from game import GameState
            now,started,phase=[0.0],[False],['start']
            games,warnings,labels,opened,closed=[],[],[],[],[]
            flags=[s.SDL_WINDOW_INPUT_FOCUS]
            factory=main._new_stage_game
            real_poll,real_present=canvas.get_events,canvas.update_canvas
            warning_draw=main.EnemyAttackRenderer.draw
            real_text=main.HealthRenderer._text
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0
                assert canvas.TTF_Init()==0
                canvas.window=s.SDL_CreateWindow(b'CHECKMATE boss test',0,0,w,h,s.SDL_WINDOW_HIDDEN)
                canvas.renderer=s.SDL_CreateRenderer(canvas.window,-1,s.SDL_RENDERER_SOFTWARE)
                assert canvas.window and canvas.renderer
                canvas.canvas_width,canvas.canvas_height=w,h
                opened.append((w,h))
            def close_window():
                s.SDL_DestroyRenderer(canvas.renderer)
                s.SDL_DestroyWindow(canvas.window)
                canvas.TTF_Quit()
                s.SDL_Quit()
                closed.append(True)
            def clear(g):
                for e in g.encounter.enemies:
                    if e.alive:
                        e.health.apply_damage(e.health.current_hp,tick=g.combat.tick)
                    g.encounter.deactivate(e.entity_instance_id,tick=g.combat.tick)
                g.update_state()
            def initial():
                g=factory(4)
                clear(g)
                games.append(g)
                return g
            def create(n, **kwargs):
                g=factory(n, **kwargs)
                games.append(g)
                return g
            def push(kind,key=None):
                event=s.SDL_Event()
                event.type=kind
                if key is not None:
                    event.key.windowID=s.SDL_GetWindowID(canvas.window)
                    event.key.keysym.sym=key
                if kind==s.SDL_MOUSEBUTTONDOWN:
                    event.button.button=s.SDL_BUTTON_LEFT
                    event.button.x,event.button.y=1295,41
                assert s.SDL_PushEvent(ctypes.byref(event))==1
            def poll():
                started[0]=True
                s.SDL_FlushEvents(s.SDL_FIRSTEVENT,s.SDL_LASTEVENT)
                if phase[0]=='start':
                    push(s.SDL_KEYDOWN,s.SDLK_1)
                    push(s.SDL_KEYUP,s.SDLK_1)
                    phase[0]='fight'
                elif phase[0]=='fight' and games[-1].combat.tick==376:
                    push(s.SDL_KEYDOWN,s.SDLK_LSHIFT)
                elif phase[0]=='clear':
                    push(s.SDL_KEYDOWN,s.SDLK_1)
                    push(s.SDL_KEYUP,s.SDLK_1)
                elif phase[0]=='restart':
                    push(s.SDL_KEYDOWN,s.SDLK_r)
                    push(s.SDL_KEYUP,s.SDLK_r)
                elif phase[0]=='menu':
                    push(s.SDL_MOUSEBUTTONDOWN)
                elif phase[0]=='escape':
                    push(s.SDL_KEYDOWN,s.SDLK_ESCAPE)
                elif phase[0]=='f11':
                    push(s.SDL_KEYDOWN,s.SDLK_F11)
                elif phase[0]=='lost':
                    flags[0]=0
                elif phase[0]=='gained':
                    flags[0]=s.SDL_WINDOW_INPUT_FOCUS
                elif phase[0]=='quit':
                    push(s.SDL_QUIT)
                return real_poll()
            def present():
                if not started[0]:
                    real_present()
                    return
                g=games[-1]
                tick=g.combat.tick
                if phase[0]=='fight' and tick==385:
                    assert g.resolver.last_parry_result.status=='perfect'
                    assert g.encounter.pulse.king.health.current_hp==20
                    assert g.combat.pending_attack_bonus==2 and g.player.health.current_hp==2
                    assert g.encounter.pulse.king.stun_until_tick==445
                if phase[0]=='fight' and tick==417:
                    clear(g)
                    phase[0]='clear'
                elif phase[0]=='clear':
                    assert g.state is GameState.BOSS_CLEAR and len(games)==2
                    phase[0]='restart'
                elif phase[0]=='restart':
                    assert len(games)==3 and tick==0 and g.stage_number==5
                    assert g.encounter.pulse.event is None
                    assert g.encounter.pulse.king.health.current_hp==22
                    phase[0]='menu'
                elif phase[0]=='menu':
                    phase[0]='paused'
                    pause_tick[0]=tick
                elif phase[0]=='paused':
                    assert tick==pause_tick[0]
                    phase[0]='escape'
                elif phase[0]=='escape':
                    phase[0]='f11'
                elif phase[0]=='f11':
                    phase[0]='lost'
                elif phase[0]=='lost':
                    pause_tick[0]=tick
                    phase[0]='gained'
                elif phase[0]=='gained':
                    assert tick==pause_tick[0]
                    phase[0]='quit'
                real_present()
                now[0]+=(2 if tick==376 else 7 if tick==378 else 8)*FIXED_TIME_STEP
                assert now[0]<20
            pause_tick=[None]
            def warning(renderer,c,ledger):
                warnings.extend(e.target_cells for e in ledger.telegraphs if e.attack_kind=='king_pulse')
                warning_draw(renderer,c,ledger)
            def text(c,value,*args,**kwargs):
                labels.append(value)
                real_text(c,value,*args,**kwargs)
            with patch.object(canvas,'open_canvas',side_effect=open_window), \\
                 patch.object(canvas,'close_canvas',side_effect=close_window), \\
                 patch.object(canvas,'get_events',side_effect=poll), \\
                 patch.object(canvas,'update_canvas',side_effect=present), \\
                 patch.object(canvas,'SDL_GetWindowFlags',side_effect=lambda w:flags[0]), \\
                 patch.object(main,'_new_game',side_effect=initial), \\
                 patch.object(main,'_new_stage_game',side_effect=create), \\
                 patch.object(main.EnemyAttackRenderer,'draw',warning), \\
                 patch.object(main.HealthRenderer,'_text',side_effect=text), \\
                 patch.object(main,'perf_counter',side_effect=lambda:now[0]), \\
                 patch.object(main,'sleep'):
                main.main(run=run)
            assert opened==[(1440,900)] and closed==[True]
            assert [g.stage_number for g in games]==[4,5,5]
            assert warnings and all(len(cells)==len(set(cells))==100 for cells in warnings)
            for label in ('STAGE 5','KING HP 22/22','KING HP 20/22','CHECKMATE PULSE',
                          'CLEANUP','PERFECT PARRY','BOSS CLEAR','R TO RESTART'):
                assert label in labels,label
            print('PASS: native Stage 5/Pulse/perfect/HP/clear/replay/settings/F11/focus/quit')
        ''')
        result=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).resolve().parents[1],
                              env={**os.environ,'SDL_VIDEODRIVER':'dummy'},capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':
    unittest.main()
