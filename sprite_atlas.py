
"""Optional sprite textures owned by one arena renderer, with mesh fallback."""
from ctypes import byref, c_int
import logging
import os
from pathlib import Path

from sprite_animation import SpriteCatalog, SpriteController

LOG = logging.getLogger(__name__)
DEFAULT_CATALOG = Path(__file__).resolve().parent / 'assets' / 'sprite_animation' / 'manifest.json'
SPRITE_COMPLETE = object()


def opted_in_catalog():
    setting = os.environ.get('CHECKMATE_ATTACK_SPRITES')
    if setting not in (None, '1'):
        return None
    alternate = os.environ.get('CHECKMATE_SPRITE_MANIFEST') if setting == '1' else None
    path = Path(alternate) if alternate else DEFAULT_CATALOG
    if setting is None and not path.is_file():
        return None
    try:
        return SpriteCatalog.read(path, allow_test=bool(alternate))
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        LOG.warning('Sprite catalog unavailable at %s; using mesh animation', path, exc_info=True)
        return None


class SpriteAtlases:
    def __init__(self, canvas, catalog, chapter, designs):
        self.canvas = canvas
        self.controller = SpriteController(catalog)
        self.textures = {}
        self._sources = {}
        self._names_by_path = {}
        needed = {clip.atlas for clip in catalog.clips.values()
                  if clip.chapter in (None, chapter) and clip.design in designs}
        by_path = {}
        for name in sorted(needed):
            spec = catalog.atlases[name]
            try:
                path = spec.path.resolve()
            except (OSError, RuntimeError):
                LOG.warning('Cannot resolve sprite atlas path %s; using mesh animation', spec.path)
                continue
            cached = by_path.get(path)
            if cached is None:
                cached = by_path[path] = self._load(spec.path)
            texture, actual_size = cached
            if texture and actual_size == spec.size:
                self.textures[name] = texture
                self._names_by_path.setdefault(path, set()).add(name)
                self._sources[name] = path
            else:
                LOG.warning('Sprite atlas unavailable at %s; using mesh animation for %s', spec.path, name)
        for path, (texture, _) in by_path.items():
            if texture and path not in self._names_by_path:
                canvas.SDL_DestroyTexture(texture)

    def _load(self, path):
        import sdl2 as s
        from sdl2.sdlimage import IMG_LoadTexture

        try:
            texture = IMG_LoadTexture(self.canvas.renderer, os.fsencode(path))
        except OSError:
            return None, None
        if not texture:
            return None, None
        width, height = c_int(), c_int()
        if (s.SDL_QueryTexture(texture, None, None, byref(width), byref(height))
                or s.SDL_SetTextureScaleMode(texture, s.SDL_ScaleModeLinear)):
            self.canvas.SDL_DestroyTexture(texture)
            return None, None
        return texture, (width.value, height.value)

    def _drop(self, name):
        path = self._sources[name]
        texture = self.textures[name]
        for alias in self._names_by_path.pop(path):
            del self._sources[alias]
            del self.textures[alias]
        self.canvas.SDL_DestroyTexture(texture)

    def close(self):
        while self.textures:
            self._drop(next(iter(self.textures)))

    def draw(self, game, actor, design, layout, animation, pose):
        if not self.textures:
            return None
        selected = self.controller.sample(game, actor, design, animation, pose, include_finished=True)
        if selected is None:
            return None
        clip, frame = selected
        texture = self.textures.get(clip.atlas)
        if texture is None:
            return None
        if frame is None:
            return SPRITE_COMPLETE
        import sdl2 as s

        rect, label = frame.placement(layout, clip.reference_height)
        try:
            if not s.SDL_RenderCopyF(self.canvas.renderer, texture, byref(s.SDL_Rect(*frame.rect)),
                                     byref(s.SDL_FRect(*rect))):
                return label
            LOG.warning('Sprite atlas copy failed for %s: %s', clip.atlas, s.SDL_GetError())
        except OSError:
            LOG.warning('Sprite atlas copy failed for %s', clip.atlas, exc_info=True)
        self._drop(clip.atlas)
        return None
