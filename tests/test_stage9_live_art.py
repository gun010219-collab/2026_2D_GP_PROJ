"""Stage9 reuses forest presentation; two independent Rooks retain real ledgers."""
import hashlib
import json
import os
import pickle
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import main
from arena_art_common import CAMERA, ArenaArtError
from render_motion import RenderMotion
import stage5_art_renderer as royal
import stage6_art_renderer as six
import stage7_art_renderer as seven
import stage8_art_renderer as eight
import stage9_art_renderer as art
from tests.test_stage6_live_art import canvas
from tools.stage9_play import session


class Stage9LiveArtTests(unittest.TestCase):
    def render(self, g, *, motion=None):
        r = art.Stage9ArtRenderer(canvas(), motion=motion)
        self.addCleanup(r.close)
        before = pickle.dumps((g, motion))
        with patch.object(royal, 'polygon'), patch.object(r, 'image'):
            r.draw(g, motion.positions if motion else {})
        self.assertEqual(pickle.dumps((g, motion)), before)
        self.assertEqual(r.warning_cells, [tuple(c) for e in g.encounter.ledger.telegraphs
                                          for c in e.target_cells] if g.playing else [])
        return r

    def test_stage9_flags_are_independent_and_other_twenty_stages_stay_legacy(self):
        flags = {f'CHECKMATE_STAGE{n}_ART': '0' for n in range(5, 10)}
        for enabled in ((), (5,), (6,), (7,), (8,), (9,), (5, 6, 7, 8, 9)):
            with patch.dict(os.environ, {**flags, **{f'CHECKMATE_STAGE{n}_ART': '1' for n in enabled}}):
                c = canvas(); path = art.LiveArenaArtPath(c)
                with patch.object(royal.Stage5ArtRenderer, 'draw'), patch.object(six.Stage6ArtRenderer, 'draw'), patch.object(seven.Stage7ArtRenderer, 'draw'), patch.object(eight.Stage8ArtRenderer, 'draw'), patch.object(art.Stage9ArtRenderer, 'draw'):
                    for n in range(1, 26):
                        self.assertEqual(path.draw(main._new_stage_game(n), {}), n in enabled, (n, enabled))
                path.close()
                expected = sum({5: 8, 6: 7, 7: 7, 8: 9, 9: 9}[n] for n in enabled)
                self.assertEqual(c.load_image.call_count, expected)
                self.assertEqual(c.SDL_DestroyTexture.call_count, expected)

    def test_original_roster_hp_receipts_no_king_and_no_new_art_profile(self):
        g, f = session()
        self.assertEqual((g.stage_number, g.chapter, g.boss, g.player.position), (9, 2, False, (5, 1)))
        self.assertEqual([(e.data_id, e.kind, e.position, e.health.max_hp, e.initial_delay_ticks) for e in g.encounter.enemies],
                         [('s9_bishop_1', 'bishop', (2, 8), 9, 48), ('s9_rook_1', 'rook', (2, 4), 12, 62),
                          ('s9_rook_2', 'rook', (7, 4), 12, 75), ('s9_knight_1', 'knight', (3, 6), 9, 88),
                          ('s9_pawn_1', 'pawn', (1, 6), 7, 101)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies), 49)
        self.assertIsNone(g.encounter.pulse)
        self.assertEqual((len(f.run.receipts), f.run.current_stage, g.player.health.current_hp), (3, 9, 5))
        self.assertIs(art.Stage9ArtRenderer.files, eight.FILES)
        self.assertEqual(len(art.Stage9ArtRenderer.files), 9)
        self.assertEqual(len(set(art.Stage9ArtRenderer.files.values())), 9)

    def test_two_rooks_independent_hp_anchors_and_one_shared_texture(self):
        g, _ = session(); a, b = g.encounter.enemies[1:3]
        self.assertIsNot(a, b); self.assertIsNot(a.health, b.health)
        self.assertNotEqual(a.entity_instance_id, b.entity_instance_id)
        a.health.apply_damage(1, tick=0)  # HP-label isolation fixture, not a live clear.
        self.assertEqual((a.health.current_hp, b.health.current_hp), (11, 12))
        r = self.render(g)
        self.assertEqual(len(r.images), 9)
        for e in (a, b):
            self.assertIn(e.entity_instance_id, r.order)
            self.assertEqual(r.actor_layouts[e.entity_instance_id], eight.actor_layout('rook', *e.position))
        self.assertNotEqual(r.actor_layouts[a.entity_instance_id]['foot'], r.actor_layouts[b.entity_instance_id]['foot'])
        self.assertEqual(sum(Path(c.args[0]).name == 'rook.png' for c in r.c.load_image.call_args_list), 1)

    def test_dual_rook_and_bishop_warnings_use_exact_source_scoped_cells(self):
        g, _ = session(); g.advance(147)
        bishop, a, b = g.encounter.enemies[:3]
        events = [e.current_attack for e in (bishop, a, b)]
        self.assertTrue(all(events))
        self.assertEqual(len(events[0].target_cells), 50)
        self.assertEqual([e.hit_tick for e in events], [156, 182, 195])
        self.assertEqual(len({e.key for e in events}), 3)
        self.assertEqual(set(events[1].target_cells) & set(events[2].target_cells), {(5, 1)})
        frozen = tuple(e.target_cells for e in events)
        r = self.render(g)
        expected = [cell for e in events for cell in e.target_cells]
        self.assertEqual(r.warning_cells, expected)
        self.assertEqual(set(r.warning_cells), set(expected))
        for cell in set(expected):
            x, y = CAMERA.center(*cell)
            self.assertEqual(CAMERA.pick(x, y), cell)
        g.advance(1)
        self.assertEqual(tuple(e.target_cells for e in events), frozen)

    def test_one_rook_death_or_cancel_never_erases_other_sources(self):
        for dead in (False, True):
            g, _ = session(); g.advance(147)
            a, b = g.encounter.enemies[1:3]; event = a.current_attack; other = b.current_attack
            remaining = [e for e in g.encounter.ledger.telegraphs if e is not event]
            if dead:
                a.health.apply_damage(a.health.current_hp, tick=g.combat.tick)
                g.encounter.deactivate(a.entity_instance_id, tick=g.combat.tick)
            else:
                g.encounter.ledger.cancel_source(a.entity_instance_id)
            self.assertEqual(list(g.encounter.ledger.telegraphs), remaining)
            self.assertIn(other, g.encounter.ledger.telegraphs)
            r = self.render(g)
            if dead: self.assertNotIn(a.entity_instance_id, r.order)
            self.assertIn(b.entity_instance_id, r.order)

    def test_each_rook_resolution_removes_only_its_event_and_shared_invulnerability(self):
        g, _ = session(); g.advance(147)
        a, b = [e.current_attack for e in g.encounter.enemies[1:3]]
        g.advance(9)  # Real Bishop hit; its invulnerability covers both first dashes.
        hp = g.player.health.current_hp
        g.advance(26)
        self.assertNotIn(a, g.encounter.ledger.telegraphs)
        self.assertIn(b, g.encounter.ledger.telegraphs)
        self.assertEqual(g.player.health.current_hp, hp)
        self.render(g)
        g.advance(13)
        self.assertNotIn(b, g.encounter.ledger.telegraphs)
        self.assertEqual(g.player.health.current_hp, hp)
        self.render(g)

    def test_actual_rook_normal_and_perfect_results_control_success_cues(self):
        for delta, status, cue in ((18, 'normal', 'parry_success'), (7, 'perfect', 'perfect_success')):
            g, _ = session(); g.advance(149)
            g.resolver.register_parry(g.parry.request(g.combat.tick))  # Real Bishop perfect.
            g.advance(136); event = g.encounter.enemies[1].current_attack
            self.assertEqual(event.hit_tick, 320)
            g.advance(event.hit_tick - delta - g.combat.tick)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            self.assertEqual(royal.cue_kind(g), 'parry_window')
            hp = g.player.health.current_hp; g.advance(delta)
            result = g.resolver.last_parry_result
            self.assertEqual((result.status, result.enemy_event_key), (status, event.key))
            self.assertEqual(self.render(g).cue, cue)
            self.assertEqual(g.player.health.current_hp, hp)
            self.assertNotIn(event, g.encounter.ledger.telegraphs)

    def test_invulnerable_failed_parry_is_not_shown_as_success(self):
        g, _ = session(); g.advance(175)
        g.resolver.register_parry(g.parry.request(g.combat.tick)); g.advance(7)
        self.assertEqual((g.resolver.last_parry_result.status, g.resolver.last_parry_result.reason), ('failed', 'invulnerable'))
        self.assertNotIn(self.render(g).cue, ('parry_success', 'perfect_success'))

    def test_actual_motion_depth_hp_and_rendering_are_readonly(self):
        g, _ = session(); m = RenderMotion(); peak = 0; saw_bishop = False; rook_positions = [set(), set()]
        r = art.Stage9ArtRenderer(canvas(), motion=m); self.addCleanup(r.close)
        with patch.object(royal, 'polygon'), patch.object(r, 'image'):
            for _ in range(360):
                if g.playing: g.advance()
                m.update((g.player, *g.encounter.enemies), 1/60, session=g.combat.combat_session_id)
                before = pickle.dumps((g, m)); r.draw(g, m.positions)
                self.assertEqual(pickle.dumps((g, m)), before)
                self.assertEqual(r.warning_cells, [tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else [])
                actors = [e for e in (g.player, *g.encounter.enemies) if e.alive and getattr(e, 'active', True)]
                actors.sort(key=lambda e: (-m.ground_pose(e)[0][1], m.ground_pose(e)[0][0], e.entity_instance_id))
                self.assertEqual(r.order, [e.entity_instance_id for e in actors])
                for e in actors:
                    u, v, lift = r.pose(e, m.positions); layout = r.actor_layouts[e.entity_instance_id]
                    base = eight.actor_layout(getattr(e, 'kind', 'player'), u, v)
                    self.assertEqual(layout['foot'], base['foot'])
                    self.assertAlmostEqual(layout['hp_y'], base['hp_y'] + lift)
                    peak = max(peak, lift)
                for i, e in enumerate(g.encounter.enemies[1:3]): rook_positions[i].add(e.position)
                self.assertEqual(g.encounter.enemies[0].position, (2, 8))
                saw_bishop |= any(len(e.target_cells) == 50 for e in g.encounter.ledger.telegraphs)
        self.assertAlmostEqual(peak, 18)
        self.assertTrue(saw_bishop and all(len(p) > 1 for p in rook_positions))

    def test_missing_partial_assets_and_runtime_sdl_fallback_leave_state_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for key, name in eight.FILES.items():
                if key != 'bishop':
                    (root/name).parent.mkdir(parents=True, exist_ok=True); (root/name).write_bytes(b'existence fixture')
            c = canvas()
            with self.assertRaises(FileNotFoundError): art.Stage9ArtRenderer(c, root=root)
            self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (8, 8))
        g, _ = session(); before = pickle.dumps(g)
        with patch.dict(os.environ, CHECKMATE_STAGE9_ART='1'):
            factory = Mock(side_effect=FileNotFoundError('Bishop')); path = art.Stage9ArtPath(canvas(), factory)
            with self.assertLogs('stage9_art_renderer', level='ERROR'):
                for _ in range(3): self.assertFalse(path.draw(g, {}))
            factory.assert_called_once()
            for error in (ArenaArtError('SDL'), TypeError('programmer error')):
                renderer = Mock(); renderer.draw.side_effect = error
                path = art.Stage9ArtPath(canvas(), lambda c, **kw: renderer)
                if isinstance(error, ArenaArtError):
                    with self.assertLogs('stage9_art_renderer', level='ERROR'): self.assertFalse(path.draw(g, {}))
                    renderer.close.assert_called_once()
                else:
                    with self.assertRaises(TypeError): path.draw(g, {})
                    path.close()
        self.assertEqual(pickle.dumps(g), before)

    def test_nine_textures_load_once_restart_replace_and_stage10_release(self):
        c = canvas(); path = art.Stage9ArtPath(c)
        with patch.dict(os.environ, CHECKMATE_STAGE9_ART='1'), patch.object(art.Stage9ArtRenderer, 'draw'):
            g, _ = session()
            for _ in range(10): self.assertTrue(path.draw(g, {}))
            self.assertEqual(c.load_image.call_count, 9)
            self.assertTrue(path.draw(session()[0], {}))
            self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (18, 9))
            self.assertFalse(path.draw(main._new_stage_game(10), {})); path.close(); path.close()
            self.assertEqual(c.SDL_DestroyTexture.call_count, 18)

    def test_real_stage8_nine_ten_flow_receipts_hp_and_resource_exchange(self):
        from tools.stage8_play import session as start_eight
        from tests.test_hp_carryover import fight
        g, flow = start_eight(); c = canvas(); path = art.LiveArenaArtPath(c)
        with patch.dict(os.environ, CHECKMATE_STAGE8_ART='1', CHECKMATE_STAGE9_ART='1'), patch.object(eight.Stage8ArtRenderer, 'draw'):
            self.assertTrue(path.draw(g, {})); run = flow.run; old = g
            self.assertEqual(fight(flow), (8, 'UPGRADE', 669, 4, 4))
            g, _ = flow.choose(flow.sync_offer(), 'hp', main._new_stage_game, lambda stats: None)
            self.assertIs(flow.run, run)
            self.assertEqual((len(run.receipts), g.player.health.current_hp, g.player.health.max_hp), (3, 5, 5))
            self.assertIsNot(g.encounter.ledger, old.encounter.ledger)
            self.assertNotEqual(g.combat.combat_session_id, old.combat.combat_session_id)
            self.assertTrue(path.draw(g, {})); self.assertEqual(c.SDL_DestroyTexture.call_count, 9)
            self.assertEqual(fight(flow), (9, 'UPGRADE', 681, 4, 5))
            old = g
            g, _ = flow.choose(flow.sync_offer(), 'attack', main._new_stage_game, lambda stats: None)
            self.assertEqual((g.stage_number, len(run.receipts), g.player.health.current_hp, g.player.health.max_hp), (10, 4, 4, 5))
            self.assertIs(flow.run, run); self.assertTrue(g.boss); self.assertIsNotNone(g.encounter.pulse)
            self.assertIsNot(g.encounter.ledger, old.encounter.ledger)
            self.assertFalse(path.draw(g, {})); path.close()
            self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (18, 18))

    def test_actual_game_over_restarts_chapter_six_and_removes_old_session(self):
        g, flow = session(); old = g.combat.combat_session_id; g.advance(3600)
        self.assertEqual(g.state.value, 'GAME_OVER')
        r = self.render(g); self.assertEqual(r.cue, 'quiet')
        g, _ = flow.restart(main._new_stage_game, lambda stats: None)
        self.assertEqual((g.stage_number, len(flow.run.receipts), g.player.health.current_hp), (6, 0, 3))
        self.assertNotEqual(g.combat.combat_session_id, old)
        with patch.dict(os.environ, CHECKMATE_STAGE9_ART='1'):
            factory = Mock(); self.assertFalse(art.Stage9ArtPath(canvas(), factory).draw(g, {})); factory.assert_not_called()

    def test_twenty_seven_prior_golden_pngs_regenerated_unchanged(self):
        pairs = [('capture_stage5_scale.py', 'artifacts/stage6_c1/stage5_regression.json'),
                 ('capture_stage6_live.py', 'artifacts/stage6_c1/capture_manifest.json'),
                 ('capture_stage7_live.py', 'artifacts/stage7_c3/capture_manifest.json'),
                 ('capture_stage8_live.py', 'artifacts/stage8_c4/capture_manifest.json')]
        total = 0
        for tool, manifest in pairs:
            with tempfile.TemporaryDirectory() as d:
                p = subprocess.run([sys.executable, 'tools/'+tool, '--capture-dir', d], cwd=royal.ROOT,
                                   env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}, capture_output=True, text=True, timeout=90)
                self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
                for row in json.loads((royal.ROOT/manifest).read_text())['captures']:
                    self.assertEqual(hashlib.sha256((Path(d)/row['file']).read_bytes()).hexdigest(), row['sha256'])
                    total += 1
        self.assertEqual(total, 27)

    def test_native_main_uses_stage9_path_and_captures_actual_dual_rook_states(self):
        script = r'''
import tempfile
from pathlib import Path
from unittest.mock import patch
import sdl2 as s
from pico2d import pico2d as c
import main
from tools.stage9_play import session
from tools.stage5_art_preview import open_preview
from tools.capture_stage9_live import capture
from stage9_art_renderer import Stage9ArtRenderer
g,f=session(); frames=[0]; draws=[0]; native=Stage9ArtRenderer.draw
def draw(self,game,positions):
    draws[0]+=1
    assert game is g
    return native(self,game,positions)
def events():
    frames[0]+=1
    return [] if frames[0]<5 else [type('Quit',(),{'type':s.SDL_QUIT})()]
with patch.object(c,'open_canvas',lambda w,h:open_preview(c,capture=True)),patch.object(c,'get_events',events),patch.object(main,'sleep'),patch.object(Stage9ArtRenderer,'draw',draw):
    main.run_session(g,f)
assert frames[0]==5 and draws[0]>0
with tempfile.TemporaryDirectory() as d:
    capture(Path(d)); assert len(list(Path(d).glob('*.png')))==7
print('STAGE9 NATIVE MAIN AND DUAL ROOKS OK')
'''
        p = subprocess.run([sys.executable, '-c', script], cwd=royal.ROOT,
                           env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy', 'CHECKMATE_STAGE9_ART': '1'},
                           capture_output=True, text=True, timeout=90)
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        self.assertIn('STAGE9 NATIVE MAIN AND DUAL ROOKS OK', p.stdout)
