"""Small Stage 1 session/outcome model; no window, input or rendering state."""
from enum import Enum

from combat_resolution import CombatResolver


class GameState(str, Enum):
    PLAYING = 'PLAYING'
    GAME_OVER = 'GAME_OVER'
    STAGE_CLEAR = 'STAGE_CLEAR'


class StageOneGame:
    """Own one combat instance. Restart creates a new instance, never rewinds it."""
    def __init__(self, player, combat, encounter, parry, resolver):
        if (not isinstance(resolver, CombatResolver) or resolver.player is not player
                or resolver.combat is not combat or resolver.encounter is not encounter
                or resolver.parry is not parry):
            raise ValueError('Stage 1 session must own the resolver entities and clocks')
        if not encounter.enemies:
            raise ValueError('Stage 1 session requires enemy data')
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
