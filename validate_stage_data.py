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

def validate(data):
    assert data['board_size'] == BOARD_SIZE
    stages = data['stages']
    assert len(stages) == 25
    assert sum(1 for c in range(BOARD_SIZE) for r in range(BOARD_SIZE) if (c+r)%2 == 0) == 50
    assert sum(1 for c in range(BOARD_SIZE) for r in range(BOARD_SIZE) if (c+r)%2 == 1) == 50
    for n, s in enumerate(stages, start=1):
        assert s['stage'] == n
        assert s['chapter'] == ((n-1)//5+1)
        assert s['boss'] == (n%5 == 0)
        assert s['boss_hp'] == KING_HP.get(n)
        assert s['player_spawn'] == [5,1]
        enemies = s['enemies']
        assert 2 <= len(enemies) <= MAX_ENEMIES
        assert Counter(e['type'] for e in enemies) == Counter(ROSTERS[n]), n
        ids = [e['id'] for e in enemies]
        assert len(set(ids)) == len(ids)
        positions = [(e['col'],e['row']) for e in enemies]
        assert len(set(positions)) == len(positions)
        assert tuple(s['player_spawn']) not in set(positions)
        for e in enemies:
            assert all(isinstance(e[c],int) and 0<=e[c]<BOARD_SIZE for c in ('col','row'))
            assert 0 <= e['initial_delay'] <= 10
            if e['type']=='pawn': assert e['forward'] == [0,-1]
        bishops = [e for e in enemies if e['type']=='bishop']
        if len(bishops)==2:
            assert (bishops[0]['col']+bishops[0]['row'])%2 != (bishops[1]['col']+bishops[1]['row'])%2
    return len(stages)

if __name__ == '__main__':
    data=json.loads(FILE.read_text(encoding='utf-8'))
    count=validate(data)
    print(f'PASS: {count} stages, 10x10, distinct in-bounds spawns, counts/boss HP, bishops checked')
    print('NOTE: actual gameplay solvability and balance require manual/simulated playtests.')
