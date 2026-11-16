"""Native captures of original Stage8 AI, Bishop fifty-cell warning and parries."""
import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.stage8_play import session
from render_motion import RenderMotion
from stage8_art_renderer import Stage8ArtRenderer
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
        renderer = Stage8ArtRenderer(c, motion=motion)

        def fresh():
            g, _ = session()
            motion.update((g.player, *g.encounter.enemies), 0, session=g.combat.combat_session_id)
            return g

        def advance(g, count):
            for _ in range(count):
                g.advance()
                motion.update((g.player, *g.encounter.enemies), 1/60, session=g.combat.combat_session_id)

        def save(name, g):
            before = pickle.dumps((g, motion))
            renderer.draw(g, motion.positions)
            GameFlowRenderer().draw_stage_label(c, g)
            GameFlowRenderer().draw(c, g)
            p = out/(name+'.png')
            capture_png(c, p)
            if pickle.dumps((g, motion)) != before:
                raise AssertionError('Capture mutated game/motion')
            records.append(dict(file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                state=snapshot(Scene('live', g)), cue=renderer.cue,
                                warning_cells=renderer.warning_cells, layouts=renderer.actor_layouts))

        g = fresh()
        save('normal', g)
        advance(g, 48)
        event = g.encounter.enemies[0].current_attack
        if not event or len(event.target_cells) != 50:
            raise RuntimeError('Original Bishop did not issue fifty-cell warning')
        save('bishop_warning', g)
        advance(g, 140-g.combat.tick)
        save('mixed_warning', g)
        advance(g, event.hit_tick-g.combat.tick)
        if event in g.encounter.ledger.telegraphs:
            raise RuntimeError('Resolved Bishop warning remains')
        save('bishop_resolved', g)
        for delta, name in ((18, 'normal'), (7, 'perfect')):
            g = fresh()
            advance(g, 48)
            event = g.encounter.enemies[0].current_attack
            advance(g, event.hit_tick-delta-g.combat.tick)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            if name == 'normal':
                save('parry_window', g)
            advance(g, delta)
            if not g.resolver.last_parry_result or g.resolver.last_parry_result.status != name:
                raise RuntimeError('Parry not genuinely adjudicated')
            save('parry_'+name, g)
        (out/'capture_manifest.json').write_text(json.dumps(dict(
            status='Actual Stage8 simulation/native SDL captures; Windows GUI approval and FPS not measured',
            preparation='Development run: synthetic Stage6 ATTACK and Stage7 HP receipts; not prior-clear evidence',
            method='Original AI/HP/clocks, real parry requests, no overrides. Bishop is stationary in existing AI.',
            captures=records), indent=2)+'\n', encoding='utf-8')
        print('CAPTURED seven live Stage8 states / Bishop50 / actual parry and resolution')
    finally:
        if renderer is not None:
            renderer.close()
        c.close_canvas()
        c.window = c.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir', type=Path, required=True)
    capture(parser.parse_args().capture_dir)
