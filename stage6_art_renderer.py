"""Stage6 forest profile over the approved Stage5 display-only pipeline."""
import logging
from arena_art_common import SessionArtPath, sprite_layout
from stage5_art_renderer import Stage5ArtRenderer, Stage5ArtPath, HP_OFFSET

FILES = {
    'background': 'assets/themed_arena/forest.png',
    'frame': 'assets/aligned_board/forest_c.png',
    'light': 'assets/polished_board/forest_light.png',
    'dark': 'assets/polished_board/forest_dark.png',
    'player': 'assets/character_concepts/player.png',
    'pawn': 'assets/chapter2_units/pawn.png',
    'rook': 'assets/chapter2_units/rook.png',
}
# Measured 256px PNG alpha bounds: Pawn (71,18,184,238), Rook (18,32,238,223).
# Sizes compensate the short/wide Rook silhouette without distorting either PNG.
BASE_SIZE = {'player': 72, 'pawn': 72, 'rook': 88}
ALPHA_ROWS = {'pawn': (18, 238), 'rook': (32, 223)}


def actor_layout(kind, u, v):
    return sprite_layout(kind, u, v, BASE_SIZE, {}, HP_OFFSET, ALPHA_ROWS)


class Stage6ArtRenderer(Stage5ArtRenderer):
    files = FILES

    def layout(self, kind, u, v):
        return actor_layout(kind, u, v)


class Stage6ArtPath(SessionArtPath):
    def __init__(self, c, factory=Stage6ArtRenderer):
        super().__init__(c, factory, stage=6, flag='CHECKMATE_STAGE6_ART',
                         logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    """Independent opt-ins; disabled paths still observe exits to free textures."""
    def __init__(self, c, stage5_factory=Stage5ArtRenderer, stage6_factory=Stage6ArtRenderer):
        self.stage5 = Stage5ArtPath(c, stage5_factory)
        self.stage6 = Stage6ArtPath(c, stage6_factory)

    def draw(self, game, positions):
        five = self.stage5.draw(game, positions)
        six = self.stage6.draw(game, positions)
        return five or six

    def close(self):
        self.stage5.close()
        self.stage6.close()
