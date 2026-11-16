"""Capture both display sizes from the SAME live, unmodified Stage5 state."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import stage5_art_renderer as art
from tools.stage5_play import session
from tools.stage5_art_preview import open_preview,capture_png,snapshot,Scene
from game_renderer import GameFlowRenderer


def capture(out):
    from pico2d import pico2d as c
    renderer=None
    try:
        open_preview(c,capture=True);renderer=art.Stage5ArtRenderer(c);g,flow=session()
        out.mkdir(parents=True,exist_ok=True);records=[]
        for target in (0,120,300,362):
            g.advance(max(0,target-g.combat.tick));before=snapshot(Scene('live',g))
            for label in ('before','after'):
                scales=dict(art.ENEMY_SCALE) if label=='after' else {k:1.0 for k in art.ENEMY_SCALE}
                offsets=dict(art.HP_OFFSET) if label=='after' else {k:5 for k in art.HP_OFFSET}
                with patch.dict(art.ENEMY_SCALE,scales,clear=True),patch.dict(art.HP_OFFSET,offsets,clear=True):
                    renderer.draw(g,{})
                GameFlowRenderer().draw_stage_label(c,g);GameFlowRenderer().draw(c,g)
                name=f'tick_{target}_{label}.png';capture_png(c,out/name)
                records.append(dict(file=name,tick=g.combat.tick,state=g.state.value,scale=scales,
                    warning_cells=renderer.warning_cells,layouts=renderer.actor_layouts,cue=renderer.cue))
                if before!=snapshot(Scene('live',g)):raise AssertionError('Capture mutated combat')
        (out/'capture_manifest.json').write_text(json.dumps(dict(status='SDL dummy scale QA, not Windows GUI approval',
            note='Same live session before/after; synthetic prior receipts, no HP/AI/clock changes during rendering',captures=records),indent=2)+'\n')
        print('Captured eight live frames; before/after combat states identical')
    finally:
        if renderer is not None:renderer.close()
        c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture-dir',required=True,type=Path)
    capture(p.parse_args().capture_dir)
