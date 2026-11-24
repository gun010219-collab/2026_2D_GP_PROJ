"""Play a supported Chapter 1 or 3 stage after genuine automated prior fights."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import _new_stage_game, run_session
from stage_progression import StageProgression
from tests.test_hp_carryover import fight
from tools.stage11_play import session as frozen_start

UPGRADES = {1: ('attack',) * 4, 3: ('hp', 'attack', 'hp', 'attack')}
STAGES = (*range(1, 6), *range(11, 16))


def session(stage):
    if stage not in STAGES:
        raise ValueError(f'Stage {stage} is outside the royal and frozen chapters')
    chapter = (stage - 1) // 5 + 1
    flow = StageProgression(_new_stage_game(1)) if chapter == 1 else frozen_start()[1]
    while flow.game.stage_number < stage:
        result = fight(flow)
        if result[1] != 'UPGRADE':
            raise RuntimeError(f'Automated fight did not clear: {result}')
        kind = UPGRADES[chapter][len(flow.run.receipts)]
        flow.choose(flow.sync_offer(), kind, _new_stage_game)
    return flow.game, flow


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=int, choices=STAGES)
    args = parser.parse_args()
    game, flow = session(args.stage)
    print(f'Development Stage {game.stage_number} | entry attack level {flow.run.entry_attack_level} | '
          f'{len(flow.run.receipts)} earned upgrades from automated fights | '
          f'CHECKMATE_CHAPTER{game.chapter}_ART=1 enables the chapter art', flush=True)
    run_session(game, flow)
