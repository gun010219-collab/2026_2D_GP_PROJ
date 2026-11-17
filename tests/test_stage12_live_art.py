"""Live Stage12 color50 rendering; actual outcomes and isolated failure fixtures."""
import contextlib
import io
import json
import os
from pathlib import Path
import pickle
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

import main
from arena_art_common import CAMERA,ArenaArtError
from bishop_behavior import color_targets
from game import StageGame
from input_controller import InputController
from render_motion import RenderMotion
import stage5_art_renderer as common
import stage11_art_renderer as eleven
import stage12_art_renderer as art
from tests.test_hp_carryover import fight
from tests.test_stage6_live_art import canvas
from tools.stage12_play import session


def sync(g,m):
    frozen=(g.player.entity_instance_id,) if g.combat.active_attack or g.parry.active_at(g.combat.tick) else ()
    m.update((g.player,*g.encounter.enemies),1/60,session=g.combat.combat_session_id,frozen=frozen)


class Stage12LiveArtTests(unittest.TestCase):
    def renderer(self,m=None):
        c=canvas();c.draw_line=lambda *a:None;c.draw_rectangle=lambda *a,**kw:None
        r=art.Stage12ArtRenderer(c,motion=m);self.addCleanup(r.close);return r

    def render(self,g,m=None,r=None):
        r=r or self.renderer(m);before=pickle.dumps((g,m))
        with patch.object(common,'polygon'),patch.object(r,'image'):r.draw(g,m.positions if m else {})
        self.assertEqual(pickle.dumps((g,m)),before)
        self.assertEqual(r.warning_cells,[tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else [])
        return r

    def test_all_eight_independent_flags_and_seventeen_legacy_stages(self):
        flags={f'CHECKMATE_STAGE{n}_ART':'0' for n in range(5,13)}
        for enabled in ((),*((n,) for n in range(5,13)),tuple(range(5,13))):
            with patch.dict(os.environ,{**flags,**{f'CHECKMATE_STAGE{n}_ART':'1' for n in enabled}}):
                c=canvas();p=art.LiveArenaArtPath(c)
                with patch.object(common.Stage5ArtRenderer,'draw'):
                    for n in range(1,26):self.assertEqual(p.draw(main._new_stage_game(n),{}),n in enabled,(n,enabled))
                p.close();expected=sum({5:8,6:7,7:7,8:9,9:9,10:9,11:8,12:8}[n] for n in enabled)
                self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(expected,expected))
        for value in ('','0','true','01',' 1'):
            with patch.dict(os.environ,CHECKMATE_STAGE12_ART=value):
                factory=Mock();p=art.Stage12ArtPath(canvas(),factory)
                self.assertFalse(p.draw(session()[0],{}));factory.assert_not_called()

    def test_real_dev_entry_roster_hp60_and_genuine_receipt_no_synthetic_clears(self):
        g,f=session();self.assertEqual((g.stage_number,g.chapter,g.boss,g.player.position),(12,3,False,(5,1)))
        self.assertEqual([(e.kind,e.position,e.health.current_hp) for e in g.encounter.enemies],
                         [('bishop',(2,8),13),('bishop',(7,8),13),('rook',(2,4),16),('pawn',(1,6),9),('pawn',(8,6),9)])
        self.assertEqual(sum(e.health.current_hp for e in g.encounter.enemies),60)
        self.assertEqual((g.player.health.current_hp,g.player.health.max_hp,g.resolver.player_damage,f.run.stats.move_interval_ticks),(3,4,4,18))
        self.assertEqual(len(f.run.receipts),1);receipt=f.run.receipts[0]
        self.assertIs(f.run.verify_receipt(receipt),receipt);self.assertEqual(receipt.offer.stage,11)
        self.assertIsNone(g.encounter.pulse)
        self.assertEqual(set(art.FILES),{'background','frame','light','dark','player','pawn','rook','bishop'})
        self.assertEqual(len(set(art.FILES.values())),8)

    def test_bishops_share_one_texture_but_hp_layout_and_ids_are_independent(self):
        g,_=session();a,b=g.encounter.enemies[:2]
        self.assertIsNot(a.health,b.health);self.assertNotEqual(a.entity_instance_id,b.entity_instance_id)
        a.health.apply_damage(1,tick=0)  # HP isolation fixture, not a clear.
        with patch.object(common.HealthRenderer,'_text') as text:r=self.render(g)
        labels=[c.args[1] for c in text.call_args_list]
        self.assertIn('12/13',labels);self.assertIn('13/13',labels)
        self.assertEqual(sum(Path(c.args[0]).name=='bishop.png' for c in r.c.load_image.call_args_list),1)
        self.assertNotEqual(r.actor_layouts[a.entity_instance_id]['foot'],r.actor_layouts[b.entity_instance_id]['foot'])

    def test_hundred_cells_reproduce_approved_static_bishop_and_stage11_profiles(self):
        from tools.ice_bishop_review import candidate_layout,ASSETS
        record=json.loads((ASSETS/'bishop_manifest.json').read_text())['assets'][0]
        for u in range(10):
            for v in range(10):
                self.assertEqual(CAMERA.pick(*CAMERA.center(u,v)),(u,v))
                self.assertEqual(art.actor_layout('bishop',u,v),candidate_layout('bishop',u,v,{'bishop':record}))
                for kind in ('pawn','rook','player'):self.assertEqual(art.actor_layout(kind,u,v),eleven.actor_layout(kind,u,v))
                l=art.actor_layout('bishop',u,v)
                self.assertEqual(l['foot'],CAMERA.project(u+.5,v+.25));self.assertAlmostEqual(l['hp_y']-l['top'],10)
                self.assertAlmostEqual(l['height']*220/256,84*(1.10-.023*v)/1.10)

    def test_opposite_color50_attacks_keep_original_serialization_and_one_tick_gap(self):
        g,_=session();a,b=g.encounter.enemies[:2];g.advance(48);first=a.current_attack
        self.assertEqual(first.target_cells,color_targets((2,8)));self.assertEqual(len(first.target_cells),50)
        for t in (62,100,149):
            g.advance(t-g.combat.tick);self.assertIsNone(b.current_attack)
            self.assertEqual((b.state,b.next_action_tick),('waiting',t+1));self.assertIs(a.current_attack,first)
            self.render(g)
        g.advance(7);self.assertIsNone(a.current_attack);self.assertIsNone(b.current_attack)
        self.assertNotIn(first,g.encounter.ledger.telegraphs);self.render(g)
        g.advance();second=b.current_attack
        self.assertEqual((second.hit_tick,len(second.target_cells)),(265,50))
        self.assertEqual(second.target_cells,color_targets((7,8)))
        self.assertFalse(set(first.target_cells)&set(second.target_cells))
        self.assertEqual(len(set(first.target_cells)|set(second.target_cells)),100)
        r=self.render(g);self.assertLessEqual(len(r.warning_cells),53)
        self.assertEqual((a.position,b.position),((2,8),(7,8)))
        g.advance(108);self.assertNotIn(second,g.encounter.ledger.telegraphs);self.render(g)

    def test_color_warning_and_rook_overlap_keep_exact_event_cells(self):
        g,_=session();g.advance(149);bishop=g.encounter.enemies[0].current_attack;rook=g.encounter.enemies[2].current_attack
        self.assertTrue(bishop and rook);self.assertTrue(set(bishop.target_cells)&set(rook.target_cells))
        expected=list(bishop.target_cells+rook.target_cells);self.assertEqual(self.render(g).warning_cells,expected)
        for c in set(expected):self.assertEqual(CAMERA.pick(*CAMERA.center(*c)),c)
        self.assertEqual(expected.count((5,1)),2)

    def test_bishop_cancel_death_and_waiting_opposite_source_are_independent(self):
        for index,dead in ((0,False),(0,True),(1,True)):
            g,_=session();g.advance(100);a,b=g.encounter.enemies[:2];event=a.current_attack;target=(a,b)[index]
            if dead:
                target.health.apply_damage(13,tick=100);g.encounter.deactivate(target.entity_instance_id,tick=100)
            else:g.encounter.cancel_attacks(target.entity_instance_id,tick=100)
            r=self.render(g)
            if dead:self.assertNotIn(target.entity_instance_id,r.order)
            if index==1:
                self.assertIn(event,g.encounter.ledger.telegraphs);self.assertIs(a.current_attack,event)
            else:
                self.assertNotIn(event,g.encounter.ledger.telegraphs);self.assertIsNone(b.current_attack)
                g.advance();self.assertEqual(b.current_attack.target_cells,color_targets((7,8)))
            self.render(g)

    def test_normal_perfect_results_and_stun_are_bound_to_real_bishop_event(self):
        for delta,status,cue in ((18,'normal','parry_success'),(7,'perfect','perfect_success')):
            g,_=session();g.advance(156-delta);event=g.encounter.enemies[0].current_attack
            g.resolver.register_parry(g.parry.request(g.combat.tick));self.assertIsNone(g.resolver.last_parry_result)
            self.assertEqual(self.render(g).cue,'parry_window');g.advance(delta)
            result=g.resolver.last_parry_result
            self.assertEqual((result.status,result.enemy_event_key),(status,event.key))
            self.assertEqual(self.render(g).cue,cue);self.assertEqual(g.player.health.current_hp,3)
            self.assertNotIn(event,g.encounter.ledger.telegraphs)
            if status=='perfect':self.assertEqual(g.encounter.enemies[0].state,'stunned')
            g.advance(18);self.assertNotIn(self.render(g).cue,('parry_success','perfect_success'))

    def test_evaded_failed_input_has_no_success_or_damage_outside_color_targets(self):
        g,_=session();g.advance(138);event=g.encounter.enemies[0].current_attack
        g.resolver.register_parry(g.parry.request(g.combat.tick))
        move=InputController();move.key_down('right',g.player,occupied=g.encounter.occupied_cells,tick=g.combat.tick)
        self.assertNotIn(g.player.position,event.target_cells);g.advance(18)
        self.assertEqual((g.resolver.last_parry_result.status,g.resolver.last_parry_result.reason),('failed','evaded'))
        self.assertEqual(g.player.health.current_hp,3);self.assertNotIn(self.render(g).cue,('parry_success','perfect_success'))
        g,_=session();g.advance(149);self.assertIn(g.player.position,g.encounter.enemies[0].current_attack.target_cells)
        g.advance(7);self.assertEqual(g.player.health.current_hp,2);g.advance(39)
        self.assertEqual(g.player.health.current_hp,2)  # Existing shared invulnerability covers the Rook.

    def test_actual_mixed_fight_readonly_motion_stationary_bishops_and_stage13_release(self):
        g,f=session();m=RenderMotion();c=canvas();c.draw_line=lambda *a:None;c.draw_rectangle=lambda *a,**kw:None
        p=art.LiveArenaArtPath(c,motion=m);resolve=StageGame.resolve_current_tick;colors=set();kinds=set();rook_cells=set()
        def observe(game):
            result=resolve(game)
            if game is g:
                sync(g,m);before=pickle.dumps((g,m,f.run));self.assertTrue(p.draw(g,m.positions))
                self.assertEqual(pickle.dumps((g,m,f.run)),before);r=p.stage12.renderer
                self.assertEqual(r.warning_cells,[tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else [])
                actors=[e for e in (g.player,*g.encounter.enemies) if e.alive and getattr(e,'active',True)]
                actors.sort(key=lambda e:(-m.ground_pose(e)[0][1],m.ground_pose(e)[0][0],e.entity_instance_id))
                self.assertEqual(r.order,[e.entity_instance_id for e in actors])
                for e,pos in zip(g.encounter.enemies[:2],((2,8),(7,8))):
                    self.assertEqual(e.position,pos);self.assertEqual(m.ground_pose(e)[1],0)
                for event in g.encounter.ledger.telegraphs:
                    source=next(e for e in g.encounter.enemies if e.entity_instance_id==event.source_entity_instance_id);kinds.add(source.kind)
                    if source.kind=='bishop':colors.add(sum(source.position)%2)
                rook_cells.add(g.encounter.enemies[2].position)
            return result
        with patch.dict(os.environ,CHECKMATE_STAGE12_ART='1'),patch.object(common,'polygon'),patch.object(common.Stage5ArtRenderer,'image'),patch.object(StageGame,'resolve_current_tick',observe):
            self.assertEqual(fight(f),(12,'UPGRADE',669,3,4));self.assertEqual(colors,{0,1});self.assertEqual(kinds,{'bishop','rook','pawn'})
            self.assertIn((2,4),rook_cells);self.assertEqual(p.stage12.renderer.order,[g.player.entity_instance_id])
            self.assertFalse(g.encounter.ledger.pending);old=g;run=f.run
            g,_=f.choose(f.sync_offer(),'attack',main._new_stage_game)
            self.assertIs(f.run,run);self.assertEqual((g.stage_number,g.player.health.current_hp,g.player.health.max_hp,len(run.receipts)),(13,3,4,2))
            self.assertIsNot(old.encounter.ledger,g.encounter.ledger);self.assertFalse(p.draw(g,{}));p.close()
        self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(8,8))

    def test_live_rook_pawn_motion_depth_hp_and_stationary_bishop_anchors(self):
        # Unlike the walking attack driver, no-input combat leaves the Rook alive to dash.
        g,_=session();m=RenderMotion();sync(g,m);r=self.renderer(m);visited=[set(),set(),set()]
        for _ in range(220):
            g.advance();sync(g,m);self.render(g,m,r)
            actors=[e for e in (g.player,*g.encounter.enemies) if e.alive and getattr(e,'active',True)]
            actors.sort(key=lambda e:(-m.ground_pose(e)[0][1],m.ground_pose(e)[0][0],e.entity_instance_id))
            self.assertEqual(r.order,[e.entity_instance_id for e in actors])
            for e in actors:
                u,v,lift=r.pose(e,m.positions);base=art.actor_layout(getattr(e,'kind','player'),u,v)
                self.assertEqual(lift,0);self.assertEqual(r.actor_layouts[e.entity_instance_id],base)
            for i,e in enumerate(g.encounter.enemies[2:]):visited[i].add(e.position)
        self.assertTrue(all(len(v)>1 for v in visited))

    def test_actual_eleven_twelve_thirteen_progression_and_texture_exchange(self):
        from tools.stage11_play import session as start
        g,f=start();c=canvas();p=art.LiveArenaArtPath(c)
        with patch.dict(os.environ,CHECKMATE_STAGE11_ART='1',CHECKMATE_STAGE12_ART='1'),patch.object(common.Stage5ArtRenderer,'draw'):
            self.assertTrue(p.draw(g,{}));self.assertEqual(fight(f),(11,'UPGRADE',669,2,3));old=g
            g,_=f.choose(f.sync_offer(),'hp',main._new_stage_game);self.assertTrue(p.draw(g,{}))
            self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
            self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(16,8))
            self.assertEqual(fight(f),(12,'UPGRADE',669,3,4));g,_=f.choose(f.sync_offer(),'attack',main._new_stage_game)
            self.assertFalse(p.draw(g,{}));p.close();self.assertEqual(c.SDL_DestroyTexture.call_count,16)

    def test_game_over_restarts_chapter_stage11_and_cleans_stage12_session(self):
        for stage11_enabled in ('0','1'):
            g,f=session();c=canvas();p=art.LiveArenaArtPath(c)
            with patch.dict(os.environ,CHECKMATE_STAGE12_ART='1',CHECKMATE_STAGE11_ART=stage11_enabled),patch.object(common.Stage5ArtRenderer,'draw'):
                for _ in range(5):self.assertTrue(p.draw(g,{}))
                self.assertEqual(c.load_image.call_count,8);g.advance(3600)
                self.assertEqual((g.state.value,g.end_tick),('GAME_OVER',471))
                g,_=f.restart(main._new_stage_game)
                self.assertEqual((g.stage_number,g.player.health.current_hp,len(f.run.receipts)),(11,3,0))
                self.assertEqual(p.draw(g,{}),stage11_enabled=='1');p.close();p.close()
                expected=16 if stage11_enabled=='1' else 8
                self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(expected,expected))

    def test_partial_missing_decode_null_texture_and_runtime_fallback_are_readonly(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for key,name in art.FILES.items():
                if key!='bishop':p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'existence fixture')
            c=canvas()
            with self.assertRaises(FileNotFoundError):art.Stage12ArtRenderer(c,root=root)
            self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(7,7))
        c=canvas();c.load_image.side_effect=[*[Mock(texture=i+1) for i in range(7)],Mock(texture=None)]
        with self.assertRaises(ArenaArtError):art.Stage12ArtRenderer(c)
        self.assertEqual(c.SDL_DestroyTexture.call_count,7)
        g,f=session();before=pickle.dumps((g,f.run))
        with patch.dict(os.environ,CHECKMATE_STAGE12_ART='1'):
            for error in (OSError('decode'),ArenaArtError('SDL copy')):
                factory=Mock(side_effect=error);p=art.Stage12ArtPath(canvas(),factory)
                with self.assertLogs('stage12_art_renderer',level='ERROR'):
                    for _ in range(3):self.assertFalse(p.draw(g,{}))
                factory.assert_called_once()
            r=Mock();r.draw.side_effect=ArenaArtError('draw');p=art.Stage12ArtPath(canvas(),lambda c,**kw:r)
            with self.assertLogs('stage12_art_renderer',level='ERROR'):self.assertFalse(p.draw(g,{}))
            r.close.assert_called_once()
            r=Mock();r.draw.side_effect=TypeError('programming');p=art.Stage12ArtPath(canvas(),lambda c,**kw:r)
            with self.assertRaises(TypeError):p.draw(g,{})
            p.close()
        self.assertEqual(pickle.dumps((g,f.run)),before)

    def test_native_main_really_draws_legacy_after_expected_sdl_failure(self):
        script=r'''
import pickle
from unittest.mock import patch
import sdl2 as s
from pico2d import pico2d as c
import main
from arena_art_common import ArenaArtError
from stage12_art_renderer import Stage12ArtRenderer
from tools.stage12_play import session
from tools.stage5_art_preview import open_preview
for fail in (False,True):
    g,f=session();g.advance(0);before=pickle.dumps(g);frames=[0];draws=[0];legacy=[0]
    original=Stage12ArtRenderer.draw;board=main.BoardRenderer.draw
    def draw(self,game,positions):
        draws[0]+=1;original(self,game,positions)
        if fail:raise ArenaArtError('intentional draw failure after actual partial art')
    def old(self,*a,**kw):legacy[0]+=1;return board(self,*a,**kw)
    def events():
        frames[0]+=1
        return [] if frames[0]<5 else [type('Quit',(),{'type':s.SDL_QUIT})()]
    with patch.object(c,'open_canvas',lambda w,h:open_preview(c,capture=True)),patch.object(c,'get_events',events),patch.object(main,'perf_counter',lambda:0),patch.object(main,'sleep'),patch.object(Stage12ArtRenderer,'draw',draw),patch.object(main.BoardRenderer,'draw',old):
        main.run_session(g,f)
    assert draws[0]>0 and (legacy[0]>0 if fail else legacy[0]==0)
    assert pickle.dumps(g)==before
print('ACTUAL STAGE12 MAIN SUCCESS AND LEGACY FALLBACK OK')
'''
        p=subprocess.run([sys.executable,'-X','utf8','-c',script],cwd=common.ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','CHECKMATE_STAGE12_ART':'1'},capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn('ACTUAL STAGE12 MAIN SUCCESS',p.stdout)

    def test_twelve_real_capture_pngs_repeat_with_actual_serialization_and_parry(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,'-X','utf8','tools/capture_stage12_live.py','--capture-dir',d],cwd=common.ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,encoding='utf-8',timeout=90)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            old=json.loads((common.ROOT/'artifacts/stage12_d3b/capture_manifest.json').read_text())
            new=json.loads((Path(d)/'capture_manifest.json').read_text());self.assertEqual(len(new['captures']),12)
            for a,b in zip(old['captures'],new['captures']):
                self.assertEqual((a['file'],a['sha256']),(b['file'],b['sha256']))
                self.assertEqual(hashlib.sha256((Path(d)/b['file']).read_bytes()).hexdigest(),b['sha256'])
            self.assertEqual(new['stage12_result'],[12,'UPGRADE',669,3,4])
            rows={r['file']:r for r in new['captures']}
            self.assertEqual(rows['parry_perfect.png']['cue'],'perfect_success')
            self.assertEqual(rows['parry_normal.png']['cue'],'parry_success')
            for name in ('bishop_even.png','bishop_odd.png'):
                self.assertEqual(sum(len(e['cells'])==50 for e in rows[name]['warnings']),1)
            self.assertFalse(any(len(e['cells'])==50 for e in rows['serialized_gap.png']['warnings']))

    def test_dev_script_routes_real_session_to_main_and_discloses_automation(self):
        output=io.StringIO()
        with patch.object(main,'run_session') as runner,contextlib.redirect_stdout(output):
            runpy.run_path(str(common.ROOT/'tools/stage12_play.py'),run_name='__main__')
        runner.assert_called_once();g,f=runner.call_args.args
        self.assertIs(g,f.game);self.assertEqual((g.stage_number,len(f.run.receipts)),(12,1))
        self.assertIn('AUTOMATED real Stage11',output.getvalue());self.assertIn('No synthetic receipts',output.getvalue())
