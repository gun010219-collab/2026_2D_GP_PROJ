"""Capture original live Stage6 AI and genuinely adjudicated parry inputs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from stage6_art_renderer import Stage6ArtRenderer
from tools.stage6_play import session
from tools.stage5_art_preview import Scene, snapshot, open_preview, capture_png
from game_renderer import GameFlowRenderer


def capture(out):
    from pico2d import pico2d as c
    renderer = None
    out.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        open_preview(c, capture=True)
        renderer = Stage6ArtRenderer(c)

        def save(name, game):
            before = snapshot(Scene('live', game))
            renderer.draw(game, {})
            GameFlowRenderer().draw_stage_label(c, game)
            GameFlowRenderer().draw(c, game)
            path = out / (name + '.png')
            capture_png(c, path)
            assert snapshot(Scene('live', game)) == before
            records.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                state=before, cue=renderer.cue, warning_cells=renderer.warning_cells,
                                layouts=renderer.actor_layouts))

        g, _ = session()
        save('normal', g)
        rook = g.encounter.enemies[-1]
        while g.playing and rook.current_attack is None and g.combat.tick < 900:
            g.advance()
        if rook.current_attack is None:
            raise RuntimeError('No genuine Rook warning')
        save('rook_warning', g)
        for delta, name in ((18, 'normal'), (7, 'perfect')):
            g, _ = session()
            rook = g.encounter.enemies[-1]
            while g.playing and rook.current_attack is None and g.combat.tick < 900:
                g.advance()
            event = rook.current_attack
            if event is None:
                raise RuntimeError('No genuine Rook warning')
            g.advance(event.hit_tick - delta - g.combat.tick)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            if name == 'normal':
                save('parry_window', g)
            g.advance(delta)
            if not g.resolver.last_parry_result or g.resolver.last_parry_result.status != name:
                raise RuntimeError('Parry not adjudicated as expected')
            save('parry_' + name, g)
        (out / 'capture_manifest.json').write_text(json.dumps(dict(
            status='Native SDL software/dummy; not Windows GUI approval or performance',
            preparation='Fresh Chapter2 run, entry attack level1; no simulated Chapter1 clear',
            method='Actual AI clocks and parry requests; no HP/positions/AI overrides',
            captures=records), indent=2) + '\n', encoding='utf-8')
        print('Captured five actual Stage6 states, including genuine normal/perfect parries')
    finally:
        if renderer is not None:
            renderer.close()
        c.close_canvas()
        c.window = c.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir', type=Path, required=True)
    capture(parser.parse_args().capture_dir)
