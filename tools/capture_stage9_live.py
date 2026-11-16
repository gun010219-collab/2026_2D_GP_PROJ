"""Capture original Stage9 dual-Rook events and genuine parry results, not fixtures."""
import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.stage9_play import session
from render_motion import RenderMotion
from stage9_art_renderer import Stage9ArtRenderer
from tools.stage5_art_preview import Scene, snapshot, open_preview, capture_png
from game_renderer import GameFlowRenderer


def capture(out):
    from pico2d import pico2d as c
    renderer = None
    out.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        open_preview(c, capture=True)
        motion = RenderMotion()
        renderer = Stage9ArtRenderer(c, motion=motion)

        def fresh():
            g, _ = session()
            motion.update((g.player, *g.encounter.enemies), 0, session=g.combat.combat_session_id)
            return g

        def advance(g, tick):
            for _ in range(tick - g.combat.tick):
                g.advance()
                motion.update((g.player, *g.encounter.enemies), 1/60, session=g.combat.combat_session_id)

        def save(name, g):
            before = pickle.dumps((g, motion))
            renderer.draw(g, motion.positions)
            GameFlowRenderer().draw_stage_label(c, g)
            GameFlowRenderer().draw(c, g)
            expected = [tuple(cell) for event in g.encounter.ledger.telegraphs for cell in event.target_cells]
            if renderer.warning_cells != expected or pickle.dumps((g, motion)) != before:
                raise AssertionError('Capture changed state or did not match actual warnings')
            p = out/(name+'.png'); capture_png(c, p)
            records.append(dict(file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                state=snapshot(Scene('live', g)), cue=renderer.cue,
                                warning_cells=renderer.warning_cells, layouts=renderer.actor_layouts,
                                warnings=[dict(source=next(e.data_id for e in g.encounter.enemies if e.entity_instance_id == event.source_entity_instance_id),
                                               attack_id=event.attack_id, hit_tick=event.hit_tick, target_cells=event.target_cells)
                                          for event in g.encounter.ledger.telegraphs]))

        g = fresh(); save('normal', g); advance(g, 147)
        bishop, first, second = [e.current_attack for e in g.encounter.enemies[:3]]
        if not all((bishop, first, second)) or len(bishop.target_cells) != 50:
            raise RuntimeError('Expected original Bishop and independent Rook warnings')
        save('dual_rook_bishop', g); advance(g, first.hit_tick)
        if first in g.encounter.ledger.telegraphs or second not in g.encounter.ledger.telegraphs:
            raise RuntimeError('Source resolution did not preserve the other Rook')
        save('rook1_resolved', g)
        g = fresh(); advance(g, 175)
        g.resolver.register_parry(g.parry.request(g.combat.tick)); advance(g, 182)
        if g.resolver.last_parry_result.status != 'failed': raise RuntimeError('Expected real invulnerability rejection')
        save('parry_failed', g)
        for delta, status in ((18, 'normal'), (7, 'perfect')):
            g = fresh(); advance(g, 149)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            advance(g, 285); event = g.encounter.enemies[1].current_attack
            advance(g, event.hit_tick-delta)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            if status == 'normal': save('parry_window', g)
            advance(g, event.hit_tick)
            result = g.resolver.last_parry_result
            if (result.status, result.enemy_event_key) != (status, event.key):
                raise RuntimeError('Expected genuine Rook parry')
            save('parry_'+status, g)
        (out/'capture_manifest.json').write_text(json.dumps(dict(
            status='Actual native SDL Stage9 captures; human GUI and Windows performance not verified',
            preparation='Synthetic Stage6 ATTACK / Stage7 HP / Stage8 HP receipts, not prior-clear evidence',
            method='Original AI/HP/clocks, real parry requests, no attack/HP overrides or new art',
            captures=records), indent=2)+'\n', encoding='utf-8')
        print('CAPTURED seven live Stage9 frames: dual Rooks / Bishop50 / genuine parry outcomes')
    finally:
        if renderer is not None: renderer.close()
        c.close_canvas()
        c.window = c.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir', type=Path, required=True)
    capture(parser.parse_args().capture_dir)
