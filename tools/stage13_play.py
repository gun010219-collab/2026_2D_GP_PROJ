"""Real Stage13 after automated original Stage11/12 fights and genuine upgrades."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from main import _new_stage_game,run_session
from tools.stage12_play import session as stage12_session
from tests.test_hp_carryover import fight


def session():
    game,flow=stage12_session()
    result=fight(flow)
    if result!=(12,'UPGRADE',669,3,4):raise RuntimeError('Development Stage12 driver did not reach its validated clear: '+str(result))
    game,_=flow.choose(flow.sync_offer(),'attack',_new_stage_game)
    return game,flow


if __name__=='__main__':
    print('DEVELOPMENT: real Stage13 after AUTOMATED real Stage11/12 fights and normal HP/attack upgrades. '
          'Fresh Chapter3 entry level3/damage4; Stage13 level4/damage5 HP3/4 MOVE18 Receipt2. '
          'No synthetic receipts, forced kills, invulnerability, human previous-clear or permanent unlock claim. '
          'CHECKMATE_STAGE13_ART=1 enables Frozen art; default is original renderer.',flush=True)
    run_session(*session())
