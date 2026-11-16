"""Stage9 opts into the unchanged forest profile; actors share nine textures."""
import logging
from arena_art_common import SessionArtPath
from stage8_art_renderer import Stage8ArtRenderer, LiveArenaArtPath as PreviousArtPath


class Stage9ArtRenderer(Stage8ArtRenderer):
    """Use actual entities and source-scoped ledger warnings, including two Rooks."""


class Stage9ArtPath(SessionArtPath):
    def __init__(self, c, factory=Stage9ArtRenderer, *, motion=None):
        super().__init__(c, lambda canvas: factory(canvas, motion=motion),
                         stage=9, flag='CHECKMATE_STAGE9_ART',
                         logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    def __init__(self, c, *, motion=None, previous_factory=PreviousArtPath,
                 stage9_factory=Stage9ArtRenderer):
        self.previous = previous_factory(c, motion=motion)
        self.stage9 = Stage9ArtPath(c, stage9_factory, motion=motion)

    def draw(self, game, positions):
        previous = self.previous.draw(game, positions)
        nine = self.stage9.draw(game, positions)
        return previous or nine

    def close(self):
        self.previous.close()
        self.stage9.close()
