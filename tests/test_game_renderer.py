"""Read-only, actual-outcome UI checks; not Windows GUI observations."""
import unittest
from unittest.mock import Mock, patch

import main
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
import test_game as game_tests


class GameRendererTests(unittest.TestCase):
    def ended_game(self, clear=False):
        game = main._new_game()
        if clear:
            game.player.health.apply_damage(1, tick=0)
            game_tests.kill_enemies(game)
        else:
            game.player.health.apply_damage(3, tick=0)
        game.update_state()
        return game

    def test_playing_draws_no_outcome_panel(self):
        canvas = Mock()
        with patch.object(HealthRenderer, '_text') as text:
            GameFlowRenderer().draw(canvas, main._new_game())
        text.assert_not_called()
        canvas.draw_rectangle.assert_not_called()

    def test_game_over_shows_actual_zero_hp_live_pawns_and_restart_hint(self):
        canvas, game = Mock(), self.ended_game()
        with patch.object(HealthRenderer, '_text') as text:
            GameFlowRenderer().draw(canvas, game)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertEqual(labels, ['GAME OVER', 'STAGE 1', 'HP 0/3', 'PAWNS LEFT 2/2',
                                  'R TO RESTART', 'ESC TO EXIT', 'SETTINGS / F11'])

    def test_clear_is_distinct_and_uses_actual_remaining_hp(self):
        canvas, game = Mock(), self.ended_game(clear=True)
        with patch.object(HealthRenderer, '_text') as text:
            GameFlowRenderer().draw(canvas, game)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertIn('STAGE CLEAR', labels)
        self.assertIn('HP 2/3', labels)
        self.assertIn('PAWNS LEFT 0/2', labels)
        self.assertNotIn('GAME OVER', labels)
        self.assertFalse(any('SCORE' in label or 'STAGE 2' in label for label in labels))

    def test_all_panel_and_glyph_pixels_fit_inside_the_central_board(self):
        for clear in (False, True):
            canvas = Mock()
            GameFlowRenderer().draw(canvas, self.ended_game(clear))
            for call in canvas.draw_rectangle.call_args_list:
                x1, y1, x2, y2 = call.args[:4]
                self.assertTrue(300 <= x1 <= x2 < 1140)
                self.assertTrue(30 <= y1 <= y2 < 870)

    def test_repeated_render_does_not_change_outcome_time_hp_or_receipts(self):
        game, canvas = self.ended_game(clear=True), Mock()
        before = (game.state, game.end_tick, game.transition_count, game.combat.tick,
                  game.player.health.current_hp, game.resolver.stopped,
                  len(game.encounter.ledger._records), len(game.encounter.ledger._consumed))
        for _ in range(20):
            GameFlowRenderer().draw(canvas, game)
        self.assertEqual((game.state, game.end_tick, game.transition_count, game.combat.tick,
                          game.player.health.current_hp, game.resolver.stopped,
                          len(game.encounter.ledger._records), len(game.encounter.ledger._consumed)), before)
        canvas.load_font.assert_not_called()
        canvas.SDL_CreateTextureFromSurface.assert_not_called()

    def test_terminal_hp_ui_does_not_freeze_an_active_hit_flash(self):
        game, canvas = self.ended_game(clear=True), Mock()
        with patch.object(HealthRenderer, '_text') as text:
            HealthRenderer().draw(canvas, game.player, game.encounter.enemies, game.combat.tick,
                                  show_feedback=False)
        self.assertNotIn('SHIFT TO PARRY', [c.args[1] for c in text.call_args_list])
        canvas.draw_line.assert_not_called()
        self.assertEqual(game.player.health.current_hp, 2)
