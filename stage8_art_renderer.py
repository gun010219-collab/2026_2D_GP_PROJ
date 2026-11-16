"""Stage8 forest mixed combat profile; exact shared ledger-based presentation."""
import logging
from arena_art_common import SessionArtPath, sprite_layout
from stage6_art_renderer import FILES as FOREST_FILES, BASE_SIZE as FOREST_SIZES, ALPHA_ROWS as FOREST_ALPHA
from stage7_art_renderer import (Stage7ArtRenderer, LiveArenaArtPath as PreviousArtPath,
                                 BASE_SIZE as SEVEN_SIZES, ALPHA_ROWS as SEVEN_ALPHA)

FILES = {**FOREST_FILES, 'knight': 'assets/chapter2_units/knight.png',
         'bishop': 'assets/chapter2_units/bishop.png'}
BASE_SIZE = {**FOREST_SIZES, 'knight': SEVEN_SIZES['knight'], 'bishop': 84}
ALPHA_ROWS = {**FOREST_ALPHA, 'knight': SEVEN_ALPHA['knight'], 'bishop': (18, 238)}
HP_OFFSET = {'player': 5, 'pawn': 7, 'rook': 8, 'knight': 9, 'bishop': 9}


def actor_layout(kind, u, v):
    return sprite_layout(kind, u, v, BASE_SIZE, {}, HP_OFFSET, ALPHA_ROWS)


class Stage8ArtRenderer(Stage7ArtRenderer):
    files = FILES

    def layout(self, kind, u, v):
        return actor_layout(kind, u, v)


class Stage8ArtPath(SessionArtPath):
    def __init__(self, c, factory=Stage8ArtRenderer, *, motion=None):
        super().__init__(c, lambda canvas: factory(canvas, motion=motion),
                         stage=8, flag='CHECKMATE_STAGE8_ART',
                         logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    def __init__(self, c, *, motion=None, previous_factory=PreviousArtPath,
                 stage8_factory=Stage8ArtRenderer):
        self.previous = previous_factory(c, motion=motion)
        self.stage8 = Stage8ArtPath(c, stage8_factory, motion=motion)

    def draw(self, game, positions):
        previous = self.previous.draw(game, positions)
        eight = self.stage8.draw(game, positions)
        return previous or eight

    def close(self):
        self.previous.close()
        self.stage8.close()
