"""Task 3-F2 experimental runtime HP; original catalog data remains unchanged."""
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
    queen: int | None = None

    def __post_init__(self):
        if type(self.chapter) is not int or not 1 <= self.chapter <= 5:
            raise ValueError('Invalid balance chapter')
        if any(type(v) is not int or v <= 0 for v in (self.pawn,self.rook,self.knight,self.bishop,self.king)):
            raise ValueError('HP must be positive integers')
        if self.queen is not None and (type(self.queen) is not int or self.queen <= 0 or self.chapter < 3):
            raise ValueError('Invalid Queen HP profile')

    def hp(self, kind):
        if kind == 'queen':
            if type(self.queen) is not int or self.queen <= 0:
                raise ValueError('Queen requires an approved chapter profile')
            return self.queen
        if kind not in ('pawn','rook','knight','bishop','king'):
            raise ValueError('Unsupported balance piece')
        return getattr(self,kind)


PROFILES = MappingProxyType({
    1: CombatProfile(1,4,8,7,7,28),
    2: CombatProfile(2,7,12,9,9,50),
    3: CombatProfile(3,9,16,13,13,75,18),
    4: CombatProfile(4,13,21,18,18,100,24),
    5: CombatProfile(5,13,20,16,16,110,22),
})


def profile_for(chapter):
    if type(chapter) is not int or chapter not in PROFILES:
        raise ValueError('Invalid balance chapter')
    return PROFILES[chapter]
