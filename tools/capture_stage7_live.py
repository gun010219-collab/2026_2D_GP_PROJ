"""Reproduce live AI motion and genuine parries; never replace combat with a scene."""
import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.stage7_play import session
from render_motion import RenderMotion
from stage7_art_renderer import Stage7ArtRenderer
from tools.stage5_art_preview import Scene, snapshot, open_preview, capture_png
from game_renderer import GameFlowRenderer


def capture(out):
    from pico2d import pico2d as c
    renderer = None
    records = []
    out.mkdir(parents=True, exist_ok=True)
    try:
        open_preview(c, capture=True)
        motion = RenderMotion()
        renderer = Stage7ArtRenderer(c, motion=motion)

        def fresh():
            g, _ = session()
            motion.update((g.player, *g.encounter.enemies), 0, session=g.combat.combat_session_id)
            return g

        def step(g, count=1):
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
                raise AssertionError('Rendering mutated combat or motion')
            records.append(dict(file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                state=snapshot(Scene('live', g)), cue=renderer.cue,
                                warning_cells=renderer.warning_cells, layouts=renderer.actor_layouts,
                                ground_poses={e.data_id: motion.ground_pose(e) for e in g.encounter.enemies}))

        g = fresh()
        save('normal', g)
        while g.playing and not g.encounter.ledger.telegraphs and g.combat.tick < 600:
            step(g)
        if not g.encounter.ledger.telegraphs:
            raise RuntimeError('Original Stage7 never issued a warning')
        save('knight_warning', g)
        knights = [e for e in g.encounter.enemies if e.kind == 'knight']
        while g.playing and max(motion.ground_pose(e)[1] for e in knights) < 17.9 and g.combat.tick < 600:
            step(g)
        if max(motion.ground_pose(e)[1] for e in knights) < 17.9:
            raise RuntimeError('No actual Knight hop observed')
        save('jump_peak', g)
        for _ in range(30):
            step(g)
            if all(motion.ground_pose(e)[1] == 0 for e in knights):
                break
        if any(motion.ground_pose(e)[1] != 0 for e in knights):
            raise RuntimeError('Knight failed to settle')
        save('landing', g)
        for delta, name in ((18, 'normal'), (7, 'perfect')):
            g = fresh()
            event = None
            while g.playing and g.combat.tick < 600:
                step(g)
                event = next((e for e in g.encounter.ledger.pending
                              if g.player.position in e.target_cells and e.hit_tick-g.combat.tick >= 18), None)
                if event is not None:
                    break
            if event is None:
                raise RuntimeError('No original attack eligible for parry')
            step(g, event.hit_tick-delta-g.combat.tick)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            if name == 'normal':
                save('parry_window', g)
            step(g, delta)
            if not g.resolver.last_parry_result or g.resolver.last_parry_result.status != name:
                raise RuntimeError('Parry not genuinely adjudicated')
            save('parry_'+name, g)
        (out/'capture_manifest.json').write_text(json.dumps(dict(
            status='Actual Stage7 AI/motion snapshots; not Windows visual approval or FPS measurement',
            preparation='Development run with synthetic Stage6 ATTACK receipt; not prior-clear evidence',
            method='Original AI/HP/clocks; no position/HP/AI overrides. Motion elapsed=1/60 per actual simulation tick.',
            captures=records), indent=2)+'\n', encoding='utf-8')
        print('CAPTURED seven live Stage7 states / authentic Knight motion and parry results')
    finally:
        if renderer is not None:
            renderer.close()
        c.close_canvas()
        c.window = c.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir', type=Path, required=True)
    capture(parser.parse_args().capture_dir)
