
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from arena_art_common import CAMERA
from attack_vfx import ENEMY_STRIKES,STYLES,beam_segments,projected_beams,sigil,strike,wave_cells
from combat_vfx import CombatVFX,Effect,MAX_EFFECTS,MAX_PARTICLES,cue_name
from combat_vfx_renderer import VFXRenderer
from game_audio import AudioManager,AudioSettings
from main import _new_stage_game
from presentation_events import PresentationEvents
from queen_behavior import queen_ray_targets
from render_motion import RenderMotion
from tests.test_game_audio import FakeMixer


class Geometry:
    def __init__(self):
        self.commands=[]
    def stroke(self,*args):
        self.commands.append(('stroke',args))
    def tri(self,*args):
        self.commands.append(('tri',args))
    def arc(self,*args,**kwargs):
        self.commands.append(('arc',args))


class AttackVisualTests(unittest.TestCase):
    def test_five_palettes_have_distinct_geometry_as_well_as_color(self):
        fingerprints=set()
        for style in STYLES.values():
            mesh=Geometry()
            sigil(mesh,300,300,21,0,style,.7)
            fingerprints.add(tuple((op,args[:-1]) for op,args in mesh.commands))
        self.assertEqual(len(fingerprints),5)
        self.assertEqual(len({m.color for m in STYLES.values()}),5)
        self.assertLess(max(STYLES[5].shadow),42)
        self.assertGreater(STYLES[5].color[2],200)

    def test_six_piece_shapes_and_pulse_use_distinct_geometry(self):
        shapes=set()
        origin=(5,5)
        target=(6,5)
        style=STYLES[3]
        for name in ENEMY_STRIKES:
            rendered=Geometry()
            cells = (queen_ray_targets(origin) if name=='queen_fire' else
                     tuple((col,row) for col in range(10) for row in range(10))
                     if name=='king_pulse' else (target,))
            fx=Effect(name,(),origin,target,cells,0,1,0,5,0)
            strike(rendered,fx,.1,.25,style)
            self.assertGreater(len(rendered.commands),2)
            shapes.add(tuple((op,args[:-1]) for op,args in rendered.commands))
        self.assertEqual(len(shapes),7)

    def test_queen_segments_preserve_origin_exclusion_and_gaps(self):
        for origin in ((5,5),(0,0),(9,5)):
            cells=queen_ray_targets(origin)
            for dx,dy,first,last in beam_segments(origin,cells):
                self.assertGreaterEqual(first,1)
                for k in range(first,last+1):
                    self.assertIn((origin[0]+dx*k,origin[1]+dy*k),cells)
            for first,last in projected_beams(origin,cells):
                self.assertIn(CAMERA.pick(*first),cells)
                self.assertIn(CAMERA.pick(*last),cells)
        self.assertEqual(beam_segments((0,0),((2,0),(4,0),(5,0))),
                         ((1,0,2,2),(1,0,4,5)))

    def test_live_bishop_queen_and_pulse_preserve_target_cells_and_audio_keys(self):
        for stage,kind in ((17,'bishop'),(24,'queen'),(25,'king')):
            g=_new_stage_game(stage)
            feed=g.encounter.ledger.presentation=PresentationEvents()
            manager=CombatVFX(renewed=True)
            old=CombatVFX()
            mixer=FakeMixer()
            audio=AudioManager(mixer,AudioSettings())
            actors={e.entity_instance_id:e for e in g.encounter.enemies}
            launches=set()
            for _ in range(480):
                g.advance()
                batch=feed.drain()
                manager.update(g,1/60,batch)
                old.update(g,1/60,batch)
                self.assertEqual(manager.effects,old.effects)
                mixer.live.clear()
                audio.update(g,1/60,batch)
                self.assertLessEqual(len(manager.effects),MAX_EFFECTS)
                self.assertLessEqual(sum(e.particles for e in manager.effects),MAX_PARTICLES)
                for event in batch:
                    if event.kind!='attack_start' or actors[event.subject].kind!=kind:
                        continue
                    attack=event.payload
                    if kind=='king' and attack.attack_kind!='king_pulse':
                        continue
                    fx=next(f for f in manager.effects if f.key==event.key)
                    self.assertEqual(fx.origin,event.origin)
                    self.assertEqual(fx.cells,attack.target_cells)
                    self.assertEqual(len(wave_cells(fx.origin,fx.cells)),len(fx.cells))
                    if kind=='queen':
                        self.assertNotIn(fx.origin,fx.cells)
                        self.assertEqual(len(projected_beams(fx.origin,fx.cells)),8)
                    else:
                        self.assertEqual(len(fx.cells),50 if kind=='bishop' else 100)
                    self.assertIn(cue_name(event,kind),mixer.cues)
                    launches.add(event.subject)
                if len(launches)==(1 if kind=='king' else 2):
                    break
            self.assertEqual(len(launches),1 if kind=='king' else 2)

    def test_real_rook_stop_and_knight_land_remain_single_events(self):
        for stage,cue in ((6,'rook_impact'),(3,'knight_land')):
            g=_new_stage_game(stage)
            q=g.encounter.ledger.presentation=PresentationEvents()
            motion=RenderMotion(improved=True)
            effects=CombatVFX(renewed=True)
            mixer=FakeMixer()
            audio=AudioManager(mixer,AudioSettings())
            for _ in range(300):
                g.advance()
                motion.update((g.player,*g.encounter.enemies),1/60,session=g.combat.combat_session_id)
                batch=q.drain()
                effects.update(g,1/60,batch,motion=motion)
                mixer.live.clear()
                audio.update(g,1/60,batch,motion=motion)
                if cue in mixer.cues:
                    fx=next(f for f in effects.effects if f.name==cue)
                    self.assertIsNotNone(fx.landed)
                    self.assertEqual(mixer.cues.count(cue),1)
                    subject=next(e for e in g.encounter.enemies if e.entity_instance_id==fx.key[2])
                    self.assertEqual(fx.cell,subject.position)
                    self.assertAlmostEqual(motion.ground_pose(subject)[1],0)
                    break
            else:
                self.fail(f'No actual {cue}')

    def test_parry_is_last_in_front_and_sdl_uses_existing_mesh(self):

        effects=CombatVFX(renewed=True)
        effects.effects=[Effect(name,(),(1,1),(1,2),(),0,.5,0,0,0)
                         for name in ('parry_perfect','king_pulse','parry_normal','rook_strike')]
        vfx=VFXRenderer(effects)
        with patch('combat_vfx_renderer.s.SDL_GetRenderDrawBlendMode',return_value=0), \
             patch('combat_vfx_renderer.s.SDL_SetRenderDrawBlendMode',return_value=0), \
             patch.object(vfx.mesh,'flush') as flush,patch.object(vfx,'effect') as draw:
            vfx.draw('front',SimpleNamespace(renderer=Mock()),SimpleNamespace(chapter=5))
        self.assertEqual([c.args[1].name for c in draw.call_args_list],
                         ['king_pulse','rook_strike','parry_perfect','parry_normal'])
        flush.assert_called_once()
