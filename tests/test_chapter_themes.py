import json
from pathlib import Path
import unittest

from chapter_themes import THEMES, get_theme


class ThemeTests(unittest.TestCase):
    def test_five_distinct_palettes(self):
        self.assertEqual(set(THEMES), {1, 2, 3, 4, 5})
        self.assertEqual(len({theme.name for theme in THEMES.values()}), 5)
        for chapter, theme in THEMES.items():
            self.assertEqual(get_theme(chapter).chapter, chapter)
            for color in (theme.background, theme.tile_light, theme.tile_dark,
                          theme.frame, theme.accent, theme.hud_background, theme.hud_accent):
                self.assertEqual(len(color), 3)
                self.assertTrue(all(type(v) is int and 0 <= v <= 255 for v in color))
            # Relative luminance separation is a palette guard, not a visual playtest.
            luminance = lambda rgb: sum(v * w for v, w in zip(rgb, (0.2126, 0.7152, 0.0722)))
            self.assertGreater(luminance(theme.tile_light) - luminance(theme.tile_dark), 80)

    def test_stage_chapters_select_expected_theme(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'stage_data.json').read_text('utf-8'))
        for stage in data['stages']:
            with self.subTest(stage=stage['stage']):
                self.assertEqual(get_theme(stage['chapter']).chapter, (stage['stage'] - 1) // 5 + 1)

    def test_invalid_chapters(self):
        for chapter in (0, -1, 6, 25):
            with self.subTest(chapter=chapter), self.assertRaises(ValueError):
                get_theme(chapter)
        for chapter in (True, 1.0, '1', None):
            with self.subTest(chapter=chapter), self.assertRaises(TypeError):
                get_theme(chapter)
