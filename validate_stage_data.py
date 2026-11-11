"""CHECKMATE stage_data.json static checker (Python standard library only).

This validates structural constraints, not playability or game difficulty.
"""
import json
from collections import Counter
from pathlib import Path

FILE = Path(__file__).with_name('stage_data.json')
BOARD_SIZE = 10
MAX_ENEMIES = 8
KING_HP = {5: 8, 10: 10, 15: 12, 20: 14, 25: 16}
ROSTERS = {
    1: {'pawn':2},2: {'rook':1,'pawn':2},3: {'knight':1,'pawn':2},
    4: {'bishop':1,'rook':1,'pawn':2},5: {'king':1,'rook':1,'pawn':2},
    6: {'pawn':3,'rook':1},7: {'knight':2,'pawn':2},
    8: {'bishop':1,'rook':1,'knight':1,'pawn':2},
    9: {'bishop':1,'rook':2,'knight':1,'pawn':1},
    10: {'king':1,'bishop':1,'knight':1,'pawn':2},
    11: {'rook':2,'knight':2,'pawn':1},
    12: {'bishop':2,'rook':1,'pawn':2},
    13: {'queen':1,'knight':1,'pawn':3},
    14: {'queen':1,'rook':1,'bishop':1,'pawn':2},
    15: {'king':1,'queen':1,'rook':1,'pawn':2},
    16: {'rook':2,'knight':2,'bishop':1,'pawn':1},
    17: {'bishop':2,'rook':2,'knight':1,'pawn':1},
    18: {'queen':1,'bishop':1,'rook':2,'pawn':2},
    19: {'queen':1,'knight':2,'rook':2,'bishop':1,'pawn':1},
    20: {'king':1,'queen':1,'bishop':1,'knight':2,'pawn':1},
    21: {'queen':1,'rook':2,'knight':2,'bishop':1,'pawn':1},
    22: {'queen':1,'bishop':2,'rook':1,'knight':2,'pawn':1},
    23: {'rook':2,'knight':2,'bishop':2,'pawn':2},
    24: {'queen':2,'rook':2,'bishop':1,'knight':2,'pawn':1},
    25: {'king':1,'queen':1,'rook':2,'knight':2,'bishop':1,'pawn':1},
}

def _require(condition, message):
    # Explicit checks also protect catalog loading under python -O. Preserve the
    # original AssertionError contract used by the static checker's callers.
    if not condition:
        raise AssertionError(message)


def validate(data):
    _require(data['board_size'] == BOARD_SIZE, 'board_size must be 10')
    stages = data['stages']
    _require(len(stages) == 25, 'stages must contain 25 entries')
    _require(sum(1 for c in range(BOARD_SIZE) for r in range(BOARD_SIZE) if (c+r)%2 == 0) == 50,
             'board must have 50 light squares')
    _require(sum(1 for c in range(BOARD_SIZE) for r in range(BOARD_SIZE) if (c+r)%2 == 1) == 50,
             'board must have 50 dark squares')
    for n, s in enumerate(stages, start=1):
        prefix = f'Stage {n}: '
        _require(s['stage'] == n, prefix + 'stage number/order mismatch')
        _require(s['chapter'] == ((n-1)//5+1), prefix + 'chapter mismatch')
        _require(s['boss'] == (n%5 == 0), prefix + 'boss flag mismatch')
        _require(s['boss_hp'] == KING_HP.get(n), prefix + 'boss_hp mismatch')
        _require(s['player_spawn'] == [5,1], prefix + 'player_spawn mismatch')
        enemies = s['enemies']
        _require(2 <= len(enemies) <= MAX_ENEMIES, prefix + 'enemy count out of range')
        _require(Counter(e['type'] for e in enemies) == Counter(ROSTERS[n]), prefix + 'roster mismatch')
        ids = [e['id'] for e in enemies]
        _require(len(set(ids)) == len(ids), prefix + 'duplicate enemy IDs')
        positions = [(e['col'],e['row']) for e in enemies]
        _require(len(set(positions)) == len(positions), prefix + 'duplicate enemy positions')
        _require(tuple(s['player_spawn']) not in set(positions), prefix + 'player/enemy overlap')
        for e in enemies:
            _require(all(isinstance(e[c],int) and 0<=e[c]<BOARD_SIZE for c in ('col','row')),
                     prefix + 'enemy position out of bounds')
            _require(0 <= e['initial_delay'] <= 10, prefix + 'initial_delay out of range')
            if e['type']=='pawn':
                _require(e['forward'] == [0,-1], prefix + 'pawn forward mismatch')
        bishops = [e for e in enemies if e['type']=='bishop']
        if len(bishops)==2:
            _require((bishops[0]['col']+bishops[0]['row'])%2 != (bishops[1]['col']+bishops[1]['row'])%2,
                     prefix + 'bishops must occupy opposite colors')
    return len(stages)

if __name__ == '__main__':
    data=json.loads(FILE.read_text(encoding='utf-8'))
    count=validate(data)
    print(f'PASS: {count} stages, 10x10, distinct in-bounds spawns, counts/boss HP, bishops checked')
    print('NOTE: actual gameplay solvability and balance require manual/simulated playtests.')
