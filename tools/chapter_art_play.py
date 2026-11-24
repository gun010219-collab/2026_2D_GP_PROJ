"""Play any stage after genuine automated prior fights and upgrades."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import _new_stage_game, run_session
from stage_progression import StageProgression
from tests.test_hp_carryover import fight
from tools.campaign_qa import choice
from tools.stage11_play import session as frozen_start

UPGRADES = {1: ('attack',) * 4, 3: ('hp', 'attack', 'hp', 'attack')}
STAGES = tuple(range(1, 26))


def advance_campaign(flow, result):
    game = flow.game
    if result[1] == 'BOSS_CLEAR' and game.stage_number < 25:
        flow.enter_next_chapter(_new_stage_game)
    elif result[1] == 'UPGRADE':
        kind = choice('attack', game.stage_number, len(flow.run.receipts))
        flow.choose(flow.sync_offer(), kind, _new_stage_game)
    else:
        raise RuntimeError(f'Automated fight did not reach a transition: {result}')


def session(stage):
    if stage not in STAGES:
        raise ValueError(f'Stage {stage} is outside the campaign')
    chapter = (stage - 1) // 5 + 1
    flow = frozen_start()[1] if chapter == 3 else StageProgression(_new_stage_game(1))
    while flow.game.stage_number < stage:
        result = fight(flow)
        if chapter == 3:
            if result[1] != 'UPGRADE':
                raise RuntimeError(f'Automated fight did not clear: {result}')
            kind = UPGRADES[chapter][len(flow.run.receipts)]
            flow.choose(flow.sync_offer(), kind, _new_stage_game)
        else:
            advance_campaign(flow, result)
    return flow.game, flow


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', type=int, choices=STAGES)
    args = parser.parse_args()
    game, flow = session(args.stage)
    print(f'Development Stage {game.stage_number} | entry attack level {flow.run.entry_attack_level} | '
          f'{len(flow.run.receipts)} earned upgrades from automated fights | '
          '2.5D campaign art enabled by default', flush=True)
    run_session(game, flow, default_art=True)
