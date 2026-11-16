"""Development-only real Stage8; prior upgrade receipts are synthetic, not clears."""
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
    for stage, kind in ((6, 'attack'), (7, 'hp')):
        run.select(run.offer_after_clear(stage, 'development-prior-stage'+str(stage)), kind)
    game = _new_stage_game(8, stats=run.stats)
    return game, StageProgression(game, run)


if __name__ == '__main__':
    print('DEVELOPMENT: synthetic Stage6 ATTACK / Stage7 HP receipts; original live Stage8')
    run_session(*session())
