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
from tests.test_chapter_four_entry import completed_three
from tests import test_chapter_three_sdl as existing

class ChapterFourSDLTests(unittest.TestCase):
    def test_native_stage15_n_lava_then_six_enemy_clear_holds17(self):
        existing.ChapterThreeSDLTests().native_path('chapter4')

    def test_native_stage16_death_restarts_fresh_lava16(self):
        existing.ChapterThreeSDLTests().native_path('stage16death')

    def test_main_chapter4_factory_input_board_failure_preserves_old_theme_then_retry(self):
        for failure in ('factory','input','board'):
            with self.subTest(failure=failure):
                f=completed_three();old_game,old_run=f.game,f.run
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
                    if failure=='board' and kw['chapter']==4 and 4 not in board_calls:
                        board_calls.append(4);raise RuntimeError('board')
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
                self.assertEqual(snapshots[3][0].stage_number,16)
                self.assertTrue(snapshots[3][2]);self.assertFalse(snapshots[3][3])
                self.assertEqual(board_calls[0],3);self.assertEqual(board_calls[-1],4)

    def test_native_mouse_first_upgrade17_death_resets_to16(self):
        existing.ChapterThreeSDLTests().native_path('stage17death')

    def test_native_second_mouse_upgrade18_death_returns16(self):
        existing.ChapterThreeSDLTests().native_path('stage18death')
