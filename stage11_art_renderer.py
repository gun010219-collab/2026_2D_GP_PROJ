"""Opt-in live Frozen Palace profile; approved D1 art, unchanged combat/draw."""
import logging

from arena_art_common import CAMERA, ArenaArtError, SessionArtPath, sprite_layout
from stage7_art_renderer import Stage7ArtRenderer
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


class Stage11ArtRenderer(Stage7ArtRenderer):
    files = FILES

    def __init__(self, c, root=None, *, motion=None):
        super().__init__(c, root=root, motion=motion)
        try:
            for key, image in self.images.items():
                if not image.texture:
                    raise ArenaArtError('Stage11 texture creation failed: ' + key)
        except BaseException:
            self.close()
            raise

    def layout(self, kind, u, v):
        return actor_layout(kind, u, v)


class Stage11ArtPath(SessionArtPath):
    def __init__(self, c, factory=Stage11ArtRenderer, *, motion=None):
        super().__init__(c, lambda canvas: factory(canvas, motion=motion),
                         stage=11, flag='CHECKMATE_STAGE11_ART',
                         logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    """Evaluate both paths so exits always release their previous session."""
    def __init__(self, c, *, motion=None, previous_factory=PreviousArtPath,
                 stage11_factory=Stage11ArtRenderer):
        self.previous = previous_factory(c, motion=motion)
        self.stage11 = Stage11ArtPath(c, stage11_factory, motion=motion)

    def draw(self, game, positions):
        previous = self.previous.draw(game, positions)
        eleven = self.stage11.draw(game, positions)
        return previous or eleven

    def close(self):
        self.previous.close()
        self.stage11.close()
