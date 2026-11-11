"""Enemy rendering contracts with recorded canvas calls, without Windows GUI."""
import unittest
from unittest.mock import Mock

from board import tile_bounds
from config import TILE_SIZE, cell_center
from enemy import Enemy
from enemy_attack import EnemyAttackLedger
from enemy_attack_renderer import EnemyAttackRenderer
from enemy_renderer import EnemyRenderer


class EnemyRendererTests(unittest.TestCase):
    def test_all_one_hundred_pawns_are_centered_and_inside_their_cells(self):
        for col in range(10):
            for row in range(10):
                with self.subTest(col=col, row=row):
                    enemy = Enemy(f'pawn-{col}-{row}', col, row, (0, -1), 0.8)
                    canvas = Mock()
                    EnemyRenderer().draw(canvas, (enemy,))
                    x, y = cell_center(col, row)
                    left, bottom, right, top = tile_bounds(col, row)
                    self.assertGreater(canvas.draw_circle.call_count, 0)
                    for call in canvas.draw_circle.call_args_list:
                        cx, cy, radius = call.args[:3]
                        self.assertEqual(cx, x)
                        self.assertTrue(left <= cx - radius <= cx + radius < right)
                        self.assertTrue(bottom <= cy - radius <= cy + radius < top)
                    body_covers_center = False
                    for call in canvas.draw_rectangle.call_args_list:
                        x1, y1, x2, y2 = call.args[:4]
                        self.assertEqual((x1 + x2) / 2, x)
                        body_covers_center |= x1 <= x <= x2 and y1 <= y <= y2
                        self.assertTrue(left <= x1 <= x2 < right)
                        self.assertTrue(bottom <= y1 <= y2 < top)
                    self.assertTrue(body_covers_center)
                    for call in canvas.draw_line.call_args_list:
                        x1, y1, x2, y2 = call.args[:4]
                        self.assertTrue(all(left <= px < right for px in (x1, x2)))
                        self.assertTrue(all(bottom <= py < top for py in (y1, y2)))

    def test_inactive_pawn_is_not_drawn(self):
        enemy = Enemy('inactive-pawn', 1, 6, (0, -1), 0.8)
        enemy.state = 'inactive'
        canvas = Mock()
        EnemyRenderer().draw(canvas, (enemy,))
        self.assertEqual(canvas.mock_calls, [])

    def test_pawn_rendering_does_not_move_or_change_state(self):
        enemy = Enemy('pawn', 1, 6, (0, -1), 0.8)
        before = vars(enemy).copy()
        first, second = Mock(), Mock()
        EnemyRenderer().draw(first, (enemy,))
        EnemyRenderer().draw(second, (enemy,))
        self.assertEqual(first.mock_calls, second.mock_calls)
        self.assertEqual(vars(enemy), before)


class EnemyAttackRendererTests(unittest.TestCase):
    def setUp(self):
        self.ledger = EnemyAttackLedger('render-test-session', 'render-test-stage')
        self.event = self.ledger.create('pawn-instance', 48, 87, ((0, 5), (2, 5)))

    def test_telegraph_outlines_exact_targets_and_every_pixel_stays_inside(self):
        canvas = Mock()
        EnemyAttackRenderer().draw(canvas, self.ledger)
        target_bounds = [tile_bounds(*cell) for cell in self.event.target_cells]
        outer_rectangles = []
        for call in canvas.draw_rectangle.call_args_list:
            x1, y1, x2, y2 = call.args[:4]
            self.assertFalse(call.kwargs.get('filled', False))
            if x2 - x1 + 1 == TILE_SIZE and y2 - y1 + 1 == TILE_SIZE:
                outer_rectangles.append((x1, y1, x2 + 1, y2 + 1))
        self.assertCountEqual(outer_rectangles, target_bounds)
        for call in canvas.draw_rectangle.call_args_list + canvas.draw_line.call_args_list:
            x1, y1, x2, y2 = call.args[:4]
            self.assertTrue(any(left <= x1 < right and left <= x2 < right
                                and bottom <= y1 < top and bottom <= y2 < top
                                for left, bottom, right, top in target_bounds))

    def test_danger_palette_is_red_pink_and_uses_stripes_without_filling_cells(self):
        canvas = Mock()
        EnemyAttackRenderer().draw(canvas, self.ledger)
        colors = [call.args[4:7] for call in canvas.draw_rectangle.call_args_list]
        # Red/pink warning contrasts with the gold attack and blue parry palettes.
        self.assertTrue(any(r > b > g and r - g >= 80 for r, g, b in colors))
        self.assertGreater(canvas.draw_line.call_count, len(self.event.target_cells))
        self.assertTrue(all(not call.kwargs.get('filled', False)
                            for call in canvas.draw_rectangle.call_args_list))
        canvas.SDL_SetRenderDrawBlendMode.assert_not_called()

    def test_due_or_cancelled_events_have_no_warning(self):
        self.ledger.mark_due(self.event, self.event.hit_tick)
        canvas = Mock()
        EnemyAttackRenderer().draw(canvas, self.ledger)
        self.assertEqual(canvas.mock_calls, [])
        cancelled = self.ledger.create('pawn-instance', 100, 139, ((2, 0),))
        self.ledger.cancel(cancelled)
        EnemyAttackRenderer().draw(canvas, self.ledger)
        self.assertEqual(canvas.mock_calls, [])

    def test_repeated_draw_does_not_publish_consume_or_change_event(self):
        first, second = Mock(), Mock()
        EnemyAttackRenderer().draw(first, self.ledger)
        for _ in range(20):
            canvas = Mock()
            EnemyAttackRenderer().draw(canvas, self.ledger)
            self.assertEqual(first.mock_calls, canvas.mock_calls)
        EnemyAttackRenderer().draw(second, self.ledger)
        self.assertEqual(first.mock_calls, second.mock_calls)
        self.assertEqual(self.ledger.state(self.event), 'telegraph')
        self.assertEqual(self.event.target_cells, ((0, 5), (2, 5)))
        self.assertTrue(self.ledger.mark_due(self.event, self.event.hit_tick))
        self.assertFalse(self.ledger.mark_due(self.event, self.event.hit_tick))
        # Rendering has not claimed the event for a target or advanced its ID.
        self.assertTrue(self.ledger.consume(self.event, 'player-instance'))
        self.assertFalse(self.ledger.consume(self.event, 'player-instance'))
        self.assertEqual(self.ledger.create('pawn-instance', 100, 139, ((0, 4),)).attack_id, 2)
