"""Presentation-only guarantees for the local parry recoil and combat skin."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from combat_vfx import CombatVFX
from combat_vfx_renderer import VFXRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from stage5_art_renderer import Stage5ArtRenderer, cue_kind
from ui_theme import COMBAT_REGIONS
from upgrade_renderer import CARD_RECTS


class CombatFeedbackTests(unittest.TestCase):
    def test_actual_perfect_pulse_at_180hz_does_not_restart_or_move_the_viewport(self):
        game = _new_stage_game(25)
        queue = game.encounter.ledger.presentation = PresentationEvents()
        game.advance(378)
        game.resolver.register_parry(game.parry.request(game.combat.tick))
        game.advance(7)
        manager = CombatVFX(layered=True)
        batch = queue.drain()
        manager.update(game,0,batch)
        fx, = (f for f in manager.effects if f.name=='parry_perfect')
        self.assertEqual(fx.cell,game.player.position)
        self.assertEqual(cue_kind(game),'perfect_success')
        self.assertNotEqual(cue_kind(game,show_result=False),'perfect_success')
        art = SimpleNamespace(c=Mock(),vfx=VFXRenderer(manager),draw_world=Mock(),draw_feedback=Mock())
        with patch('sdl2.SDL_RenderSetViewport') as viewport:
            for frame in range(90):
                manager.update(game,1/180,batch)
                active = [f for f in manager.effects if f.name=='parry_perfect']
                self.assertEqual(active,[fx] if (frame+1)/180 < fx.duration else [])
                Stage5ArtRenderer.draw(art,game,{})
            viewport.assert_not_called()
        self.assertEqual(art.draw_world.call_count,90)
        self.assertEqual(art.draw_feedback.call_count,90)

    def test_combat_atlas_matches_card_hitboxes_and_left_margin(self):
        for rect in CARD_RECTS:
            self.assertEqual(COMBAT_REGIONS['card'][2:],(rect.width,rect.height))
        for name in ('player','boss'):
            self.assertLess(30+COMBAT_REGIONS[name][2],300)
        for x,y,w,h in COMBAT_REGIONS.values():
            self.assertTrue(0<=x<x+w<=960 and 0<=y<y+h<=1122)
