import unittest

from parry import Parry
from parry_input import ParryInput


class ParryInputTests(unittest.TestCase):
    def setUp(self):
        self.parry = Parry()
        self.input = ParryInput()

    def test_either_shift_starts_one_attempt(self):
        for key in ('left', 'right'):
            with self.subTest(key=key):
                parry, controls = Parry(), ParryInput()
                self.assertEqual(controls.key_down(key, parry, 0).parry_id, 1)
                self.assertEqual(controls.held, {key})

    def test_holding_shift_does_not_repeat_after_window_or_cooldown(self):
        first = self.input.key_down('left', self.parry, 0)
        for tick in (1, 8, 18, 60, 120):
            self.assertIsNone(self.input.key_down('left', self.parry, tick))
        self.assertIs(self.parry.last_attempt, first)

    def test_release_then_fresh_press_can_start_after_cooldown(self):
        self.input.key_down('left', self.parry, 0)
        self.input.key_up('left')
        second = self.input.key_down('left', self.parry, 60)
        self.assertEqual((second.parry_id, second.start_tick), (2, 60))

    def test_both_shift_keys_share_one_latch(self):
        first = self.input.key_down('left', self.parry, 0)
        self.assertIsNone(self.input.key_down('right', self.parry, 0))
        self.input.key_up('left')
        self.assertIsNone(self.input.key_down('left', self.parry, 60))
        self.input.key_up('left')
        self.input.key_up('right')
        self.assertEqual(self.input.key_down('right', self.parry, 60).parry_id, 2)
        self.assertEqual(first.parry_id, 1)

    def test_rejected_cooldown_press_is_consumed_not_buffered(self):
        self.input.key_down('left', self.parry, 0)
        self.input.key_up('left')
        self.assertIsNone(self.input.key_down('left', self.parry, 59))
        self.assertIsNone(self.input.key_down('left', self.parry, 60))
        self.input.key_up('left')
        self.assertEqual(self.input.key_down('left', self.parry, 60).parry_id, 2)

    def test_menu_press_needs_release_before_fresh_request(self):
        self.assertIsNone(self.input.key_down('left', self.parry, 0, blocked=True))
        self.assertIsNone(self.parry.last_attempt)
        self.assertIsNone(self.input.key_down('left', self.parry, 0))
        self.input.key_up('left')
        self.assertEqual(self.input.key_down('left', self.parry, 0).parry_id, 1)

    def test_pre_menu_held_shift_does_not_create_ghost_request(self):
        first = self.input.key_down('right', self.parry, 0)
        self.assertIsNone(self.input.key_down('right', self.parry, 60, blocked=True))
        self.assertIsNone(self.input.key_down('right', self.parry, 60))
        self.assertIs(self.parry.last_attempt, first)

    def test_menu_release_allows_later_fresh_shift(self):
        self.input.key_down('left', self.parry, 0, blocked=True)
        self.input.key_up('left')
        self.assertEqual(self.input.key_down('right', self.parry, 5).start_tick, 5)

    def test_transition_sync_does_not_synthesize_attempt(self):
        self.input.reconcile(('left', 'right'))
        self.assertIsNone(self.parry.last_attempt)
        self.assertIsNone(self.input.key_down('right', self.parry, 0))
        self.input.key_up('left')
        self.input.key_up('right')
        self.assertEqual(self.input.key_down('right', self.parry, 0).parry_id, 1)

    def test_missing_release_can_be_recovered_by_sync(self):
        self.input.key_down('left', self.parry, 0)
        self.input.reconcile(())
        self.assertEqual(self.input.held, frozenset())
        self.assertEqual(self.input.key_down('left', self.parry, 60).parry_id, 2)

    def test_unknown_keys_do_not_change_shift_state(self):
        self.assertIsNone(self.input.key_down('space', self.parry, 0))
        self.input.key_up(None)
        self.input.reconcile(('space',))
        self.assertEqual(self.input.held, frozenset())
        self.assertIsNone(self.parry.last_attempt)
