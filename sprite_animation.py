
"""Read-only frame selection and the versioned sprite atlas metadata format."""
from bisect import bisect_right
from dataclasses import dataclass, field
from itertools import accumulate
import json
from pathlib import Path

from actor_animation import PARRY_POSES, State
from player import DIRECTIONS

ACTIONS = frozenset({'attack', 'parry_ready', 'parry_normal', 'parry_perfect', 'parry_failed'})
FACINGS = frozenset(DIRECTIONS) | {'neutral'}
ATTACK_KINDS = frozenset({'basic', 'pawn_contact', 'queen_diagonal', 'king_pulse'})


def integers(value, count):
    if not isinstance(value, (list, tuple)) or len(value) != count or any(type(n) is not int for n in value):
        raise ValueError(f'Expected {count} integers: {value!r}')
    return tuple(value)


@dataclass(frozen=True)
class SpriteFrame:
    rect: tuple[int, int, int, int]
    foot: tuple[int, int]
    duration_ms: int
    offset: tuple[int, int]
    visible_top: int

    @classmethod
    def read(cls, data, atlas_size):
        x, y, w, h = rect = integers(data['rect'], 4)
        ax, ay = foot = integers(data['foot'], 2)
        offset = integers(data.get('offset', (0, 0)), 2)
        ms, top = integers((data['ms'], data['visible_top']), 2)
        if (not (0 <= x < x+w <= atlas_size[0] and 0 <= y < y+h <= atlas_size[1])
                or not (0 <= ax < w and 0 <= top <= ay < h)
                or not (1 <= ms <= 10000)
                or abs(offset[0]) > w or abs(offset[1]) > h):
            raise ValueError(f'Invalid sprite frame: {data!r}')
        return cls(rect, foot, ms, offset, top)

    def placement(self, layout, reference_height, *, flip_x=False):
        """Return SDL rect and HP anchor; the source foot follows world foot plus visual lift."""
        scale = layout['height'] / reference_height
        foot_x, foot_y = layout['foot']
        foot_y += layout.get('elevation', 0.)
        local_x = self.rect[2]-self.foot[0] if flip_x else self.foot[0]
        x = foot_x + (self.offset[0] - local_x) * scale
        sdl_y = 899 - foot_y + (self.offset[1] - self.foot[1]) * scale
        visible_top = 899 - sdl_y - self.visible_top * scale
        return ((x, sdl_y, self.rect[2] * scale, self.rect[3] * scale),
                (foot_x, layout['hp_y'] + max(0., visible_top - layout['top'])))


@dataclass(frozen=True)
class SpriteClip:
    chapter: int | None
    design: str
    action: str
    facing: str
    attack_kind: str
    atlas: str
    reference_height: int
    frames: tuple[SpriteFrame, ...]
    impact: int
    loop: bool
    flip_x: bool = False
    contact: int | None = None
    ends_ms: tuple[int, ...] = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'ends_ms', tuple(accumulate(frame.duration_ms for frame in self.frames)))

    @property
    def key(self):
        return self.chapter, self.design, self.action, self.facing, self.attack_kind

    def preparation(self, progress):
        if self.impact == 0 or not 0. <= progress < 1.:
            return None
        duration = self.ends_ms[self.impact - 1]
        return self.frames[bisect_right(self.ends_ms, progress * duration)]

    def reaction(self, elapsed, *, first=None):
        if elapsed < 0.:
            return None
        first = self.impact if first is None else first
        start = self.ends_ms[first - 1] if first else 0
        total = self.ends_ms[-1] - start
        ms = round(elapsed * 1000, 7)
        if self.loop:
            ms %= total
        elif ms >= total:
            return None
        return self.frames[bisect_right(self.ends_ms, start + ms)]


@dataclass(frozen=True)
class AtlasSpec:
    path: Path
    size: tuple[int, int]


@dataclass(frozen=True)
class SpriteCatalog:
    atlases: dict[str, AtlasSpec]
    clips: dict[tuple, SpriteClip]

    @classmethod
    def read(cls, path, *, allow_test=False):
        return cls.parse(json.loads(path.read_text(encoding='utf-8')), path.parent, allow_test=allow_test)

    @classmethod
    def parse(cls, data, directory, *, allow_test=False):
        if (type(data['version']) is not int or data['version'] != 1
                or data['purpose'] not in (('production', 'test') if allow_test else ('production',))):
            raise ValueError('Unsupported version or sprite catalog purpose')
        atlases = {}
        for name, spec in data['atlases'].items():
            file = Path(spec['file'])
            size = integers(spec['size'], 2)
            if (not name or '\0' in str(file) or file.is_absolute() or file.drive or '..' in file.parts
                    or file.suffix.lower() != '.png' or not all(1 <= n <= 4096 for n in size)):
                raise ValueError(f'Invalid atlas: {name}')
            atlases[name] = AtlasSpec(directory / file, size)
        clips = {}
        for clip in data['clips']:
            chapter, design = clip.get('chapter'), clip['design']
            action, facing, attack_kind = clip['action'], clip['facing'], clip.get('attack_kind', 'basic')
            atlas, reference = clip['atlas'], clip['reference_height']
            impact, loop = clip['impact'], clip.get('loop', False)
            if (chapter is not None and (type(chapter) is not int or not 1 <= chapter <= 5)
                    or not isinstance(design, str) or not design.strip()
                    or action not in ACTIONS or facing not in FACINGS or attack_kind not in ATTACK_KINDS
                    or type(reference) is not int or not 1 <= reference <= 4096
                    or type(loop) is not bool or (loop and action != 'parry_ready')):
                raise ValueError(f'Invalid sprite clip: {design} / {action} / {facing}')
            frames = tuple(SpriteFrame.read(frame, atlases[atlas].size) for frame in clip['frames'])
            if type(impact) is not int or not 0 <= impact < len(frames):
                raise ValueError(f'Invalid impact index: {impact}')
            flip_x, contact = clip.get('flip_x', False), clip.get('contact')
            if (type(flip_x) is not bool or (contact is not None and
                    (design not in ('rook', 'knight') or action != 'attack' or loop
                     or type(contact) is not int or not impact < contact < len(frames)))):
                raise ValueError(f'Invalid sprite transform or contact index: {design} / {facing}')
            item = SpriteClip(chapter, design, action, facing, attack_kind, atlas, reference, frames, impact, loop,
                              flip_x, contact)
            if item.key in clips:
                raise ValueError(f'Duplicate sprite clip: {item.key}')
            clips[item.key] = item
        return cls(atlases, clips)

    def clip(self, chapter, design, action, facing, attack_kind):
        return (self.clips.get((chapter, design, action, facing, attack_kind))
                or self.clips.get((None, design, action, facing, attack_kind)))


def cardinal(x, y):
    if x == y == 0:
        return 'neutral'
    if abs(x) >= abs(y):
        return 'right' if x > 0 else 'left'
    return 'up' if y > 0 else 'down'


class SpriteController:
    """Use the existing pose priority and accepted receipts, with no second combat clock."""
    def __init__(self, catalog):
        self.catalog = catalog
        self.designs = frozenset(clip.design for clip in catalog.clips.values())

    def sample(self, game, actor, design, animation, pose, *, include_finished=False):
        if design not in self.designs:
            return None
        source = animation.sprite_source(game, actor, pose)
        if source is None:
            return None
        state, receipt, elapsed, vector = source
        if state in (State.WINDUP, State.ATTACK):
            facing = (receipt.facing if actor is game.player
                      else cardinal(*vector))
            attack_kind = getattr(receipt, 'attack_kind', 'basic')
            action = 'attack'
        else:
            facing, attack_kind, action = cardinal(*vector), 'basic', state.value
        clip = self.catalog.clip(game.chapter, design, action, facing, attack_kind)
        if clip is None and state in PARRY_POSES and facing != 'neutral':
            clip = self.catalog.clip(game.chapter, design, action, 'neutral', attack_kind)
        if clip is None:
            return None
        if state is State.WINDUP:
            frame = clip.preparation((game.combat.tick - receipt.telegraph_start_tick)
                                     / (receipt.hit_tick - receipt.telegraph_start_tick))
        elif clip.contact is not None:
            if pose.state is not State.ATTACK:
                return None
            if pose.attack_motion == 'arrival':
                frame = clip.reaction(pose.phase*animation.recovery_seconds[actor.kind],first=clip.contact)
            else:
                frame = clip.frames[clip.impact]
        else:
            frame = clip.reaction(elapsed)
        # Return to locomotion when a spent action would briefly fall back to an older mesh cue.
        ended_during_mesh = (state is pose.state is State.ATTACK
                             or pose.state is State.PARRY_READY and state is not State.PARRY_READY)
        if frame is not None or (include_finished and ended_during_mesh and elapsed >= 0.):
            return clip, frame
        return None
