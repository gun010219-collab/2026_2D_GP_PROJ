"""Royal and Frozen chapter profiles for the live campaign renderer."""
import logging

from arena_art_common import CAMERA, sprite_layout
from arena_art_profile import ChapterArtProfile, PieceArt, ProfileArtPath
from stage5_art_renderer import FILES as ROYAL_FILES, actor_layout as stage5_layout
from stage11_art_renderer import FROZEN_PROFILE
from stage12_art_renderer import FILES as STAGE12_FILES
from stage13_art_renderer import FILES as STAGE13_FILES, LiveArenaArtPath as LegacyArtPath
from stage13_art_renderer import actor_layout as stage13_layout


def royal_layout(kind, u, v):
    if kind in ('knight', 'bishop'):
        return sprite_layout(kind, u, v, {'knight': 72, 'bishop': 72}, {},
                             {'knight': 9, 'bishop': 9}, {'knight': (21, 235)})
    return stage5_layout(kind, u, v)


ROYAL = ChapterArtProfile(
    chapter=1,
    surfaces={name: ROYAL_FILES[name] for name in ('background', 'frame', 'light', 'dark')},
    pieces={
        **{kind: PieceArt(ROYAL_FILES[kind], kind) for kind in ('player', 'pawn', 'rook', 'king')},
        'knight': PieceArt('assets/character_concepts/ch1_knight.png', 'knight'),
        'bishop': PieceArt('assets/character_concepts/ch1_bishop.png', 'bishop'),
    },
    layout=royal_layout,
)

# 112 px of visible armor at the front row, using the prepared 220 px alpha height.
ICE_KING_SIZE = 112 * 256 / 220 / (CAMERA.sprite_scale * 1.10)


def frozen_layout(kind, u, v):
    if kind == 'king':
        return sprite_layout(kind, u, v, {'king': ICE_KING_SIZE}, {}, {'king': 13})
    return stage13_layout(kind, u, v)


FROZEN = ChapterArtProfile(
    chapter=3,
    surfaces=FROZEN_PROFILE.surfaces,
    pieces={
        **FROZEN_PROFILE.pieces,
        'bishop': PieceArt(STAGE12_FILES['bishop'], 'bishop'),
        'queen': PieceArt(STAGE13_FILES['queen'], 'queen'),
        'king': PieceArt('assets/character_concepts/ch3_king.png', 'king'),
    },
    layout=frozen_layout,
)


class LiveArenaArtPath:
    """Dispatch one path and release outgoing textures before loading the next stage."""
    def __init__(self, canvas, *, motion=None):
        royal = ProfileArtPath(canvas, ROYAL, motion=motion, stage=range(1, 5),
                               flag=None, logger=logging.getLogger(__name__))
        frozen = ProfileArtPath(canvas, FROZEN, motion=motion, stage=range(14, 16),
                                flag=None, logger=logging.getLogger(__name__))
        self.legacy = LegacyArtPath(canvas, motion=motion)
        self.paths = {stage: path for path in (royal, frozen) for stage in path.stage}
        self.stage = self.path = None

    def draw(self, game, positions):
        if game.stage_number != self.stage:
            self.close()
            self.stage = game.stage_number
            self.path = self.paths.get(self.stage, self.legacy)
        return self.path.draw(game, positions)

    def close(self):
        if self.path is not None:
            self.path.close()
        self.stage = self.path = None
