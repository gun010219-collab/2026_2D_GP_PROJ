"""Stage 1–3 session outcomes and transition destinations; no SDL/rendering."""
from enum import Enum

from combat_resolution import CombatResolver


class GameState(str, Enum):
    PLAYING = 'PLAYING'
    GAME_OVER = 'GAME_OVER'
    STAGE_CLEAR = 'STAGE_CLEAR'


class StageGame:
    """Own one combat instance. Restart creates a new instance, never rewinds it."""
    def __init__(self, player, combat, encounter, parry, resolver, *, stage_number=1, chapter=1):
        if type(stage_number) is not int or stage_number not in (1, 2, 3):
            raise ValueError('Only Stage 1 through Stage 3 combat sessions are supported')
        if type(chapter) is not int or chapter != 1:
            raise ValueError('Stage 1 through Stage 3 require Chapter 1')
        if (not isinstance(resolver, CombatResolver) or resolver.player is not player
                or resolver.combat is not combat or resolver.encounter is not encounter
                or resolver.parry is not parry):
            raise ValueError(f'Stage {stage_number} session must own the resolver entities and clocks')
        if not encounter.enemies:
            raise ValueError(f'Stage {stage_number} session requires enemy data')
        self._stage_number = stage_number
        self._chapter = chapter
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
    def next_stage_number(self):
        # Temporary direct continuation until the upgrade flow is implemented.
        return (self.stage_number + 1 if self.stage_number < 3
                and self.state is GameState.STAGE_CLEAR else None)

    @property
    def restart_stage_number(self):
        if self.playing:
            return None
        # All supported stages are in Chapter 1. Death retries its first stage.
        return 1 if self.state is GameState.GAME_OVER else self.stage_number

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
            state = GameState.STAGE_CLEAR
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
