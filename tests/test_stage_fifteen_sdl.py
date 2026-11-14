"""Native shared main mouse fourth upgrade and Stage15 GAME_OVER restart."""
import unittest
from tests import test_chapter_three_sdl as existing

class StageFifteenSDLTests(unittest.TestCase):
    def test_native_fourth_mouse_choice_pulse_perfect_and_death(self):
        existing.ChapterThreeSDLTests().native_path('stage15death')
