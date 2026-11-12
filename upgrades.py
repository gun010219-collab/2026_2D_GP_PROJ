"""Immutable PDF p.19 upgrade values and offers; no input, rendering or clock."""
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class UpgradeKind(str, Enum):
    ATTACK = 'attack'
    HP = 'hp'
    MOVE = 'move'


UPGRADE_VALUES = MappingProxyType({
    UpgradeKind.ATTACK: (1, 2, 3),
    UpgradeKind.HP: (3, 4, 5, 6),
    UpgradeKind.MOVE: (18, 15, 12),
})


def upgrade_kind(value):
    if not isinstance(value, (str, UpgradeKind)):
        raise ValueError('Unknown upgrade kind')
    try:
        return UpgradeKind(value)
    except ValueError as exc:
        raise ValueError('Unknown upgrade kind') from exc


def _level(value, kind):
    if type(value) is not int or not 0 <= value < len(UPGRADE_VALUES[kind]):
        raise ValueError(f'Invalid {kind.value} upgrade level')


def _identifier(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Upgrade identifiers must be nonempty strings')


def chapter_first_stage(chapter):
    if type(chapter) is not int or not 1 <= chapter <= 5:
        raise ValueError('Chapter must be an integer in 1..5')
    return (chapter - 1) * 5 + 1


@dataclass(frozen=True, slots=True)
class ChapterBuild:
    attack_level: int = 0
    hp_level: int = 0
    move_level: int = 0

    def __post_init__(self):
        for kind in UpgradeKind:
            _level(self.level(kind), kind)

    def level(self, kind):
        return getattr(self, upgrade_kind(kind).value + '_level')

    @property
    def stats(self):
        return DerivedStats(*(UPGRADE_VALUES[k][self.level(k)] for k in UpgradeKind))

    def upgraded(self, kind):
        kind = upgrade_kind(kind)
        levels = [self.level(k) + (k is kind) for k in UpgradeKind]
        return ChapterBuild(*levels)  # Rejects MAX rather than clamping it.


@dataclass(frozen=True, slots=True)
class DerivedStats:
    attack_damage: int
    max_hp: int
    move_interval_ticks: int

    def __post_init__(self):
        for value, kind in zip((self.attack_damage, self.max_hp, self.move_interval_ticks), UpgradeKind):
            if type(value) is not int or value not in UPGRADE_VALUES[kind]:
                raise ValueError(f'Invalid derived {kind.value} value')


@dataclass(frozen=True, slots=True)
class UpgradeOption:
    kind: UpgradeKind
    current_level: int

    def __post_init__(self):
        object.__setattr__(self, 'kind', upgrade_kind(self.kind))
        _level(self.current_level, self.kind)

    @property
    def current_value(self):
        return UPGRADE_VALUES[self.kind][self.current_level]

    @property
    def enabled(self):
        return self.current_level + 1 < len(UPGRADE_VALUES[self.kind])

    @property
    def is_max(self):
        return not self.enabled

    @property
    def next_level(self):
        return self.current_level + 1 if self.enabled else None

    @property
    def next_value(self):
        return UPGRADE_VALUES[self.kind][self.next_level] if self.enabled else None


@dataclass(frozen=True, slots=True)
class UpgradeOffer:
    run_id: str
    offer_id: str
    chapter: int
    stage: int
    stage_instance_id: str
    before_build: ChapterBuild

    def __post_init__(self):
        for value in (self.run_id, self.offer_id, self.stage_instance_id):
            _identifier(value)
        first = chapter_first_stage(self.chapter)
        if type(self.stage) is not int or not first <= self.stage < first + 4:
            raise ValueError('Only the four ordinary stages have upgrade offers')
        if not isinstance(self.before_build, ChapterBuild):
            raise TypeError('Offer requires a ChapterBuild')

    @property
    def options(self):
        return tuple(UpgradeOption(k, self.before_build.level(k)) for k in UpgradeKind)


@dataclass(frozen=True, slots=True)
class UpgradeReceipt:
    offer: UpgradeOffer
    kind: UpgradeKind
    after_build: ChapterBuild

    def __post_init__(self):
        if not isinstance(self.offer, UpgradeOffer):
            raise TypeError('Receipt requires an UpgradeOffer')
        object.__setattr__(self, 'kind', upgrade_kind(self.kind))
        if (not isinstance(self.after_build, ChapterBuild)
                or self.after_build != self.offer.before_build.upgraded(self.kind)):
            raise ValueError('Receipt must describe exactly one upgrade')

    @property
    def run_id(self):
        return self.offer.run_id

    @property
    def before_build(self):
        return self.offer.before_build
