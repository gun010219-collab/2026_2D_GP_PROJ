"""Chapter profiles and live campaign art dispatch."""
import logging

from arena_art_common import CAMERA, sprite_layout
from arena_art_profile import ChapterArtProfile, PieceArt, ProfileArtPath
from late_chapter_art import FacadeArtRenderer, LATE_PROFILES
from stage5_art_renderer import FILES as ROYAL_FILES, Stage5ArtPath, actor_layout as stage5_layout
from stage6_art_renderer import Stage6ArtPath
from stage7_art_renderer import Stage7ArtPath
from stage8_art_renderer import FILES as FOREST_FILES, Stage8ArtPath, actor_layout as forest_layout
from stage9_art_renderer import Stage9ArtPath
from stage10_art_renderer import FILES as STAGE10_FILES, Stage10ArtPath, actor_layout as forest_boss_layout
from stage11_art_renderer import FROZEN_PROFILE, Stage11ArtPath
from stage12_art_renderer import FILES as STAGE12_FILES, Stage12ArtPath
from stage13_art_renderer import FILES as STAGE13_FILES, Stage13ArtPath
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

FOREST = ChapterArtProfile(
    chapter=2,
    surfaces={name: FOREST_FILES[name] for name in ROYAL.surfaces},
    pieces={kind: PieceArt(path, kind) for kind, path in {**FOREST_FILES, **STAGE10_FILES}.items()
            if kind not in ROYAL.surfaces},
    layout=lambda kind, u, v: (forest_boss_layout if kind == 'king' else forest_layout)(kind, u, v),
)
CHAPTER_PROFILES = {1: ROYAL, 2: FOREST, 3: FROZEN, **LATE_PROFILES}


class LiveArenaArtPath:
    """Dispatch one path and release outgoing textures before loading the next stage."""
    def __init__(self, canvas, *, motion=None, default_enabled=False, animation=None, vfx=None,
                 enlarged=False, telegraph=None, player_combat_visual=False, sprite_catalog=None):
        royal = ProfileArtPath(canvas, ROYAL, motion=motion, stage=range(1, 5),
                               flag=None, logger=logging.getLogger(__name__))
        frozen = ProfileArtPath(canvas, FROZEN, motion=motion, stage=range(14, 16),
                                flag=None, logger=logging.getLogger(__name__))
        late = [ProfileArtPath(canvas, profile, motion=motion, stage=range(chapter*5-4, chapter*5+1),
                               flag=None, logger=logging.getLogger(__name__), renderer_type=FacadeArtRenderer)
                for chapter, profile in LATE_PROFILES.items()]
        self.paths = {stage: path for path in (royal, frozen, *late) for stage in path.stage}
        legacy = (Stage7ArtPath, Stage8ArtPath, Stage9ArtPath, Stage10ArtPath,
                  Stage11ArtPath, Stage12ArtPath, Stage13ArtPath)
        original_paths = (Stage5ArtPath(canvas), Stage6ArtPath(canvas),
                          *(path(canvas, motion=motion) for path in legacy))
        self.stage_paths = {**self.paths, **{path.stage: path for path in original_paths}}
        self.vfx = vfx
        self.effects_renderer = None
        if vfx is not None:
            from combat_vfx_renderer import VFXRenderer
            self.effects_renderer = VFXRenderer(vfx)
        for path in self.stage_paths.values():
            if vfx is not None:
                path.vfx = self.effects_renderer
            path.telegraph = telegraph
            path.player_combat_visual = player_combat_visual
            path.default_enabled = default_enabled
            path.enlarged = enlarged
            path.animation = animation
            path.animation_motion = motion
            path.sprite_catalog = sprite_catalog
        self.stage = self.path = None

    def draw(self, game, positions):
        if game.stage_number != self.stage:
            if self.path is not None:
                self.path.close()
            self.stage = game.stage_number
            self.path = self.stage_paths.get(self.stage)
        return self.path is not None and self.path.draw(game, positions)

    def close(self):
        if self.effects_renderer is not None:
            self.effects_renderer.close()
            self.vfx.close()
        if self.path is not None:
            self.path.close()
        self.stage = self.path = None
