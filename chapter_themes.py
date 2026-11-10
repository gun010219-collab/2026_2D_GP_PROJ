"""Visual palettes only. Chapter IDs match stage_data.json, without game rules."""
from dataclasses import dataclass
from types import MappingProxyType

Color = tuple[int, int, int]


@dataclass(frozen=True)
class ChapterTheme:
    chapter: int
    name: str
    background: Color
    tile_light: Color
    tile_dark: Color
    frame: Color
    accent: Color
    hud_background: Color
    hud_accent: Color


THEMES = MappingProxyType({
    1: ChapterTheme(1, 'Royal Chess', (17, 21, 28), (218, 216, 203), (45, 53, 64),
                    (54, 45, 32), (188, 155, 91), (25, 30, 39), (207, 176, 109)),
    2: ChapterTheme(2, 'Ancient Forest', (14, 25, 22), (170, 185, 145), (46, 70, 54),
                    (49, 45, 32), (155, 171, 100), (22, 36, 29), (173, 193, 119)),
    3: ChapterTheme(3, 'Frozen Palace', (16, 26, 40), (204, 226, 234), (52, 82, 108),
                    (38, 62, 82), (132, 190, 214), (22, 38, 55), (170, 222, 240)),
    4: ChapterTheme(4, 'Obsidian Caldera', (27, 18, 21), (183, 159, 142), (56, 42, 45),
                    (58, 35, 31), (192, 104, 59), (37, 25, 28), (224, 143, 79)),
    5: ChapterTheme(5, 'Gothic Throne', (20, 18, 29), (181, 174, 189), (47, 38, 57),
                    (55, 44, 57), (153, 123, 95), (29, 24, 38), (187, 112, 127)),
})


def get_theme(chapter: int) -> ChapterTheme:
    if type(chapter) is not int:
        raise TypeError('Chapter must be an integer')
    if chapter not in THEMES:
        raise ValueError('Chapter must be between 1 and 5')
    return THEMES[chapter]
