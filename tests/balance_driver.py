"""Deterministic walking/attack/parry driver; never edits HP, AI or positions."""
from collections import deque
from contextlib import contextmanager, nullcontext
from unittest.mock import patch
from math import ceil
from board import in_bounds
from input_controller import InputController
from player import DIRECTIONS
from game import GameState
from chapter_run import ChapterRun
from stage_progression import StageProgression
from upgrades import ChapterBuild
import main


STYLES = {
    'attack': ('attack',)*4,
    'survival': ('hp','hp','hp','attack'),
    'evasion': ('move','move','attack','attack'),
    'balanced': ('attack','hp','move','attack'),
}


class HistoricalGrowthProgression(StageProgression):
    """Replay archived campaign measurements with the pre-C3 growth rules."""

    def enter_next_chapter(self, factory):
        return super().enter_next_chapter(factory,entry_build=ChapterBuild(self.run.build.attack_level))


@contextmanager
def historical_recovery():
    """Use original recovery only for the historical snapshots and experiments."""
    with patch.object(main, 'recovery_reductions', return_value={}, create=True):
        yield


def _guard_direction(game, direction, tick, move_ticks):
    x,y = game.player.position
    danger = {cell for event in game.encounter.ledger.pending
              if 0 <= event.hit_tick-tick <= move_ticks for cell in event.target_cells}
    if (x,y) in danger:
        occupied = game.encounter.occupied_cells
        for name,(dx,dy) in DIRECTIONS.items():
            cell = x+dx,y+dy
            if in_bounds(*cell) and cell not in danger and cell not in occupied:
                return name
        return None  # Hold for the parry when no adjacent tile is safe.
    if direction:
        dx,dy = DIRECTIONS[direction]
        if (x+dx,y+dy) in danger:
            return None
    return direction


def measure(style, stage, limit=3600, *, current=False, policy='pursue', build=None):
    """Replay an independent fight with a chosen upgrade build and movement policy."""
    if policy not in ('pursue', 'guard'):
        raise ValueError('Unknown movement policy')
    if build is None:
        # Preserve the isolated builds used by the archived enemy-balance fixtures.
        choices=STYLES[style]
        run=ChapterRun()
        for chapter in range(1, (stage-1)//5 + 1):
            for kind in (('attack','attack','attack','hp') if chapter==4 and style=='attack' else choices):run.select(run.offer_after_clear(run.current_stage,str(run.current_stage)),kind)
            run=ChapterRun(chapter+1,entry_attack_level=run.build.attack_level)
        first=(stage-1)//5*5+1
        for kind in (('hp','hp','hp','move') if stage==25 and style=='attack' else ('hp','hp','hp','attack') if stage in (22,23,24) and style=='attack' else ('attack','attack','attack','hp') if stage==20 and style=='attack' else choices)[:stage-first]:run.select(run.offer_after_clear(run.current_stage,str(run.current_stage)),kind)
        build = run.build
    stats = build.stats
    with nullcontext() if current else historical_recovery():
        g=main._new_stage_game(stage,stats=stats)
    movement=InputController(move_interval_ticks=stats.move_interval_ticks)
    hits=damage=perfect=0
    pulse_events=set();reflected=0
    original=tuple(e.health.max_hp for e in g.encounter.enemies)
    for tick in range(limit):
        if not g.playing:break
        if tick:g.combat.advance()
        occupied=set(g.encounter.occupied_cells)
        queue=deque([(g.player.position,None)]);seen={g.player.position};direction=None
        while queue and direction is None:
            (x,y),first_direction=queue.popleft()
            for name,(dx,dy) in DIRECTIONS.items():
                cell=x+dx,y+dy
                if cell in occupied:
                    direction=first_direction or name;break
                if 0<=cell[0]<10 and 0<=cell[1]<10 and cell not in seen:
                    seen.add(cell);queue.append((cell,first_direction or name))
        if policy == 'guard':
            direction = _guard_direction(g,direction,tick,stats.move_interval_ticks)
        if direction:
            movement.key_down(direction,g.player,occupied=occupied,tick=tick);movement.key_up(direction)
        if any(g.player.position in e.target_cells and 0<=e.hit_tick-tick<=7 for e in g.encounter.ledger.pending):
            attempt=g.parry.request(tick)
            if attempt:g.resolver.register_parry(attempt)
        attack=g.combat.request_attack(g.player)
        if attack:
            result=g.resolver.resolve_player_attack(attack)
            if result:hits+=1
        hp=g.player.health.current_hp
        pulse=g.encounter.pulse
        king_hp=pulse.king.health.current_hp if pulse else 0
        previous=g.resolver.last_parry_result
        g.resolve_current_tick()
        if pulse and pulse.event is not None:pulse_events.add(pulse.event.key)
        if pulse and pulse.event and pulse.event.hit_tick==tick:
            reflected+=max(0,king_hp-pulse.king.health.current_hp)
        damage+=int(g.player.health.current_hp<hp)
        result=g.resolver.last_parry_result
        perfect+=int(result is not previous and result is not None and result.status=='perfect')
    row=dict(style=style,stage=stage,attack=stats.attack_damage,hp=list(original),
                basic_hits=[ceil(h/stats.attack_damage) for h in original],
                ticks=g.combat.tick,hits=hits,received=damage,perfect=perfect,
                result=g.state.value,remaining_hp=g.player.health.current_hp)

    if current:
        row.update(max_hp=stats.max_hp, move_ticks=stats.move_interval_ticks)
    if stage in (20,25):row.update(pulse_events=len(pulse_events),reflected_damage=reflected,max_hp=stats.max_hp,move_ticks=stats.move_interval_ticks,pulse_outcomes=[(r.state,r.outcome) for r in g.encounter.ledger._records.values() if r.event.attack_kind=='king_pulse'])
    return row
