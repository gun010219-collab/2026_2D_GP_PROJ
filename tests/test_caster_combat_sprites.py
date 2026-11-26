"""Caster atlases use the same real telegraphs, releases and parries as VFX/audio."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from actor_animation import ActorAnimation, State, attack_direction
from chapter_art_renderer import CHAPTER_PROFILES, LiveArenaArtPath
from combat_vfx import CombatVFX
from game_audio import AudioManager, AudioSettings
from input_controller import InputController
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from sprite_animation import SpriteCatalog, SpriteController, cardinal
from sprite_atlas import DEFAULT_CATALOG
from tests.test_game_audio import FakeMixer
from tools.stage5_art_preview import open_preview


class CasterScene:
    def __init__(self, stage, controller):
        self.game = _new_stage_game(stage)
        self.feed = self.game.encounter.ledger.presentation = PresentationEvents()
        self.animation = ActorAnimation(improved=True, enemy_attacks=True, player_actions=True,
                                        articulated=True, sprites=True)
        self.motion = RenderMotion(improved=True)
        self.vfx = CombatVFX(layered=True)
        self.mixer = FakeMixer()
        self.audio = AudioManager(self.mixer, AudioSettings())
        self.controller = controller
        self.controls = InputController()
        self.actors = {actor.entity_instance_id:actor for actor in self.game.encounter.enemies}
        self.animation.update(self.game, 0, (), motion=self.motion)

    def step(self, keys='', parries=()):
        game = self.game
        tick = game.combat.tick
        if tick%18==0 and tick//18<len(keys):
            direction = {'U':'up','R':'right'}[keys[tick//18]]
            self.controls.key_down(direction, game.player, occupied=game.encounter.occupied_cells, tick=tick)
            self.controls.key_up(direction)
        if tick+1 in parries:
            game.combat.advance(1)
            attempt = game.parry.request(game.combat.tick)
            game.resolver.register_parry(attempt)
            game.resolve_current_tick()
        else:
            game.advance()
        pulse = game.encounter.pulse
        frozen = () if pulse is None else tuple(k for k, e in self.actors.items() if pulse.frozen(e))
        self.motion.update((game.player, *game.encounter.enemies), 1/60,
                           session=game.combat.combat_session_id, frozen=frozen)
        batch = self.feed.drain()
        self.animation.update(game, 1/60, batch, motion=self.motion)
        self.vfx.update(game, 1/60, batch, motion=self.motion)
        self.mixer.calls.clear()
        self.mixer.live.clear()
        self.audio.update(game, 1/60, batch, motion=self.motion)
        return batch

    def sample(self, actor):
        pose = self.animation.pose(self.game, actor, self.motion)
        return self.controller.sample(self.game, actor, actor.kind, self.animation, pose)


class CasterCombatSpritesTests(TestCase):
    def setUp(self):
        self.catalog = SpriteCatalog.read(DEFAULT_CATALOG)
        self.controller = SpriteController(self.catalog)

    def test_twenty_caster_pages_keep_all_approved_clips_and_king_modes_distinct(self):
        base = SpriteCatalog.read(DEFAULT_CATALOG.with_name('manifest_martial.json'))
        self.assertEqual({k:self.catalog.clips[k] for k in base.clips}, base.clips)
        self.assertEqual({k:self.catalog.atlases[k] for k in base.atlases}, base.atlases)
        extra = self.catalog.atlases.keys() - base.atlases.keys()
        self.assertEqual(len(extra), 20)
        self.assertEqual(len(self.catalog.clips)-len(base.clips), 35)
        for chapter in range(1, 6):
            for design, kind in (('bishop','basic'), ('queen','queen_diagonal'), ('king','king_pulse')):
                clip = self.catalog.clip(chapter, design, 'attack', 'neutral', kind)
                self.assertEqual((len(clip.frames),clip.impact,clip.flip_x), (4,2,False))
                self.assertEqual(clip.atlas, f'ch{chapter}_{design}' + ('_pulse' if design=='king' else ''))
                if (chapter,design) not in ((1,'queen'),(2,'queen')):
                    self.assert_planted(clip,CHAPTER_PROFILES[chapter].layout(design,5,5))
            for direction in ('left','right','up','down'):
                clip = self.catalog.clip(chapter, 'king', 'attack', direction, 'basic')
                self.assertEqual(clip.atlas, f'ch{chapter}_king_melee')
                self.assertNotEqual(clip.atlas, self.catalog.clip(chapter,'king','attack',
                                                                 'neutral','king_pulse').atlas)
                self.assert_planted(clip,CHAPTER_PROFILES[chapter].layout('king',5,5))
        for stage in range(1,11):
            self.assertNotIn('queen', {actor.kind for actor in _new_stage_game(stage).encounter.enemies})

    def assert_planted(self, clip, layout):
        scale = layout['height']/clip.reference_height
        for frame in clip.frames:
            rect, label = frame.placement(layout,clip.reference_height,flip_x=clip.flip_x)
            x = frame.rect[2]-frame.foot[0] if clip.flip_x else frame.foot[0]
            self.assertAlmostEqual(rect[0]+x*scale,layout['foot'][0])
            self.assertAlmostEqual(899-rect[1]-frame.foot[1]*scale,layout['foot'][1])
            self.assertGreaterEqual(label[1],layout['hp_y'])

    def test_bishops_charge_and_cast_on_real_serial_receipts(self):
        scene = CasterScene(12, self.controller)
        charge, casts = {}, []
        for _ in range(280):
            for event in scene.step():
                actor = scene.actors.get(event.subject)
                if not actor or actor.kind!='bishop':
                    continue
                if event.kind=='telegraph':
                    clip, frame = scene.sample(actor)
                    self.assertIs(frame,clip.frames[0])
                    self.assertIn('bishop_charge',scene.mixer.cues)
                    charge[actor.entity_instance_id] = event.origin
                if event.kind=='attack_start':
                    clip, frame = scene.sample(actor)
                    self.assertIs(frame,clip.frames[clip.impact])
                    self.assertEqual((event.payload.hit_tick, len(event.payload.target_cells)),
                                     (scene.game.combat.tick,50))
                    self.assertEqual(charge[actor.entity_instance_id],actor.position)
                    self.assertIn('bishop_cast',scene.mixer.cues)
                    self.assertTrue(any(fx.name=='bishop_cast' and fx.key[2]==event.subject
                                        for fx in scene.vfx.effects))
                    casts.append((event.tick, event.subject))
        self.assertEqual([tick for tick,_ in casts], [156,265])
        self.assertEqual(len({actor for _,actor in casts}),2)

    def test_stage24_crossing_queens_keep_independent_release_frames(self):
        scene = CasterScene(24, self.controller)
        release = []
        for _ in range(135):
            for event in scene.step():
                actor = scene.actors.get(event.subject)
                if actor and actor.kind=='queen' and event.kind=='attack_start':
                    clip, frame = scene.sample(actor)
                    self.assertIs(frame,clip.frames[2])
                    self.assertNotIn(event.origin,event.payload.target_cells)
                    self.assertIn('queen_fire',scene.mixer.cues)
                    release.append(event)
        self.assertEqual([e.tick for e in release],[121,135])
        self.assertTrue(set(release[0].payload.target_cells)&set(release[1].payload.target_cells))
        first,second = (scene.sample(scene.actors[event.subject]) for event in release)
        self.assertIs(first[1],first[0].frames[3])
        self.assertIs(second[1],second[0].frames[2])
        self.assertEqual(len({fx.key[2] for fx in scene.vfx.effects if fx.name=='queen_fire'}),2)

    def test_directional_king_melee_and_radial_pulse_sync_with_original_events(self):
        cases = ((5,'UUUUU',(164,224),240,'basic','king_strike',1),
                 (25,'',(367,),385,'king_pulse','king_pulse',100))
        for stage, keys, parries, end, mode, cue, cells in cases:
            with self.subTest(mode=mode):
                scene = CasterScene(stage, self.controller)
                for tick in range(1,end+1):
                    batch = scene.step(keys,parries)
                event, = tuple(e for e in batch if e.kind=='attack_start' and e.payload.attack_kind==mode)
                actor = scene.actors[event.subject]
                clip, frame = scene.sample(actor)
                self.assertIs(frame,clip.frames[clip.impact])
                self.assertEqual(event.tick,end)
                self.assertEqual(len(event.payload.target_cells),cells)
                self.assertEqual(clip.facing,cardinal(*attack_direction('king',event.origin,event.payload)))
                self.assertIn(cue,scene.mixer.cues)
                self.assertTrue(any(fx.name==cue for fx in scene.vfx.effects))

    def test_cancelled_queen_and_perfect_pulse_stun_keep_priority(self):
        scene = CasterScene(24, self.controller)
        warning = None
        for _ in range(135):
            scene.step()
            warning = next((e for e in scene.game.encounter.ledger.telegraphs
                            if e.attack_kind=='queen_diagonal'),None)
            if warning:
                break
        self.assertIsNotNone(warning)
        actor = scene.actors[warning.source_entity_instance_id]
        self.assertIsNotNone(scene.sample(actor))
        scene.game.encounter.ledger.cancel(warning)
        scene.animation.update(scene.game, 0, (), motion=scene.motion)
        self.assertIsNone(scene.sample(actor))

        scene = CasterScene(25, self.controller)
        king = next(a for a in scene.actors.values() if a.kind=='king')
        for _ in range(385):
            scene.step(parries=(379,))
        self.assertEqual(scene.game.resolver.last_parry_result.status,'perfect')
        self.assertEqual(king.health.max_hp-king.health.current_hp,2)
        self.assertIs(scene.animation.pose(scene.game,king,scene.motion).state,State.STUN)
        self.assertIsNone(scene.sample(king))
        self.assertIn('king_pulse',scene.mixer.cues)

    def test_missing_pulse_page_keeps_king_mesh_and_other_sprite_pages(self):
        from pico2d import pico2d as c

        scene = CasterScene(25, self.controller)
        for _ in range(378):
            scene.step(parries=(367,))
        king = next(a for a in scene.actors.values() if a.kind=='king')
        self.assertIsNotNone(scene.sample(king))
        with TemporaryDirectory() as directory, patch.dict('os.environ',{'SDL_VIDEODRIVER':'dummy'}):
            atlases = dict(self.catalog.atlases)
            name = 'ch5_king_pulse'
            atlases[name] = replace(atlases[name],path=Path(directory)/'absent.png')
            catalog = replace(self.catalog,atlases=atlases)
            open_preview(c,capture=True)
            art = LiveArenaArtPath(c,default_enabled=True,motion=scene.motion,
                                   animation=scene.animation,sprite_catalog=catalog)
            try:
                with self.assertLogs('sprite_atlas',level='WARNING'):
                    self.assertTrue(art.draw(scene.game,scene.motion.positions))
                renderer = art.path.renderer
                self.assertFalse(renderer.animation_failed)
                self.assertNotIn('sprite_frame',renderer.actor_layouts[king.entity_instance_id])
                self.assertIn('ch5_king_melee',renderer.sprite_atlases.textures)
                self.assertIn('ch5_queen',renderer.sprite_atlases.textures)
                self.assertIn('actors',renderer.sprite_atlases.textures)
            finally:
                art.close()
                c.close_canvas()
                c.window=c.renderer=None
