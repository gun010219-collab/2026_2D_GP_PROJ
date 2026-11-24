"""Shared display coordinates and session lifetime; no gameplay dependencies."""
import os
from tools.arena_projection import ArenaCamera, CAMERAS

CAMERA = ArenaCamera('B +12', tuple(
    (735 + (x - 735) * 1.12, 427.5 + (y - 427.5) * 1.12)
    for x, y in CAMERAS[1].corners), 35.84, 1.232)


PIECE_INCREASE = {'pawn':1.08,'rook':1.08,'knight':1.07,'bishop':1.07,'queen':1.06,'king':1.05}


def enlarge_sprite(layout, kind):
    scale = PIECE_INCREASE.get(kind)
    if scale is None:
        return layout
    x,y = layout['foot']
    top = y+(layout['top']-y)*scale
    return {**layout,'height':layout['height']*scale,
            'center':(x,y+(layout['center'][1]-y)*scale),'top':top,
            'hp_y':top+layout['hp_y']-layout['top']}


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
        self.default_enabled = False
        self.animation = self.animation_motion = None
        self.enlarged = False

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None
        self.session = None

    def load_renderer(self, game):
        return self.factory(self.c)

    def enabled(self, stage_number):
        if isinstance(self.stage, range):
            if stage_number not in self.stage:
                return False
        elif stage_number != self.stage:
            return False
        stage_flag = self.flag or f'CHECKMATE_STAGE{stage_number}_ART'
        setting = os.environ.get(stage_flag)
        if setting is None:
            chapter = (stage_number - 1) // 5 + 1
            setting = os.environ.get(f'CHECKMATE_CHAPTER{chapter}_ART')
        return self.default_enabled if setting is None else setting == '1'

    def draw(self, g, positions):
        enabled = self.enabled(g.stage_number)
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
                if self.enlarged:
                    self.renderer.enlarged = True
                if getattr(self, 'vfx', None) is not None:
                    self.renderer.vfx = self.vfx
                if self.animation is not None:
                    self.renderer.animation = self.animation
                    self.renderer.animation_motion = self.animation_motion
            self.renderer.draw(g, positions)
            return True
        except (OSError, ArenaArtError):
            self.logger.exception('Stage%s art unavailable; using original renderer for this session', g.stage_number)
            self.close()
            self.session, self.failed = session, True
            self.c.SDL_SetRenderDrawColor(self.c.renderer, 0, 0, 0, 255)
            self.c.SDL_RenderClear(self.c.renderer)
            return False
