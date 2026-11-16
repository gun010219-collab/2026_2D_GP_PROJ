"""Development-only original Stage10; synthetic prior receipts are not clears."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from chapter_run import ChapterRun
from main import _new_stage_game, run_session
from stage_progression import StageProgression


def session():
    run = ChapterRun(2, entry_attack_level=1)
    for stage, kind in ((6, 'attack'), (7, 'hp'), (8, 'hp'), (9, 'attack')):
        run.select(run.offer_after_clear(stage, 'development-prior-stage'+str(stage)), kind)
    game = _new_stage_game(10, stats=run.stats)
    return game, StageProgression(game, run)


if __name__ == '__main__':
    print('DEVELOPMENT: synthetic Stage6 ATTACK / Stage7 HP / Stage8 HP / Stage9 ATTACK receipts; original Stage10 boss')
    run_session(*session())
