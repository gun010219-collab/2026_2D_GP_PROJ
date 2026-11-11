"""Read-only input-window versus adjudicated parry feedback, without GUI."""
from copy import deepcopy
import unittest
from unittest.mock import Mock, patch

from board import tile_bounds
from config import cell_center
from enemy import Enemy
from health_renderer import HealthRenderer
from parry import Parry
from parry_renderer import ParryRenderer, ParryResultRenderer
from parry_resolution import ParryResult
from player import Player


def result(status='normal', tick=39, cell=(5, 1)):
    return ParryResult(parry_id=1, status=status, tick=tick, player_cell=cell,
                       enemy_event_key=('session', 'stage', 'pawn', 1), reason='test')


class ParryFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.renderer = ParryResultRenderer()

    def test_preview_gold_marks_never_draw_actual_success_label(self):
        parry, player = Parry(), Player(5, 1)
        parry.request(32)
        canvas = Mock()
        with patch.object(HealthRenderer, '_text') as text:
            ParryRenderer().draw(canvas, player, parry, 39)
        self.assertEqual(canvas.draw_line.call_count, 4)
        text.assert_not_called()

    def test_no_result_or_future_result_produces_no_success_feedback(self):
        for candidate, tick in ((None, 39), (result(), 38), (result('perfect'), 38)):
            with self.subTest(candidate=candidate):
                canvas = Mock()
                self.renderer.draw(canvas, candidate, tick)
                self.assertEqual(canvas.mock_calls, [])

    def test_actual_normal_and_perfect_have_distinct_labels_colors_and_shapes(self):
        for status, label, color, circles in (
                ('normal', 'PARRY SUCCESS', self.renderer.NORMAL, 0),
                ('perfect', 'PERFECT PARRY', self.renderer.PERFECT, 1)):
            with self.subTest(status=status):
                canvas = Mock()
                with patch.object(HealthRenderer, '_text') as text:
                    self.renderer.draw(canvas, result(status), 39)
                self.assertEqual(text.call_args.args[1], label)
                self.assertEqual(text.call_args.kwargs['color'], color)
                self.assertEqual(canvas.draw_circle.call_count, circles)
                self.assertEqual(canvas.draw_line.call_count, 8)
                self.assertTrue(all(call.args[4:7] == color
                                    for call in canvas.draw_line.call_args_list))

    def test_failed_or_unbound_result_never_draws_success_geometry(self):
        for status, label in (('failed', 'PARRY FAILED'), ('unbound', 'NO LINK')):
            with self.subTest(status=status):
                canvas = Mock()
                with patch.object(HealthRenderer, '_text') as text:
                    self.renderer.draw(canvas, result(status), 39)
                self.assertEqual(text.call_args.args[1], label)
                self.assertEqual(text.call_args.kwargs['color'], self.renderer.NEUTRAL)
                canvas.draw_circle.assert_not_called()
                canvas.draw_line.assert_not_called()

    def test_feedback_starts_at_result_tick_and_expires_after_eighteen_ticks(self):
        for tick, visible in ((38, False), (39, True), (56, True), (57, False)):
            with self.subTest(tick=tick):
                canvas = Mock()
                self.renderer.draw(canvas, result('perfect'), tick)
                self.assertEqual(bool(canvas.mock_calls), visible)

    def test_result_marks_use_resolved_cell_snapshot(self):
        fixed = result('perfect', cell=(1, 6))
        canvas = Mock()
        self.renderer.draw(canvas, fixed, 40)
        self.assertEqual(canvas.draw_circle.call_args.args[:2], cell_center(1, 6))

    def test_success_geometry_stays_inside_every_resolved_cell(self):
        for status in ('normal', 'perfect'):
            for col in range(10):
                for row in range(10):
                    with self.subTest(status=status, col=col, row=row):
                        canvas = Mock()
                        self.renderer.draw(canvas, result(status, cell=(col, row)), 39)
                        left, bottom, right, top = tile_bounds(col, row)
                        for call in canvas.draw_line.call_args_list:
                            x1, y1, x2, y2 = call.args[:4]
                            self.assertTrue(left < x1 < right and left < x2 < right)
                            self.assertTrue(bottom < y1 < top and bottom < y2 < top)
                        for call in canvas.draw_circle.call_args_list:
                            x, y, radius = call.args[:3]
                            self.assertTrue(left < x - radius < x + radius < right)
                            self.assertTrue(bottom < y - radius < y + radius < top)
                            self.assertFalse(call.kwargs.get('filled', False))

    def test_paused_repeated_render_leaves_result_and_state_unchanged(self):
        fixed = result('perfect')
        snapshot = deepcopy(fixed)
        first = Mock()
        self.renderer.draw(first, fixed, 40)
        for _ in range(10):
            canvas = Mock()
            self.renderer.draw(canvas, fixed, 40)
            self.assertEqual(canvas.mock_calls, first.mock_calls)
        self.assertEqual(fixed, snapshot)

    def test_feedback_allocates_no_font_texture_or_sound_resources(self):
        canvas = Mock()
        self.renderer.draw(canvas, result('perfect'), 39)
        self.assertTrue(all(call[0] in ('draw_line', 'draw_rectangle', 'draw_circle')
                            for call in canvas.mock_calls))

    def test_health_ui_reports_actual_pending_bonus_without_inventing_or_consuming_it(self):
        player = Player(5, 1)
        for bonus, expected in ((None, False), (0, False), (2, True)):
            with self.subTest(bonus=bonus), patch.object(HealthRenderer, '_text') as text:
                HealthRenderer().draw(Mock(), player, (), 39, attack_bonus=bonus)
                labels = [call.args[1] for call in text.call_args_list]
                self.assertEqual('NEXT +2' in labels, expected)
                self.assertIn('PARRY WINDOW', labels)
                self.assertNotIn('NO BLOCK YET', labels)
        self.assertEqual(player.health.current_hp, 3)

    def test_health_ui_stun_label_tracks_actual_enemy_state_and_tick(self):
        player = Player(5, 1)
        enemy = Enemy('stunned-pawn', 4, 2, (0, -1), 0)
        enemy.state = 'stunned'
        enemy.stun_until_tick = 100
        before = vars(enemy).copy()
        health_before = vars(enemy.health).copy()
        for tick, expected in ((99, True), (100, False)):
            with self.subTest(tick=tick), patch.object(HealthRenderer, '_text') as text:
                HealthRenderer().draw(Mock(), player, (enemy,), tick)
                labels = [call.args[1] for call in text.call_args_list]
                self.assertEqual('STUN' in labels, expected)
        self.assertEqual(vars(enemy), before)
        self.assertEqual(vars(enemy.health), health_before)

    def test_dead_player_does_not_display_pending_reward_as_an_action_hint(self):
        player = Player(5, 1)
        player.health.apply_damage(3, tick=39)
        with patch.object(HealthRenderer, '_text') as text:
            HealthRenderer().draw(Mock(), player, (), 39, attack_bonus=2)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertEqual(labels, ['PLAYER HP', '0/3', 'DEAD', 'INPUT LOCKED'])


if __name__ == '__main__':
    unittest.main()
