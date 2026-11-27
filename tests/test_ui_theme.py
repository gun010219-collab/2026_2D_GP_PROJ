"""Logical hit geometry and native ownership for the release UI."""
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from front_menu import FrontInput, buttons
from save_manager import SaveData
from settings_menu import Rect
from ui_theme import fitted_rect
from upgrade_renderer import CARD_RECTS, UpgradeRenderer, card_at
from upgrades import ChapterBuild, UpgradeOffer


class UIThemeTests(unittest.TestCase):
    def test_reward_card_hp_notes_use_real_options_and_hide_maxed_effects(self):
        theme = Mock()
        theme.pointer.return_value = None
        game = SimpleNamespace(chapter=1,stage_number=1)
        for build, hp_notes, carry_notes in ((ChapterBuild(),1,2),(ChapterBuild(0,3,2),0,1)):
            with self.subTest(build=build):
                theme.reset_mock()
                offer = UpgradeOffer('run','offer',1,1,'stage',build)
                UpgradeRenderer._draw_themed(theme,game,offer,False)
                text = [call.args[0] for call in theme.text.call_args_list]
                self.assertEqual(text.count('+1 current and max HP'),hp_notes)
                self.assertEqual(text.count('Current HP carries over'),carry_notes)
    def test_title_buttons_and_cards_share_the_drawn_rectangles(self):
        items = buttons('main',SaveData())
        self.assertEqual(tuple(item.label for item in items),
                         ('NEW GAME','CONTINUE','CHAPTER SELECT','SETTINGS','EXIT'))
        mouse = SimpleNamespace(SDL_MOUSEBUTTONDOWN=1,SDL_BUTTON_LEFT=1,SDL_KEYDOWN=2)
        event = SimpleNamespace(type=1,button=1)
        for item in items:
            box = item.rect
            self.assertEqual(fitted_rect(832,126,box),box)
            self.assertEqual(FrontInput().action(mouse,event,items,(box.left,box.bottom)),
                             item.action if item.enabled else None)
            self.assertIsNone(FrontInput().action(mouse,event,items,(box.left+box.width,box.bottom)))
        for i,box in enumerate(CARD_RECTS):
            self.assertEqual(card_at((box.left,box.bottom)),i)
            self.assertIsNone(card_at((box.left+box.width,box.bottom)))

    def test_background_covers_without_changing_aspect(self):
        box = fitted_rect(1672,941,Rect(0,0,1440,900),cover=True)
        self.assertEqual((box.bottom,box.height),(0,900))
        self.assertAlmostEqual(box.width/box.height,1672/941,places=3)
        self.assertLessEqual(abs(2*box.left+box.width-1440),1)

    def test_native_cache_evicts_and_frees_owned_resources(self):
        source = '''
from unittest.mock import patch
from pico2d import pico2d as c
from tools.stage5_art_preview import open_preview
from ui_theme import SPRITES, TEXT_LIMIT, UITheme, current
open_preview(c, capture=True)
try:
    with patch.object(c,'SDL_DestroyTexture',wraps=c.SDL_DestroyTexture) as destroy, \\
         patch.object(c,'TTF_CloseFont',wraps=c.TTF_CloseFont) as close_font, \\
         patch.object(c,'SDL_CreateTextureFromSurface',wraps=c.SDL_CreateTextureFromSurface) as create:
        ui = UITheme(c)
        try:
            for _ in range(3):
                ui.text('PLAYER HP',720,420)
            assert create.call_count == 1
            for index in range(TEXT_LIMIT+12):
                ui.text(f'PULSE {index}',720,420)
            assert len(ui.textures)==TEXT_LIMIT and len(ui.fonts)==1
        finally:
            ui.close()
            ui.close()
        assert current(c) is None
        assert close_font.call_count==1
        assert sum(bool(call.args[0]) for call in destroy.call_args_list)==create.call_count+len(SPRITES)
finally:
    c.close_canvas()
'''
        outcome = subprocess.run([sys.executable,'-c',source],
                                 cwd=Path(__file__).resolve().parents[1],capture_output=True,
                                 env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                                 timeout=25)
        self.assertEqual(outcome.returncode,0,outcome.stderr.decode(errors='replace'))
