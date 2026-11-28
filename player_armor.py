"""Own the current upgraded player appearance for one live arena path."""

from dataclasses import dataclass
import logging

from sprite_animation import SpriteCatalog
from sprite_atlas import DEFAULT_CATALOG, SpriteAtlases

LOG = logging.getLogger(__name__)
ARMOR_ROOT = DEFAULT_CATALOG.parent / 'armor_tiers'


@dataclass(frozen=True)
class ArmorAppearance:
    image: object
    sprites: SpriteAtlases | None


class PlayerArmor:
    def __init__(self, canvas, *, combat_sprites):
        self.canvas = canvas
        self.combat_sprites = combat_sprites
        self.max_hp = 3
        self.appearance = None

    def select(self, max_hp):
        if max_hp == self.max_hp:
            return self.appearance
        self.close()
        self.max_hp = max_hp
        if max_hp not in (4, 5, 6):
            return None

        directory = ARMOR_ROOT / f'hp{max_hp}'
        try:
            image = self.canvas.load_image(str(directory / 'player.png'))
        except OSError:
            LOG.warning('Player appearance unavailable for max HP %s', max_hp, exc_info=True)
            return None

        self.appearance = ArmorAppearance(image, None)
        if self.combat_sprites:
            try:
                catalog = SpriteCatalog.read(directory / 'manifest.json')
                # Armor clips are shared by all chapters, and owned outside the stage renderer.
                atlas = SpriteAtlases(self.canvas, catalog, None, {'player'})
                self.appearance = ArmorAppearance(image, atlas)
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                LOG.warning('Player armor atlas unavailable for max HP %s', max_hp, exc_info=True)
        return self.appearance

    def close(self):
        appearance, self.appearance = self.appearance, None
        self.max_hp = 3
        if appearance is not None:
            if appearance.sprites is not None:
                appearance.sprites.close()
            self.canvas.SDL_DestroyTexture(appearance.image.texture)
            appearance.image.texture = None
