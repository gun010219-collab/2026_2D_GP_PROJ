"""Live Stage7 display adds a split pose without altering legacy or combat."""
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
from config import cell_center
from render_motion import RenderMotion
from arena_art_common import CAMERA, ArenaArtError
import stage5_art_renderer as royal
import stage7_art_renderer as art
from tools.stage7_play import session
from tests.test_stage6_live_art import canvas


class Stage7LiveArtTests(unittest.TestCase):
    def test_independent_flags_all_twenty_five_stages(self):
        for f5, f6, f7 in (('0','0','0'), ('1','0','0'), ('0','1','0'), ('0','0','1'), ('1','1','1')):
            with patch.dict(os.environ, CHECKMATE_STAGE5_ART=f5, CHECKMATE_STAGE6_ART=f6, CHECKMATE_STAGE7_ART=f7):
                previous = Mock()
                previous.return_value.draw.side_effect = lambda g,p: g.stage_number==5 and f5=='1' or g.stage_number==6 and f6=='1'
                factory = Mock()
                path = art.LiveArenaArtPath(canvas(), previous_factory=previous, stage7_factory=factory)
                for n in range(1,26):
                    expected = n==5 and f5=='1' or n==6 and f6=='1' or n==7 and f7=='1'
                    self.assertEqual(path.draw(main._new_stage_game(n), {}), expected, (n,f5,f6,f7))
                self.assertEqual(factory.call_count, int(f7=='1'))
                self.assertEqual(previous.return_value.draw.call_count, 25)
                path.close()

    def test_real_roster_receipt_and_asset_alpha_source_provenance(self):
        from tools.prepare_stage5_art import alpha_bounds
        import sdl2 as s
        from sdl2.sdlimage import IMG_Load
        g, flow = session()
        self.assertEqual([(e.data_id,e.kind,e.position,e.health.max_hp,e.initial_delay_ticks) for e in g.encounter.enemies],
                         [('s7_knight_1','knight',(3,6),9,48),('s7_knight_2','knight',(6,6),9,62),
                          ('s7_pawn_1','pawn',(1,6),7,75),('s7_pawn_2','pawn',(8,6),7,88)])
        self.assertEqual((len(flow.run.receipts), flow.run.current_stage, g.player.health.current_hp), (1,7,3))
        self.assertIsNone(g.encounter.pulse)
        folder = royal.ROOT/'assets/chapter2_units'
        row = json.loads((folder/'knight_manifest.json').read_text())['assets'][0]
        for file,key in ((row['file'],'sha256'),(row['source'],'source_sha256')):
            self.assertEqual(hashlib.sha256((folder/file).read_bytes()).hexdigest(), row[key])
        self.assertTrue(json.loads((folder/'knight_prompt.json').read_text())['prompt'])
        a = IMG_Load(str(folder/row['file']).encode('utf-8'))
        self.assertTrue(a)
        b = s.SDL_ConvertSurfaceFormat(a, s.SDL_PIXELFORMAT_RGBA32, 0)
        try:
            box, clear = alpha_bounds(b)
            self.assertEqual((b.contents.w,b.contents.h), (256,256))
            self.assertEqual(list(box), row['alpha_bbox'])
            self.assertEqual((box[1],box[3]), art.ALPHA_ROWS['knight'])
            self.assertGreater(clear, 0)
        finally:
            s.SDL_FreeSurface(b)
            s.SDL_FreeSurface(a)
        self.assertEqual(len(art.FILES),7)
        self.assertEqual({e.kind for e in g.encounter.enemies}|{'player'}, set(art.BASE_SIZE))

    def test_ground_pose_hop_is_readonly_and_landing_returns_exact_anchor(self):
        g,_ = session()
        e = g.encounter.enemies[0]
        m = RenderMotion()
        m.update((e,),0,session='fixture')
        start = cell_center(*e.position)
        e.col, e.row = 5,5  # Motion-only L landing fixture, not a campaign measurement.
        m.update((e,),0,session='fixture')
        m.update((e,),.05,session='fixture')
        before = pickle.dumps((g,m))
        ground,lift = m.ground_pose(e)
        self.assertEqual(ground, ((start[0]+cell_center(5,5)[0])/2, (start[1]+cell_center(5,5)[1])/2))
        self.assertAlmostEqual(lift,18)
        self.assertEqual(m.positions[e.entity_instance_id], (ground[0],ground[1]+lift))
        self.assertEqual(e.position,(5,5))
        self.assertEqual(pickle.dumps((g,m)),before)
        m.update((e,),.1,session='fixture')
        self.assertEqual(m.ground_pose(e),(cell_center(5,5),0))

    def test_ground_retarget_freeze_snap_death_and_session_reset(self):
        g,_ = session()
        e = g.encounter.enemies[0]
        m = RenderMotion()
        m.update((e,),0,session='fixture')
        e.col,e.row = 5,5
        m.update((e,),0,session='fixture')
        m.update((e,),.03,session='fixture')
        ground = m.ground_pose(e)[0]
        e.col,e.row = 4,3
        m.update((e,),0,session='fixture')
        self.assertEqual(m.ground_pose(e)[0],ground)
        m.update((e,),.01,session='fixture',frozen=(e.entity_instance_id,))
        self.assertEqual(m.ground_pose(e),(cell_center(4,3),0))
        m.update((e,),.01,session='new')
        self.assertEqual(m.ground_pose(e),(cell_center(4,3),0))
        e.health.apply_damage(e.health.current_hp,tick=0)
        m.update((e,),.01,session='new')
        self.assertFalse(m.positions)
        self.assertFalse(m._ground_origins)

    def test_sprite_proportions_alpha_foot_hp_clearance_all_rows(self):
        for kind in ('player','pawn','knight'):
            for row in (0,4,6,9,3.25):
                p = art.actor_layout(kind,3,row)
                top,bottom = art.ALPHA_ROWS.get(kind,(18,238))
                self.assertEqual(p['foot'],CAMERA.project(3.5,row+.25))
                self.assertAlmostEqual(p['center'][1]-p['height']*(.5-(256-bottom)/256),p['foot'][1])
                self.assertAlmostEqual(p['top']-p['foot'][1],p['height']*(bottom-top)/256)
                self.assertGreaterEqual(p['hp_y']-3-p['top'],2)
                self.assertLess(p['hp_y']+13,900)

    def test_jump_raises_only_body_and_hp_not_shadow_ground_or_depth(self):
        g,_ = session()
        m = RenderMotion()
        m.update((g.player,*g.encounter.enemies),0,session='fixture')
        e = g.encounter.enemies[0]
        e.col,e.row = 5,5
        m.update((g.player,*g.encounter.enemies),0,session='fixture')
        m.update((g.player,*g.encounter.enemies),.05,session='fixture')
        r = art.Stage7ArtRenderer(canvas(),motion=m)
        try:
            with patch.object(royal,'polygon') as poly, patch.object(r,'image') as image:
                r.draw(g,m.positions)
                ground,lift = m.ground_pose(e)
                base = art.actor_layout('knight',(ground[0]-300)/84-.5,(ground[1]-30)/84-.5)
                shown = r.actor_layouts[e.entity_instance_id]
                self.assertEqual(shown['foot'],base['foot'])
                self.assertAlmostEqual(shown['center'][1]-base['center'][1],lift)
                self.assertAlmostEqual(shown['hp_y']-base['hp_y'],lift)
                expected = sorted((g.player,*g.encounter.enemies),
                    key=lambda a:(-m.ground_pose(a)[0][1],m.ground_pose(a)[0][0],a.entity_instance_id))
                self.assertEqual(r.order,[a.entity_instance_id for a in expected])
                shadows = [call.args[1] for call in poly.call_args_list if len(call.args[1])==8]
                index = r.order.index(e.entity_instance_id)
                self.assertAlmostEqual(sum(p[0] for p in shadows[index])/8,shown['foot'][0]+4)
                self.assertAlmostEqual(sum(p[1] for p in shadows[index])/8,shown['foot'][1]-2)
                for call in image.call_args_list:
                    if call.args[0] in art.BASE_SIZE:
                        self.assertEqual(call.args[3],call.args[4])
        finally:
            r.close()

    def test_actual_ai_warning_cells_motion_hp_and_state_immutable(self):
        g,_ = session()
        m = RenderMotion()
        r = art.Stage7ArtRenderer(canvas(),motion=m)
        lifted = warnings = 0
        try:
            with patch.object(royal,'polygon'),patch.object(r,'image'):
                for _ in range(320):
                    if g.playing:g.advance()
                    m.update((g.player,*g.encounter.enemies),1/60,session=g.combat.combat_session_id)
                    before = pickle.dumps((g,m))
                    r.draw(g,m.positions)
                    self.assertEqual(pickle.dumps((g,m)),before)
                    expected = [tuple(p) for e in g.encounter.ledger.telegraphs for p in e.target_cells] if g.playing else []
                    self.assertEqual(r.warning_cells,expected)
                    warnings += bool(expected)
                    lifted += any(p.get('elevation',0)>0 for p in r.actor_layouts.values())
                    self.assertIsNone(g.encounter.pulse)
                    self.assertEqual(set(r.order),{e.entity_instance_id for e in (g.player,*g.encounter.enemies) if e.alive and getattr(e,'active',True)})
            self.assertGreater(lifted,0)
            self.assertGreater(warnings,0)
        finally:
            r.close()

    def test_genuine_parry_input_normal_perfect_not_synthetic_success(self):
        r = art.Stage7ArtRenderer(canvas())
        try:
            for delta,status,cue in ((18,'normal','parry_success'),(7,'perfect','perfect_success')):
                g,_ = session()
                event = None
                for _ in range(600):
                    g.advance()
                    event = next((e for e in g.encounter.ledger.pending if g.player.position in e.target_cells and e.hit_tick-g.combat.tick>=18),None)
                    if event:break
                self.assertIsNotNone(event)
                g.advance(event.hit_tick-delta-g.combat.tick)
                g.resolver.register_parry(g.parry.request(g.combat.tick))
                self.assertEqual(royal.cue_kind(g),'parry_window')
                self.assertIsNone(g.resolver.last_parry_result)
                g.advance(delta)
                self.assertEqual(g.resolver.last_parry_result.status,status)
                with patch.object(royal,'polygon'),patch.object(r,'image'):
                    r.draw(g,{})
                self.assertEqual(r.cue,cue)
                g.advance(18)
                self.assertNotEqual(royal.cue_kind(g),cue)
        finally:
            r.close()

    def test_missing_knight_partial_loading_fallback_and_error_types(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for key,name in art.FILES.items():
                if key!='knight':
                    (root/name).parent.mkdir(parents=True,exist_ok=True)
                    (root/name).write_bytes(b'existence fixture')
            c = canvas()
            with self.assertRaises(FileNotFoundError):
                art.Stage7ArtRenderer(c,root=root)
            self.assertEqual(c.load_image.call_count,6)
            self.assertEqual(c.SDL_DestroyTexture.call_count,6)
        g,_ = session()
        with patch.dict(os.environ,CHECKMATE_STAGE7_ART='1'):
            factory = Mock(side_effect=FileNotFoundError('Knight missing'))
            path = art.Stage7ArtPath(canvas(),factory)
            before = pickle.dumps(g)
            with self.assertLogs('stage7_art_renderer',level='ERROR'):
                for _ in range(3):self.assertFalse(path.draw(g,{}))
            self.assertEqual(factory.call_count,1)
            self.assertEqual(pickle.dumps(g),before)
            for error,handled in ((ArenaArtError('device'),True),(TypeError('bug'),False)):
                renderer = Mock();renderer.draw.side_effect=error
                path = art.Stage7ArtPath(canvas(),lambda c,**k:renderer)
                if handled:
                    with self.assertLogs('stage7_art_renderer',level='ERROR'):self.assertFalse(path.draw(g,{}))
                    renderer.close.assert_called_once()
                else:
                    with self.assertRaises(TypeError):path.draw(g,{})

    def test_seven_textures_once_per_session_restart_exit_release(self):
        c = canvas()
        path = art.Stage7ArtPath(c)
        with patch.dict(os.environ,CHECKMATE_STAGE7_ART='1'),patch.object(art.Stage7ArtRenderer,'draw'):
            g,_ = session()
            for _ in range(10):self.assertTrue(path.draw(g,{}))
            self.assertEqual(c.load_image.call_count,7)
            path.draw(session()[0],{})
            self.assertEqual(c.SDL_DestroyTexture.call_count,7)
            self.assertFalse(path.draw(main._new_stage_game(8),{}))
            path.close();path.close()
            self.assertEqual(c.load_image.call_count,14)
            self.assertEqual(c.SDL_DestroyTexture.call_count,14)

    def test_actual_battle_clear_and_owned_upgrade_to_legacy_stage_eight(self):
        from tests.test_hp_carryover import fight
        g,flow = session()
        r = art.Stage7ArtRenderer(canvas())
        native = g.resolve_current_tick
        rendered = []
        def resolve_and_render():
            native()
            with patch.object(royal,'polygon'),patch.object(r,'image'):
                r.draw(g,{})
            rendered.append(tuple(r.order))
        try:
            with patch.object(g,'resolve_current_tick',resolve_and_render):
                result = fight(flow)
            self.assertEqual(result,(7,'UPGRADE',524,3,3))
            self.assertGreater(len(rendered),0)
            self.assertEqual(r.order,[g.player.entity_instance_id])
            self.assertFalse(r.warning_cells)
            offer=flow.sync_offer()
            next_game,_=flow.choose(offer,'hp',main._new_stage_game,lambda stats:None)
            self.assertEqual((next_game.stage_number,len(flow.run.receipts),
                              next_game.player.health.current_hp,next_game.player.health.max_hp),(8,2,4,4))
            factory=Mock()
            path=art.Stage7ArtPath(canvas(),factory)
            with patch.dict(os.environ,CHECKMATE_STAGE7_ART='1'):
                self.assertFalse(path.draw(next_game,{}))
            factory.assert_not_called()
        finally:
            r.close()

    def test_restart_receipt_hp_and_stage_eight_resource_transition(self):
        from tests.test_stage_transition import finish
        g,flow = session()
        with patch.dict(os.environ,CHECKMATE_STAGE7_ART='1'):
            factory = Mock(side_effect=lambda c,**k:Mock())
            path = art.Stage7ArtPath(canvas(),factory)
            path.draw(g,{})
            old_session=g.combat.combat_session_id
            finish(g,'dead')
            g,_=flow.restart(main._new_stage_game,lambda stats:None)
            self.assertEqual((g.stage_number,len(flow.run.receipts),g.player.health.current_hp),(6,0,3))
            self.assertNotEqual(g.combat.combat_session_id,old_session)
            self.assertFalse(path.draw(g,{}))
            g,flow=session();path.draw(g,{})
            finish(g,'clear');offer=flow.sync_offer()
            g,_=flow.choose(offer,'hp',main._new_stage_game,lambda stats:None)
            self.assertEqual((g.stage_number,len(flow.run.receipts),g.player.health.current_hp,g.player.health.max_hp),(8,2,4,4))
            self.assertFalse(path.draw(g,{}))
            self.assertEqual(factory.call_count,2)
            path.close()

    def test_stage5_and_stage6_png_golden_hashes_survive_common_hooks(self):
        env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
        for stage,tool,manifest in ((5,'capture_stage5_scale.py','stage5_regression.json'),(6,'capture_stage6_live.py','capture_manifest.json')):
            with tempfile.TemporaryDirectory() as d:
                result=subprocess.run([sys.executable,'tools/'+tool,'--capture-dir',d],cwd=royal.ROOT,env=env,capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                data=json.loads((royal.ROOT/'artifacts/stage6_c1'/manifest).read_text())
                for row in data['captures']:
                    self.assertEqual(hashlib.sha256((Path(d)/row['file']).read_bytes()).hexdigest(),row['sha256'])

    def test_native_stage7_main_and_seven_live_motion_parry_captures(self):
        script=r"""
from pathlib import Path
from unittest.mock import patch
import tempfile
import sdl2 as s
from pico2d import pico2d as c
import main
from tools.stage7_play import session
from tools.capture_stage7_live import capture
from tools.stage5_art_preview import open_preview
g,flow=session();frames=[0]
def events():
    frames[0]+=1
    return [] if frames[0]<5 else [type('Quit',(),{'type':s.SDL_QUIT})()]
with patch.object(c,'open_canvas',lambda w,h:open_preview(c,capture=True)),patch.object(c,'get_events',events),patch.object(main,'sleep'):
    main.run_session(g,flow)
assert frames[0]==5
with tempfile.TemporaryDirectory() as d:
    capture(Path(d))
    assert len(list(Path(d).glob('*.png')))==7
print('STAGE7 NATIVE MAIN AND LIVE MOTION OK')
"""
        run=subprocess.run([sys.executable,'-c',script],cwd=royal.ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','CHECKMATE_STAGE7_ART':'1'},capture_output=True,text=True,timeout=90)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertIn('STAGE7 NATIVE MAIN AND LIVE MOTION OK',run.stdout)
