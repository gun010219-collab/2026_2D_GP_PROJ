"""Chapter3 real main/SDL paths; terminal fixtures are separate from real fight tests."""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import main
from game import GameState
from chapter_run import ChapterRun
from renderer import BoardRenderer
from sdl_input import GameplayInput
from tests.test_chapter_three_entry import completed_two
from tests import test_main as canvas_tests
from tests.test_stage_transition import key, N, R, SPACE, SHIFT, UP, run_loop
from upgrades import ChapterBuild


class ChapterThreeSDLTests(unittest.TestCase):
    def native_path(self, mode):
        script=textwrap.dedent('''
            import ctypes,sys
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main
            from game import GameState
            from config import FIXED_TIME_STEP
            from tests.test_chapter_three_entry import completed_two
            from tests.test_stage_transition import finish
            mode=sys.argv[1]
            initial=completed_two();old_run=initial.run
            games=[initial.game];flows=[];themes=[];labels=[];closed=[]
            now,frame,started=[0.0],[0],[False]
            flags=[s.SDL_WINDOW_INPUT_FOCUS]
            phase=[0];done=[False];held=[None]
            factory_real=main._new_stage_game
            flow_real=main.StageProgression
            poll_real,present_real=canvas.get_events,canvas.update_canvas
            board_real=main.BoardRenderer.draw;text_real=main.HealthRenderer._text
            def create(n,**kw):
                assert n in (11,12,13,14,15),n  # Stage16 must never be requested.
                g=factory_real(n,**kw);games.append(g);return g
            def progress(*a,**kw):
                f=flow_real(*a,**kw);flows.append(f);return f
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0 and canvas.TTF_Init()==0
                canvas.window=s.SDL_CreateWindow(b'CHECKMATE Chapter3',0,0,w,h,s.SDL_WINDOW_HIDDEN)
                canvas.renderer=s.SDL_CreateRenderer(canvas.window,-1,s.SDL_RENDERER_SOFTWARE)
                assert canvas.window and canvas.renderer
                canvas.canvas_width,canvas.canvas_height=w,h
            def close_window():
                s.SDL_DestroyRenderer(canvas.renderer);s.SDL_DestroyWindow(canvas.window)
                canvas.TTF_Quit();s.SDL_Quit();closed.append(True)
            def push(kind,key=None,x=0,y=0):
                e=s.SDL_Event();e.type=kind
                if key is not None:e.key.keysym.sym=key
                if kind in (s.SDL_MOUSEBUTTONDOWN,s.SDL_MOUSEBUTTONUP):
                    e.button.button=s.SDL_BUTTON_LEFT;e.button.x,e.button.y=x,y
                assert s.SDL_PushEvent(ctypes.byref(e))==1
            def tap(key):
                push(s.SDL_KEYDOWN,key);push(s.SDL_KEYUP,key)
            def click(x,y):
                push(s.SDL_MOUSEBUTTONDOWN,x=x,y=y);push(s.SDL_MOUSEBUTTONUP,x=x,y=y)
            def poll():
                started[0]=True;s.SDL_FlushEvents(s.SDL_FIRSTEVENT,s.SDL_LASTEVENT)
                f=frame[0];g=games[-1]
                flags[0]=0 if f==8 else s.SDL_WINDOW_INPUT_FOCUS
                if done[0]:
                    if mode=='boundary':tap(s.SDLK_ESCAPE)
                    else:push(s.SDL_QUIT)
                elif f==1:
                    tap(s.SDLK_n);tap(s.SDLK_SPACE);tap(s.SDLK_LSHIFT);tap(s.SDLK_UP)
                elif f==4:
                    if mode=='boundary':tap(s.SDLK_2)
                    else:click(450,500)  # ATTACK through the real mouse mapping.
                    tap(s.SDLK_r);tap(s.SDLK_n)
                elif f==5:tap(s.SDLK_F11)
                elif f==6:click(1295,41)
                elif f==7:tap(s.SDLK_ESCAPE)
                elif g.stage_number in (12,13,14,15) and g.state is GameState.GAME_OVER:
                    tap(s.SDLK_r)
                elif phase[0]==7:
                    if mode=='boundary':tap(s.SDLK_2)
                    else:click(450,500)
                elif phase[0]==8:tap(s.SDLK_n)
                elif phase[0]==9:tap(s.SDLK_r)
                elif g.stage_number==15 and g.encounter.pulse.event is not None and g.playing and g.combat.tick==g.encounter.pulse.event.hit_tick-8:tap(s.SDLK_LSHIFT)
                elif phase[0]==5:
                    if mode=='boundary':tap(s.SDLK_1)
                    else:click(450,500)
                elif phase[0]==3:
                    tap(s.SDLK_1)
                elif g.stage_number==13 and g.playing and g.combat.tick==49:tap(s.SDLK_UP)
                elif g.stage_number==13 and g.playing and g.combat.tick==67:tap(s.SDLK_UP)
                elif mode=='stage13death' and g.stage_number==13 and g.playing and g.combat.tick==113:tap(s.SDLK_LSHIFT)
                elif phase[0]==2:
                    for k in (s.SDLK_1,s.SDLK_2,s.SDLK_3,s.SDLK_r,s.SDLK_n,s.SDLK_SPACE,s.SDLK_LSHIFT,s.SDLK_UP):tap(k)
                    click(450,500);click(730,500);click(990,500)
                return poll_real()
            def present():
                if not started[0]:present_real();return
                f=frame[0];g=games[-1];flow=flows[0]
                if g.stage_number in (13,14,15) and g.combat.tick==0 and phase[0] in (3,5,7):phase[0]=0
                if f==0:
                    assert g.state is GameState.BOSS_CLEAR and g.next_stage_number==11
                if f==1:
                    assert old_run.retired and flow.run.chapter==3 and flow.run.entry_attack_level==4
                    assert g.stage_number==11 and g.combat.tick==0 and g.player.position==(5,1)
                    assert (g.resolver.player_damage,g.player.health.current_hp,flow.run.stats.move_interval_ticks)==(5,3,18)
                    assert len(flow.run.receipts)==0 and flow.offer is None
                    assert not g.encounter.ledger.pending and g.parry.last_attempt is None
                    assert g.combat.active_attack is None and themes[-1]==3
                    assert [e.health.max_hp for e in g.encounter.enemies]==[12,12,10,10,7]
                if f==2:finish(g,'clear')  # Terminal fixture, not actual enemy combat proof.
                if f==3:assert flow.offer.stage==11
                if f==4:
                    assert g.stage_number==12 and g.combat.tick==0 and len(flow.run.receipts)==1
                    assert [e.health.max_hp for e in g.encounter.enemies]==[10,10,12,7,7]
                    assert g.player.health.current_hp==(4 if mode=='boundary' else 3)
                    assert g.resolver.player_damage==(5 if mode=='boundary' else 6)
                    assert themes[-1]==3
                if g.stage_number==12 and g.playing and g.combat.tick>=80:
                    a,b=g.encounter.enemies[:2]
                    assert a.current_attack and len(a.current_attack.target_cells)==50
                    assert b.current_attack is None  # Opposite-color serialization in real main.
                    finish(g,'dead' if mode=='death' else 'clear')
                    phase[0]=1
                elif phase[0]==1 and g.stage_number==12 and g.state is GameState.UPGRADE:
                    assert flow.offer.stage==12 and len(flow.run.receipts)==1
                    phase[0]=3
                elif g.stage_number==13 and g.playing and g.combat.tick>=121:
                    qe=next(r.event for r in g.encounter.ledger._records.values() if r.event.attack_kind=='queen_diagonal')
                    assert g.encounter.ledger.outcome(qe)==('parried_perfect' if mode=='stage13death' else 'hit')
                    if mode=='stage13death':assert g.combat.pending_attack_bonus==2
                    assert [e.health.max_hp for e in g.encounter.enemies]==[14,10,7,7,7]
                    finish(g,'dead' if mode=='stage13death' else 'clear')
                    phase[0]=4
                elif phase[0]==4 and g.stage_number==13 and g.state is GameState.UPGRADE:
                    assert flow.offer.stage==13 and len(flow.run.receipts)==2
                    phase[0]=5
                elif g.stage_number==14 and g.playing and g.combat.tick>=80:
                    assert len(flow.run.receipts)==3 and themes[-1]==3
                    assert [e.health.max_hp for e in g.encounter.enemies]==[14,12,10,7,7]
                    q,r,b,*_=g.encounter.enemies
                    assert q.current_attack and q.current_attack.attack_kind=='queen_diagonal'
                    assert b.current_attack and len(b.current_attack.target_cells)==50
                    finish(g,'dead' if mode=='stage14death' else 'clear')
                    phase[0]=6
                elif phase[0]==6 and g.stage_number==14 and g.state is GameState.UPGRADE:
                    assert flow.offer.stage==14 and len(flow.run.receipts)==3
                    phase[0]=7
                elif g.stage_number==15 and g.playing and phase[0]!=9:
                    assert len(flow.run.receipts)==4 and themes[-1]==3
                    assert [e.health.max_hp for e in g.encounter.enemies]==[60,14,12,7,7]
                    ev=g.encounter.pulse.event
                    if ev and g.encounter.ledger.state(ev)=='resolved':
                        assert g.encounter.ledger.outcome(ev)=='parried_perfect'
                        assert g.encounter.pulse.king.health.current_hp==58
                        finish(g,'dead' if mode=='stage15death' else 'clear');phase[0]=10
                elif phase[0]==10 and g.stage_number==15 and g.state is GameState.BOSS_CLEAR:
                    assert flow.offer is None and g.next_stage_number is None
                    held[0]=(flow.run,flow.run.build,flow.run.receipts);phase[0]=8
                elif phase[0]==8:
                    assert (flow.run,flow.run.build,flow.run.receipts)==held[0] and len(games)==6
                    phase[0]=9
                elif phase[0]==9 and g.stage_number==15 and g.combat.tick==0:
                    assert (flow.run,flow.run.build,flow.run.receipts)==held[0]
                    assert g.encounter.pulse.king.health.current_hp==60;done[0]=True
                if (mode=='death' and len(games)==4) or (mode=='stage13death' and len(games)==5) or (mode=='stage14death' and len(games)==6) or (mode=='stage15death' and len(games)==7):
                    assert g.stage_number==11 and g.combat.tick==0 and themes[-1]==3
                    assert (g.resolver.player_damage,g.player.health.current_hp,flow.run.stats.move_interval_ticks)==(5,3,18)
                    assert flow.run.receipts==() and flow.run.entry_attack_level==4
                    assert g.combat.stage_instance_id!=games[-2].combat.stage_instance_id
                    done[0]=True
                present_real();frame[0]+=1;now[0]+=FIXED_TIME_STEP
                assert frame[0]<1000
            def board(self,*a,**kw):themes.append(self.theme.chapter);board_real(self,*a,**kw)
            def text(c,label,*a,**kw):labels.append(label);text_real(c,label,*a,**kw)
            with patch.object(canvas,'open_canvas',side_effect=open_window), \\
                 patch.object(canvas,'close_canvas',side_effect=close_window), \\
                 patch.object(canvas,'get_events',side_effect=poll), \\
                 patch.object(canvas,'update_canvas',side_effect=present), \\
                 patch.object(canvas,'SDL_GetWindowFlags',side_effect=lambda w:flags[0]), \\
                 patch.object(main,'_new_game',return_value=initial.game), \\
                 patch.object(main,'_new_stage_game',side_effect=create), \\
                 patch.object(main,'StageProgression',side_effect=progress), \\
                 patch.object(main.BoardRenderer,'draw',board), \\
                 patch.object(main.HealthRenderer,'_text',side_effect=text), \\
                 patch.object(main.UpgradeRenderer,'_text',side_effect=text), \\
                 patch.object(main,'perf_counter',side_effect=lambda:now[0]), \\
                 patch.object(main,'sleep'):
                main.main(run=old_run)
            assert done[0] and closed==[True] and themes[0]==2 and themes[-1]==3
            assert 'N TO CHAPTER 3' in labels
            if mode=='boundary':
                assert 'BOSS CLEAR' in labels and 'R TO RESTART' in labels
                assert not any('TRY AGAIN' in s for s in labels)
            assert [g.stage_number for g in games]==([10,11,12,13,14,15,15] if mode=='boundary' else [10,11,12,13,14,15,11] if mode=='stage15death' else [10,11,12,13,14,11] if mode=='stage14death' else [10,11,12,13,11] if mode=='stage13death' else [10,11,12,11])
            print('PASS native Chapter3',mode,'ice/receipt/keyboard/mouse/settings/F11/focus/quit')
        ''')
        result=subprocess.run([sys.executable,'-c',script,mode],cwd=Path(__file__).resolve().parents[1],
                              env={**os.environ,'SDL_VIDEODRIVER':'dummy'},capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_native_boss_n_ice_keyboard_upgrade_and_held_boundary(self):
        self.native_path('boundary')

    def test_native_mouse_upgrade_death_restart_restores_entry_attack(self):
        self.native_path('death')

    def test_main_factory_input_board_failure_preserves_old_theme_then_retry(self):
        for failure in ('factory','input','board'):
            with self.subTest(failure=failure):
                f=completed_two();old_game,old_run=f.game,f.run
                canvas=canvas_tests.WindowLoopTests().make_canvas()
                canvas.SDL_SCANCODE_N=17
                batches=iter([[key(N)],[key(N,repeat=True)],[key(N,False)],[key(N)],[SimpleNamespace(type=256)]])
                canvas.get_events.side_effect=lambda:next(batches)
                controls_calls=[0];factory_calls=[0];board_calls=[];snapshots=[]
                def controls(*a,**kw):
                    controls_calls[0]+=1
                    if failure=='input' and controls_calls[0]==2:raise RuntimeError('input')
                    return GameplayInput(*a,**kw)
                def board(*a,**kw):
                    if failure=='board' and kw['chapter']==3 and 3 not in board_calls:
                        board_calls.append(3);raise RuntimeError('board')
                    board_calls.append(kw['chapter']);return BoardRenderer(*a,**kw)
                def factory(n,**kw):
                    factory_calls[0]+=1
                    if failure=='factory' and factory_calls[0]==1:raise RuntimeError('factory')
                    return original(n,**kw)
                def rendered():
                    snapshots.append((f.game,f.run,old_run.retired,f.error))
                canvas.update_canvas.side_effect=rendered
                original=main._new_stage_game
                with patch.dict(sys.modules,{'pico2d':SimpleNamespace(pico2d=canvas)}), \
                     patch.object(main,'_new_game',return_value=old_game), \
                     patch.object(main,'StageProgression',return_value=f), \
                     patch.object(main,'_new_stage_game',side_effect=factory), \
                     patch.object(main,'GameplayInput',side_effect=controls), \
                     patch.object(main,'BoardRenderer',side_effect=board), \
                     patch.object(main,'SettingsRenderer'),patch.object(main,'DisplaySettings'),patch.object(main,'sleep'):
                    main.main(run=old_run)
                for g,r,retired,error in snapshots[:3]:
                    self.assertIs(g,old_game);self.assertIs(r,old_run)
                    self.assertFalse(retired);self.assertTrue(error)
                self.assertEqual(snapshots[3][0].stage_number,11)
                self.assertTrue(snapshots[3][2]);self.assertFalse(snapshots[3][3])
                self.assertEqual(board_calls[0],2);self.assertEqual(board_calls[-1],3)

    def test_main_chapter_three_attack_max_blocked_while_hp_choice_works(self):
        factory=main._new_stage_game
        games,snapshots,*_=run_loop([[key(49)],[key(49,False)],[key(50)]],initial_stage=11,
            entry_attack_level=15,initial_factory=lambda:factory(11,stats=ChapterBuild(15).stats))
        self.assertEqual([g.stage_number for g in games],[11,12])
        self.assertEqual([s['stage'] for s in snapshots],[11,11,12])
        self.assertEqual((games[-1].resolver.player_damage,games[-1].player.health.max_hp),(16,4))


if __name__=='__main__':
    unittest.main()
