"""Development real Stage12 after automated real Stage11 and a genuine HP receipt."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from main import _new_stage_game,run_session
from tools.stage11_play import session as stage11_session
from tests.test_hp_carryover import fight


def session():
    game,flow=stage11_session()
    # Original movement/SPACE/parry policy, no forced HP/deaths/receipts.
    result=fight(flow)
    if result!=(11,'UPGRADE',669,2,3):raise RuntimeError('Development Stage11 driver did not reach its validated clear: '+str(result))
    game,_=flow.choose(flow.sync_offer(),'hp',_new_stage_game)
    return game,flow


if __name__=='__main__':
    print('DEVELOPMENT: starting real Stage12 after an AUTOMATED real Stage11 fight and normal HP upgrade. '
          'Fresh Chapter3 entry level3/damage4; Stage12 HP3/4 MOVE18 Receipt1. '
          'No synthetic receipts, no human Chapter1/2/3 clear or permanent unlock claim. '
          'CHECKMATE_STAGE12_ART=1 enables Frozen art; default is original renderer.',flush=True)
    run_session(*session())
