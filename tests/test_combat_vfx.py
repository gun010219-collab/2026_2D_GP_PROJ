import pickle
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from arena_art_common import ArenaArtError
from combat_vfx import CombatVFX, MATERIALS, MAX_EFFECTS, MAX_PARTICLES
from combat_vfx_renderer import VFXRenderer, ray_ends
from main import _new_stage_game
from presentation_events import PresentationEvents
from tests.test_combat_resolution import pawn, setup
from tests.test_king_pulse import parry, pulse_battle


class CombatEffectsTests(unittest.TestCase):
    def test_direction_miss_damage_overkill_and_locked_position(self):
        for column in (5, 6):
            p,c,e,r = setup((pawn(col=column),))
            q = e.ledger.presentation = PresentationEvents()
            g = SimpleNamespace(player=p,combat=c,encounter=e)
            v = CombatVFX()
            r.player_damage = 99
            attack = c.request_attack(p)
            r.resolve_player_attack(attack)
            batch = q.drain()
            e.enemies[0].col = 8
            v.update(g,0,batch)
            self.assertEqual(v.effects[0].origin, attack.origin_cell)
            self.assertEqual(v.effects[0].cell, attack.target_cell)
            if column == 6:
                self.assertEqual([fx.name for fx in v.effects], ['player_swing'])
            else:
                self.assertEqual([fx.name for fx in v.effects], ['player_swing','player_hit','enemy_death'])
                self.assertEqual((v.effects[1].amount,v.effects[1].cell),(2,(5,2)))
            count = len(v.effects)
            v.update(g,0,batch)
            self.assertEqual(len(v.effects),count)

    def test_real_pulse_grades_and_invulnerable_outcome(self):
        for mode in ('normal','perfect','immune','failed'):
            parts = pulse_battle(hp=1)
            p,c,_,e,r = parts
            q = e.ledger.presentation = PresentationEvents()
            g = SimpleNamespace(player=p,combat=c,encounter=e)
            r.advance(1)
            v = CombatVFX()
            v.update(g,0,q.drain())
            self.assertEqual(len(v.charges),1)
            if mode=='immune':
                r.player_invulnerable_until_tick = e.pulse.event.hit_tick+1
                r.advance(120)
            else:
                parry(parts,{'normal':18,'perfect':7,'failed':19}[mode])
            batch = q.drain()
            v.update(g,.1,batch)
            self.assertFalse(v.charges)
            names = [fx.name for fx in v.effects]
            self.assertIn('king_pulse', names)
            self.assertEqual(len(next(fx.cells for fx in v.effects if fx.name=='king_pulse')),100)
            self.assertEqual('parry_normal' in names,mode=='normal')
            self.assertEqual('parry_perfect' in names,mode=='perfect')
            self.assertEqual('player_hurt' in names,mode=='failed')
            self.assertEqual('boss_death' in names,mode=='perfect')
            if mode=='perfect':
                self.assertEqual(next(fx.amount for fx in v.effects if fx.name=='player_hit'),1)
                self.assertNotEqual(v.shake(),(0,0))

    def test_ledger_charges_bishop_serialization_and_two_queen_origins(self):
        for stage in (17,24):
            g = _new_stage_game(stage)
            q = g.encounter.ledger.presentation = PresentationEvents()
            v = CombatVFX()
            observed = set()
            for _ in range(450):
                if not g.playing:
                    break
                g.advance()
                v.update(g,1/60,q.drain())
                self.assertEqual(set(v.charges), {e.key for e in g.encounter.ledger.telegraphs})
                bishops = set()
                for attack,origin,kind in v.charges.values():
                    if kind=='bishop':
                        self.assertEqual(len(attack.target_cells),50)
                        bishops.add(sum(origin)%2)
                    if kind=='queen':
                        self.assertNotIn(origin,attack.target_cells)
                        for a,b in ray_ends(origin,attack.target_cells):
                            self.assertIn(a,attack.target_cells)
                            self.assertIn(b,attack.target_cells)
                    if kind==('queen' if stage==24 else 'bishop'):
                        observed.add(attack.source_entity_instance_id)
                self.assertLessEqual(len(bishops),1)
            self.assertEqual(len(observed),2)

    def test_real_knight_trail_tracks_ground_and_lands_once(self):
        from render_motion import RenderMotion

        game = _new_stage_game(3)
        knight = next(e for e in game.encounter.enemies if e.kind=='knight')
        feed = game.encounter.ledger.presentation = PresentationEvents()
        motion, vfx = RenderMotion(), CombatVFX()
        lifts, arrivals = [], set()
        for _ in range(100):
            game.advance()
            motion.update((knight,),1/60,session=game.combat.combat_session_id)
            vfx.update(game,1/60,feed.drain(),motion=motion)
            for fx in vfx.effects:
                if fx.name=='knight_land':
                    if fx.travel_pose:
                        lifts.append(fx.travel_pose[-1])
                        self.assertEqual(lifts[-1],motion.ground_pose(knight)[1])
                    if fx.landed is not None:
                        arrivals.add(fx.landed)
        self.assertAlmostEqual(max(lifts),18)
        self.assertEqual(len(arrivals),1)

    def test_cancelled_warning_disappears_without_strike(self):
        g = _new_stage_game(13)
        q = g.encounter.ledger.presentation = PresentationEvents()
        v = CombatVFX()
        while not v.charges:
            g.advance()
            v.update(g,1/60,q.drain())
        event,_,_ = next(iter(v.charges.values()))
        g.encounter.cancel_attacks(event.source_entity_instance_id,tick=g.combat.tick)
        v.update(g,0,())
        self.assertNotIn(event.key,v.charges)
        self.assertFalse(any(fx.key[0]==event.key for fx in v.effects))

    def test_visual_time_freeze_multitick_batch_and_session_reset(self):
        g = _new_stage_game(3)
        q = g.encounter.ledger.presentation = PresentationEvents()
        v = CombatVFX()
        g.advance(85)
        batch = q.drain()
        before = pickle.dumps(g)
        v.update(g,0,batch)
        self.assertEqual([fx.name for fx in v.effects], ['knight_strike', 'knight_land'])
        self.assertAlmostEqual(v.effects[-1].start, -1/60)
        expired = CombatVFX()
        later = pickle.loads(pickle.dumps(g))
        later.advance(20)
        expired.update(later,0,batch)
        self.assertFalse(expired.effects)
        self.assertEqual(pickle.dumps(g),before)
        other = CombatVFX()
        other.update(g,0,batch)
        for _ in range(6):
            v.update(g,1/60,())
        for _ in range(18):
            other.update(g,1/180,())
        self.assertAlmostEqual(v.time,other.time)
        for elapsed,paused in ((.08,True),(3,False)):
            now=v.time
            v.update(g,elapsed,(),paused=paused)
            self.assertEqual(now,v.time)
        v.update(_new_stage_game(3),0,batch)
        self.assertFalse(v.effects or v.charges or v.seen)

    def test_main_passes_one_batch_to_independently_enabled_consumers(self):
        import os
        import sys
        import main
        from actor_animation import ActorAnimation
        from stage_progression import StageProgression
        from tests.test_main import WindowLoopTests

        for anim, effects in ((True, True), (False, True), (True, False), (False, False)):
            game = _new_stage_game(1)
            flow = StageProgression(game)
            canvas = WindowLoopTests().make_canvas()
            canvas.get_events.side_effect = [[SimpleNamespace(type=768,key=32)], [SimpleNamespace(type=256)]]
            batches = []
            drain = PresentationEvents.drain
            def record(queue):
                batch = drain(queue)
                batches.append(batch)
                return batch
            env = dict(CHECKMATE_STAGE1_ART='0', CHECKMATE_ANIMATION=str(int(anim)),
                       CHECKMATE_VFX=str(int(effects)))
            with patch.dict(os.environ,env), patch.dict(sys.modules,{'pico2d':SimpleNamespace(pico2d=canvas)}), \
                 patch.object(main,'DisplaySettings'), patch.object(main,'SettingsRenderer'), patch.object(main,'sleep'), \
                 patch.object(PresentationEvents,'drain',record), patch.object(ActorAnimation,'update') as actor, \
                 patch.object(CombatVFX,'update') as vfx:
                main.run_session(game,flow,default_art=True)
            self.assertEqual(len(batches),canvas.update_canvas.call_count if anim or effects else 0)
            for consumer,enabled in ((actor,anim),(vfx,effects)):
                self.assertEqual(consumer.call_count,len(batches) if enabled else 0)
                for call,batch in zip(consumer.call_args_list,batches):
                    self.assertIs(call.args[2],batch)
            if batches:
                self.assertEqual(sum(e.kind=='attack_start' for b in batches for e in b),1)

    def test_particle_budget_expiry_profiles_and_local_fallback(self):
        p,c,e,r = setup()
        q = e.ledger.presentation = PresentationEvents()
        g = SimpleNamespace(player=p,combat=c,encounter=e,chapter=1)
        r.resolve_player_attack(c.request_attack(p))
        batch = q.drain()
        v = CombatVFX()
        v.update(g,0,batch)
        for _ in range(200):
            v._start(g,batch[0],'boss_death','boss')
        self.assertLessEqual(len(v.effects),MAX_EFFECTS)
        self.assertLessEqual(sum(fx.particles for fx in v.effects),MAX_PARTICLES)
        self.assertIn('player_hit',[fx.name for fx in v.effects])
        self.assertEqual(len({m.fragment for m in MATERIALS.values()}),5)
        draw = VFXRenderer(v)
        with patch('combat_vfx_renderer.s.SDL_GetRenderDrawBlendMode',return_value=0), \
             patch('combat_vfx_renderer.s.SDL_SetRenderDrawBlendMode',return_value=0), \
             patch.object(draw.mesh,'flush',side_effect=ArenaArtError('injected')) as failure:
            draw.draw('labels',SimpleNamespace(renderer=None),g)
            draw.draw('labels',SimpleNamespace(renderer=None),g)
            self.assertEqual(failure.call_count,1)
        self.assertTrue(v.failed)
        v.update(_new_stage_game(3),0,batch)
        self.assertFalse(v.failed)
        v.update(g,0,batch)
        for _ in range(12):
            v.update(g,.1,())
        self.assertEqual(v.effects,[])
