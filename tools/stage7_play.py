"""Development-only live Stage7, with one clearly synthetic prior receipt."""
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
    run.select(run.offer_after_clear(6, 'development-prior-stage6'), 'attack')
    game = _new_stage_game(7, stats=run.stats)
    return game, StageProgression(game, run)


if __name__ == '__main__':
    print('DEVELOPMENT: synthetic Stage6 ATTACK receipt; live original Stage7, not prior-clear evidence')
    run_session(*session())
