"""Frozen Stage11 reads real combat; fixture mutations are explicitly isolated."""
import hashlib
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import main
from arena_art_common import CAMERA, ArenaArtError
from config import cell_center
from game import StageGame
from render_motion import RenderMotion
import stage5_art_renderer as common
import stage11_art_renderer as art
from tests.test_stage6_live_art import canvas
from tests.test_hp_carryover import fight
from tools.stage11_play import session


def sync(g, m, elapsed=1/60):
    frozen = (g.player.entity_instance_id,) if g.combat.active_attack or g.parry.active_at(g.combat.tick) else ()
    m.update((g.player, *g.encounter.enemies), elapsed,
             session=g.combat.combat_session_id, frozen=frozen)


def advance(g, m, until):
    for _ in range(until-g.combat.tick):
        g.advance(); sync(g, m)


class Stage11LiveArtTests(unittest.TestCase):
    def renderer(self, motion=None):
        c = canvas()
        c.draw_line = lambda *a: None
        c.draw_rectangle = lambda *a, **k: None
        r = art.Stage11ArtRenderer(c, motion=motion)
        self.addCleanup(r.close)
        return r

    def render(self, g, m=None, r=None):
        r = r or self.renderer(m)
        before = pickle.dumps((g, m))
        with patch.object(common, 'polygon'), patch.object(r, 'image'):
            r.draw(g, m.positions if m else {})
        self.assertEqual(pickle.dumps((g, m)), before)
        self.assertEqual(r.warning_cells, [tuple(c) for e in g.encounter.ledger.telegraphs
                                          for c in e.target_cells] if g.playing else [])
        return r

    def test_seven_flags_independent_and_other_eighteen_stages_legacy(self):
        flags = {f'CHECKMATE_STAGE{n}_ART': '0' for n in range(5, 12)}
        for enabled in ((), *((n,) for n in range(5, 12)), tuple(range(5, 12))):
            with patch.dict(os.environ, {**flags, **{f'CHECKMATE_STAGE{n}_ART': '1' for n in enabled}}):
                c = canvas(); path = art.LiveArenaArtPath(c)
                with patch.object(common.Stage5ArtRenderer, 'draw'):
                    for n in range(1, 26):
                        self.assertEqual(path.draw(main._new_stage_game(n), {}), n in enabled, (n, enabled))
                path.close()
                expected = sum({5:8, 6:7, 7:7, 8:9, 9:9, 10:9, 11:8}[n] for n in enabled)
                self.assertEqual((c.load_image.call_count, c.SDL_DestroyTexture.call_count), (expected, expected))
        for value in ('', '0', 'true', 'yes', '01', ' 1'):
            with patch.dict(os.environ, CHECKMATE_STAGE11_ART=value):
                factory = Mock(); path = art.Stage11ArtPath(canvas(), factory)
                self.assertFalse(path.draw(session()[0], {})); factory.assert_not_called()

    def test_original_roster_hp67_fresh_run_and_only_eight_approved_assets(self):
        g, flow = session()
        self.assertEqual((g.stage_number, g.chapter, g.boss, g.player.position), (11, 3, False, (5, 1)))
        self.assertEqual([(e.kind, e.position, e.health.current_hp) for e in g.encounter.enemies],
                         [('rook', (2,4), 16), ('rook', (7,4), 16),
                          ('knight', (3,6), 13), ('knight', (6,6), 13), ('pawn', (1,6), 9)])
        self.assertEqual(sum(e.health.current_hp for e in g.encounter.enemies), 67)
        self.assertEqual((flow.run.entry_attack_level, g.resolver.player_damage, flow.run.receipts), (3, 4, ()))
        self.assertIsNone(g.encounter.pulse)
        self.assertEqual(set(art.FILES), {'background','frame','light','dark','player','pawn','rook','knight'})
        self.assertEqual(len(set(art.FILES.values())), 8)
        manifest = json.loads((common.ROOT/'assets/chapter3_units/asset_manifest.json').read_text(encoding='utf-8'))
        for row in manifest['assets']:
            for file_key, hash_key in (('file','sha256'), ('source','source_sha256')):
                p = common.ROOT/'assets/chapter3_units'/row[file_key]
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), row[hash_key])

    def test_all_hundred_cells_visible_alpha_sizes_foot_hp_and_inverse(self):
        widths = {'pawn':103, 'rook':183, 'knight':186}
        for u in range(10):
            for v in range(10):
                self.assertEqual(CAMERA.pick(*CAMERA.center(u,v)), (u,v))
                for kind, target in art.TARGET_ALPHA_HEIGHT.items():
                    layout = art.actor_layout(kind,u,v); h = layout['height']
                    self.assertEqual(layout['foot'], CAMERA.project(u+.5,v+.25))
                    self.assertAlmostEqual(layout['top']-layout['foot'][1], h*220/256)
                    self.assertAlmostEqual(layout['hp_y']-layout['top'], art.HP_OFFSET[kind])
                    self.assertAlmostEqual(layout['center'][1]-h/2+h*18/256, layout['foot'][1])
                    self.assertAlmostEqual(h*220/256, target*(1.10-.023*v)/1.10)
                    if v == 0:
                        self.assertAlmostEqual(h*widths[kind]/256, target*widths[kind]/220)
                self.assertEqual(art.actor_layout('player',u,v), __import__('stage6_art_renderer').actor_layout('player',u,v))
        for v in (0,5,9.99):
            self.assertIsNone(CAMERA.pick(*CAMERA.project(10,v)))
            self.assertIsNone(CAMERA.pick(*CAMERA.project(v,10)))

    def test_two_rooks_and_two_knights_share_textures_keep_independent_hp(self):
        g, _ = session(); a,b = g.encounter.enemies[:2]
        a.health.apply_damage(1, tick=0)  # HP isolation fixture only.
        self.assertEqual((a.health.current_hp,b.health.current_hp), (15,16))
        self.assertIsNot(a.health,b.health)
        r = self.render(g)
        for kind in ('rook','knight'):
            self.assertEqual(sum(Path(call.args[0]).name == kind+'.png' for call in r.c.load_image.call_args_list), 1)
        for e in g.encounter.enemies:
            self.assertEqual(r.actor_layouts[e.entity_instance_id], art.actor_layout(e.kind,*e.position))
        self.assertNotEqual(r.actor_layouts[a.entity_instance_id]['foot'], r.actor_layouts[b.entity_instance_id]['foot'])

    def test_real_knight_peak_shadow_ground_depth_and_landing(self):
        g, _ = session(); m = RenderMotion(); sync(g,m,0); advance(g,m,114)
        knight = g.encounter.enemies[2]
        self.assertEqual(knight.position,(5,5))
        ground,lift = m.ground_pose(knight)
        self.assertAlmostEqual(lift,18)
        self.assertNotEqual(ground,cell_center(*knight.position))
        r = self.render(g,m); u,v,_ = r.pose(knight,m.positions)
        base = art.actor_layout('knight',u,v); layout = r.actor_layouts[knight.entity_instance_id]
        self.assertEqual(layout['foot'],base['foot'])
        self.assertAlmostEqual(layout['center'][1],base['center'][1]+18)
        self.assertAlmostEqual(layout['hp_y'],base['hp_y']+18)
        advance(g,m,119)
        self.assertEqual(m.ground_pose(knight),(cell_center(5,5),0))
        self.render(g,m)

    def test_actual_mixed_motion_depth_and_readonly_360_ticks(self):
        g,_ = session(); m = RenderMotion(); sync(g,m,0); r = self.renderer(m)
        peak = [0,0]; rook_positions = [set(),set()]
        for tick in range(1,361):
            advance(g,m,tick); self.render(g,m,r)
            actors = [e for e in (g.player,*g.encounter.enemies) if e.alive and getattr(e,'active',True)]
            actors.sort(key=lambda e:(-m.ground_pose(e)[0][1],m.ground_pose(e)[0][0],e.entity_instance_id))
            self.assertEqual(r.order,[e.entity_instance_id for e in actors])
            for i,e in enumerate(g.encounter.enemies[2:4]): peak[i] = max(peak[i],m.ground_pose(e)[1])
            for i,e in enumerate(g.encounter.enemies[:2]): rook_positions[i].add(e.position)
        self.assertEqual([round(p,6) for p in peak],[18,18])
        self.assertTrue(all(len(p)>1 for p in rook_positions))

    def test_knight_blocked_landing_and_perfect_stun_use_actual_rules(self):
        # Occupancy fixtures exercise existing encounter rules, not campaign results.
        for blocker in ('player','pawn','perfect'):
            g,_ = session(); g.advance(75); knight = g.encounter.enemies[2]
            event = knight.current_attack; self.assertEqual(event.target_cells,((5,5),))
            if blocker == 'pawn': g.encounter.enemies[-1].col, g.encounter.enemies[-1].row = 5,5
            else:
                for _ in range(4): self.assertTrue(g.player.move('up'))
            if blocker == 'perfect':
                g.advance(event.hit_tick-7-g.combat.tick)
                g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.advance(event.hit_tick-g.combat.tick)
            self.assertEqual(knight.position,(3,6))
            m = RenderMotion(); sync(g,m,0)
            self.assertEqual(m.ground_pose(knight)[1],0)
            self.assertNotIn(event,g.encounter.ledger.telegraphs)
            if blocker == 'perfect':
                self.assertEqual(g.resolver.last_parry_result.status,'perfect')
                self.assertEqual(knight.state,'stunned')
            self.render(g,m)

    def test_airborne_death_cancels_source_and_removes_body_hp_shadow(self):
        g,_ = session(); m = RenderMotion(); sync(g,m,0); advance(g,m,114)
        knight = g.encounter.enemies[2]
        self.assertAlmostEqual(m.ground_pose(knight)[1],18)
        knight.health.apply_damage(knight.health.current_hp,tick=g.combat.tick)  # Death fixture.
        g.encounter.deactivate(knight.entity_instance_id,tick=g.combat.tick); sync(g,m)
        r = self.render(g,m)
        self.assertNotIn(knight.entity_instance_id,r.order)
        self.assertNotIn(knight.entity_instance_id,r.actor_layouts)
        self.assertNotIn(knight.entity_instance_id,m.positions)
        self.assertFalse(any(e.source_entity_instance_id == knight.entity_instance_id for e in g.encounter.ledger.telegraphs))

    def test_dual_rook_exact_cells_overlap_and_source_scoped_resolution(self):
        g,_ = session(); g.advance(134)
        a,b = [e.current_attack for e in g.encounter.enemies[:2]]
        self.assertEqual((a.hit_tick,b.hit_tick),(168,182))
        self.assertNotEqual(a.key,b.key)
        self.assertEqual(set(a.target_cells)&set(b.target_cells),{(5,1)})
        self.assertEqual(self.render(g).warning_cells,list(a.target_cells+b.target_cells))
        g.advance(34); self.assertNotIn(a,g.encounter.ledger.telegraphs); self.assertIn(b,g.encounter.ledger.telegraphs)
        hp = g.player.health.current_hp; self.render(g)
        g.advance(14); self.assertNotIn(b,g.encounter.ledger.telegraphs)
        self.assertEqual(g.player.health.current_hp,hp)  # Existing shared invulnerability.
        self.render(g)

    def test_rook_cancel_or_death_preserves_other_rook_warning(self):
        for dead in (False,True):
            g,_ = session(); g.advance(134); rook = g.encounter.enemies[0]
            event = rook.current_attack; other = g.encounter.enemies[1].current_attack
            if dead:
                rook.health.apply_damage(16,tick=g.combat.tick)
                g.encounter.deactivate(rook.entity_instance_id,tick=g.combat.tick)
            else: g.encounter.ledger.cancel_source(rook.entity_instance_id)
            self.assertNotIn(event,g.encounter.ledger.telegraphs)
            self.assertIn(other,g.encounter.ledger.telegraphs)
            r = self.render(g)
            if dead: self.assertNotIn(rook.entity_instance_id,r.order)

    def test_genuine_normal_perfect_input_and_cooldown_cues(self):
        for delta,status,cue in ((18,'normal','parry_success'),(7,'perfect','perfect_success')):
            g,_ = session(); g.advance(134); event = g.encounter.enemies[0].current_attack
            g.advance(event.hit_tick-delta-g.combat.tick)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            self.assertEqual(self.render(g).cue,'parry_window')
            self.assertIsNone(g.resolver.last_parry_result)
            g.advance(delta)
            self.assertEqual((g.resolver.last_parry_result.status,g.resolver.last_parry_result.enemy_event_key),(status,event.key))
            self.assertEqual(self.render(g).cue,cue)
            self.assertEqual(g.player.health.current_hp,3)
            g.advance(18)
            self.assertNotIn(self.render(g).cue,('parry_success','perfect_success'))

    def test_actual_evaded_parry_never_displays_success(self):
        from input_controller import InputController
        g,_ = session(); g.advance(150)
        g.resolver.register_parry(g.parry.request(g.combat.tick))
        move = InputController(); move.key_down('right',g.player,occupied=g.encounter.occupied_cells,tick=g.combat.tick)
        self.assertEqual(g.player.position,(6,1))
        g.advance(18)
        self.assertEqual(g.resolver.last_parry_result.status,'failed')
        self.assertNotIn(self.render(g).cue,('parry_success','perfect_success'))

    def test_original_fight_live_observer_hp_receipt_and_stage12_release(self):
        g,flow = session(); c = canvas(); m = RenderMotion(); sync(g,m,0)
        path = art.LiveArenaArtPath(c,motion=m); resolve = StageGame.resolve_current_tick
        observed = set()
        def observe(game):
            result = resolve(game)
            if game is g:
                sync(g,m); before = pickle.dumps((g,m))
                self.assertTrue(path.draw(g,m.positions))
                self.assertEqual(pickle.dumps((g,m)),before)
                r = path.stage11.renderer
                self.assertEqual(r.warning_cells,[tuple(cell) for e in g.encounter.ledger.telegraphs for cell in e.target_cells] if g.playing else [])
                for e in g.encounter.ledger.telegraphs:
                    observed.add(next(a.kind for a in g.encounter.enemies if a.entity_instance_id == e.source_entity_instance_id))
            return result
        with patch.dict(os.environ,CHECKMATE_STAGE11_ART='1'), patch.object(common,'polygon'), patch.object(common.Stage5ArtRenderer,'image'), patch.object(StageGame,'resolve_current_tick',observe):
            self.assertEqual(fight(flow),(11,'UPGRADE',669,2,3))
            self.assertEqual(observed,{'rook','knight','pawn'})
            self.assertEqual(path.stage11.renderer.order,[g.player.entity_instance_id])
            old = g
            g,_ = flow.choose(flow.sync_offer(),'hp',main._new_stage_game)
            self.assertEqual((g.stage_number,g.player.health.current_hp,g.player.health.max_hp,len(flow.run.receipts)),(12,3,4,1))
            self.assertIs(flow.run.verify_receipt(flow.run.receipts[0]),flow.run.receipts[0])
            self.assertIsNot(g.encounter.ledger,old.encounter.ledger)
            self.assertFalse(path.draw(g,{})); path.close()
        self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(8,8))

    def test_actual_game_over_restart_replaces_all_eight_resources(self):
        g,flow = session(); c = canvas(); path = art.Stage11ArtPath(c)
        with patch.dict(os.environ,CHECKMATE_STAGE11_ART='1'), patch.object(art.Stage11ArtRenderer,'draw'):
            for _ in range(10): self.assertTrue(path.draw(g,{}))
            self.assertEqual(c.load_image.call_count,8)
            g.advance(435); old_session = g.combat.combat_session_id
            self.assertEqual(g.state.value,'GAME_OVER'); self.assertEqual(common.cue_kind(g),'quiet')
            g,_ = flow.restart(main._new_stage_game)
            self.assertNotEqual(g.combat.combat_session_id,old_session)
            self.assertEqual((g.stage_number,g.resolver.player_damage,flow.run.receipts),(11,4,()))
            self.assertTrue(path.draw(g,{}))
            self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(16,8))
            with patch.dict(os.environ,CHECKMATE_STAGE11_ART='0'): self.assertFalse(path.draw(g,{}))
            path.close(); path.close()
            self.assertEqual(c.SDL_DestroyTexture.call_count,16)

    def test_stage10_eleven_twelve_real_outcomes_and_resource_exchange(self):
        from tools.stage10_play import session as ten
        # Stage10 dev tool has synthetic prior upgrades; this is not a campaign-clear claim.
        g,flow = ten(); c = canvas(); path = art.LiveArenaArtPath(c)
        with patch.dict(os.environ,CHECKMATE_STAGE10_ART='1',CHECKMATE_STAGE11_ART='1'), patch.object(common.Stage5ArtRenderer,'draw'):
            self.assertTrue(path.draw(g,{})); old_run = flow.run
            self.assertEqual(fight(flow)[1],'BOSS_CLEAR')
            g,_ = flow.enter_next_chapter(main._new_stage_game)
            self.assertTrue(old_run.retired)
            self.assertEqual((g.stage_number,g.resolver.player_damage,g.player.health.current_hp,flow.run.receipts),(11,4,5,()))
            self.assertTrue(path.draw(g,{}))
            self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(17,9))
            self.assertEqual(fight(flow),(11,'UPGRADE',669,4,5))
            g,_ = flow.choose(flow.sync_offer(),'hp',main._new_stage_game)
            self.assertFalse(path.draw(g,{})); path.close()
            self.assertEqual(c.SDL_DestroyTexture.call_count,17)

    def test_missing_decode_null_texture_and_draw_errors_fallback_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for key,name in art.FILES.items():
                if key != 'knight':
                    p = root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b'existence fixture')
            c = canvas()
            with self.assertRaises(FileNotFoundError): art.Stage11ArtRenderer(c,root=root)
            self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(7,7))
        c = canvas(); images = [Mock(texture=i+1) for i in range(7)]+[Mock(texture=None)]
        c.load_image.side_effect = images
        with self.assertRaises(ArenaArtError): art.Stage11ArtRenderer(c)
        self.assertEqual(c.SDL_DestroyTexture.call_count,7)
        g,_ = session(); before = pickle.dumps(g)
        with patch.dict(os.environ,CHECKMATE_STAGE11_ART='1'):
            for error in (OSError('PNG decode'),ArenaArtError('SDL geometry')):
                factory = Mock(side_effect=error); path = art.Stage11ArtPath(canvas(),factory)
                with self.assertLogs('stage11_art_renderer',level='ERROR'):
                    for _ in range(3): self.assertFalse(path.draw(g,{}))
                factory.assert_called_once()
            r = Mock(); r.draw.side_effect = ArenaArtError('copy failed')
            path = art.Stage11ArtPath(canvas(),lambda c,**k:r)
            with self.assertLogs('stage11_art_renderer',level='ERROR'): self.assertFalse(path.draw(g,{}))
            r.close.assert_called_once()
            r = Mock(); r.draw.side_effect = TypeError('programming error')
            path = art.Stage11ArtPath(canvas(),lambda c,**k:r)
            with self.assertRaises(TypeError): path.draw(g,{})
            path.close()
        self.assertEqual(pickle.dumps(g),before)

    def test_native_main_success_and_failure_really_call_correct_renderer(self):
        script = r'''
import pickle
from unittest.mock import patch
import sdl2 as s
from pico2d import pico2d as c
import main
from arena_art_common import ArenaArtError
from stage11_art_renderer import Stage11ArtRenderer
from tools.stage11_play import session
from tools.stage5_art_preview import open_preview
for fail in (False,True):
    g,f=session(); g.advance(0); before=pickle.dumps(g); frames=[0]; draws=[0]; legacy=[0]
    native=Stage11ArtRenderer.draw; original=main.BoardRenderer.draw
    def draw(self,game,positions):
        draws[0]+=1
        if fail: raise ArenaArtError('intentional native fallback fixture')
        return native(self,game,positions)
    def board(self,*args,**kwargs):
        legacy[0]+=1; return original(self,*args,**kwargs)
    def events():
        frames[0]+=1
        return [] if frames[0]<5 else [type('Quit',(),{'type':s.SDL_QUIT})()]
    with patch.object(c,'open_canvas',lambda w,h:open_preview(c,capture=True)),patch.object(c,'get_events',events),patch.object(main,'sleep'),patch.object(main,'perf_counter',lambda:0),patch.object(Stage11ArtRenderer,'draw',draw),patch.object(main.BoardRenderer,'draw',board):
        main.run_session(g,f)
    assert draws[0]>0 and (legacy[0]>0 if fail else legacy[0]==0)
    assert pickle.dumps(g)==before
print('STAGE11 ACTUAL MAIN AND LEGACY FALLBACK OK')
'''
        p = subprocess.run([sys.executable,'-X','utf8','-c',script],cwd=common.ROOT,
                           env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','CHECKMATE_STAGE11_ART':'1'},
                           capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('STAGE11 ACTUAL MAIN AND LEGACY FALLBACK OK',p.stdout)

    def test_eleven_live_captures_reproduce_and_manifest_tracks_actual_events(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable,'-X','utf8','tools/capture_stage11_live.py','--capture-dir',d],cwd=common.ROOT,
                               env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                               capture_output=True,text=True,encoding='utf-8',timeout=90)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            baseline = json.loads((common.ROOT/'artifacts/stage11_d2/capture_manifest.json').read_text())
            actual = json.loads((Path(d)/'capture_manifest.json').read_text())
            self.assertEqual(len(actual['captures']),11)
            for old,new in zip(baseline['captures'],actual['captures']):
                expected = old['sha256']
                if old['file'] == 'upgrade.png':
                    expected = '0ebe555d0383a6fbc6ea0255ac33f17b1ca7c25aa59cf056f2a28bbfc50c02a7'
                self.assertEqual((old['file'],expected),(new['file'],new['sha256']))
                self.assertEqual(hashlib.sha256((Path(d)/new['file']).read_bytes()).hexdigest(),new['sha256'])
            rows = {r['file']:r for r in actual['captures']}
            self.assertEqual(rows['parry_normal.png']['cue'],'parry_success')
            self.assertEqual(rows['parry_perfect.png']['cue'],'perfect_success')
            self.assertEqual(len(rows['dual_rook.png']['warnings']),2)
            self.assertEqual(len(rows['rook1_resolved.png']['warnings']),1)
            self.assertEqual(actual['fight_result'],[11,'UPGRADE',669,2,3])
