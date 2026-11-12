"""Deterministic walking/attack/parry driver; never edits HP, AI or positions."""
from collections import deque
from math import ceil
from input_controller import InputController
from player import DIRECTIONS
from game import GameState
from chapter_run import ChapterRun
from upgrades import ChapterBuild
import main


STYLES = {
    'attack': ('attack',)*4,
    'survival': ('hp','hp','hp','attack'),
    'evasion': ('move','move','attack','attack'),
    'balanced': ('attack','hp','move','attack'),
}


def measure(style, stage, limit=3600):
    choices=STYLES[style]
    run=ChapterRun()
    if stage>=6:
        for kind in choices:run.select(run.offer_after_clear(run.current_stage,str(run.current_stage)),kind)
        run=run.start_chapter(2)
    first=(stage-1)//5*5+1
    for kind in choices[:stage-first]:run.select(run.offer_after_clear(run.current_stage,str(run.current_stage)),kind)
    g=main._new_stage_game(stage,stats=run.stats)
    movement=InputController(move_interval_ticks=run.stats.move_interval_ticks)
    hits=damage=perfect=0
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
        previous=g.resolver.last_parry_result
        g.resolve_current_tick()
        damage+=int(g.player.health.current_hp<hp)
        result=g.resolver.last_parry_result
        perfect+=int(result is not previous and result is not None and result.status=='perfect')
    return dict(style=style,stage=stage,attack=run.stats.attack_damage,hp=list(original),
                basic_hits=[ceil(h/run.stats.attack_damage) for h in original],
                ticks=g.combat.tick,hits=hits,received=damage,perfect=perfect,
                result=g.state.value,remaining_hp=g.player.health.current_hp)
