"""Development-only live boss session; synthetic prior receipts are not clears."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from chapter_run import ChapterRun
from main import _new_stage_game,run_session
from stage_progression import StageProgression


def session():
    run=ChapterRun()
    for stage,kind in enumerate(('move','move','attack','hp'),1):
        run.select(run.offer_after_clear(stage,'development-prior-'+str(stage)),kind)
    game=_new_stage_game(5,stats=run.stats)
    return game,StageProgression(game,run)


if __name__=='__main__':
    print('DEVELOPMENT SESSION: synthetic Stage1-4 receipt history; live original Stage5 combat')
    run_session(*session())
