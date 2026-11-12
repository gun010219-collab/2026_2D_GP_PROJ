"""Actual SDL Chapter 1 completion/Chapter 2 entry without desktop GUI claims."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


class StageSixSDLTests(unittest.TestCase):
    def test_native_main_boss_replay_next_chapter_death_boundary_and_modal_inputs(self):
        script=textwrap.dedent('''
            import ctypes
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from chapter_run import ChapterRun
            from config import FIXED_TIME_STEP
            from game import GameState
            run=ChapterRun()
            now,frame,started=[0.0],[0],[False]
            games,flows,themes,labels,closed=[],[],[],[],[]
            flags=[s.SDL_WINDOW_INPUT_FOCUS]
            first_factory,stage_factory=main._new_game,main._new_stage_game
            flow_factory=main.StageProgression
            poll_real,present_real=canvas.get_events,canvas.update_canvas
            board_real=main.BoardRenderer.draw
            text_real=main.HealthRenderer._text
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0
                assert canvas.TTF_Init()==0
                canvas.window=s.SDL_CreateWindow(b'CHECKMATE Chapter 2 test',0,0,w,h,s.SDL_WINDOW_HIDDEN)
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
                game=first_factory(**kwargs)
                games.append(game)
                return game
            def create(n,**kwargs):
                assert 1<=n<=9,n
                game=stage_factory(n,**kwargs)
                if n!=1:games.append(game)
                return game
            def progress(*args,**kwargs):
                flow=flow_factory(*args,**kwargs)
                flows.append(flow)
                return flow
            def clear(game):
                for enemy in game.encounter.enemies:
                    if enemy.alive:enemy.health.apply_damage(enemy.health.current_hp,tick=game.combat.tick)
                    game.encounter.deactivate(enemy.entity_instance_id,tick=game.combat.tick)
                game.update_state()
            def push(kind,key=None,x=0,y=0,repeat=0):
                event=s.SDL_Event()
                event.type=kind
                if key is not None:
                    event.key.keysym.sym=key
                    event.key.repeat=repeat
                if kind in (s.SDL_MOUSEBUTTONDOWN,s.SDL_MOUSEBUTTONUP):
                    event.button.button=s.SDL_BUTTON_LEFT
                    event.button.x,event.button.y=x,y
                assert s.SDL_PushEvent(ctypes.byref(event))==1
            def tap(key):
                push(s.SDL_KEYUP,key)
                push(s.SDL_KEYDOWN,key)
                push(s.SDL_KEYUP,key)
            def poll():
                started[0]=True
                s.SDL_FlushEvents(s.SDL_FIRSTEVENT,s.SDL_LASTEVENT)
                f=frame[0]
                if f in (2,4,6,8):tap({2:s.SDLK_1,4:s.SDLK_2,6:s.SDLK_3,8:s.SDLK_2}[f])
                if f==9:tap(s.SDLK_r)
                if f==11:
                    push(s.SDL_KEYDOWN,s.SDLK_n)
                    tap(s.SDLK_UP)
                    tap(s.SDLK_SPACE)
                    tap(s.SDLK_LSHIFT)
                    tap(s.SDLK_r)
                    push(s.SDL_KEYDOWN,s.SDLK_n,repeat=1)
                if f==12:push(s.SDL_KEYDOWN,s.SDLK_n,repeat=1)
                if f==13:push(s.SDL_KEYUP,s.SDLK_n)
                if f==14:tap(s.SDLK_r)
                if f in (15,22,25,26,27,28,29):
                    if f==25:tap(s.SDLK_F11)
                    if f==26:tap(s.SDLK_ESCAPE)
                    if f==27:flags[0]=0
                    if f==28:flags[0]=s.SDL_WINDOW_INPUT_FOCUS
                    tap(s.SDLK_n)
                    tap(s.SDLK_r)
                    if f!=15:
                        tap(s.SDLK_UP)
                        tap(s.SDLK_SPACE)
                        tap(s.SDLK_LSHIFT)
                if f==23:
                    push(s.SDL_MOUSEBUTTONDOWN,x=1295,y=41)
                    push(s.SDL_MOUSEBUTTONUP,x=1295,y=41)
                if f==30:push(s.SDL_QUIT)
                if f in (17,19):tap(s.SDLK_1)
                if f==20:tap(s.SDLK_1)  # MAX must not advance.
                if f==21:
                    push(s.SDL_MOUSEBUTTONDOWN,x=730,y=500)
                    push(s.SDL_MOUSEBUTTONUP,x=730,y=500)
                return poll_real()
            boundary_tick=[None]
            second_run=[None]
            def present():
                if not started[0]:
                    present_real()
                    return
                f=frame[0];game=games[-1];flow=flows[0]
                if f in (0,2,4,6,8,9):
                    assert game.stage_number=={0:1,2:2,4:3,6:4,8:5,9:5}[f]
                    assert game.combat.tick==0
                    if f==9:
                        assert len(flow.run.receipts)==4
                        assert (game.player.health.current_hp,game.resolver.player_damage)==(5,2)
                    clear(game)
                if f==10:
                    assert game.state is GameState.BOSS_CLEAR
                    assert len(flow.run.receipts)==4 and not run.retired
                if f==11:
                    assert game.stage_number==6 and game.chapter==2 and game.playing
                    assert run.retired
                    assert flow.run.chapter==2 and flow.run.current_stage==6
                    assert len(flow.run.receipts)==0 and flow.offer is None
                    assert game.player.position==(5,1) and game.combat.tick==0
                    assert game.combat.active_attack is None and game.parry.last_attempt is None
                    assert (game.player.health.current_hp,game.resolver.player_damage)==(3,1)
                    assert themes[-1]==2
                    second_run[0]=flow.run
                if f==12:
                    assert len(games)==7 and game.stage_number==6
                if f==13:
                    game.player.health.apply_damage(3,tick=game.combat.tick)
                    game.update_state()
                    assert game.state is GameState.GAME_OVER
                if f==14:
                    assert game.stage_number==6 and game.chapter==2 and game.playing
                    assert game.combat.tick==0 and game.player.health.current_hp==3
                    assert second_run[0].retired and flow.run is not second_run[0]
                    assert len(flow.run.receipts)==0
                if f==15:
                    clear(game)
                    boundary_tick[0]=game.combat.tick
                if f in (17,19,21):
                    assert game.stage_number=={17:7,19:8,21:9}[f]
                    assert len(flow.run.receipts)=={17:1,19:2,21:3}[f]
                    assert game.resolver.player_damage=={17:2,19:3,21:3}[f]
                    clear(game)
                    boundary_tick[0]=game.combat.tick
                if f==20:
                    assert game.stage_number==8 and len(games)==10
                if 22<=f<=29:
                    assert game.state is GameState.DEV_BOUNDARY
                    assert game.combat.tick==boundary_tick[0]
                    assert flow.offer is None and len(flow.run.receipts)==3
                    assert flow.run.current_stage==9
                    assert game.restart_stage_number is None and game.next_stage_number is None
                    assert game.combat.active_attack is None and game.parry.last_attempt is None
                    assert game.player.position==(5,1)
                    assert len(games)==11
                present_real()
                frame[0]+=1
                now[0]+=FIXED_TIME_STEP
                assert frame[0]<32
            def board(self,*args,**kwargs):
                themes.append(self.theme.chapter)
                board_real(self,*args,**kwargs)
            def text(c,value,*args,**kwargs):
                labels.append(value)
                text_real(c,value,*args,**kwargs)
            with patch.object(canvas,'open_canvas',side_effect=open_window), \
                 patch.object(canvas,'close_canvas',side_effect=close_window), \
                 patch.object(canvas,'get_events',side_effect=poll), \
                 patch.object(canvas,'update_canvas',side_effect=present), \
                 patch.object(canvas,'SDL_GetWindowFlags',side_effect=lambda w:flags[0]), \
                 patch.object(main,'_new_game',side_effect=first), \
                 patch.object(main,'_new_stage_game',side_effect=create), \
                 patch.object(main,'StageProgression',side_effect=progress), \
                 patch.object(main.BoardRenderer,'draw',board), \
                 patch.object(main.HealthRenderer,'_text',side_effect=text), \
                 patch.object(main,'perf_counter',side_effect=lambda:now[0]), \
                 patch.object(main,'sleep'):
                main.main(run=run)
            assert [g.stage_number for g in games]==[1,2,3,4,5,5,6,6,7,8,9]
            assert len({g.combat.stage_instance_id for g in games})==11
            assert themes[0]==1 and themes[-1]==2
            for label in ('STAGE 6','STAGE 9 CLEAR','CHAPTER 2 DEVELOPMENT','STAGE 10 NOT AVAILABLE'):
                assert label in labels,label
            assert closed==[True]
            print('PASS: native main four upgrades/boss replay/N/forest/Stage6/death/boundary/settings/F11/focus/quit')
        ''')
        result=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).resolve().parents[1],
                              env={**os.environ,'SDL_VIDEODRIVER':'dummy'},capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
