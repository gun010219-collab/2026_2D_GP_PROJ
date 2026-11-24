"""Opt-in live Frozen Palace profile; approved D1 art, unchanged combat/draw."""
import logging

from arena_art_common import CAMERA, sprite_layout
from arena_art_profile import ChapterArtProfile, PieceArt, ProfileArtPath, ProfileArtRenderer
from stage10_art_renderer import LiveArenaArtPath as PreviousArtPath

FILES = {
    'background': 'assets/themed_arena/frozen.png',
    'frame': 'assets/aligned_board/frozen_c.png',
    'light': 'assets/polished_board/frozen_light.png',
    'dark': 'assets/polished_board/frozen_dark.png',
    'player': 'assets/character_concepts/player.png',
    'pawn': 'assets/chapter3_units/pawn.png',
    'rook': 'assets/chapter3_units/rook.png',
    'knight': 'assets/chapter3_units/knight.png',
}
# Reproduce the approved D1 *visible alpha* heights at front row v=0.
# These are not PNG dimensions or collision footprints. All PNGs draw square.
TARGET_ALPHA_HEIGHT = {'pawn': 66, 'rook': 78, 'knight': 80}
ALPHA_ROWS = {kind: (18, 238) for kind in TARGET_ALPHA_HEIGHT}
BASE_SIZE = {'player': 72, **{
    kind: height * 256 / 220 / (CAMERA.sprite_scale * 1.10)
    for kind, height in TARGET_ALPHA_HEIGHT.items()}}
HP_OFFSET = {'player': 5, 'pawn': 8, 'rook': 10, 'knight': 10}


def actor_layout(kind, u, v):
    return sprite_layout(kind, u, v, BASE_SIZE, {}, HP_OFFSET, ALPHA_ROWS)


FROZEN_PROFILE = ChapterArtProfile(
    chapter=3,
    surfaces={key: FILES[key] for key in ('background', 'frame', 'light', 'dark')},
    pieces={kind: PieceArt(FILES[kind], kind) for kind in BASE_SIZE},
    layout=actor_layout,
)


class Stage11ArtRenderer(ProfileArtRenderer):
    files = FILES

    def __init__(self, c, root=None, *, motion=None, kinds=None, profile=FROZEN_PROFILE):
        super().__init__(c, root, profile=profile, motion=motion, kinds=kinds)


class Stage11ArtPath(ProfileArtPath):
    def __init__(self, c, factory=None, *, motion=None):
        override = None if factory is None else lambda canvas: factory(canvas, motion=motion)
        super().__init__(c, FROZEN_PROFILE, factory=override, renderer_type=Stage11ArtRenderer, motion=motion,
                         stage=11, flag='CHECKMATE_STAGE11_ART',
                         logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    """Evaluate both paths so exits always release their previous session."""
    def __init__(self, c, *, motion=None, previous_factory=PreviousArtPath,
                 stage11_factory=None):
        self.previous = previous_factory(c, motion=motion)
        self.stage11 = Stage11ArtPath(c, stage11_factory, motion=motion)

    def draw(self, game, positions):
        previous = self.previous.draw(game, positions)
        eleven = self.stage11.draw(game, positions)
        return previous or eleven

    def close(self):
        self.previous.close()
        self.stage11.close()
