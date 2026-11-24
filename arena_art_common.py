"""Shared display coordinates and session lifetime; no gameplay dependencies."""
import os
from tools.arena_projection import ArenaCamera, CAMERAS

CAMERA = ArenaCamera('B +12', tuple(
    (735 + (x - 735) * 1.12, 427.5 + (y - 427.5) * 1.12)
    for x, y in CAMERAS[1].corners), 35.84, 1.232)


class ArenaArtError(RuntimeError):
    """An anticipated asset/SDL presentation failure, eligible for fallback."""


def sprite_layout(kind, u, v, sizes, scales, offsets, alpha=None):
    x, y = CAMERA.project(u + .5, v + .25)
    height = sizes[kind] * CAMERA.sprite_scale * (1.10 - .23 * v / 10) * scales.get(kind, 1.0)
    top_alpha, bottom_alpha = (alpha or {}).get(kind, (18, 238))
    center = y + height * (.5 - (256 - bottom_alpha) / 256)
    top = center + height * (128 - top_alpha) / 256
    return dict(foot=(x, y), height=height, center=(x, center), top=top, hp_y=top + offsets[kind])


class SessionArtPath:
    """Load once per opted-in combat session; release on exit/restart/error."""
    def __init__(self, c, factory, *, stage, flag, logger):
        self.c = c
        self.factory = factory
        self.stage, self.flag, self.logger = stage, flag, logger
        self.session = self.renderer = None
        self.failed = False

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None
        self.session = None

    def load_renderer(self, game):
        return self.factory(self.c)

    def draw(self, g, positions):
        enabled = os.environ.get(self.flag) == '1' and g.stage_number == self.stage
        session = g.combat.combat_session_id if enabled else None
        if session != self.session:
            self.close()
            self.session = session
            self.failed = False
        if not enabled or self.failed:
            return False
        try:
            if self.renderer is None:
                self.renderer = self.load_renderer(g)
            self.renderer.draw(g, positions)
            return True
        except (OSError, ArenaArtError):
            self.logger.exception('Stage%s art unavailable; using original renderer for this session', self.stage)
            self.close()
            self.session, self.failed = session, True
            self.c.SDL_SetRenderDrawColor(self.c.renderer, 0, 0, 0, 255)
            self.c.SDL_RenderClear(self.c.renderer)
            return False
