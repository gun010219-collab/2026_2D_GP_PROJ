"""Native SDL upgrade events/rendering; this is not a Windows GUI playtest."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class UpgradeSDLTests(unittest.TestCase):
    def test_native_main_four_upgrades_max_menu_focus_replay_and_reset(self):
        script=textwrap.dedent('''
            import ctypes
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from chapter_run import ChapterRun
            from game import GameState
            from config import FIXED_TIME_STEP
            run=ChapterRun()
            now,frame,started=[0.0],[0],[False]
            games,labels,draw_order,closed=[],[],[],[]
            flags=[s.SDL_WINDOW_INPUT_FOCUS]
            one,stage=main._new_game,main._new_stage_game
            poll_real,present_real=canvas.get_events,canvas.update_canvas
            text_real=main.UpgradeRenderer._text
            upgrade_real,settings_real=main.UpgradeRenderer.draw,main.SettingsRenderer.draw
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0
                assert canvas.TTF_Init()==0
                canvas.window=s.SDL_CreateWindow(b'CHECKMATE upgrade test',0,0,w,h,s.SDL_WINDOW_HIDDEN)
                canvas.renderer=s.SDL_CreateRenderer(canvas.window,-1,s.SDL_RENDERER_SOFTWARE)
                assert canvas.window and canvas.renderer
                canvas.canvas_width,canvas.canvas_height=w,h
            def close_window():
                s.SDL_DestroyRenderer(canvas.renderer)
                s.SDL_DestroyWindow(canvas.window)
                canvas.TTF_Quit()
                s.SDL_Quit()
                closed.append(True)
            def first(**kwargs):
                g=one(**kwargs)
                games.append(g)
                return g
            def create(n,**kwargs):
                # Stage 1 dispatches through the wrapped legacy factory.
                g=stage(n,**kwargs)
                if n!=1:games.append(g)
                return g
            def clear(g):
                for e in g.encounter.enemies:
                    if e.alive:e.health.apply_damage(e.health.current_hp,tick=g.combat.tick)
                    g.encounter.deactivate(e.entity_instance_id,tick=g.combat.tick)
                g.update_state()
            def push(kind,key=None,x=0,y=0,repeat=0):
                e=s.SDL_Event()
                e.type=kind
                if key is not None:
                    e.key.keysym.sym=key
                    e.key.repeat=repeat
                if kind in (s.SDL_MOUSEBUTTONDOWN,s.SDL_MOUSEBUTTONUP):
                    e.button.button=s.SDL_BUTTON_LEFT
                    e.button.x,e.button.y=x,y
                assert s.SDL_PushEvent(ctypes.byref(e))==1
            def tap(k):
                push(s.SDL_KEYUP,k)
                push(s.SDL_KEYDOWN,k)
                push(s.SDL_KEYUP,k)
            def click(x,y):
                push(s.SDL_MOUSEBUTTONUP,x=x,y=y)
                push(s.SDL_MOUSEBUTTONDOWN,x=x,y=y)
                push(s.SDL_MOUSEBUTTONUP,x=x,y=y)
            def poll():
                started[0]=True
                s.SDL_FlushEvents(s.SDL_FIRSTEVENT,s.SDL_LASTEVENT)
                f=frame[0]
                if f in (1,2):tap(s.SDLK_1)
                if f==4:click(450,499)
                if f==6:tap(s.SDLK_1)
                if f==7:click(450,499)
                if f==8:
                    click(1295,41)
                    tap(s.SDLK_2)
                if f==9:
                    tap(s.SDLK_F11)
                    tap(s.SDLK_2)
                if f==10:
                    tap(s.SDLK_ESCAPE)
                    tap(s.SDLK_2)
                if f==12:
                    flags[0]=0
                    tap(s.SDLK_2)
                if f==13:
                    flags[0]=s.SDL_WINDOW_INPUT_FOCUS
                    tap(s.SDLK_2)
                if f in (15,17):
                    click(730,499)
                    tap(s.SDLK_3)
                    tap(s.SDLK_SPACE)
                    tap(s.SDLK_UP)
                if f==18:tap(s.SDLK_1)  # Boss N enters Chapter 2 in the separate Stage 6 SDL path.
                if f==20:tap(s.SDLK_n)
                if f in (19,21):tap(s.SDLK_r)
                if f==22:push(s.SDL_QUIT)
                return poll_real()
            def present():
                if not started[0]:
                    present_real()
                    return
                f=frame[0];g=games[-1]
                if f in (0,2,4,15,17):
                    assert g.stage_number=={0:1,2:2,4:3,15:4,17:5}[f]
                    assert g.combat.tick==0
                    assert g.combat.pending_attack_bonus==0 and g.parry.last_attempt is None
                    assert g.player.position==(5,1)
                    assert g.player.health.current_hp==g.player.health.max_hp
                    clear(g)
                if f in (1,3,5,6,7,8,9,10,11,12,13,14,16):
                    assert g.state is GameState.UPGRADE
                    assert g.combat.tick==0
                if 5<=f<=14:assert len(games)==3
                if f==18:
                    assert g.state is GameState.BOSS_CLEAR
                    assert run.active_offer is None and len(run.receipts)==4
                if f==19:
                    assert g.stage_number==5 and g.playing
                    assert g.player.health.current_hp==5 and g.resolver.player_damage==3
                    assert g.encounter.pulse.king.health.max_hp==8
                    assert g.encounter.pulse.event is None
                    g.player.health.apply_damage(5,tick=g.combat.tick)
                    g.update_state()
                if f==20:assert g.state is GameState.GAME_OVER
                if f==21:
                    assert g.stage_number==1 and g.playing
                    assert g.player.health.current_hp==3 and g.resolver.player_damage==1
                    assert run.retired
                assert draw_order[-1]=='settings'
                present_real()
                now[0]+=FIXED_TIME_STEP
                frame[0]+=1
                assert frame[0]<25
            def text(c,value,*args,**kwargs):
                labels.append(value)
                text_real(c,value,*args,**kwargs)
            def upgrade(self,*args,**kwargs):
                draw_order.append('upgrade')
                upgrade_real(self,*args,**kwargs)
            def settings(self,*args,**kwargs):
                draw_order.append('settings')
                settings_real(self,*args,**kwargs)
            with patch.object(canvas,'open_canvas',side_effect=open_window), \
                 patch.object(canvas,'close_canvas',side_effect=close_window), \
                 patch.object(canvas,'get_events',side_effect=poll), \
                 patch.object(canvas,'update_canvas',side_effect=present), \
                 patch.object(canvas,'SDL_GetWindowFlags',side_effect=lambda w:flags[0]), \
                 patch.object(main,'_new_game',side_effect=first), \
                 patch.object(main,'_new_stage_game',side_effect=create), \
                 patch.object(main.UpgradeRenderer,'_text',side_effect=text), \
                 patch.object(main.UpgradeRenderer,'draw',upgrade), \
                 patch.object(main.SettingsRenderer,'draw',settings), \
                 patch.object(main,'perf_counter',side_effect=lambda:now[0]), \
                 patch.object(main,'sleep'):
                main.main(run=run)
            assert [g.stage_number for g in games]==[1,2,3,4,5,5,1]
            assert len({g.combat.stage_instance_id for g in games})==7
            assert [(g.player.health.max_hp,g.resolver.player_damage) for g in games]==[(3,1),(3,2),(3,3),(4,3),(5,3),(5,3),(3,1)]
            assert len(run.receipts)==4 and closed==[True]
            for value in ('UPGRADE','1 ATTACK','2 MAX HP','3 MOVE','MAX','NOW 3','NEXT 4','NEXT 15'):
                assert value in labels,value
            print('PASS: native SDL four upgrades/MAX/settings/F11/focus/boss replay/game over')
        ''')
        result=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).resolve().parents[1],
                              env={**os.environ,'SDL_VIDEODRIVER':'dummy'},capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
