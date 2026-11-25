from collections import defaultdict
import pickle
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import os
import sys

from arena_art_common import CAMERA
from attack_telegraph import WarningGeometry, risk_at, warning_frame
from input_controller import InputController
import main
from parry_resolution import grade_for_delta
from presentation_events import PresentationEvents
from stage_progression import StageProgression
from tests import test_main


def fixture(hit=40):
    g = main._new_stage_game(1)
    source = g.encounter.enemies[0]
    ledger = g.encounter.ledger
    event = ledger.create(source.entity_instance_id,0,hit,(g.player.position,(1,1)))
    return g,ledger,event


class AttackTelegraphTests(unittest.TestCase):
    def test_progress_and_phase_boundaries_are_hit_relative(self):
        _,_,event = fixture()
        self.assertIsNone(risk_at(event,-1))
        self.assertIsNone(risk_at(event,40))
        risks = [risk_at(event,t) for t in range(40)]
        self.assertAlmostEqual(risks[0].opacity,.04)
        self.assertAlmostEqual(risks[10].opacity,.04+.40*.25**1.75)
        self.assertAlmostEqual(risks[20].opacity,.04+.40*.5**1.75)
        self.assertGreater(risks[20].opacity-risks[10].opacity,risks[10].opacity-risks[0].opacity)
        g_pulse = main._new_stage_game(25)
        king = next(enemy for enemy in g_pulse.encounter.enemies if enemy.kind=='king')
        pulse = g_pulse.encounter.ledger.create(king.entity_instance_id,0,120,((0,0),),attack_kind='king_pulse')
        self.assertAlmostEqual(risk_at(pulse,0).opacity,.05)
        self.assertAlmostEqual(risk_at(pulse,60).opacity,.05+.285*.5**1.75)
        self.assertAlmostEqual(risk_at(pulse,102).opacity,.341)
        self.assertAlmostEqual(risk_at(pulse,113).opacity,.457)
        self.assertEqual([r.progress for r in risks], [t/40 for t in range(40)])
        self.assertEqual([r.opacity for r in risks],sorted(r.opacity for r in risks))
        for delta,expected in ((19,None),(18,'normal'),(8,'normal'),(7,'perfect'),(1,'perfect')):
            self.assertEqual(risk_at(event,40-delta).grade,expected)

    def test_readout_uses_fresh_input_tick_without_claiming_success(self):
        g,_,e = fixture()
        for delta,grade,hint in ((20,None,'wait'),(19,None,'normal'),(18,'normal','normal'),
                                 (8,'normal','perfect'),(7,'perfect','perfect'),
                                 (2,'perfect','perfect'),(1,'perfect','impact')):
            g.advance(e.hit_tick-delta-g.combat.tick)
            cells,tip = warning_frame(g)
            self.assertIs(cells[g.player.position].attack,e)
            self.assertEqual(cells[g.player.position].grade,grade)
            self.assertEqual(tip.status,hint)
            self.assertEqual(tip.tick,g.combat.tick+1)
            self.assertEqual(tip.target,e.key if grade_for_delta(delta-1) else None)
        g.advance()
        self.assertNotIn(e, [risk.attack for risk in warning_frame(g)[0].values()])

    def test_timing_ring_shrinks_and_expires_on_the_ledger_tick(self):
        game,ledger,event = fixture()
        earlier = .59
        for delta in (40,19,18,8,7,1):
            game.advance(event.hit_tick-delta-game.combat.tick)
            _,hint = warning_frame(game)
            self.assertEqual(hint.ring.attack_key,event.key)
            self.assertEqual(hint.ring.ticks_left,delta)
            self.assertLess(hint.ring.radius,earlier)
            self.assertAlmostEqual(hint.ring.radius,.23+.35*delta/40)
            earlier = hint.ring.radius
        game.advance()
        self.assertIsNone(warning_frame(game)[1])
        retry,ledger,event = fixture()
        ledger.cancel(event)
        self.assertIsNone(warning_frame(retry)[1])

    def test_ring_switches_to_the_actual_link_and_keeps_blocked_styles_neutral(self):
        game,ledger,first = fixture(12)
        second = ledger.create(game.encounter.enemies[1].entity_instance_id,0,15,(game.player.position,))
        game.combat.advance(1)
        link = game.resolver.register_parry(game.parry.request(game.combat.tick))
        self.assertEqual(link.linked_enemy_event_key,first.key)
        cells,hint = warning_frame(game)
        self.assertIs(cells[game.player.position].attack,first)
        self.assertEqual(hint.ring.attack_key,second.key)
        self.assertEqual(hint.status,'cooldown')
        held = warning_frame(game,held=True)[1]
        self.assertEqual(held.status,'release')
        self.assertIsNone(held.target)
        self.assertEqual(held.ring,hint.ring)
        self.assertIsNone(warning_frame(game,blocked=True)[1])

    def test_ties_and_consumed_candidate_match_resolver(self):
        g,ledger,first = fixture(12)
        second = ledger.create(g.encounter.enemies[1].entity_instance_id,0,12,(g.player.position,(2,2)))
        cells,tip = warning_frame(g)
        self.assertEqual(set(cells),{g.player.position,(1,1),(2,2)})
        self.assertIs(cells[g.player.position].attack,first)
        self.assertEqual(tip.target,first.key)
        g.resolver.player_invulnerable_until_tick = first.hit_tick + 1
        self.assertEqual(warning_frame(g)[1].status,'immune')
        self.assertIsNone(warning_frame(g)[1].target)
        g.resolver.player_invulnerable_until_tick = first.hit_tick
        self.assertEqual(warning_frame(g)[1],tip)
        g.combat.advance(1)
        bind = g.resolver.register_parry(g.parry.request(g.combat.tick))
        self.assertEqual(tip.target,bind.linked_enemy_event_key)
        cells,tip = warning_frame(g)
        self.assertIs(cells[g.player.position].attack,first)
        self.assertIs(g.resolver.parry_target(g.combat.tick),second)
        self.assertEqual(tip.status,'cooldown')
        self.assertIsNone(tip.target)
        self.assertEqual(warning_frame(g,held=True)[1].status,'release')
        self.assertEqual(warning_frame(g,blocked=True),(cells,None))

    def test_cancel_death_and_restart_remove_overlay(self):
        g,ledger,event = fixture()
        self.assertTrue(warning_frame(g)[0])
        ledger.cancel(event)
        self.assertEqual(warning_frame(g),({},None))
        ledger.create(event.source_entity_instance_id,0,45,event.target_cells)
        g.encounter.enemies[0].health.apply_damage(100)
        self.assertEqual(warning_frame(g),({},None))
        retry = main._new_stage_game(1)
        self.assertNotEqual(g.encounter.ledger.stage_instance_id,retry.encounter.ledger.stage_instance_id)
        self.assertEqual(warning_frame(retry),({},None))

    def test_every_live_warning_agrees_with_ledger_and_observed_six_pieces(self):
        seen = set()
        for number in (1,3,4,5,14,17,24,25):
            game = main._new_stage_game(number)
            game.encounter.ledger.presentation = PresentationEvents()
            actors = {e.entity_instance_id:e for e in game.encounter.enemies}
            movement = InputController()
            for i in range(900 if number==1 else 390):
                if number==1 and i in (0,18,36,54):
                    movement.key_down('left',game.player,occupied=game.encounter.occupied_cells,tick=i)
                    movement.key_up('left')
                game.advance()
                events = tuple(game.resolver.live_telegraphs(game.combat.tick))
                cells,_ = warning_frame(game)
                self.assertEqual(set(cells),{c for e in events for c in e.target_cells})
                for event in events:
                    actor = actors[event.source_entity_instance_id]
                    seen.add(actor.kind)
                    if event.attack_kind == 'king_pulse':
                        self.assertEqual(len(event.target_cells),100)
                        self.assertLess(risk_at(event,game.combat.tick).opacity,.55)
                    elif event.attack_kind == 'queen_diagonal':
                        self.assertNotIn(actor.position,event.target_cells)
                    elif actor.kind=='bishop':
                        self.assertEqual(len(event.target_cells),50)
                if not game.playing:
                    break
        self.assertEqual(seen,{'pawn','rook','knight','bishop','queen','king'})

    def test_same_resolved_tick_across_refresh_rates_and_no_game_mutations(self):
        states = defaultdict(dict)
        for hz in (60,144,180):
            g,_,e = fixture()
            for frame in range(hz//2):
                tick = 60*frame//hz
                g.advance(tick-g.combat.tick)
                before = pickle.dumps(g)
                risks,hint = warning_frame(g)
                self.assertEqual(pickle.dumps(g),before)
                risk = risks[g.player.position]
                states[hz][tick] = (risk.progress,risk.grade,risk.opacity,hint.status)
        common = set.intersection(*(set(m) for m in states.values()))
        self.assertGreater(len(common),20)
        for tick in common:
            self.assertEqual(states[60][tick],states[144][tick])
            self.assertEqual(states[60][tick],states[180][tick])

    def test_geometry_inside_tiles_and_one_batch(self):
        geometry = WarningGeometry()
        for cell,groups in geometry.groups.items():
            for start,size,_ in groups:
                for i in range(start,start+size):
                    self.assertEqual(CAMERA.pick(geometry.xy[2*i],899-geometry.xy[2*i+1]),cell)
        g,_,e = fixture(5)
        cells,hint = warning_frame(g)
        with patch('attack_telegraph.s.SDL_GetRenderDrawBlendMode',return_value=0), \
             patch('attack_telegraph.s.SDL_SetRenderDrawBlendMode',return_value=0) as blend, \
             patch('attack_telegraph.s.SDL_RenderGeometryRaw',return_value=0) as draw:
            geometry.draw(SimpleNamespace(renderer=object()),cells,g.player.position,hint)
        draw.assert_called_once()
        self.assertEqual(blend.call_count,2)
        self.assertEqual(geometry.rgba[geometry.ring_start*4:geometry.ring_start*4+4],bytes((255,245,216,255)))

    def test_modal_focus_f11_and_legacy_gate_on_main_loop(self):
        c = test_main.WindowLoopTests().make_canvas()
        key = lambda code: SimpleNamespace(type=c.SDL_KEYDOWN,key=code)
        c.get_events.side_effect = [[],[key(c.SDLK_F11)],[],[],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=1,x=1295,y=41)],
            [key(c.SDLK_ESCAPE)],[],[SimpleNamespace(type=c.SDL_QUIT)]]
        c.SDL_GetWindowFlags.side_effect = [512,512,512,0,512,512,512,512]
        observed = []
        path = Mock()
        def create(*args,**kwargs):
            overlay = kwargs['telegraph']
            path.draw.side_effect = lambda g,p: observed.append(overlay.blocked) or True
            return path
        game,_,event = fixture()
        with patch.dict(os.environ,{'CHECKMATE_TELEGRAPH':'1','CHECKMATE_AUDIO':'0'}), \
             patch.dict(sys.modules,{'pico2d':SimpleNamespace(pico2d=c)}), \
             patch('chapter_art_renderer.LiveArenaArtPath',side_effect=create), \
             patch.object(main,'DisplaySettings'),patch.object(main,'SettingsRenderer'),patch.object(main,'sleep'):
            main.run_session(game,StageProgression(game),default_art=True)
        self.assertEqual(observed,[False,True,True,True,True,True,False])

        c = test_main.WindowLoopTests().make_canvas()
        c.get_events.return_value = [SimpleNamespace(type=c.SDL_QUIT)]
        game = main._new_stage_game(1)
        with patch.dict(os.environ,{'CHECKMATE_TELEGRAPH':'legacy','CHECKMATE_AUDIO':'0'}), \
             patch.dict(sys.modules,{'pico2d':SimpleNamespace(pico2d=c)}), \
             patch('chapter_art_renderer.LiveArenaArtPath') as create, \
             patch.object(main,'DisplaySettings'),patch.object(main,'SettingsRenderer'):
            main.run_session(game,StageProgression(game),default_art=True)
        self.assertIsNone(create.call_args.kwargs['telegraph'])
