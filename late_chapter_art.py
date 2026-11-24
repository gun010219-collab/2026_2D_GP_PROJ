"""Chapter 4/5 presentation and independent deck/facade layers."""
from functools import partial
import ctypes

from arena_art_common import CAMERA, ArenaArtError, sprite_layout
from arena_art_profile import ChapterArtProfile, PieceArt, ProfileArtRenderer
from stage5_art_renderer import polygon


THEMES = {4: 'volcanic', 5: 'gothic'}
VISIBLE_HEIGHTS = {
    4: dict(player=83.85, pawn=65, rook=84, knight=83, bishop=88, queen=96, king=116),
    5: dict(player=83.85, pawn=66, rook=86, knight=84, bishop=89, queen=99, king=126),
}
HP = dict(player=5, pawn=8, rook=10, knight=10, bishop=10, queen=12, king=13)
ALPHA_ROWS = {(5, 'knight'): (20, 236)}


def layout(chapter, kind, u, v):
    rows = ALPHA_ROWS.get((chapter, kind), (18, 238))
    height = VISIBLE_HEIGHTS[chapter][kind]
    size = 72 if kind == 'player' else height * 256 / (rows[1] - rows[0]) / (CAMERA.sprite_scale * 1.10)
    return sprite_layout(kind, u, v, {kind: size}, {}, HP, {kind: rows})


LATE_PROFILES = {
    chapter: ChapterArtProfile(
        chapter=chapter,
        surfaces={
            'background': f'assets/themed_arena/{theme}.png',
            'frame': f'assets/aligned_board/{theme}_c.png',
            'light': f'assets/polished_board/{theme}_light.png',
            'dark': f'assets/polished_board/{theme}_dark.png',
            'panel': f'assets/side_cleanup/{theme}_panel.png',
        },
        pieces={
            'player': PieceArt('assets/character_concepts/player.png', 'player'),
            'king': PieceArt(f'assets/character_concepts/ch{chapter}_king.png', 'king'),
            **{kind: PieceArt(f'assets/late_chapter_units/ch{chapter}_{kind}.png', kind)
               for kind in ('pawn', 'rook', 'knight', 'bishop', 'queen')},
        },
        layout=partial(layout, chapter),
    )
    for chapter, theme in THEMES.items()
}

# Coordinates use the same logical canvas as CAMERA. All panel paint is below the rim.
BAY_LEFT, BAY_RIGHT, BAY_BOTTOM = 585, 885, 12
DECK_EDGE = CAMERA.corners[0][1]
RIM_EDGE = CAMERA.project(0, -.12)[1]
PANEL_TOP = int(RIM_EDGE) - 13
_PANEL_ALPHA_ROWS = {4: (43, 213), 5: (49, 207)}


class FacadeArtRenderer(ProfileArtRenderer):
    def draw_frame(self):
        import sdl2 as s

        canvas = self.c
        renderer = canvas.renderer
        former = s.SDL_Rect()
        had_clip = s.SDL_RenderIsClipEnabled(renderer)
        s.SDL_RenderGetClipRect(renderer, ctypes.byref(former))

        def select_clip(rect):
            if had_clip:
                result = s.SDL_Rect()
                if not s.SDL_IntersectRect(ctypes.byref(former), ctypes.byref(rect), ctypes.byref(result)):
                    return False
                rect = result
            if s.SDL_RenderSetClipRect(renderer, ctypes.byref(rect)):
                raise ArenaArtError('Could not clip the board facade')
            return True

        top = int(899 - DECK_EDGE)
        bottom = 899 - BAY_BOTTOM
        middle = bottom - top
        outside = ((0, 0, 1440, top), (0, bottom, 1440, 900-bottom),
                   (0, top, BAY_LEFT, middle), (BAY_RIGHT, top, 1440-BAY_RIGHT, middle))
        try:
            for bounds in outside:
                if select_clip(s.SDL_Rect(*bounds)):
                    super().draw_frame()
            if select_clip(s.SDL_Rect(BAY_LEFT, top, BAY_RIGHT-BAY_LEFT, middle)):
                self.draw_panel()
        finally:
            s.SDL_RenderSetClipRect(renderer, ctypes.byref(former) if had_clip else None)

    def draw_panel(self):
        import sdl2 as s

        chapter = self.profile.chapter
        texture = self.images['dark'].texture
        left, right = BAY_LEFT, BAY_RIGHT
        # Continue the existing horizontal fascia course through the cutout.
        # The donor strip between a corner pilaster and the first ornament is plain.
        top = int(899 - DECK_EDGE)
        height = 899 - BAY_BOTTOM - top
        donor = s.SDL_Rect(351 if chapter == 4 else 366, top, 8, height)
        dest = s.SDL_FRect(left, top, right-left, height)
        if s.SDL_RenderCopyF(self.c.renderer, self.images['frame'].texture,
                             ctypes.byref(donor), ctypes.byref(dest)):
            raise ArenaArtError('Could not join the facade material course')

        def band(bottom, top, color):
            polygon(self.c, ((left,bottom),(right,bottom),(right,top),(left,top)),
                    (*color,255), texture)

        lo, hi = _PANEL_ALPHA_ROWS[chapter]
        scale = min((right-left-12) / 476, (PANEL_TOP - BAY_BOTTOM - 2) / (hi - lo))
        self.image('panel', 735, PANEL_TOP - (128-lo)*scale, 512*scale, 256*scale)
        band(PANEL_TOP + 3, RIM_EDGE, (197, 169, 145) if chapter == 4 else (177, 170, 194))
        band(RIM_EDGE - 2, DECK_EDGE, (225, 207, 183) if chapter == 4 else (199, 188, 210))
