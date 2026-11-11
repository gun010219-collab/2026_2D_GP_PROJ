"""Actual SDL events/Pico2D Stage 4 drawing; not a Windows manual playtest."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class StageFourSDLTests(unittest.TestCase):
    def test_native_n_transition_fifty_square_warning_and_perfect_bishop(self):
        script=textwrap.dedent('''
            import ctypes
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from config import FIXED_TIME_STEP
            from game_renderer import GameFlowRenderer
            now,frames,started=[0.0],[0],[False]
            games,warnings,labels,opened,closed=[],[],[],[],[]
            factory=main._new_stage_game
            real_poll,real_present=canvas.get_events,canvas.update_canvas
            warning_draw=main.EnemyAttackRenderer.draw
            real_text=main.HealthRenderer._text
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0
                assert canvas.TTF_Init()==0
                canvas.window=s.SDL_CreateWindow(b'Bishop test',0,0,w,h,s.SDL_WINDOW_HIDDEN)
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
                    e.health.apply_damage(e.health.current_hp,tick=g.combat.tick)
                    g.encounter.deactivate(e.entity_instance_id)
                g.update_state()
            def initial():
                g=factory(3)
                clear(g)
                games.append(g)
                return g
            def create(n):
                g=factory(n)
                games.append(g)
                return g
            def push(kind,key=None):
                e=s.SDL_Event()
                e.type=kind
                if key is not None:
                    e.key.windowID=s.SDL_GetWindowID(canvas.window)
                    e.key.keysym.sym=key
                assert s.SDL_PushEvent(ctypes.byref(e))==1
            def poll():
                started[0]=True
                s.SDL_FlushEvents(s.SDL_FIRSTEVENT,s.SDL_LASTEVENT)
                if frames[0]==0:
                    push(s.SDL_KEYDOWN,s.SDLK_n)
                    push(s.SDL_KEYUP,s.SDLK_n)
                elif frames[0]==19:
                    push(s.SDL_KEYDOWN,s.SDLK_LSHIFT)
                elif frames[0]==21:
                    push(s.SDL_QUIT)
                return real_poll()
            def present():
                if not started[0]:
                    real_present()
                    return
                if frames[0]==20:
                    g=games[-1]
                    assert g.stage_number==4 and g.combat.tick==156
                    assert g.resolver.last_parry_result.status=='perfect'
                    assert g.player.health.current_hp==3 and g.combat.pending_attack_bonus==2
                    assert g.encounter.enemies[0].state=='stunned'
                    assert g.encounter.enemies[0].position==(2,8)
                    assert [e.kind for e in g.encounter.enemies]==['bishop','rook','pawn','pawn']
                    for terminal in ('dead','clear'):
                        t=factory(4)
                        if terminal=='dead':
                            t.player.health.apply_damage(3,tick=0)
                            t.update_state()
                        else:
                            clear(t)
                        GameFlowRenderer().draw(canvas,t)
                real_present()
                now[0]+=(5 if frames[0]==18 else 7 if frames[0]==19 else 8)*FIXED_TIME_STEP
                frames[0]+=1
            def warning(renderer,c,ledger):
                bishop_id=games[-1].encounter.enemies[0].entity_instance_id
                warnings.extend(e.target_cells for e in ledger.telegraphs if e.source_entity_instance_id==bishop_id)
                warning_draw(renderer,c,ledger)
            def text(c,value,*args,**kwargs):
                labels.append(value)
                real_text(c,value,*args,**kwargs)
            with patch.object(canvas,'open_canvas',side_effect=open_window), \
                 patch.object(canvas,'close_canvas',side_effect=close_window), \
                 patch.object(canvas,'get_events',side_effect=poll), \
                 patch.object(canvas,'update_canvas',side_effect=present), \
                 patch.object(canvas,'SDL_GetWindowFlags',return_value=s.SDL_WINDOW_INPUT_FOCUS), \
                 patch.object(main,'_new_game',side_effect=initial), \
                 patch.object(main,'_new_stage_game',side_effect=create), \
                 patch.object(main.EnemyAttackRenderer,'draw',warning), \
                 patch.object(main.HealthRenderer,'_text',side_effect=text), \
                 patch.object(main,'perf_counter',side_effect=lambda:now[0]), \
                 patch.object(main,'sleep'):
                main.main()
            assert opened==[(1440,900)] and closed==[True]
            assert [g.stage_number for g in games]==[3,4]
            assert warnings and all(len(set(cells))==50 for cells in warnings)
            assert all((x+y)%2==0 for cells in warnings for x,y in cells)
            assert 'STAGE 4' in labels and '4/4' in labels and '2/2' in labels
            assert 'STAGE CLEAR' in labels and 'GAME OVER' in labels and 'R TO STAGE 1' in labels
            print('PASS: actual SDL N event, Bishop fifty-cell warning, perfect and overlays')
        ''')
        result=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).resolve().parents[1],
            env={**os.environ,'SDL_VIDEODRIVER':'dummy'},capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':
    unittest.main()
