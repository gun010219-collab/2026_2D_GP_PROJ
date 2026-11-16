"""Stage10 forest boss display; KingPulse remains owned by the actual encounter."""
import logging
from arena_art_common import SessionArtPath, sprite_layout
from stage8_art_renderer import FILES as FOREST_FILES, BASE_SIZE as FOREST_SIZES, ALPHA_ROWS as FOREST_ALPHA, HP_OFFSET as FOREST_HP
from stage9_art_renderer import Stage9ArtRenderer, LiveArenaArtPath as PreviousArtPath

FILES = {k: v for k, v in FOREST_FILES.items() if k != 'rook'}
FILES['king'] = 'assets/chapter2_units/king_c6.png'
BASE_SIZE = {k: v for k, v in FOREST_SIZES.items() if k != 'rook'}
BASE_SIZE['king'] = 104
ALPHA_ROWS = {k: v for k, v in FOREST_ALPHA.items() if k != 'rook'}
ALPHA_ROWS['king'] = (18, 238)
HP_OFFSET = {k: v for k, v in FOREST_HP.items() if k != 'rook'}
HP_OFFSET['king'] = 12


def actor_layout(kind, u, v):
    return sprite_layout(kind, u, v, BASE_SIZE, {}, HP_OFFSET, ALPHA_ROWS)


class Stage10ArtRenderer(Stage9ArtRenderer):
    files = FILES

    def layout(self, kind, u, v):
        return actor_layout(kind, u, v)


class Stage10ArtPath(SessionArtPath):
    def __init__(self, c, factory=Stage10ArtRenderer, *, motion=None):
        super().__init__(c, lambda canvas: factory(canvas, motion=motion),
                         stage=10, flag='CHECKMATE_STAGE10_ART',
                         logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    def __init__(self, c, *, motion=None, previous_factory=PreviousArtPath,
                 stage10_factory=Stage10ArtRenderer):
        self.previous = previous_factory(c, motion=motion)
        self.stage10 = Stage10ArtPath(c, stage10_factory, motion=motion)

    def draw(self, game, positions):
        previous = self.previous.draw(game, positions)
        ten = self.stage10.draw(game, positions)
        return previous or ten

    def close(self):
        self.previous.close()
        self.stage10.close()
