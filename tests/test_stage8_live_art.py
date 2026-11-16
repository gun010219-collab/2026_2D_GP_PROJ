"""Live forest mixed display: all danger cells originate in the actual ledger."""
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
from bishop_behavior import color_targets
from config import cell_center
from render_motion import RenderMotion
import stage5_art_renderer as royal
import stage6_art_renderer as six
import stage7_art_renderer as seven
import stage8_art_renderer as art
from tools.stage8_play import session
from tests.test_stage6_live_art import canvas


class Stage8LiveArtTests(unittest.TestCase):
    def test_independent_flags_all_stages_and_prior_paths_still_observe_exits(self):
        with patch.dict(os.environ, {f'CHECKMATE_STAGE{n}_ART':'0' for n in (5,6,7,8)}):
            for flags in ((),(5,),(6,),(7,),(8,),(5,6,7,8)):
                with patch.dict(os.environ, {f'CHECKMATE_STAGE{n}_ART':'1' for n in flags}):
                    c=canvas()
                    path=art.LiveArenaArtPath(c)
                    with patch.object(royal.Stage5ArtRenderer,'draw'),patch.object(six.Stage6ArtRenderer,'draw'),patch.object(seven.Stage7ArtRenderer,'draw'),patch.object(art.Stage8ArtRenderer,'draw'):
                        for n in range(1,26):
                            self.assertEqual(path.draw(main._new_stage_game(n),{}),n in flags,(n,flags))
                    path.close()
                    expected=sum({5:8,6:7,7:7,8:9}[n] for n in flags)
                    self.assertEqual(c.load_image.call_count,expected)
                    self.assertEqual(c.SDL_DestroyTexture.call_count,expected)

    def test_original_roster_hp_profile_receipts_and_no_pulse(self):
        g,f=session()
        self.assertEqual((g.stage_number,g.chapter,g.player.position,g.boss),(8,2,(5,1),False))
        self.assertEqual([(e.data_id,e.kind,e.position,e.health.max_hp,e.initial_delay_ticks) for e in g.encounter.enemies],
                         [('s8_bishop_1','bishop',(2,8),9,48),('s8_rook_1','rook',(2,4),12,62),
                          ('s8_knight_1','knight',(3,6),9,75),('s8_pawn_1','pawn',(1,6),7,88),
                          ('s8_pawn_2','pawn',(8,6),7,101)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),44)
        self.assertEqual((len(f.run.receipts),f.run.current_stage,g.player.health.current_hp),(2,8,4))
        for e in g.encounter.enemies:
            if e.kind=='pawn':self.assertEqual(e.forward,(0,-1))
        self.assertIsNone(g.encounter.pulse)
        self.assertEqual(set(art.BASE_SIZE),{'player','pawn','rook','knight','bishop'})
        self.assertEqual(len(art.FILES),9)

    def test_bishop_source_prepared_alpha_hashes_and_prior_units_unchanged(self):
        import sdl2 as s
        from sdl2.sdlimage import IMG_Load
        from tools.prepare_stage5_art import alpha_bounds
        folder=royal.ROOT/'assets/chapter2_units'
        for name in ('asset_manifest.json','knight_manifest.json','bishop_manifest.json'):
            for row in json.loads((folder/name).read_text())['assets']:
                for f,h in ((row['file'],row['sha256']),(row['source'],row['source_sha256'])):
                    self.assertEqual(hashlib.sha256((folder/f).read_bytes()).hexdigest(),h)
        prompt=json.loads((folder/'bishop_prompt.json').read_text())
        self.assertEqual(prompt['generator'],'OpenAI built-in image_gen')
        self.assertTrue(prompt['transparent_background'])
        a=IMG_Load(str(folder/'bishop.png').encode('utf-8'))
        self.assertTrue(a)
        b=s.SDL_ConvertSurfaceFormat(a,s.SDL_PIXELFORMAT_RGBA32,0)
        try:
            box,clear=alpha_bounds(b)
            row=json.loads((folder/'bishop_manifest.json').read_text())['assets'][0]
            self.assertEqual((b.contents.w,b.contents.h),(256,256))
            self.assertEqual(list(box),row['alpha_bbox'])
            self.assertGreater(clear,0)
            self.assertEqual((box[1],box[3]),art.ALPHA_ROWS['bishop'])
        finally:s.SDL_FreeSurface(b);s.SDL_FreeSurface(a)
        for kind in ('player','pawn','rook'):
            self.assertEqual(art.actor_layout(kind,3,6),six.actor_layout(kind,3,6))
        self.assertEqual(art.actor_layout('knight',3,6),seven.actor_layout('knight',3,6))

    def test_all_fifty_bishop_cells_exactly_match_drawn_polygons(self):
        g,_=session();g.advance(48)
        event=g.encounter.enemies[0].current_attack
        self.assertEqual(len(event.target_cells),50)
        self.assertEqual(tuple(event.target_cells),color_targets((2,8)))
        r=art.Stage8ArtRenderer(canvas())
        try:
            before=pickle.dumps(g)
            with patch.object(royal,'polygon'),patch.object(r,'image'),patch.object(r,'mark',wraps=r.mark) as mark:
                r.draw(g,{})
            self.assertEqual(pickle.dumps(g),before)
            self.assertEqual(r.warning_cells,[tuple(c) for c in event.target_cells])
            self.assertEqual([call.args[0] for call in mark.call_args_list],list(event.target_cells))
            self.assertEqual({tuple(c) for c in r.warning_cells},set(event.target_cells))
            for cell in event.target_cells:self.assertEqual(CAMERA.tile(*cell),tuple(CAMERA.project(*p) for p in ((cell[0],cell[1]),(cell[0]+1,cell[1]),(cell[0]+1,cell[1]+1),(cell[0],cell[1]+1))))
        finally:r.close()

    def test_real_hit_safe_cell_and_resolution_remove_only_bishop_warning(self):
        for warned in (True,False):
            g,_=session();g.advance(48);bishop=g.encounter.enemies[0];event=bishop.current_attack
            if not warned:self.assertTrue(g.player.move('up',g.encounter.occupied_cells))
            self.assertEqual(g.player.position in event.target_cells,warned)
            hp=g.player.health.current_hp
            g.advance(event.hit_tick-g.combat.tick)
            self.assertEqual(g.player.health.current_hp,hp-int(warned))
            self.assertEqual(g.encounter.ledger.outcome(event),'hit' if warned else 'miss')
            self.assertEqual(bishop.position,(2,8))
            self.assertNotIn(event,g.encounter.ledger.telegraphs)
            r=art.Stage8ArtRenderer(canvas())
            try:
                with patch.object(royal,'polygon'),patch.object(r,'image'):r.draw(g,{})
                self.assertEqual(r.warning_cells,[tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells])
            finally:r.close()

    def test_source_death_cancels_bishop_without_erasing_other_live_attacks(self):
        g,_=session();g.advance(140);bishop=g.encounter.enemies[0];event=bishop.current_attack
        self.assertIsNotNone(event)
        others=[e for e in g.encounter.ledger.telegraphs if e.source_entity_instance_id!=bishop.entity_instance_id]
        self.assertTrue(others)
        bishop.health.apply_damage(bishop.health.current_hp,tick=g.combat.tick)
        g.encounter.deactivate(bishop.entity_instance_id,tick=g.combat.tick)
        self.assertNotIn(event,g.encounter.ledger.telegraphs)
        self.assertEqual(list(g.encounter.ledger.telegraphs),others)
        r=art.Stage8ArtRenderer(canvas())
        try:
            with patch.object(royal,'polygon'),patch.object(r,'image'):r.draw(g,{})
            self.assertNotIn(bishop.entity_instance_id,r.order)
            self.assertEqual(r.warning_cells,[tuple(c) for e in others for c in e.target_cells])
        finally:r.close()

    def test_bishop_snap_pose_and_hp_have_no_intermediate_path(self):
        g,_=session();bishop=g.encounter.enemies[0];m=RenderMotion()
        m.update((g.player,*g.encounter.enemies),0,session='snap-fixture')
        # Presentation-only displacement fixture, not an added AI teleport.
        bishop.col,bishop.row=7,7
        m.update((g.player,*g.encounter.enemies),.01,session='snap-fixture')
        self.assertEqual(m.positions[bishop.entity_instance_id],cell_center(7,7))
        self.assertEqual(m.ground_pose(bishop),(cell_center(7,7),0))
        r=art.Stage8ArtRenderer(canvas(),motion=m)
        try:
            with patch.object(royal,'polygon'),patch.object(r,'image'):r.draw(g,m.positions)
            layout=r.actor_layouts[bishop.entity_instance_id]
            self.assertEqual(layout['foot'],CAMERA.project(7.5,7.25))
            self.assertEqual(layout['hp_y'],layout['top']+art.HP_OFFSET['bishop'])
            expected=sorted((g.player,*g.encounter.enemies),key=lambda e:(-m.ground_pose(e)[0][1],m.ground_pose(e)[0][0],e.entity_instance_id))
            self.assertEqual(r.order,[e.entity_instance_id for e in expected])
        finally:r.close()

    def test_knight_jump_ground_shadow_and_all_hp_offsets_preserved(self):
        g,_=session();knight=g.encounter.enemies[2];m=RenderMotion()
        m.update((g.player,*g.encounter.enemies),0,session='jump-fixture')
        knight.col,knight.row=5,5
        m.update((g.player,*g.encounter.enemies),0,session='jump-fixture')
        m.update((g.player,*g.encounter.enemies),.05,session='jump-fixture')
        r=art.Stage8ArtRenderer(canvas(),motion=m)
        try:
            with patch.object(royal,'polygon'),patch.object(r,'image') as image:r.draw(g,m.positions)
            ground,lift=m.ground_pose(knight);self.assertAlmostEqual(lift,18)
            base=art.actor_layout('knight',(ground[0]-300)/84-.5,(ground[1]-30)/84-.5)
            shown=r.actor_layouts[knight.entity_instance_id]
            self.assertEqual(shown['foot'],base['foot'])
            self.assertAlmostEqual(shown['center'][1]-base['center'][1],18)
            self.assertAlmostEqual(shown['hp_y']-base['hp_y'],18)
            for call in image.call_args_list:
                if call.args[0] in art.BASE_SIZE:self.assertEqual(call.args[3],call.args[4])
            for kind in art.BASE_SIZE:
                for row in (0,4,8,9):
                    layout=art.actor_layout(kind,4,row)
                    self.assertGreaterEqual(layout['hp_y']-3-layout['top'],2)
                    self.assertLess(layout['hp_y']+13,900)
        finally:r.close()

    def test_genuine_bishop_normal_perfect_and_window_are_distinct(self):
        for delta,status,cue in ((18,'normal','parry_success'),(7,'perfect','perfect_success')):
            g,_=session();g.advance(48);event=g.encounter.enemies[0].current_attack
            g.advance(event.hit_tick-delta-g.combat.tick)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            self.assertEqual(royal.cue_kind(g),'parry_window')
            self.assertIsNone(g.resolver.last_parry_result)
            g.advance(delta)
            self.assertEqual(g.resolver.last_parry_result.status,status)
            self.assertEqual(g.resolver.last_parry_result.enemy_event_key,event.key)
            self.assertEqual(g.player.health.current_hp,4)
            r=art.Stage8ArtRenderer(canvas())
            try:
                with patch.object(royal,'polygon'),patch.object(r,'image'):r.draw(g,{})
                self.assertEqual(r.cue,cue)
                self.assertNotIn(event,g.encounter.ledger.telegraphs)
            finally:r.close()

    def test_live_mixed_ai_warnings_depth_and_entire_state_are_readonly(self):
        g,_=session();m=RenderMotion();r=art.Stage8ArtRenderer(canvas(),motion=m)
        saw_fifty=saw_jump=False
        try:
            with patch.object(royal,'polygon'),patch.object(r,'image'):
                for _ in range(350):
                    if g.playing:g.advance()
                    m.update((g.player,*g.encounter.enemies),1/60,session=g.combat.combat_session_id)
                    before=pickle.dumps((g,m));r.draw(g,m.positions)
                    self.assertEqual(pickle.dumps((g,m)),before)
                    self.assertEqual(r.warning_cells,[tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else [])
                    self.assertEqual(g.encounter.enemies[0].position,(2,8))
                    saw_fifty|=any(len(e.target_cells)==50 for e in g.encounter.ledger.telegraphs)
                    saw_jump|=any(v.get('elevation',0)>0 for v in r.actor_layouts.values())
                    actors=[e for e in (g.player,*g.encounter.enemies) if e.alive and getattr(e,'active',True)]
                    actors.sort(key=lambda e:(-m.ground_pose(e)[0][1],m.ground_pose(e)[0][0],e.entity_instance_id))
                    self.assertEqual(r.order,[e.entity_instance_id for e in actors])
            self.assertTrue(saw_fifty and saw_jump)
        finally:r.close()

    def test_missing_asset_partial_load_fallback_once_and_program_errors_propagate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for key,name in art.FILES.items():
                if key!='bishop':
                    (root/name).parent.mkdir(parents=True,exist_ok=True);(root/name).write_bytes(b'existence fixture')
            c=canvas()
            with self.assertRaises(FileNotFoundError):art.Stage8ArtRenderer(c,root=root)
            self.assertEqual(c.load_image.call_count,8)
            self.assertEqual(c.SDL_DestroyTexture.call_count,8)
        g,_=session()
        with patch.dict(os.environ,CHECKMATE_STAGE8_ART='1'):
            before=pickle.dumps(g);factory=Mock(side_effect=FileNotFoundError('Bishop'))
            path=art.Stage8ArtPath(canvas(),factory)
            with self.assertLogs('stage8_art_renderer',level='ERROR'):
                for _ in range(3):self.assertFalse(path.draw(g,{}))
            factory.assert_called_once();self.assertEqual(pickle.dumps(g),before)
            for error in (ArenaArtError('SDL'),TypeError('bug')):
                renderer=Mock();renderer.draw.side_effect=error;path=art.Stage8ArtPath(canvas(),lambda c,**k:renderer)
                if isinstance(error,ArenaArtError):
                    with self.assertLogs('stage8_art_renderer',level='ERROR'):self.assertFalse(path.draw(g,{}))
                    renderer.close.assert_called_once()
                else:
                    with self.assertRaises(TypeError):path.draw(g,{})

    def test_nine_textures_cached_restarted_and_released_on_stage_exit(self):
        c=canvas();path=art.Stage8ArtPath(c)
        with patch.dict(os.environ,CHECKMATE_STAGE8_ART='1'),patch.object(art.Stage8ArtRenderer,'draw'):
            g,_=session()
            for _ in range(10):self.assertTrue(path.draw(g,{}))
            self.assertEqual(c.load_image.call_count,9)
            path.draw(session()[0],{});self.assertEqual(c.SDL_DestroyTexture.call_count,9)
            self.assertFalse(path.draw(main._new_stage_game(9),{}));path.close();path.close()
            self.assertEqual(c.load_image.call_count,18);self.assertEqual(c.SDL_DestroyTexture.call_count,18)

    def test_real_battle_clear_upgrade_to_nine_and_game_over_restarts_six(self):
        from tests.test_hp_carryover import fight
        from tests.test_stage_transition import finish
        g,flow=session();r=art.Stage8ArtRenderer(canvas());native=g.resolve_current_tick
        def resolve_and_render():
            native()
            with patch.object(royal,'polygon'),patch.object(r,'image'):r.draw(g,{})
        try:
            with patch.object(g,'resolve_current_tick',resolve_and_render):result=fight(flow)
            self.assertEqual(result,(8,'UPGRADE',669,4,4))
            self.assertEqual(r.order,[g.player.entity_instance_id])
            offer=flow.sync_offer();g,_=flow.choose(offer,'hp',main._new_stage_game,lambda stats:None)
            self.assertEqual((g.stage_number,len(flow.run.receipts),g.player.health.current_hp,g.player.health.max_hp),(9,3,5,5))
            with patch.dict(os.environ,CHECKMATE_STAGE8_ART='1'):
                path=art.Stage8ArtPath(canvas(),Mock());self.assertFalse(path.draw(g,{}))
            g,flow=session();old=g.combat.combat_session_id;finish(g,'dead')
            g,_=flow.restart(main._new_stage_game,lambda stats:None)
            self.assertEqual((g.stage_number,len(flow.run.receipts),g.player.health.current_hp),(6,0,3))
            self.assertNotEqual(g.combat.combat_session_id,old)
        finally:r.close()

    def test_stage5_six_seven_golden_pngs_preserved(self):
        env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
        for tool,manifest in (('capture_stage5_scale.py','artifacts/stage6_c1/stage5_regression.json'),
                              ('capture_stage6_live.py','artifacts/stage6_c1/capture_manifest.json'),
                              ('capture_stage7_live.py','artifacts/stage7_c3/capture_manifest.json')):
            with tempfile.TemporaryDirectory() as d:
                run=subprocess.run([sys.executable,'tools/'+tool,'--capture-dir',d],cwd=royal.ROOT,env=env,capture_output=True,text=True,timeout=90)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                for row in json.loads((royal.ROOT/manifest).read_text())['captures']:
                    self.assertEqual(hashlib.sha256((Path(d)/row['file']).read_bytes()).hexdigest(),row['sha256'])

    def test_native_main_and_seven_live_fifty_cell_parry_captures(self):
        script=r"""
import tempfile
from pathlib import Path
from unittest.mock import patch
import sdl2 as s
from pico2d import pico2d as c
import main
from tools.stage8_play import session
from tools.stage5_art_preview import open_preview
from tools.capture_stage8_live import capture
g,f=session();frames=[0]
def events():
    frames[0]+=1
    return [] if frames[0]<5 else [type('Quit',(),{'type':s.SDL_QUIT})()]
with patch.object(c,'open_canvas',lambda w,h:open_preview(c,capture=True)),patch.object(c,'get_events',events),patch.object(main,'sleep'):
    main.run_session(g,f)
assert frames[0]==5
with tempfile.TemporaryDirectory() as d:
    capture(Path(d));assert len(list(Path(d).glob('*.png')))==7
print('STAGE8 NATIVE FIFTY CELLS OK')
"""
        run=subprocess.run([sys.executable,'-c',script],cwd=royal.ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','CHECKMATE_STAGE8_ART':'1'},capture_output=True,text=True,timeout=90)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr);self.assertIn('STAGE8 NATIVE FIFTY CELLS OK',run.stdout)
