"""Real Stage13 Queen ledger, display-only motion, progression and fallback."""
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
from config import cell_center
from game import StageGame
from input_controller import InputController
from queen_behavior import queen_ray_targets,choose_reposition
from render_motion import RenderMotion
import stage5_art_renderer as common
import stage11_art_renderer as eleven
import stage13_art_renderer as art
from tests.test_hp_carryover import fight
from tests.test_stage6_live_art import canvas
from tests.test_stage12_live_art import sync
from tools.stage13_play import session


class Stage13LiveArtTests(unittest.TestCase):
    def renderer(self,m=None):
        c=canvas();c.draw_line=lambda *a:None;c.draw_rectangle=lambda *a,**kw:None
        r=art.Stage13ArtRenderer(c,motion=m);self.addCleanup(r.close);return r

    def render(self,g,m=None,r=None):
        r=r or self.renderer(m);before=pickle.dumps((g,m))
        with patch.object(common,'polygon'),patch.object(r,'image'):r.draw(g,m.positions if m else {})
        self.assertEqual(pickle.dumps((g,m)),before)
        self.assertEqual(r.warning_cells,[tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else [])
        return r

    def test_nine_flags_are_independent_and_other_sixteen_stages_remain_legacy(self):
        flags={f'CHECKMATE_STAGE{n}_ART':'0' for n in range(5,14)}
        for enabled in ((),*((n,) for n in range(5,14)),tuple(range(5,14))):
            with patch.dict(os.environ,{**flags,**{f'CHECKMATE_STAGE{n}_ART':'1' for n in enabled}}):
                c=canvas();p=art.LiveArenaArtPath(c)
                with patch.object(common.Stage5ArtRenderer,'draw'):
                    for n in range(1,26):self.assertEqual(p.draw(main._new_stage_game(n),{}),n in enabled,(n,enabled))
                p.close();expected=sum({5:8,6:7,7:7,8:9,9:9,10:9,11:8,12:8,13:8}[n] for n in enabled)
                self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(expected,expected))
        for value in ('','0','true','01',' 1'):
            with patch.dict(os.environ,CHECKMATE_STAGE13_ART=value):
                factory=Mock();p=art.Stage13ArtPath(canvas(),factory)
                self.assertFalse(p.draw(session()[0],{}));factory.assert_not_called()

    def test_actual_roster_hp58_and_real_two_receipts_no_synthetic_clears(self):
        g,f=session();self.assertEqual((g.stage_number,g.chapter,g.boss,g.player.position),(13,3,False,(5,1)))
        self.assertEqual([(e.kind,e.position,e.health.current_hp) for e in g.encounter.enemies],
                         [('queen',(4,7),18),('knight',(3,6),13),('pawn',(1,6),9),('pawn',(8,6),9),('pawn',(3,8),9)])
        self.assertEqual(sum(e.health.current_hp for e in g.encounter.enemies),58)
        self.assertEqual((g.player.health.current_hp,g.player.health.max_hp,g.resolver.player_damage,f.run.stats.move_interval_ticks),(3,4,5,18))
        self.assertEqual([r.offer.stage for r in f.run.receipts],[11,12])
        for receipt in f.run.receipts:self.assertIs(f.run.verify_receipt(receipt),receipt)
        self.assertIsNone(g.encounter.pulse)
        self.assertEqual(set(art.FILES),{'background','frame','light','dark','player','pawn','knight','queen'})
        self.assertEqual(len(set(art.FILES.values())),8)

    def test_hundred_cells_reproduce_approved_queen_and_unchanged_other_profiles(self):
        from tools.ice_queen_review import candidate_layout,ASSETS
        record=json.loads((ASSETS/'queen_manifest.json').read_text())['assets'][0]
        for u in range(10):
            for v in range(10):
                self.assertEqual(CAMERA.pick(*CAMERA.center(u,v)),(u,v))
                self.assertEqual(art.actor_layout('queen',u,v),candidate_layout('queen',u,v,{'queen':record}))
                for kind in ('pawn','knight','player'):self.assertEqual(art.actor_layout(kind,u,v),eleven.actor_layout(kind,u,v))
                l=art.actor_layout('queen',u,v)
                self.assertEqual(l['foot'],CAMERA.project(u+.5,v+.25));self.assertAlmostEqual(l['hp_y']-l['top'],12)
                self.assertAlmostEqual(l['height']*220/256,90*(1.10-.023*v)/1.10)
                self.assertAlmostEqual(l['center'][1]-l['height']/2+l['height']*18/256,l['foot'][1])
        self.assertAlmostEqual(art.actor_layout('queen',0,0)['height']*159/256,65.04545454545455)
        self.assertAlmostEqual(art.actor_layout('queen',0,9)['height']*220/256,73.06363636363636)

    def test_initial31_is_not_fabricated_live_warning_and_reposition_uses_actual_rays(self):
        g,_=session();q=g.encounter.enemies[0];self.assertEqual(len(queen_ray_targets(q.position)),31)
        self.assertEqual(self.render(g).warning_cells,[])
        occupied=g.encounter.occupied_cells-{q.position};expected=choose_reposition(q.position,g.player.position,occupied)
        g.advance(47);self.assertEqual(q.position,(4,7));self.assertIsNone(q.current_attack)
        g.advance();self.assertEqual((q.position,q.state,q.next_action_tick),(expected,'waiting',49))
        self.assertIsNone(q.current_attack);g.advance();event=q.current_attack
        self.assertEqual((q.position,event.hit_tick,len(event.target_cells)),((5,6),121,33))
        self.assertEqual(event.target_cells,queen_ray_targets(q.position));self.assertNotIn(q.position,event.target_cells)
        self.assertEqual(self.render(g).warning_cells,list(event.target_cells))
        g.advance(72);self.assertNotIn(event,g.encounter.ledger.telegraphs);self.render(g)
        g.advance(180);self.assertEqual(q.position,(5,3));self.assertIsNone(q.current_attack)
        g.advance();new=q.current_attack
        self.assertNotEqual(event.key,new.key);self.assertEqual(new.target_cells,queen_ray_targets((5,3)))
        self.assertEqual(new.hit_tick,374);self.render(g)

    def test_projected_marks_preserve_real_target_order_and_no_origin_or_extra_cells(self):
        g,_=session();g.advance(49);r=self.renderer()
        with patch.object(r,'mark') as mark:self.render(g,r=r)
        self.assertEqual([c.args[0] for c in mark.call_args_list],list(g.encounter.enemies[0].current_attack.target_cells))
        for cell in r.warning_cells:self.assertEqual(CAMERA.pick(*CAMERA.center(*cell)),cell)

    def test_real_queen_normal_perfect_and_stun_require_resolver_success(self):
        for delta,status,cue in ((18,'normal','parry_success'),(7,'perfect','perfect_success')):
            g,_=session();g.advance(121-delta);event=g.encounter.enemies[0].current_attack
            g.resolver.register_parry(g.parry.request(g.combat.tick));self.assertIsNone(g.resolver.last_parry_result)
            self.assertEqual(self.render(g).cue,'parry_window');g.advance(delta)
            result=g.resolver.last_parry_result
            self.assertEqual((result.status,result.enemy_event_key),(status,event.key))
            self.assertEqual(self.render(g).cue,cue);self.assertEqual(g.player.health.current_hp,3)
            self.assertNotIn(event,g.encounter.ledger.telegraphs)
            if status=='perfect':self.assertEqual(g.encounter.enemies[0].state,'stunned')
            g.advance(18);self.assertNotIn(self.render(g).cue,('parry_success','perfect_success'))

    def test_real_damage_and_evaded_failed_input_do_not_invent_a_success(self):
        g,_=session();g.advance(121);self.assertEqual(g.player.health.current_hp,2);self.render(g)
        g,_=session();g.advance(103);event=g.encounter.enemies[0].current_attack
        g.resolver.register_parry(g.parry.request(103))
        InputController().key_down('left',g.player,occupied=g.encounter.occupied_cells,tick=103)
        self.assertNotIn(g.player.position,event.target_cells);g.advance(18)
        self.assertEqual((g.resolver.last_parry_result.status,g.resolver.last_parry_result.reason),('failed','evaded'))
        self.assertEqual(g.player.health.current_hp,3);self.assertNotIn(self.render(g).cue,('parry_success','perfect_success'))

    def test_queen_cancel_or_death_cleans_only_its_event_not_knight_warning(self):
        for dead in (False,True):
            g,_=session();g.advance(80);q,k=g.encounter.enemies[:2];a,b=q.current_attack,k.current_attack
            self.assertTrue(a and b)
            if dead:
                q.health.apply_damage(18,tick=80);g.encounter.deactivate(q.entity_instance_id,tick=80)  # source death isolation fixture, not a clear
            else:g.encounter.cancel_attacks(q.entity_instance_id,tick=80)
            r=self.render(g);self.assertNotIn(a,g.encounter.ledger.telegraphs);self.assertIn(b,g.encounter.ledger.telegraphs)
            if dead:self.assertNotIn(q.entity_instance_id,r.order)
            self.assertEqual(r.warning_cells,list(b.target_cells))

    def test_knight_peak18_shadow_ground_hp_lift_and_landing(self):
        g,_=session();m=RenderMotion();sync(g,m);r=self.renderer(m)
        for _ in range(101):g.advance();sync(g,m)
        k=g.encounter.enemies[1];ground,lift=m.ground_pose(k);self.assertAlmostEqual(lift,18)
        u,v,_=r.pose(k,m.positions);base=art.actor_layout('knight',u,v)
        with patch.object(common,'polygon') as poly,patch.object(r,'image'):r.draw(g,m.positions)
        l=r.actor_layouts[k.entity_instance_id];self.assertEqual(l['foot'],base['foot'])
        self.assertAlmostEqual(l['hp_y']-base['hp_y'],18);self.assertAlmostEqual(l['center'][1]-base['center'][1],18)
        shadows=[call.args[1] for call in poly.call_args_list if len(call.args)>2 and call.args[2]==(24,25,29,255)]
        self.assertTrue(any(abs(sum(p[0] for p in points)/8-(base['foot'][0]+4))<1e-7 and abs(sum(p[1] for p in points)/8-(base['foot'][1]-2))<1e-7 for points in shadows))
        for _ in range(4):g.advance();sync(g,m)
        self.assertEqual(m.ground_pose(k),(cell_center(*k.position),0));self.render(g,m,r)

    def test_actual_queen_motion_ground_depth_and_hp_labels_follow_all_live_actors(self):
        g,_=session();m=RenderMotion();sync(g,m);r=self.renderer(m);q=g.encounter.enemies[0];positions=set()
        for tick in range(1,310):
            g.advance();sync(g,m);self.render(g,m,r);positions.add(q.position)
            actors=[e for e in (g.player,*g.encounter.enemies) if e.alive and getattr(e,'active',True)]
            actors.sort(key=lambda e:(-m.ground_pose(e)[0][1],m.ground_pose(e)[0][0],e.entity_instance_id))
            self.assertEqual(r.order,[e.entity_instance_id for e in actors])
            self.assertEqual(m.ground_pose(q)[1],0)
            if tick==51:self.assertNotEqual(m.ground_pose(q)[0],cell_center(*q.position))
            if tick==55:self.assertEqual(m.ground_pose(q)[0],cell_center(*q.position))
            self.assertEqual(set(r.actor_layouts),set(r.order))
        self.assertEqual(positions,{(4,7),(5,6),(5,3)})

    def test_all_hp_labels_draw_after_cape_and_pawns_share_one_texture_with_independent_hp(self):
        g,_=session();pawns=g.encounter.enemies[2:];self.assertEqual(len({e.entity_instance_id for e in pawns}),3)
        pawns[0].health.apply_damage(1,tick=0)  # HP isolation fixture
        r=self.renderer();order=[]
        with patch.object(common,'polygon'),patch.object(r,'image',side_effect=lambda *a:order.append(a[0])),patch.object(common.HealthRenderer,'_text',side_effect=lambda c,text,*a,**kw:order.append(text)):
            r.draw(g,{})
        self.assertGreater(order.index('8/9'),max(order.index(kind) for kind in ('queen','knight','pawn')))
        self.assertIn('9/9',order);self.assertIn('18/18',order)
        self.assertEqual(sum(Path(c.args[0]).name=='pawn.png' for c in r.c.load_image.call_args_list),1)
        self.assertEqual(len({r.actor_layouts[e.entity_instance_id]['foot'] for e in pawns}),3)

    def test_actual_mixed_fight_readonly_and_normal_clear_upgrade_to_fourteen(self):
        g,f=session();m=RenderMotion();c=canvas();c.draw_line=lambda *a:None;c.draw_rectangle=lambda *a,**kw:None
        p=art.LiveArenaArtPath(c,motion=m);resolve=StageGame.resolve_current_tick;kinds=set();positions=set()
        def observe(game):
            result=resolve(game)
            if game is g:
                sync(g,m);before=pickle.dumps((g,m,f.run));self.assertTrue(p.draw(g,m.positions))
                self.assertEqual(pickle.dumps((g,m,f.run)),before);r=p.stage13.renderer
                self.assertEqual(r.warning_cells,[tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else [])
                positions.add(g.encounter.enemies[0].position)
                for event in g.encounter.ledger.telegraphs:
                    source=next(e for e in g.encounter.enemies if e.entity_instance_id==event.source_entity_instance_id);kinds.add(source.kind)
                    if source.kind=='queen':self.assertEqual(event.target_cells,queen_ray_targets(source.position))
            return result
        with patch.dict(os.environ,CHECKMATE_STAGE13_ART='1'),patch.object(common,'polygon'),patch.object(common.Stage5ArtRenderer,'image'),patch.object(StageGame,'resolve_current_tick',observe):
            self.assertEqual(fight(f),(13,'UPGRADE',543,3,4));self.assertEqual(kinds,{'queen','knight'})
            self.assertGreater(len(positions),1);self.assertEqual(p.stage13.renderer.order,[g.player.entity_instance_id]);self.assertFalse(g.encounter.ledger.pending)
            old=g;run=f.run;g,_=f.choose(f.sync_offer(),'hp',main._new_stage_game)
            self.assertIs(f.run,run);self.assertEqual((g.stage_number,g.player.health.current_hp,g.player.health.max_hp,len(run.receipts)),(14,4,5,3))
            self.assertIsNot(old.encounter.ledger,g.encounter.ledger);self.assertFalse(p.draw(g,{}));p.close()
        self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(8,8))

    def test_real_twelve_thirteen_fourteen_and_new_session_texture_exchange(self):
        from tools.stage12_play import session as start
        g,f=start();c=canvas();p=art.LiveArenaArtPath(c)
        with patch.dict(os.environ,CHECKMATE_STAGE12_ART='1',CHECKMATE_STAGE13_ART='1'),patch.object(common.Stage5ArtRenderer,'draw'):
            self.assertTrue(p.draw(g,{}));self.assertEqual(fight(f),(12,'UPGRADE',669,3,4));old=g
            g,_=f.choose(f.sync_offer(),'attack',main._new_stage_game);self.assertTrue(p.draw(g,{}))
            self.assertNotEqual(g.combat.combat_session_id,old.combat.combat_session_id)
            self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(16,8))
            self.assertEqual(fight(f),(13,'UPGRADE',543,3,4));g,_=f.choose(f.sync_offer(),'hp',main._new_stage_game)
            self.assertFalse(p.draw(g,{}));p.close();self.assertEqual(c.SDL_DestroyTexture.call_count,16)

    def test_game_over_restarts_eleven_and_session_loads_only_once_then_releases(self):
        for stage11_enabled in ('0','1'):
            g,f=session();c=canvas();p=art.LiveArenaArtPath(c)
            with patch.dict(os.environ,CHECKMATE_STAGE13_ART='1',CHECKMATE_STAGE11_ART=stage11_enabled),patch.object(common.Stage5ArtRenderer,'draw'):
                for _ in range(5):self.assertTrue(p.draw(g,{}))
                self.assertEqual(c.load_image.call_count,8);g.advance(3600)
                self.assertEqual((g.state.value,g.end_tick),('GAME_OVER',374))
                g,_=f.restart(main._new_stage_game)
                self.assertEqual((g.stage_number,g.player.health.current_hp,g.player.health.max_hp,len(f.run.receipts),g.resolver.player_damage),(11,3,3,0,4))
                self.assertEqual(p.draw(g,{}),stage11_enabled=='1');p.close();p.close()
                expected=16 if stage11_enabled=='1' else 8
                self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(expected,expected))

    def test_restart_releases_eight_outgoing_textures_before_loading_previous_stage(self):
        g,f=session();c=canvas();p=art.LiveArenaArtPath(c);counts=[]
        def load(*args):
            counts.append(c.load_image.call_count-c.SDL_DestroyTexture.call_count)
            return Mock(texture=c.load_image.call_count)
        c.load_image.side_effect=load
        with patch.dict(os.environ,CHECKMATE_STAGE13_ART='1',CHECKMATE_STAGE11_ART='1'),patch.object(common.Stage5ArtRenderer,'draw'):
            self.assertTrue(p.draw(g,{}));g.advance(3600);g,_=f.restart(main._new_stage_game)
            self.assertTrue(p.draw(g,{}));p.close()
        self.assertEqual(max(counts),8);self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(16,16))

    def test_partial_missing_decode_null_texture_and_runtime_fallback_are_readonly(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for key,name in art.FILES.items():
                if key!='queen':p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'existence fixture')
            c=canvas()
            with self.assertRaises(FileNotFoundError):art.Stage13ArtRenderer(c,root=root)
            self.assertEqual((c.load_image.call_count,c.SDL_DestroyTexture.call_count),(7,7))
        c=canvas();c.load_image.side_effect=[*[Mock(texture=i+1) for i in range(7)],Mock(texture=None)]
        with self.assertRaises(ArenaArtError):art.Stage13ArtRenderer(c)
        self.assertEqual(c.SDL_DestroyTexture.call_count,7)
        g,f=session();before=pickle.dumps((g,f.run))
        with patch.dict(os.environ,CHECKMATE_STAGE13_ART='1'):
            for error in (OSError('decode'),ArenaArtError('SDL copy')):
                factory=Mock(side_effect=error);p=art.Stage13ArtPath(canvas(),factory)
                with self.assertLogs('stage13_art_renderer',level='ERROR'):
                    for _ in range(3):self.assertFalse(p.draw(g,{}))
                factory.assert_called_once()
            r=Mock();r.draw.side_effect=ArenaArtError('draw');p=art.Stage13ArtPath(canvas(),lambda c,**kw:r)
            with self.assertLogs('stage13_art_renderer',level='ERROR'):self.assertFalse(p.draw(g,{}))
            r.close.assert_called_once()
            r=Mock();r.draw.side_effect=TypeError('programming');p=art.Stage13ArtPath(canvas(),lambda c,**kw:r)
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
from stage13_art_renderer import Stage13ArtRenderer
from tools.stage13_play import session
from tools.stage5_art_preview import open_preview
for fail in (False,True):
    g,f=session();g.advance(0);before=pickle.dumps(g);frames=[0];draws=[0];legacy=[0]
    original=Stage13ArtRenderer.draw;board=main.BoardRenderer.draw
    def draw(self,game,positions):
        draws[0]+=1;original(self,game,positions)
        if fail:raise ArenaArtError('intentional draw failure after actual partial art')
    def old(self,*a,**kw):legacy[0]+=1;return board(self,*a,**kw)
    def events():
        frames[0]+=1
        return [] if frames[0]<5 else [type('Quit',(),{'type':s.SDL_QUIT})()]
    with patch.object(c,'open_canvas',lambda w,h:open_preview(c,capture=True)),patch.object(c,'get_events',events),patch.object(main,'perf_counter',lambda:0),patch.object(main,'sleep'),patch.object(Stage13ArtRenderer,'draw',draw),patch.object(main.BoardRenderer,'draw',old):
        main.run_session(g,f)
    assert draws[0]>0 and (legacy[0]>0 if fail else legacy[0]==0)
    assert pickle.dumps(g)==before
print('ACTUAL STAGE13 MAIN SUCCESS AND LEGACY FALLBACK OK')
'''
        p=subprocess.run([sys.executable,'-X','utf8','-c',script],cwd=common.ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','CHECKMATE_STAGE13_ART':'1'},capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn('ACTUAL STAGE13 MAIN SUCCESS',p.stdout)


    def test_real_pawn_contact_warning_after_legal_input_uses_original_ledger(self):
        g,_=session();ctl=InputController()
        for direction in ['left']*4+['up']*5:
            ctl.key_down(direction,g.player,occupied=g.encounter.occupied_cells,tick=g.combat.tick);ctl.key_up(direction);g.advance(18)
        g.advance(207-g.combat.tick);pawn=g.encounter.enemies[2];event=pawn.current_attack
        self.assertEqual((g.player.position,pawn.position,event.hit_tick,event.target_cells),((1,4),(1,5),246,((1,4),)))
        r=self.render(g);self.assertIn((1,4),r.warning_cells);self.assertIn(pawn.entity_instance_id,r.order)

    def test_fourteen_actual_capture_pngs_repeat_with_ledger_parry_and_reposition(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,'-X','utf8','tools/capture_stage13_live.py','--capture-dir',d],cwd=common.ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,encoding='utf-8',timeout=90)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            old=json.loads((common.ROOT/'artifacts/stage13_d4b/capture_manifest.json').read_text())
            new=json.loads((Path(d)/'capture_manifest.json').read_text());self.assertEqual(len(new['captures']),14)
            for a,b in zip(old['captures'],new['captures']):
                expected = a['sha256']
                if a['file'] == 'upgrade.png':
                    expected = '120625654c80c17a96e3f40e391bdc04e6849e4e666308c8200a65cfd48d23f8'
                self.assertEqual((a['file'],expected),(b['file'],b['sha256']))
                self.assertEqual(hashlib.sha256((Path(d)/b['file']).read_bytes()).hexdigest(),b['sha256'])
            self.assertEqual(new['stage13_result'],[13,'UPGRADE',543,3,4])
            rows={r['file']:r for r in new['captures']}
            self.assertEqual(rows['parry_perfect.png']['cue'],'perfect_success')
            self.assertEqual(rows['parry_normal.png']['cue'],'parry_success')
            self.assertEqual(len(rows['queen_rays.png']['warning_cells']),33)
            self.assertEqual(len(rows['normal.png']['warning_cells']),0)
            self.assertEqual(rows['knight_peak.png']['layouts']['s13_knight_1']['elevation'],18)

    def test_dev_script_routes_real_session_and_discloses_automated_preceding_fights(self):
        output=io.StringIO()
        with patch.object(main,'run_session') as runner,contextlib.redirect_stdout(output):
            runpy.run_path(str(common.ROOT/'tools/stage13_play.py'),run_name='__main__')
        runner.assert_called_once();g,f=runner.call_args.args
        self.assertIs(g,f.game);self.assertEqual((g.stage_number,len(f.run.receipts)),(13,2))
        self.assertIn('AUTOMATED real Stage11/12',output.getvalue());self.assertIn('No synthetic receipts',output.getvalue())
