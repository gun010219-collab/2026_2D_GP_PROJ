"""Native captures of the original Stage10 boss, real Pulse and actual full fight."""
import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.stage10_play import session
from render_motion import RenderMotion
from stage10_art_renderer import Stage10ArtRenderer
from input_controller import InputController
from tools.stage5_art_preview import Scene, snapshot, open_preview, capture_png
from game_renderer import GameFlowRenderer


def capture(out):
    from pico2d import pico2d as c
    renderer = None
    out.mkdir(parents=True, exist_ok=True); records = []
    try:
        open_preview(c, capture=True); motion = RenderMotion(); renderer = Stage10ArtRenderer(c, motion=motion)

        def sync(g, elapsed):
            frozen = [e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse.frozen(e)]
            motion.update((g.player, *g.encounter.enemies), elapsed, session=g.combat.combat_session_id, frozen=frozen)

        def fresh():
            g, flow = session(); sync(g, 0); return g, flow

        def advance(g, tick):
            for _ in range(tick-g.combat.tick): g.advance(); sync(g, 1/60)

        def save(name, g):
            before = pickle.dumps((g, motion)); renderer.draw(g, motion.positions)
            GameFlowRenderer().draw_stage_label(c, g); GameFlowRenderer().draw(c, g)
            expected = [tuple(cell) for event in g.encounter.ledger.telegraphs for cell in event.target_cells] if g.playing else []
            if renderer.warning_cells != expected or pickle.dumps((g, motion)) != before:
                raise AssertionError('Capture changed state or did not match actual ledger')
            path = out/(name+'.png'); capture_png(c, path); p = g.encounter.pulse
            records.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                state=snapshot(Scene('live', g)), cue=renderer.cue,
                                pulse=dict(state=p.state, freeze_tick=p.freeze_tick, resume_tick=p.resume_tick,
                                           next_use_tick=p.next_use_tick, king_hp=p.king.health.current_hp),
                                warning_cells=renderer.warning_cells, layouts=renderer.actor_layouts))

        g, _ = fresh(); save('normal', g); advance(g, 90); save('mixed_warning', g)
        g, flow = fresh(); movement = InputController(move_interval_ticks=flow.run.stats.move_interval_ticks)
        for _ in range(220):
            movement.key_down('up', g.player, occupied=g.encounter.occupied_cells, tick=g.combat.tick)
            movement.key_up('up'); g.advance(); sync(g, 1/60)
            if g.encounter.pulse.king.current_attack: break
        if not g.encounter.pulse.king.current_attack: raise RuntimeError('No original King melee')
        save('king_melee', g)
        g, _ = fresh(); advance(g, 265); event = g.encounter.pulse.event
        if not event or len(event.target_cells) != 100: raise RuntimeError('No original hundred-cell Pulse')
        save('pulse_telegraph', g); advance(g, event.hit_tick); save('pulse_cleanup', g)
        advance(g, event.hit_tick+30); save('pulse_resumed', g)
        for delta, status in ((18, 'normal'), (7, 'perfect')):
            g, _ = fresh(); advance(g, 265); event = g.encounter.pulse.event
            advance(g, event.hit_tick-delta); g.resolver.register_parry(g.parry.request(g.combat.tick))
            advance(g, event.hit_tick)
            if (g.resolver.last_parry_result.status, g.encounter.pulse.king.health.current_hp) != (status, 48 if status == 'perfect' else 50):
                raise RuntimeError('Pulse was not genuinely parried with original reflection')
            save('pulse_parry_'+status, g)
        # Original deterministic driver; no HP, AI, clock or enemy-death overrides.
        from tests.test_hp_carryover import fight
        g, flow = fresh()
        if fight(flow) != (10, 'BOSS_CLEAR', 749, 4, 5): raise RuntimeError('Original boss fight changed')
        sync(g, 0); save('boss_clear', g)
        (out/'capture_manifest.json').write_text(json.dumps(dict(
            status='Actual Stage10/native SDL boss captures; Windows human GUI and performance not verified',
            preparation='Synthetic Stage6 ATTACK / Stage7 HP / Stage8 HP / Stage9 ATTACK receipts, not prior-clear evidence',
            method='Original AI/HP/clock, legal input and real parry requests, genuine full fight for boss clear',
            captures=records), indent=2)+'\n', encoding='utf-8')
        print('CAPTURED nine actual Stage10 frames: King melee, Pulse, reflection2, full boss clear')
    finally:
        if renderer is not None: renderer.close()
        c.close_canvas(); c.window = c.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--capture-dir', type=Path, required=True)
    capture(parser.parse_args().capture_dir)
