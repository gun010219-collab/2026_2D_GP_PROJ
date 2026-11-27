"""Live Stage10 forest boss: presentation reads the original Pulse/Resolver only."""
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
from input_controller import InputController
from render_motion import RenderMotion
import stage5_art_renderer as royal
import stage6_art_renderer as six
import stage7_art_renderer as seven
import stage8_art_renderer as eight
import stage9_art_renderer as nine
import stage10_art_renderer as art
from tests.test_stage6_live_art import canvas
from tools.stage10_play import session


def first_pulse(g):
    for _ in range(700):
        if g.encounter.pulse.event is not None: return g.encounter.pulse.event
        if not g.playing: break
        g.advance()
    raise AssertionError('Original Stage10 did not issue a Pulse')


class Stage10LiveArtTests(unittest.TestCase):
    def render(self, g, *, motion=None):
        r = art.Stage10ArtRenderer(canvas(), motion=motion); self.addCleanup(r.close)
        before = pickle.dumps((g, motion))
        with patch.object(royal, 'polygon'), patch.object(r, 'image'):
            r.draw(g, motion.positions if motion else {})
        self.assertEqual(pickle.dumps((g, motion)), before)
        self.assertEqual(r.warning_cells, [tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else [])
        return r

    def test_stage10_flag_is_independent_and_stage11_plus_others_keep_legacy(self):
        flags = {f'CHECKMATE_STAGE{n}_ART': '0' for n in range(5, 11)}
        for enabled in ((), (5,), (6,), (7,), (8,), (9,), (10,), (5, 6, 7, 8, 9, 10)):
            with patch.dict(os.environ, {**flags, **{f'CHECKMATE_STAGE{n}_ART': '1' for n in enabled}}):
                c = canvas(); path = art.LiveArenaArtPath(c)
                with patch.object(royal.Stage5ArtRenderer, 'draw'), patch.object(six.Stage6ArtRenderer, 'draw'), patch.object(seven.Stage7ArtRenderer, 'draw'), patch.object(eight.Stage8ArtRenderer, 'draw'), patch.object(nine.Stage9ArtRenderer, 'draw'), patch.object(art.Stage10ArtRenderer, 'draw'):
                    for n in range(1, 26): self.assertEqual(path.draw(main._new_stage_game(n), {}), n in enabled)
                path.close(); expected = sum({5: 8, 6: 7, 7: 7, 8: 9, 9: 9, 10: 9}[n] for n in enabled)
                self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (expected, expected))

    def test_original_roster_static_boss10_runtime_king50_total82_and_receipt4(self):
        g, f = session()
        self.assertEqual((g.stage_number, g.chapter, g.boss, g.player.position), (10, 2, True, (5, 1)))
        self.assertEqual([(e.kind, e.position, e.health.max_hp, e.initial_delay_ticks) for e in g.encounter.enemies],
                         [('king', (5, 9), 50, 48), ('bishop', (2, 8), 9, 62), ('knight', (3, 6), 9, 75),
                          ('pawn', (1, 6), 7, 88), ('pawn', (8, 6), 7, 101)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies), 82)
        self.assertEqual(json.loads((royal.ROOT/'stage_data.json').read_text())['stages'][9]['boss_hp'], 10)
        self.assertIs(g.encounter.pulse.king, g.encounter.enemies[0])
        self.assertEqual((f.run.current_stage, len(f.run.receipts), g.player.health.current_hp), (10, 4, 5))
        self.assertEqual((f.run.stats.attack_damage, f.run.stats.move_interval_ticks), (4, 18))
        self.assertEqual((len(art.FILES), set(art.BASE_SIZE)), (9, {'player', 'pawn', 'knight', 'bishop', 'king'}))

    def test_original_crown_clipped_new_source_complete_alpha_and_hash_provenance(self):
        import sdl2 as s
        from sdl2.sdlimage import IMG_Load
        from tools.prepare_stage5_art import alpha_bounds
        folder = royal.ROOT/'assets/chapter2_units'
        for name in ('asset_manifest.json', 'knight_manifest.json', 'bishop_manifest.json', 'king_manifest.json'):
            for row in json.loads((folder/name).read_text())['assets']:
                for key, sha in (('file', 'sha256'), ('source', 'source_sha256')):
                    self.assertEqual(hashlib.sha256((folder/row[key]).read_bytes()).hexdigest(), row[sha])
        row = json.loads((folder/'king_manifest.json').read_text())['assets'][0]
        for p, old in ((royal.ROOT/'assets/character_concepts/source/ch2_king.png', True), (folder/row['source'], False), (folder/row['file'], False)):
            a = IMG_Load(str(p).encode('utf-8')); self.assertTrue(a)
            b = s.SDL_ConvertSurfaceFormat(a, s.SDL_PIXELFORMAT_RGBA32, 0)
            try:
                box, clear = alpha_bounds(b); self.assertGreater(clear, 0)
                if old: self.assertEqual(box[1], 0)
                else:
                    self.assertGreater(box[0], 0); self.assertGreater(box[1], 0)
                    self.assertLess(box[2], b.contents.w); self.assertLess(box[3], b.contents.h)
                if p == folder/row['file']:
                    self.assertEqual((b.contents.w, b.contents.h), (256, 256))
                    self.assertEqual(list(box), row['alpha_bbox']); self.assertEqual((box[1], box[3]), art.ALPHA_ROWS['king'])
            finally: s.SDL_FreeSurface(b); s.SDL_FreeSurface(a)
        prompt = json.loads((folder/'king_prompt.json').read_text())
        self.assertEqual(prompt['generator'], 'OpenAI built-in image_gen'); self.assertTrue(prompt['transparent_background'])

    def test_king_scale_foot_and_hp_clearance_preserve_other_actors(self):
        r = art.Stage10ArtRenderer(canvas()); self.addCleanup(r.close)
        for row in range(10):
            for col in range(10):
                layout = art.actor_layout('king', col, row)
                self.assertEqual(layout['foot'], CAMERA.project(col+.5, row+.25))
                self.assertGreaterEqual(layout['hp_y']-3-layout['top'], 9)
                self.assertLess(layout['hp_y']+13, 900)
                self.assertGreater(layout['height'], art.actor_layout('pawn', col, row)['height'])
        self.assertEqual(art.BASE_SIZE['king'], 104)
        for kind in ('player', 'pawn', 'knight', 'bishop'):
            self.assertEqual(art.actor_layout(kind, 3, 6), eight.actor_layout(kind, 3, 6))
        g, _ = session(); r = self.render(g)
        self.assertEqual(r.actor_layouts[g.encounter.pulse.king.entity_instance_id], art.actor_layout('king', 5, 9))

    def test_real_king_melee_warning_after_legal_player_approach(self):
        g, f = session(); movement = InputController(move_interval_ticks=f.run.stats.move_interval_ticks)
        for _ in range(220):
            movement.key_down('up', g.player, occupied=g.encounter.occupied_cells, tick=g.combat.tick)
            movement.key_up('up'); g.advance()
            event = g.encounter.pulse.king.current_attack
            if event: break
        self.assertEqual((g.combat.tick, event.attack_kind, event.hit_tick), (120, 'basic', 168))
        self.assertEqual(event.target_cells, ((5, 7),))
        self.assertEqual(g.encounter.pulse.king.position, (5, 8))
        self.render(g)

    def test_natural_pulse_states_all100_cells_and_original_times(self):
        g, _ = session(); p = g.encounter.pulse; seen = {p.state}; native = g.resolver.resolve_enemy_attack
        def resolve(resolver, event):
            if event.attack_kind == 'king_pulse': seen.add(p.state)
            return native(event)
        with patch.object(type(g.resolver), 'resolve_enemy_attack', resolve):
            self.assertEqual(p.next_use_tick, 240)
            g.advance(240); self.assertIsNone(p.event)
            g.advance(24); seen.add(p.state); self.assertEqual(p.state, 'DRAINING')
            self.assertIsNone(p.event); g.advance(); seen.add(p.state)
            event = p.event
            self.assertEqual((event.start_tick, event.hit_tick), (265, 385))
            self.assertEqual(set(event.target_cells), {(c, r) for c in range(10) for r in range(10)})
            self.assertEqual(self.render(g).warning_cells, list(event.target_cells))
            self.assertEqual(self.render(g).cue, 'pulse')
            g.advance(120); seen.add(p.state)
            self.assertEqual((p.state, p.resume_tick, p.next_use_tick), ('CLEANUP', 415, 865))
            self.assertNotIn(event, g.encounter.ledger.telegraphs); self.assertNotEqual(self.render(g).cue, 'pulse')
            g.advance(30); seen.add(p.state)
        self.assertEqual(seen, {'NORMAL', 'DRAINING', 'PULSE_TELEGRAPH', 'PULSE_RESOLUTION', 'CLEANUP'})

    def test_draining_preserves_existing_mixed_warnings_until_real_resolution(self):
        g, _ = session(); g.advance(90); p = g.encounter.pulse
        events = (g.encounter.enemies[1].current_attack, g.encounter.enemies[2].current_attack)
        self.assertEqual([e.hit_tick for e in events], [170, 111])
        # Coordinator timing fixture only, not a claimed unmodified campaign trace.
        p.next_use_tick = 91; p.king.next_action_tick = 91
        g.advance(); self.assertEqual(p.state, 'DRAINING'); self.assertIsNone(p.event)
        self.render(g); g.advance(79)
        self.assertTrue(all(g.encounter.ledger.state(e) == 'resolved' for e in events))
        self.assertIsNone(p.event); self.render(g); g.advance()
        self.assertEqual((p.event.start_tick, len(p.event.target_cells)), (171, 100)); self.render(g)

    def test_pulse_freeze_preserves_actions_stuns_positions_and_resumes(self):
        g, _ = session(); event = first_pulse(g); p = g.encounter.pulse
        saved = p._remaining.copy()
        snapshot = [(e.position, e.state, e.next_action_tick, e.stun_until_tick) for e in g.encounter.enemies[1:]]
        g.advance(100)
        self.assertEqual(snapshot, [(e.position, e.state, e.next_action_tick, e.stun_until_tick) for e in g.encounter.enemies[1:]])
        self.render(g); g.advance(event.hit_tick-7-g.combat.tick)
        g.resolver.register_parry(g.parry.request(g.combat.tick)); g.advance(36)
        self.assertEqual(p.state, 'CLEANUP'); g.advance(); self.assertEqual(p.state, 'NORMAL')
        self.assertIsNone(p.freeze_tick)
        for e in g.encounter.enemies[1:]:
            if saved[e.entity_instance_id][1] > 0:
                self.assertEqual(e.next_action_tick, event.hit_tick+30+saved[e.entity_instance_id][1])
        self.render(g)

    def test_actual_pulse_normal_perfect_and_reflected_two_are_single_use(self):
        for delta, status, damage, cue in ((18, 'normal', 0, 'parry_success'), (7, 'perfect', 2, 'perfect_success')):
            g, _ = session(); event = first_pulse(g); p = g.encounter.pulse
            g.advance(event.hit_tick-delta-g.combat.tick); g.resolver.register_parry(g.parry.request(g.combat.tick))
            self.assertEqual(self.render(g).cue, 'pulse')  # Active real Pulse has display priority over input window.
            hp = p.king.health.current_hp; player_hp = g.player.health.current_hp; g.advance(delta)
            result = g.resolver.last_parry_result
            self.assertEqual((result.status, result.enemy_event_key), (status, event.key))
            self.assertEqual(p.king.health.current_hp, hp-damage); self.assertEqual(g.player.health.current_hp, player_hp)
            self.assertEqual(self.render(g).cue, cue)
            self.assertIsNone(g.resolver.resolve_enemy_attack(event))
            self.assertEqual(p.king.health.current_hp, hp-damage)

    def test_king_death_cancels_pulse_but_remaining_enemies_resume(self):
        g, _ = session(); event = first_pulse(g); p = g.encounter.pulse
        p.king.health.apply_damage(50, tick=g.combat.tick)  # Death-branch fixture, not a live win.
        g.encounter.deactivate(p.king.entity_instance_id, tick=g.combat.tick); g.update_state()
        self.assertTrue(g.playing); self.assertEqual(g.encounter.ledger.state(event), 'cancelled')
        r = self.render(g); self.assertNotIn(p.king.entity_instance_id, r.order); self.assertNotEqual(r.cue, 'pulse')
        g.advance(); self.assertIsNone(p.freeze_tick); self.assertEqual(p.state, 'NORMAL')
        g.advance(300)
        self.assertFalse(any(e.source_entity_instance_id == p.king.entity_instance_id for e in g.encounter.ledger.pending))
        self.assertTrue(any(e.alive for e in g.encounter.enemies[1:])); self.render(g)

    def test_perfect_reflection_king_death_releases_frozen_survivors(self):
        g, _ = session(); event = first_pulse(g); p = g.encounter.pulse
        g.advance(event.hit_tick-7-g.combat.tick)
        p.king.health.apply_damage(48, tick=g.combat.tick)  # 2HP reflection-death branch fixture.
        g.resolver.register_parry(g.parry.request(g.combat.tick)); g.advance(7)
        self.assertFalse(p.king.alive); self.assertEqual(g.resolver.last_parry_result.status, 'perfect')
        self.assertTrue(g.playing); self.render(g); g.advance(); self.assertIsNone(p.freeze_tick)
        self.assertNotIn(p.king.entity_instance_id, self.render(g).order)

    def test_actual_mixed_motion_pulse_and_hp_are_readonly(self):
        g, _ = session(); m = RenderMotion(); r = art.Stage10ArtRenderer(canvas(), motion=m); self.addCleanup(r.close)
        peak = 0; saw_bishop = saw_pulse = False
        with patch.object(royal, 'polygon'), patch.object(r, 'image'):
            for _ in range(450):
                p = g.encounter.pulse
                if p.event and g.combat.tick == p.event.hit_tick-7:
                    g.resolver.register_parry(g.parry.request(g.combat.tick))
                g.advance(); frozen = [e.entity_instance_id for e in g.encounter.enemies if p.frozen(e)]
                m.update((g.player, *g.encounter.enemies), 1/60, session=g.combat.combat_session_id, frozen=frozen)
                before = pickle.dumps((g, m)); r.draw(g, m.positions); self.assertEqual(pickle.dumps((g, m)), before)
                self.assertEqual(r.warning_cells, [tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells])
                actors = [e for e in (g.player, *g.encounter.enemies) if e.alive and getattr(e, 'active', True)]
                actors.sort(key=lambda e: (-m.ground_pose(e)[0][1], m.ground_pose(e)[0][0], e.entity_instance_id))
                self.assertEqual(r.order, [e.entity_instance_id for e in actors])
                for e in actors:
                    u, v, lift = r.pose(e, m.positions); base = art.actor_layout(getattr(e, 'kind', 'player'), u, v)
                    self.assertEqual(r.actor_layouts[e.entity_instance_id]['foot'], base['foot'])
                    self.assertAlmostEqual(r.actor_layouts[e.entity_instance_id]['hp_y'], base['hp_y']+lift)
                    peak = max(peak, lift)
                saw_bishop |= any(len(e.target_cells) == 50 for e in g.encounter.ledger.telegraphs)
                saw_pulse |= any(e.attack_kind == 'king_pulse' for e in g.encounter.ledger.telegraphs)
        self.assertAlmostEqual(peak, 18); self.assertTrue(saw_bishop and saw_pulse)

    def test_annihilation_and_simultaneous_player_death_priority(self):
        for dead, expected in ((False, 'BOSS_CLEAR'), (True, 'GAME_OVER')):
            g, flow = session(); first_pulse(g)
            # Terminal-state fixtures; the genuine full fight is tested separately.
            for e in g.encounter.enemies:
                e.health.apply_damage(e.health.current_hp, tick=g.combat.tick)
                g.encounter.deactivate(e.entity_instance_id, tick=g.combat.tick)
            if dead: g.player.health.apply_damage(5, tick=g.combat.tick)
            g.update_state(); self.assertEqual(g.state.value, expected)
            self.assertTrue(g.resolver.stopped and g.encounter.pulse.stopped)
            self.assertEqual(g.transition_count, 1); self.assertFalse(g.encounter.ledger.pending)
            self.assertIsNone(flow.sync_offer()); self.assertEqual(len(flow.run.receipts), 4)
            for _ in range(3): self.assertEqual(self.render(g).warning_cells, [])
            end = g.end_tick; g.advance(500); self.assertEqual((g.combat.tick, g.transition_count), (end, 1))

    def test_actual_full_fight_boss_replay_and_chapter_three_transition(self):
        from tests.test_hp_carryover import fight
        g, flow = session(); run = flow.run; c = canvas(); path = art.LiveArenaArtPath(c)
        with patch.dict(os.environ, CHECKMATE_STAGE10_ART='1'), patch.object(art.Stage10ArtRenderer, 'draw'):
            self.assertTrue(path.draw(g, {}))
            self.assertEqual(fight(flow), (10, 'BOSS_CLEAR', 749, 4, 5)); self.assertIsNone(flow.sync_offer())
            self.assertTrue(all(not e.alive for e in g.encounter.enemies)); self.assertTrue(g.encounter.pulse.stopped)
            old = g; replay, _ = flow.restart(main._new_stage_game, lambda stats: None)
            self.assertIs(flow.run, run); self.assertEqual((replay.stage_number, replay.player.health.current_hp, len(run.receipts)), (10, 5, 4))
            self.assertIsNot(replay.encounter.pulse, old.encounter.pulse); self.assertTrue(path.draw(replay, {}))
            self.assertEqual(fight(flow), (10, 'BOSS_CLEAR', 749, 4, 5))
            g, _ = flow.enter_next_chapter(main._new_stage_game, lambda stats: None)
            self.assertEqual((g.stage_number, flow.run.chapter, len(flow.run.receipts), g.player.health.current_hp), (11, 3, 0, 5))
            self.assertEqual(flow.run.stats.move_interval_ticks, 18); self.assertTrue(run.retired)
            self.assertFalse(path.draw(g, {})); path.close()
            self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (18, 18))

    def test_actual_game_over_restart_chapter_six_replaces_session(self):
        g, flow = session(); old = g; g.advance(3600)
        self.assertEqual(g.state.value, 'GAME_OVER'); self.assertEqual(self.render(g).cue, 'quiet')
        g, _ = flow.restart(main._new_stage_game, lambda stats: None)
        self.assertEqual((g.stage_number, len(flow.run.receipts), g.player.health.current_hp, flow.run.stats.move_interval_ticks), (6, 0, 3, 18))
        self.assertIsNone(g.encounter.pulse); self.assertNotEqual(g.combat.combat_session_id, old.combat.combat_session_id)
        with patch.dict(os.environ, CHECKMATE_STAGE10_ART='1'):
            factory = Mock(); self.assertFalse(art.Stage10ArtPath(canvas(), factory).draw(g, {})); factory.assert_not_called()

    def test_nine_textures_once_per_session_released_on_stage11_exit(self):
        c = canvas(); path = art.Stage10ArtPath(c)
        with patch.dict(os.environ, CHECKMATE_STAGE10_ART='1'), patch.object(art.Stage10ArtRenderer, 'draw'):
            g, _ = session()
            for _ in range(10): self.assertTrue(path.draw(g, {}))
            self.assertEqual(c.load_image.call_count, 9); self.assertTrue(path.draw(session()[0], {}))
            self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (18, 9))
            self.assertFalse(path.draw(main._new_stage_game(11), {})); path.close(); path.close()
            self.assertEqual(c.SDL_DestroyTexture.call_count, 18)

    def test_missing_king_partial_load_and_sdl_fallback_do_not_mutate_combat(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for key, name in art.FILES.items():
                if key != 'king':
                    (root/name).parent.mkdir(parents=True, exist_ok=True); (root/name).write_bytes(b'existence fixture')
            c = canvas()
            with self.assertRaises(FileNotFoundError): art.Stage10ArtRenderer(c, root=root)
            self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (8, 8))
        g, _ = session(); first_pulse(g); before = pickle.dumps(g)
        with patch.dict(os.environ, CHECKMATE_STAGE10_ART='1'):
            factory = Mock(side_effect=FileNotFoundError('King')); path = art.Stage10ArtPath(canvas(), factory)
            with self.assertLogs('stage10_art_renderer', level='ERROR'):
                for _ in range(3): self.assertFalse(path.draw(g, {}))
            factory.assert_called_once()
            for error in (ArenaArtError('SDL'), TypeError('bug')):
                renderer = Mock(); renderer.draw.side_effect = error; path = art.Stage10ArtPath(canvas(), lambda c, **k: renderer)
                if isinstance(error, ArenaArtError):
                    with self.assertLogs('stage10_art_renderer', level='ERROR'): self.assertFalse(path.draw(g, {}))
                    renderer.close.assert_called_once()
                else:
                    with self.assertRaises(TypeError): path.draw(g, {})
                    path.close()
        self.assertEqual(pickle.dumps(g), before)

    def test_thirty_four_prior_golden_pngs_regenerated_identically(self):
        pairs = [('capture_stage5_scale.py', 'artifacts/stage6_c1/stage5_regression.json'),
                 ('capture_stage6_live.py', 'artifacts/stage6_c1/capture_manifest.json'),
                 ('capture_stage7_live.py', 'artifacts/stage7_c3/capture_manifest.json'),
                 ('capture_stage8_live.py', 'artifacts/stage8_c4/capture_manifest.json'),
                 ('capture_stage9_live.py', 'artifacts/stage9_c5/capture_manifest.json')]
        total = 0
        for tool, manifest in pairs:
            with tempfile.TemporaryDirectory() as d:
                p = subprocess.run([sys.executable, 'tools/'+tool, '--capture-dir', d], cwd=royal.ROOT,
                                   env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}, capture_output=True, text=True, timeout=90)
                self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
                for row in json.loads((royal.ROOT/manifest).read_text())['captures']:
                    self.assertEqual(hashlib.sha256((Path(d)/row['file']).read_bytes()).hexdigest(), row['sha256']); total += 1
        self.assertEqual(total, 34)

    def test_native_main_and_actual_boss_clear_n_to_stage11(self):
        script = r'''
from unittest.mock import patch
import sdl2 as s
from pico2d import pico2d as c
import main
from tools.stage10_play import session
from tools.stage5_art_preview import open_preview
from tests.test_hp_carryover import fight
from tests.test_stage_transition import key,N
from stage10_art_renderer import Stage10ArtRenderer
import tempfile
from pathlib import Path
from tools.capture_stage10_live import capture
for terminal in (False,True):
    g,f=session()
    if terminal: assert fight(f)==(10,'BOSS_CLEAR',749,4,5)
    frames=[0];draws=[0];native=Stage10ArtRenderer.draw
    def draw(self,game,positions):
        draws[0]+=1
        return native(self,game,positions)
    def events():
        frames[0]+=1
        if terminal and frames[0]==2:return [key(N)]
        return [] if frames[0]<5 else [type('Quit',(),{'type':s.SDL_QUIT})()]
    # Hidden windows have no real focus; supply focus for this synthetic N-input harness only.
    with patch.object(c,'open_canvas',lambda w,h:open_preview(c,capture=True)),patch.object(c,'get_events',events),patch.object(c,'SDL_GetWindowFlags',return_value=s.SDL_WINDOW_INPUT_FOCUS),patch.object(main,'sleep'),patch.object(Stage10ArtRenderer,'draw',draw):
        main.run_session(g,f)
    assert frames[0]==5 and draws[0]>0
    assert f.game.stage_number==(11 if terminal else 10)
with tempfile.TemporaryDirectory() as d:
    capture(Path(d)); assert len(list(Path(d).glob('*.png')))==9
print('STAGE10 NATIVE MAIN AND N TO STAGE11 OK')
'''
        p = subprocess.run([sys.executable, '-c', script], cwd=royal.ROOT,
                           env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy', 'CHECKMATE_STAGE10_ART': '1'},
                           capture_output=True, text=True, timeout=90)
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr); self.assertIn('STAGE10 NATIVE MAIN AND N TO STAGE11 OK', p.stdout)
