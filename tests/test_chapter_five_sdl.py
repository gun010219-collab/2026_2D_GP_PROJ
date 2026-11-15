"""Native main through Stage15 N, lava Stage16/17, held18 and death/restart."""
import unittest
from types import SimpleNamespace
import sys
from unittest.mock import patch
import main
from sdl_input import GameplayInput
from renderer import BoardRenderer
from tests import test_main as canvas_tests
from tests.test_stage_transition import key,N
from tests.test_chapter_five_entry import completed_four
from tests import test_chapter_three_sdl as existing

class ChapterFiveSDLTests(unittest.TestCase):
    def test_main_chapter5_factory_input_board_failure_preserves_old_theme_then_retry(self):
        for failure in ('factory','input','board'):
            with self.subTest(failure=failure):
                f=completed_four();old_game,old_run=f.game,f.run
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
                    if failure=='board' and kw['chapter']==5 and 5 not in board_calls:
                        board_calls.append(5);raise RuntimeError('board')
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
                self.assertEqual(snapshots[3][0].stage_number,21)
                self.assertTrue(snapshots[3][2]);self.assertFalse(snapshots[3][3])
                self.assertEqual(board_calls[0],4);self.assertEqual(board_calls[-1],5)


    def test_native_sdl_main_n_chapter5_boundary_and_death_restart(self):
        import subprocess,os,textwrap
        from pathlib import Path
        script=textwrap.dedent('''
            from unittest.mock import patch
            import sdl2 as s
            from pico2d import pico2d as canvas
            import main,sys
            from tests.test_chapter_five_entry import completed_four
            from tests.test_stage_transition import finish
            from game import GameState
            f=completed_four();old=f.game;run=f.run;now=[0.0];frame=[0];labels=[]
            real_poll=canvas.get_events;present=canvas.update_canvas;text=main.HealthRenderer._text
            def open_window(w,h):
                assert s.SDL_Init(s.SDL_INIT_VIDEO)==0
                assert canvas.TTF_Init()==0
                canvas.window=s.SDL_CreateWindow(b'CHECKMATE Chapter5',0,0,w,h,s.SDL_WINDOW_HIDDEN)
                canvas.renderer=s.SDL_CreateRenderer(canvas.window,-1,s.SDL_RENDERER_SOFTWARE)
                assert canvas.window and canvas.renderer
                canvas.canvas_width,canvas.canvas_height=w,h
            def close_window():
                s.SDL_DestroyRenderer(canvas.renderer);s.SDL_DestroyWindow(canvas.window)
                canvas.TTF_Quit();s.SDL_Quit()
            def tap(key):
                for kind in (s.SDL_KEYDOWN,s.SDL_KEYUP):
                    e=s.SDL_Event();e.type=kind;e.key.keysym.sym=key;e.key.keysym.scancode=s.SDL_GetScancodeFromKey(key);s.SDL_PushEvent(e)
            def poll():
                i=frame[0]
                if i==1:tap(s.SDLK_n)
                if i==2:
                    assert f.game.stage_number==21 and f.game.chapter==5
                    assert f.run.stats.max_hp==3 and f.game.player.health.current_hp==3 and f.run.stats.move_interval_ticks==18
                    assert [e.health.max_hp for e in f.game.encounter.enemies]==[22,20,20,16,16,16,13]
                    finish(f.game,'dead' if sys.argv[1]=='dead' else 'clear')
                if i==3:
                    if sys.argv[1]=='dead':tap(s.SDLK_r)
                    elif sys.argv[2]=='keyboard':tap(s.SDLK_2)
                    else:
                        e=s.SDL_Event();e.type=s.SDL_MOUSEBUTTONDOWN;e.button.button=1;e.button.x=730;e.button.y=500;s.SDL_PushEvent(e)
                if i==4:
                    if sys.argv[1]=='dead':assert f.game.stage_number==21 and f.game.playing and f.game.player.health.current_hp==3
                    else:
                        assert f.game.stage_number==22 and len(f.run.receipts)==1 and f.game.player.health.current_hp==4
                        finish(f.game,'dead' if sys.argv[1]=='22dead' else 'clear')
                if i==5:
                    if sys.argv[1]=='22dead':tap(s.SDLK_r)
                    elif sys.argv[1] in ('clear','23dead'):
                        if sys.argv[2]=='keyboard':tap(s.SDLK_2)
                        else:
                            e=s.SDL_Event();e.type=s.SDL_MOUSEBUTTONDOWN;e.button.button=1;e.button.x=730;e.button.y=500;s.SDL_PushEvent(e)
                if i==6:
                    if sys.argv[1] in ('dead','22dead'):assert f.game.stage_number==21 and f.game.playing and f.run.receipts==() and f.game.player.health.current_hp==3
                    else:
                        assert f.game.stage_number==23 and len(f.run.receipts)==2 and f.game.player.health.current_hp==5
                        finish(f.game,'dead' if sys.argv[1]=='23dead' else 'clear')
                if i==7:
                    if sys.argv[1]=='23dead':tap(s.SDLK_r)
                    elif sys.argv[1]=='clear':
                        for k in (s.SDLK_1,s.SDLK_2,s.SDLK_3,s.SDLK_r,s.SDLK_n):tap(k)
                if i==8:
                    if sys.argv[1] in ('dead','22dead','23dead'):assert f.game.stage_number==21 and f.game.playing and f.run.receipts==() and f.game.player.health.current_hp==3
                    else:assert f.game.stage_number==23 and len(f.run.receipts)==2 and f.game.state is GameState.UPGRADE and f.offer.stage==23
                    event=s.SDL_Event();event.type=s.SDL_QUIT;s.SDL_PushEvent(event)
                return real_poll()
            def draw():
                present();frame[0]+=1;now[0]+=1/60
            def label(*a,**kw):labels.append(a[1]);return text(*a,**kw)
            with patch.object(canvas,'open_canvas',side_effect=open_window),patch.object(canvas,'close_canvas',side_effect=close_window),patch.object(canvas,'get_events',side_effect=poll),patch.object(canvas,'update_canvas',side_effect=draw),patch.object(canvas,'SDL_GetWindowFlags',return_value=s.SDL_WINDOW_INPUT_FOCUS),patch.object(main,'_new_game',return_value=old),patch.object(main,'StageProgression',return_value=f),patch.object(main,'perf_counter',side_effect=lambda:now[0]),patch.object(main,'sleep'),patch.object(main.HealthRenderer,'_text',side_effect=label),patch.object(main.UpgradeRenderer,'_text',side_effect=label):
                main.main(run=run)
            assert old.combat.stage_instance_id!=f.game.combat.stage_instance_id and run.retired
            if sys.argv[1]=='clear':assert 'STAGE 23 CLEAR' in labels and 'STAGE 24 NOT AVAILABLE' in labels and 'CHOOSE ONE  1 2 3 OR CLICK' in labels
            print('PASS native Stage20 N Stage21',sys.argv[1])
        ''')
        for outcome,method in (('clear','keyboard'),('clear','mouse'),('dead','keyboard'),('22dead','mouse'),('23dead','keyboard'),('23dead','mouse')):
            result=subprocess.run([sys.executable,'-c',script,outcome,method],cwd=Path(__file__).resolve().parents[1],env={**os.environ,'SDL_VIDEODRIVER':'dummy'},capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
