"""Approved Y-A runtime HP; original catalog data remains unchanged."""
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class CombatProfile:
    chapter: int
    pawn: int
    rook: int
    knight: int
    bishop: int
    king: int

    def __post_init__(self):
        if type(self.chapter) is not int or not 1 <= self.chapter <= 5:
            raise ValueError('Invalid balance chapter')
        if any(type(v) is not int or v <= 0 for v in (self.pawn,self.rook,self.knight,self.bishop,self.king)):
            raise ValueError('HP must be positive integers')

    def hp(self, kind):
        if kind not in ('pawn','rook','knight','bishop','king'):
            raise ValueError('Unsupported balance piece')
        return getattr(self,kind)


PROFILES = MappingProxyType({
    1: CombatProfile(1,3,6,5,5,22),
    2: CombatProfile(2,5,9,7,7,40),
    3: CombatProfile(3,7,12,10,10,60),
    4: CombatProfile(4,10,16,13,13,85),
    5: CombatProfile(5,13,20,16,16,110),
})


def profile_for(chapter):
    if type(chapter) is not int or chapter not in PROFILES:
        raise ValueError('Invalid balance chapter')
    return PROFILES[chapter]
