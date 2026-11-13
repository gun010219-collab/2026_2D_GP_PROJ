"""Extend the existing native Chapter3 path to the new death/restart endpoint."""
import unittest
from tests import test_chapter_three_sdl as existing

class StageThirteenSDLTests(unittest.TestCase):
    def test_native_stage13_game_over_restarts11_after_two_choices(self):
        existing.ChapterThreeSDLTests().native_path('stage13death')
