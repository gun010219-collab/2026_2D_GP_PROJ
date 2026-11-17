"""Development-only real Stage11; no prior chapter clears or synthetic receipts."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chapter_run import ChapterRun
from main import _new_stage_game, run_session
from stage_progression import StageProgression

# Legal damage4 entry, also reached by the recorded CFF balanced campaign.
# This selects a development starting build, not a Chapter1/2 clear history.
ENTRY_ATTACK_LEVEL = 3


def session():
    run = ChapterRun(3, entry_attack_level=ENTRY_ATTACK_LEVEL)
    game = _new_stage_game(11, stats=run.stats)
    return game, StageProgression(game, run)


if __name__ == '__main__':
    print('DEVELOPMENT: fresh Chapter3 Stage11; entry attack level3 / damage4; '
          'HP3/3 MOVE18 Receipt0. No Chapter1/2 clear history. '
          'Original Frozen Palace renderer; Stage11 2.5D art is not implemented.')
    run_session(*session())
