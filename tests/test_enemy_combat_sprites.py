
"""Verify frame metadata and real movement receipts for the staged enemy artwork."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from actor_animation import ActorAnimation, State
from chapter_art_renderer import CHAPTER_PROFILES, LiveArenaArtPath
from combat_vfx import CombatVFX
from game_audio import AudioManager, AudioSettings
from input_controller import InputController
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from sprite_animation import SpriteCatalog, SpriteController
from sprite_atlas import DEFAULT_CATALOG
from tests.test_game_audio import FakeMixer
from tools.stage5_art_preview import open_preview


class EnemyCombatSpritesTests(TestCase):
    def setUp(self):
        self.catalog=SpriteCatalog.read(DEFAULT_CATALOG)
        self.controller=SpriteController(self.catalog)

    def test_all_chapters_have_own_atlas_and_preserve_approved_player(self):
        base=SpriteCatalog.read(DEFAULT_CATALOG.with_name('manifest_player_only.json'))
        self.assertEqual({k:c for k,c in self.catalog.clips.items() if c.design=='player'},base.clips)
        self.assertEqual({k:v for k,v in self.catalog.atlases.items() if k in base.atlases},base.atlases)
        for chapter,profile in CHAPTER_PROFILES.items():
            for kind in ('pawn','rook','knight'):
                kind_attack='pawn_contact' if kind=='pawn' else 'basic'
                choices={direction:self.catalog.clip(chapter,kind,'attack',direction,kind_attack)
                         for direction in ('up','down','left','right')}
                self.assertTrue(all(choices.values()))
                self.assertEqual({c.atlas for c in choices.values()},{f'ch{chapter}_{kind}'})
                self.assertEqual(choices['left'].frames,choices['right'].frames)
                self.assertNotEqual(choices['left'].flip_x,choices['right'].flip_x)
                self.assertNotEqual(choices['up'].frames,choices['down'].frames)
                for clip in choices.values():
                    self.assertEqual(clip.contact,3 if kind!='pawn' else None)
                    layout=profile.layout(kind,5,4)
                    for frame in clip.frames:
                        rect,label=frame.placement(layout,clip.reference_height,flip_x=clip.flip_x)
                        scale=layout['height']/256
                        x=frame.rect[2]-frame.foot[0] if clip.flip_x else frame.foot[0]
                        self.assertAlmostEqual(rect[0]+x*scale,layout['foot'][0])
                        self.assertAlmostEqual(899-rect[1]-frame.foot[1]*scale,layout['foot'][1])
                        self.assertGreaterEqual(label[1],layout['hp_y'])

    def scene(self,stage,kind):
        game=_new_stage_game(stage)
        actor=next(e for e in game.encounter.enemies if e.kind==kind)
        feed=game.encounter.ledger.presentation=PresentationEvents()
        anim=ActorAnimation(improved=True,enemy_attacks=True,player_actions=True,articulated=True,sprites=True)
        motion=RenderMotion(improved=True)
        anim.update(game,0,(),motion=motion)
        return game,actor,feed,anim,motion

    def step(self,components):
        game,actor,feed,anim,motion=components
        game.advance()
        motion.update((game.player,*game.encounter.enemies),1/60,session=game.combat.combat_session_id)
        batch=feed.drain()
        anim.update(game,1/60,batch,motion=motion)
        pose=anim.pose(game,actor,motion)
        sample=self.controller.sample(game,actor,actor.kind,anim,pose)
        return batch,pose,sample

    def test_pawn_windup_release_and_recovery_use_a_real_spear_contact(self):
        components=self.scene(1,'pawn')
        game,actor,_,_,_=components
        controls=InputController()
        seen=set()
        for _ in range(660):
            now=game.combat.tick
            if now%18==0 and now<72:
                controls.key_down('left',game.player,occupied=game.encounter.occupied_cells,tick=now)
                controls.key_up('left')
            batch,pose,sample=self.step(components)
            if sample:
                clip,frame=sample
                seen.add(clip.frames.index(frame))
                if pose.state is State.ATTACK and frame is clip.frames[2] and 'release' not in seen:
                    receipt=next(e for e in batch if e.kind=='attack_start' and e.subject==actor.entity_instance_id)
                    self.assertEqual(receipt.tick,game.combat.tick)
                    self.assertEqual(clip.facing,'down')
                    self.assertEqual(game.encounter.ledger.state(receipt.payload),'resolved')
                    seen.add('release')
            if seen=={0,1,2,3,'release'}:
                break
        self.assertEqual(seen,{0,1,2,3,'release'})

    def test_rook_and_knight_contact_switch_on_the_vfx_and_sfx_arrival_frame(self):
        for stage,kind,effect in ((6,'rook','rook_impact'),(3,'knight','knight_land')):
            with self.subTest(kind=kind):
                components=self.scene(stage,kind)
                game,actor,_,_,motion=components
                vfx=CombatVFX(layered=True)
                mixer=FakeMixer()
                audio=AudioManager(mixer,AudioSettings())
                travel_lift=0.
                for _ in range(245):
                    batch,pose,sample=self.step(components)
                    vfx.update(game,1/60,batch,motion=motion)
                    mixer.live.clear()
                    audio.update(game,1/60,batch,motion=motion)
                    if pose.attack_motion=='travel':
                        clip,frame=sample
                        self.assertIs(frame,clip.frames[clip.impact])
                        self.assertNotIn(effect,mixer.cues)
                        travel_lift=max(travel_lift,motion.ground_pose(actor)[1])
                    if pose.attack_motion=='arrival':
                        clip,frame=sample
                        self.assertIs(frame,clip.frames[clip.contact])
                        self.assertAlmostEqual(motion.ground_pose(actor)[1],0.)
                        self.assertIn(effect,mixer.cues)
                        self.assertTrue(any(f.name==effect and f.landed is not None for f in vfx.effects))
                        break
                else:
                    self.fail(f'No contact for {kind}')
                self.assertAlmostEqual(travel_lift,18. if kind=='knight' else 0.)

    def test_blocked_rook_uses_the_contact_pose_without_a_fake_dash(self):
        components=self.scene(2,'rook')
        game,actor,_,_,motion=components
        for _ in range(310):
            batch,pose,sample=self.step(components)
            blocked=next((e for e in batch if e.kind=='rook_blocked' and e.subject==actor.entity_instance_id),None)
            if blocked:
                self.assertEqual(blocked.tick,game.combat.tick)
                self.assertEqual(blocked.origin,blocked.destination)
                self.assertEqual(pose.attack_motion,'arrival')
                clip,frame=sample
                self.assertIs(frame,clip.frames[clip.contact])
                self.assertEqual(motion.ground_pose(actor)[1],0.)
                break
        else:
            self.fail('Expected the actual Stage2 blocked rook receipt')

    def test_corrupt_enemy_page_falls_back_only_for_its_own_design(self):
        from pico2d import pico2d as c

        game,actor,_,anim,motion=components=self.scene(3,'knight')
        for _ in range(85):
            _,_,sample=self.step(components)
        self.assertIsNotNone(sample)
        with TemporaryDirectory() as folder,patch.dict('os.environ',{'SDL_VIDEODRIVER':'dummy'}):
            bad=Path(folder)/'bad.png'
            bad.write_bytes(b'bad image')
            specs=dict(self.catalog.atlases)
            original=specs['ch1_knight']
            specs['ch1_knight']=replace(original,path=bad)
            catalog=replace(self.catalog,atlases=specs)
            open_preview(c,capture=True)
            art=LiveArenaArtPath(c,default_enabled=True,animation=anim,motion=motion,sprite_catalog=catalog)
            try:
                with self.assertLogs('sprite_atlas',level='WARNING'):
                    self.assertTrue(art.draw(game,motion.positions))
                renderer=art.path.renderer
                self.assertNotIn('sprite_frame',renderer.actor_layouts[actor.entity_instance_id])
                self.assertFalse(renderer.animation_failed)
                self.assertIn('actors',renderer.sprite_atlases.textures)
                self.assertIn('ch1_pawn',renderer.sprite_atlases.textures)
            finally:
                art.close()
                c.close_canvas()
                c.window=c.renderer=None
