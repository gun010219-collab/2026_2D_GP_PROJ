import ctypes
import hashlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from combat_vfx import CombatVFX, Effect, MATERIALS, MAX_EFFECTS, MAX_PARTICLES
from health import Health
from presentation_events import PresentationEvents
from tests.test_combat_resolution import pawn, setup
from tests.test_king_pulse import parry, pulse_battle


def attack(damage, *, bonus=False, miss=False, target_hp=20):
    player, combat, encounter, resolver = setup((pawn(col=6 if miss else 5),))
    resolver.player_damage = damage
    encounter.enemies[0].health = Health(target_hp)
    game = SimpleNamespace(player=player, combat=combat, encounter=encounter, resolver=resolver)
    feed = encounter.ledger.presentation = PresentationEvents()
    if bonus:
        combat.grant_perfect_counter()
    result = resolver.resolve_player_attack(combat.request_attack(player))
    batch = feed.drain()
    effects = CombatVFX(layered=True)
    effects.update(game, 0, batch)
    return game, effects, result, batch


class BladeGrowthTests(unittest.TestCase):
    def test_basic_blade_matches_approved_vertices_in_every_chapter_and_direction(self):
        import sdl2 as s
        from combat_vfx_renderer import VFXRenderer
        renderer = VFXRenderer(CombatVFX())
        mesh = renderer.mesh
        digest = hashlib.sha256()
        for target in ((5,6),(6,5),(5,4),(4,5)):
            for name,duration,particles in (('player_swing',.19,0),('player_hit',.38,9)):
                fx = Effect(name,(),(5,5),target,(),0.,duration,int(particles>0),12,particles)
                for mat in MATERIALS.values():
                    for t in (0.,.375,.75):
                        mesh.count = 0
                        renderer.effect('front',fx,t*duration,t,mat)
                        digest.update(bytes(mesh.vertices)[:mesh.count*ctypes.sizeof(s.SDL_Vertex)])
        # Captured from the approved player geometry at f638559.
        self.assertEqual(digest.hexdigest(),'8900e7ee10db297fd56e37dea31f5124aaaa0bb032ef2beecf2c4980ff785983')

    def test_packed_ribbon_keeps_both_triangles_across_a_batch_boundary(self):
        import sdl2 as s
        from combat_vfx_renderer import Mesh
        mesh = Mesh()
        mesh.vertices = (s.SDL_Vertex*6)()
        points = ((1.5,2.),(3.,4.),(5.,6.),(7.,8.75))
        tint = (231,194,105,170)
        submitted = []
        def record(renderer,texture,vertices,count,indices,n):
            submitted.append([(p.position.x,p.position.y,bytes(p.color)) for p in vertices[:count]])
            return 0
        with patch.object(s,'SDL_RenderGeometry',record):
            mesh.tri(*points[:3],tint)
            mesh.ribbon_quad(*points,bytes(tint))
            mesh.flush()
        expected = [(x,899-y,bytes(tint)) for x,y in points]
        self.assertEqual(submitted,[expected[:3],[expected[i] for i in (0,1,2,2,1,3)]])

    def test_every_attack_value_uses_same_tier_for_swing_and_actual_hit(self):
        for damage, tier in enumerate((1,1,1,2,2,2,3,3,3,4,4,4,5,5,5,5), 1):
            with self.subTest(damage=damage):
                game, vfx, result, batch = attack(damage)
                self.assertEqual(result.amount, damage)
                self.assertEqual([(f.name,f.blade_tier) for f in vfx.effects],
                                 [('player_swing',tier),('player_hit',tier)])
                vfx.update(game, 0, batch)
                self.assertEqual([f.particles for f in vfx.effects], [0,9])

    def test_perfect_counter_and_overkill_do_not_reclassify_receipt(self):
        for damage in (3,6,9,12):
            _, vfx, result, _ = attack(damage, bonus=True)
            self.assertGreater(result.amount, damage)
            self.assertEqual([f.blade_tier for f in vfx.effects], [damage//3]*2)
        _, vfx, result, _ = attack(16, target_hp=1)
        self.assertEqual(result.amount, 1)
        self.assertEqual([f.blade_tier for f in vfx.effects], [5,5,1])

    def test_max_tier_miss_only_emits_blade_without_contact_particles(self):
        _, vfx, result, _ = attack(16, miss=True)
        self.assertIsNone(result)
        self.assertEqual([(f.name,f.blade_tier,f.particles) for f in vfx.effects],
                         [('player_swing',5,0)])

    def test_max_tier_keeps_hard_limits_and_contact_when_particles_exhausted(self):
        game, vfx, _, batch = attack(16)
        for _ in range(5):
            vfx._start(game,batch[0],'boss_death','budget')
        while len(vfx.effects) < MAX_EFFECTS:
            vfx._start(game,batch[0],'player_swing','player')
        vfx._start(game,next(event for event in batch if event.kind=='hurt'),'player_hit','pawn')
        self.assertEqual(len(vfx.effects), MAX_EFFECTS)
        self.assertEqual(sum(f.particles for f in vfx.effects), MAX_PARTICLES)
        self.assertEqual((vfx.effects[-1].blade_tier,vfx.effects[-1].particles), (5,0))

    def test_reflected_pulse_preserves_original_perfect_feedback_at_max_attack(self):
        parts = pulse_battle(hp=5)
        player, combat, _, encounter, resolver = parts
        resolver.player_damage = 16
        feed = encounter.ledger.presentation = PresentationEvents()
        resolver.advance(1)
        parry(parts,7)
        game = SimpleNamespace(player=player,combat=combat,encounter=encounter,resolver=resolver)
        vfx = CombatVFX(layered=True)
        vfx.update(game,0,feed.drain())
        self.assertIn('parry_perfect',[f.name for f in vfx.effects])
        self.assertIn('player_hit',[f.name for f in vfx.effects])
        self.assertTrue(all(f.blade_tier==1 for f in vfx.effects))
