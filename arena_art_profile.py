"""Chapter presentation data. Only explicitly registered sprites can be loaded."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from arena_art_common import ArenaArtError, SessionArtPath
from stage7_art_renderer import Stage7ArtRenderer


@dataclass(frozen=True)
class PieceArt:
    sprite: str
    animation_profile: str


@dataclass(frozen=True)
class ChapterArtProfile:
    chapter: int
    surfaces: Mapping[str, str]
    pieces: Mapping[str, PieceArt]
    layout: Callable

    def files_for(self, kinds):
        required = {'player', *kinds}
        missing = required.difference(self.pieces)
        if missing:
            raise ArenaArtError(f'Chapter {self.chapter} lacks approved art for {sorted(missing)}')
        return {**self.surfaces, **{kind: piece.sprite for kind, piece in self.pieces.items()
                                   if kind in required}}


class ProfileArtRenderer(Stage7ArtRenderer):
    """Reuse the live board, ground pose, shadows, warnings and label passes."""
    def __init__(self, canvas, root=None, *, profile, motion=None, kinds=None):
        self.profile = profile
        self.files = profile.files_for(profile.pieces if kinds is None else kinds)
        super().__init__(canvas, root=root, motion=motion)
        for key, image in self.images.items():
            if not image.texture:
                self.close()
                raise ArenaArtError(f'Could not create texture for {key}')

    def layout(self, kind, u, v):
        return self.profile.layout(kind, u, v)


class ProfileArtPath(SessionArtPath):
    """Inspect the encounter once, including actors already defeated on entry."""
    def load_renderer(self, game):
        if self.factory is not None:  # Existing canvas-only factory overrides.
            return super().load_renderer(game)
        if self.profile.chapter != game.chapter:
            raise ArenaArtError('Art profile does not match the active chapter')
        return self.renderer_type(self.c, profile=self.profile, motion=self.motion,
                                  kinds=(enemy.kind for enemy in game.encounter.enemies))

    def __init__(self, canvas, profile, *, factory=None, renderer_type=ProfileArtRenderer,
                 motion=None, stage, flag, logger):
        self.profile = profile
        self.renderer_type = renderer_type
        self.motion = motion
        super().__init__(canvas, factory, stage=stage, flag=flag, logger=logger)
