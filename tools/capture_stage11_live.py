"""Capture real Stage11 combat/ledger outcomes; no scene or combat overrides."""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game import StageGame
from game_renderer import GameFlowRenderer
from render_motion import RenderMotion
from stage11_art_renderer import Stage11ArtRenderer
from tools.stage11_play import session
from tools.stage5_art_preview import Scene, snapshot, open_preview, capture_png
from upgrade_renderer import UpgradeRenderer


def capture(out):
    from pico2d import pico2d as c
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    renderer = None; records = []
    try:
        open_preview(c, capture=True)
        motion = RenderMotion()
        renderer = Stage11ArtRenderer(c, motion=motion)

        def sync(g, elapsed):
            frozen = (g.player.entity_instance_id,) if g.combat.active_attack or g.parry.active_at(g.combat.tick) else ()
            motion.update((g.player, *g.encounter.enemies), elapsed,
                          session=g.combat.combat_session_id, frozen=frozen)

        def fresh():
            g, flow = session(); sync(g, 0)
            return g, flow

        def advance(g, tick):
            for _ in range(tick-g.combat.tick):
                g.advance(); sync(g, 1/60)

        def save(name, g, flow=None):
            before = pickle.dumps((g, motion))
            renderer.draw(g, motion.positions)
            GameFlowRenderer().draw_stage_label(c, g)
            GameFlowRenderer().draw(c, g)
            if flow and flow.offer:
                UpgradeRenderer().draw(c, g, flow.offer, flow.error)
            expected = [tuple(cell) for e in g.encounter.ledger.telegraphs for cell in e.target_cells] if g.playing else []
            if renderer.warning_cells != expected or pickle.dumps((g, motion)) != before:
                raise AssertionError('Rendering changed state or disagreed with the actual ledger')
            path = out/(name+'.png'); capture_png(c, path)
            names = {e.entity_instance_id:e.data_id for e in g.encounter.enemies}
            names[g.player.entity_instance_id] = 'player'
            records.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                state=snapshot(Scene('live Stage11', g)), cue=renderer.cue,
                                warning_cells=renderer.warning_cells,
                                order=[names[i] for i in renderer.order],
                                layouts={names[i]:v for i,v in renderer.actor_layouts.items()},
                                warnings=[dict(source=names[e.source_entity_instance_id],
                                               attack_id=e.attack_id, hit_tick=e.hit_tick,
                                               cells=e.target_cells) for e in g.encounter.ledger.telegraphs]))

        g, _ = fresh(); save('normal', g)
        advance(g, 114)
        if abs(motion.ground_pose(g.encounter.enemies[2])[1]-18) > 1e-6:
            raise AssertionError('Actual Knight movement did not reach its visual peak')
        save('knight_peak', g)
        advance(g, 134)
        a, b = [e.current_attack for e in g.encounter.enemies[:2]]
        if not a or not b: raise AssertionError('Expected two original Rook events')
        save('dual_rook', g)
        advance(g, a.hit_tick)
        if a in g.encounter.ledger.telegraphs or b not in g.encounter.ledger.telegraphs:
            raise AssertionError('Rook resolution removed the wrong source')
        save('rook1_resolved', g)
        for delta, status in ((18, 'normal'), (7, 'perfect')):
            g, _ = fresh(); advance(g, 134); event = g.encounter.enemies[0].current_attack
            advance(g, event.hit_tick-delta)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            if status == 'normal': save('parry_window', g)
            advance(g, event.hit_tick)
            if (g.resolver.last_parry_result.status, g.resolver.last_parry_result.enemy_event_key) != (status, event.key):
                raise AssertionError('Expected genuine Rook parry result')
            save('parry_'+status, g)

        # Original deterministic movement/attack/parry driver, unchanged.
        from tests.test_hp_carryover import fight
        g, flow = fresh(); resolve = StageGame.resolve_current_tick
        observed = set()
        def observe(game):
            result = resolve(game)
            if game is g:
                sync(game, 1/60)
                if game.combat.active_attack and 'attack' not in observed:
                    save('player_attack', game); observed.add('attack')
                pawn = game.encounter.enemies[-1]
                if pawn.current_attack and 'pawn' not in observed:
                    save('pawn_warning', game); observed.add('pawn')
            return result
        with patch.object(StageGame, 'resolve_current_tick', observe):
            result = fight(flow)
        if result != (11, 'UPGRADE', 669, 2, 3) or observed != {'attack', 'pawn'}:
            raise AssertionError('Original Stage11 real fight result changed')
        flow.sync_offer(); save('upgrade', g, flow)
        next_game, _ = flow.choose(flow.offer, 'hp', __import__('main')._new_stage_game)
        if (next_game.stage_number, next_game.player.health.current_hp, len(flow.run.receipts)) != (12, 3, 1):
            raise AssertionError('Original Stage12 entry changed')
        g, _ = fresh(); advance(g, 435)
        if g.state.value != 'GAME_OVER': raise AssertionError('Expected original no-input death')
        save('game_over', g)
        manifest = dict(status='Actual Stage11 SDL captures; Windows human GUI/performance pending',
                        preparation='Fresh development Chapter3 entry level3/damage4, HP3/3, MOVE18, Receipt0; no prior-clear evidence',
                        method='Original mixed AI/HP/ledger, actual requests/outcomes and unchanged driver; no forced clears',
                        fight_result=result, stage12=dict(hp=3, max_hp=4, receipts=1, legacy_display=True),
                        captures=records)
        (out/'capture_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
        print('CAPTURED', len(records), 'live Stage11 frames; real fight', result, 'Stage12 HP3/4 Receipt1')
        return manifest
    finally:
        if renderer is not None: renderer.close()
        if c.window: c.close_canvas(); c.window = c.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir', required=True, type=Path)
    capture(parser.parse_args().capture_dir)
