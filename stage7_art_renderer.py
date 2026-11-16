"""Opt-in live forest Knight arena; ground depth is independent of jump height."""
import logging
from arena_art_common import SessionArtPath, sprite_layout
from config import BOARD_LEFT, BOARD_BOTTOM, TILE_SIZE
from stage5_art_renderer import Stage5ArtRenderer
from stage6_art_renderer import FILES as FOREST_FILES, LiveArenaArtPath as PreviousArtPath

FILES = {k: v for k, v in FOREST_FILES.items() if k != 'rook'}
FILES['knight'] = 'assets/chapter2_units/knight.png'
BASE_SIZE = {'player': 72, 'pawn': 72, 'knight': 82}
ALPHA_ROWS = {'pawn': (18, 238), 'knight': (20, 235)}
HP_OFFSET = {'player': 5, 'pawn': 7, 'knight': 9}


def actor_layout(kind, u, v):
    return sprite_layout(kind, u, v, BASE_SIZE, {}, HP_OFFSET, ALPHA_ROWS)


class Stage7ArtRenderer(Stage5ArtRenderer):
    files = FILES

    def __init__(self, c, root=None, *, motion=None):
        self.motion = motion
        if root is None:
            super().__init__(c)
        else:
            super().__init__(c, root=root)

    def layout(self, kind, u, v):
        return actor_layout(kind, u, v)

    def pose(self, entity, positions):
        if self.motion is None:
            return super().pose(entity, positions)
        (x, y), lift = self.motion.ground_pose(entity)
        return (x-BOARD_LEFT)/TILE_SIZE-.5, (y-BOARD_BOTTOM)/TILE_SIZE-.5, lift


class Stage7ArtPath(SessionArtPath):
    def __init__(self, c, factory=Stage7ArtRenderer, *, motion=None):
        super().__init__(c, lambda canvas: factory(canvas, motion=motion),
                         stage=7, flag='CHECKMATE_STAGE7_ART',
                         logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    """Retain the Stage5/6 controller and evaluate exits before returning."""
    def __init__(self, c, *, motion=None, previous_factory=PreviousArtPath,
                 stage7_factory=Stage7ArtRenderer):
        self.previous = previous_factory(c)
        self.stage7 = Stage7ArtPath(c, stage7_factory, motion=motion)

    def draw(self, game, positions):
        previous = self.previous.draw(game, positions)
        seven = self.stage7.draw(game, positions)
        return previous or seven

    def close(self):
        self.previous.close()
        self.stage7.close()
