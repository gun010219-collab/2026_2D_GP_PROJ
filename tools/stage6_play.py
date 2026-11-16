"""Development-only real Stage6 combat; no prior clears or unlocks implied."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from chapter_run import ChapterRun
from main import _new_stage_game, run_session
from stage_progression import StageProgression


def session():
    # A fresh Chapter2 run, with the legal entry attack level from a base Ch1 run.
    # No receipts, HP refill, AI override, frozen scene or progression bypass in game.
    run = ChapterRun(2, entry_attack_level=1)
    game = _new_stage_game(6, stats=run.stats)
    return game, StageProgression(game, run)


if __name__ == '__main__':
    print('DEVELOPMENT: fresh Chapter2 run; live original Stage6; not evidence of Chapter1 completion')
    run_session(*session())
