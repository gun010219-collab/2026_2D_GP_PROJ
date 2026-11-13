"""Supported stage session outcomes and transition destinations; no SDL/rendering."""
from enum import Enum

from combat_resolution import CombatResolver
from stage_manager import StageCatalog
from upgrades import chapter_first_stage


# Catalog availability is not execution support. Expand only with verified tasks.
SUPPORTED_STAGES = frozenset(range(1, 14))


class GameState(str, Enum):
    PLAYING = 'PLAYING'
    GAME_OVER = 'GAME_OVER'
    STAGE_CLEAR = 'STAGE_CLEAR'
    UPGRADE = 'UPGRADE'
    BOSS_CLEAR = 'BOSS_CLEAR'
    DEV_BOUNDARY = 'DEV_BOUNDARY'


class StageGame:
    """Own one combat instance. Restart creates a new instance, never rewinds it."""
    def __init__(self, player, combat, encounter, parry, resolver, *, stage_number=1, chapter=1, boss=False):
        if type(stage_number) is not int or stage_number not in SUPPORTED_STAGES:
            raise ValueError('Only Stage 1 through Stage 13 combat sessions are supported')
        definition = StageCatalog.load().get_stage(stage_number)
        if type(chapter) is not int or chapter != definition.chapter:
            raise ValueError('Playable chapter metadata must match the stage catalog')
        if (type(boss) is not bool or boss != definition.boss
                or boss != (encounter.pulse is not None)):
            raise ValueError('Playable boss metadata must match the catalog and encounter')
        if (not isinstance(resolver, CombatResolver) or resolver.player is not player
                or resolver.combat is not combat or resolver.encounter is not encounter
                or resolver.parry is not parry):
            raise ValueError(f'Stage {stage_number} session must own the resolver entities and clocks')
        if not encounter.enemies:
            raise ValueError(f'Stage {stage_number} session requires enemy data')
        self._stage_number = stage_number
        self._chapter = chapter
        self._boss = boss
        self.player = player
        self.combat = combat
        self.encounter = encounter
        self.parry = parry
        self.resolver = resolver
        self._state = GameState.PLAYING
        self._end_tick = None
        self._transition_count = 0
        self.update_state()

    @property
    def stage_number(self):
        return self._stage_number

    @property
    def chapter(self):
        return self._chapter

    @property
    def boss(self):
        return self._boss

    @property
    def next_stage_number(self):
        # The progression owner additionally authenticates all four upgrades.
        return self.stage_number + 1 if self.stage_number in (5, 10) and self.state is GameState.BOSS_CLEAR else None

    @property
    def upgrade_selection_enabled(self):
        """A legitimate offer may wait at the current development boundary."""
        return self.state is GameState.UPGRADE and self.stage_number + 1 in SUPPORTED_STAGES

    @property
    def restart_stage_number(self):
        if self.playing or self.state in (GameState.UPGRADE, GameState.DEV_BOUNDARY):
            return None
        return chapter_first_stage(self.chapter) if self.state is GameState.GAME_OVER else self.stage_number

    @property
    def state(self):
        return self._state

    @property
    def playing(self):
        return self.state is GameState.PLAYING

    @property
    def end_tick(self):
        return self._end_tick

    @property
    def transition_count(self):
        return self._transition_count

    def update_state(self):
        """Latch one outcome; player death wins if both conditions are true."""
        if not self.playing:
            return False
        if not self.player.alive:
            state = GameState.GAME_OVER
        elif all(not enemy.alive for enemy in self.encounter.enemies):
            state = GameState.BOSS_CLEAR if self.boss else GameState.UPGRADE
        else:
            return False
        self._state = state
        self._end_tick = self.combat.tick
        self._transition_count += 1
        self.resolver.stop()
        return True

    def resolve_current_tick(self):
        if not self.playing:
            return ()
        if not self.player.alive:
            self.update_state()
            return ()
        results = self.resolver.resolve_current_tick()
        self.update_state()
        return results

    def advance(self, ticks=1):
        """Settle each elapsed tick, stopping immediately on either outcome."""
        if type(ticks) is not int:
            raise TypeError('Game steps must be integer ticks')
        if ticks < 0:
            raise ValueError('Game steps cannot move backwards')
        self.update_state()
        if not self.playing:
            return ()
        results = list(self.resolve_current_tick())
        for _ in range(ticks):
            if not self.playing:
                break
            self.combat.advance()
            results.extend(self.resolve_current_tick())
        return tuple(results)


class StageOneGame(StageGame):
    """Preserve the original five-argument Stage 1 constructor and behavior."""
    def __init__(self, player, combat, encounter, parry, resolver):
        super().__init__(player, combat, encounter, parry, resolver)
