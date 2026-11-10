import unittest
from unittest.mock import Mock

from attack_renderer import AttackRenderer
from board import tile_bounds
from combat import Combat
from player import Player


class AttackRendererTests(unittest.TestCase):
    def test_all_effect_pixels_stay_in_exact_target(self):
        for col, row, facing in [(5, 1, 'up'), (5, 1, 'down'), (5, 1, 'left'),
                                  (5, 1, 'right'), (0, 8, 'up'), (8, 9, 'right')]:
            with self.subTest(col=col, row=row, facing=facing):
                attack = Combat().request_attack(Player(col, row, facing))
                left, bottom, right, top = tile_bounds(*attack.target_cell)
                canvas = Mock()
                AttackRenderer().draw(canvas, attack)
                self.assertEqual(canvas.draw_rectangle.call_args_list[0].args[:4],
                                 (left, bottom, right - 1, top - 1))
                for call in canvas.draw_rectangle.call_args_list + canvas.draw_line.call_args_list:
                    x1, y1, x2, y2 = call.args[:4]
                    self.assertTrue(all(left <= x < right for x in (x1, x2)))
                    self.assertTrue(all(bottom <= y < top for y in (y1, y2)))
                canvas.SDL_SetRenderDrawBlendMode.assert_not_called()

    def test_expired_or_rejected_attack_draws_nothing(self):
        combat = Combat()
        self.assertIsNone(combat.request_attack(Player(9, 5, 'right')))
        canvas = Mock()
        AttackRenderer().draw(canvas, combat.active_attack)
        self.assertEqual(canvas.mock_calls, [])
        combat.request_attack(Player(5, 1))
        combat.advance(combat.effect_ticks)
        AttackRenderer().draw(canvas, combat.active_attack)
        self.assertEqual(canvas.mock_calls, [])

    def test_move_and_turn_do_not_relocate_effect(self):
        combat = Combat()
        player = Player(5, 1)
        event = combat.request_attack(player)
        first, second = Mock(), Mock()
        AttackRenderer().draw(first, event)
        player.move('right')
        AttackRenderer().draw(second, event)
        self.assertEqual(first.mock_calls, second.mock_calls)
