"""Native SDL shared main path with third mouse choice and Stage14 restart."""
import unittest
from tests import test_chapter_three_sdl as existing

class StageFourteenSDLTests(unittest.TestCase):
    def test_native_mouse_third_choice_and_death_restores_entry(self):
        existing.ChapterThreeSDLTests().native_path('stage14death')
