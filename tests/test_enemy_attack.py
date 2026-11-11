from dataclasses import FrozenInstanceError, replace
import unittest

from enemy_attack import EnemyAttackEvent, EnemyAttackLedger


class EnemyAttackTests(unittest.TestCase):
    def setUp(self):
        self.ledger = EnemyAttackLedger('combat-session', 'stage-run')

    def create(self, source='pawn-instance', start=10, hit=49, targets=((0, 5), (2, 5))):
        return self.ledger.create(source, start, hit, targets)

    def test_schedule_key_and_fixed_target_snapshot(self):
        cells = [[0, 5], [2, 5]]
        event = self.create(targets=cells)
        cells[0][0] = 9
        cells.append([3, 5])
        self.assertEqual(event.target_cells, ((0, 5), (2, 5)))
        self.assertEqual((event.start_tick, event.telegraph_start_tick, event.hit_tick), (10, 10, 49))
        self.assertEqual(event.key, ('combat-session', 'stage-run', 'pawn-instance', 1))
        with self.assertRaises(FrozenInstanceError):
            event.hit_tick = 50

    def test_direct_event_construction_also_freezes_nested_cells(self):
        cells = [[1, 1]]
        event = EnemyAttackEvent(1, 'session', 'stage', 'source', 0, 0, 1, cells)
        cells[0][0] = 2
        self.assertEqual(event.target_cells, ((1, 1),))

    def test_ids_are_unique_across_sources_in_one_stage_ledger(self):
        a = self.create()
        b = self.create(source='other-pawn')
        c = self.create()
        self.assertEqual([a.attack_id, b.attack_id, c.attack_id], [1, 2, 3])
        self.assertEqual(len({a.key, b.key, c.key}), 3)

    def test_due_transition_happens_once_at_hit_tick_without_auto_consume(self):
        event = self.create()
        self.assertFalse(self.ledger.mark_due(event, 48))
        self.assertEqual(self.ledger.state(event), 'telegraph')
        self.assertTrue(self.ledger.mark_due(event, 49))
        self.assertEqual(self.ledger.state(event), 'due')
        self.assertFalse(self.ledger.mark_due(event, 49))
        self.assertFalse(self.ledger.mark_due(event, 50))
        self.assertTrue(self.ledger.consume(event, 'player-instance'))

    def test_same_event_target_can_only_be_consumed_once(self):
        event = self.create()
        self.assertFalse(self.ledger.consume(event, 'player-instance'))
        self.ledger.mark_due(event, 49)
        self.assertTrue(self.ledger.consume(event, 'player-instance'))
        self.assertFalse(self.ledger.consume(event, 'player-instance'))
        self.assertTrue(self.ledger.consume(event, 'another-target'))
        self.assertFalse(self.ledger.consume(event, 'another-target'))

    def test_distinct_events_have_distinct_receipts_for_same_target(self):
        a, b = self.create(), self.create()
        self.ledger.mark_due(a, 49)
        self.ledger.mark_due(b, 49)
        self.assertTrue(self.ledger.consume(a, 'player'))
        self.assertTrue(self.ledger.consume(b, 'player'))

    def test_cancelled_telegraph_cannot_be_published_or_consumed(self):
        event = self.create()
        self.assertTrue(self.ledger.cancel(event))
        self.assertEqual(self.ledger.state(event), 'cancelled')
        self.assertNotIn(event, self.ledger.telegraphs)
        self.assertFalse(self.ledger.mark_due(event, 49))
        self.assertFalse(self.ledger.consume(event, 'player'))
        self.assertFalse(self.ledger.cancel(event))

    def test_cancel_after_due_preserves_tombstone_and_rejects_replay(self):
        event = self.create()
        self.ledger.mark_due(event, 49)
        self.assertTrue(self.ledger.consume(event, 'player'))
        self.assertTrue(self.ledger.cancel(event))
        self.assertFalse(self.ledger.consume(event, 'player'))
        self.assertFalse(self.ledger.consume(event, 'other-target'))
        self.assertFalse(self.ledger.mark_due(event, 100))

    def test_cancel_source_only_cancels_its_own_events(self):
        a, b, c = self.create(), self.create(), self.create(source='other-pawn')
        self.ledger.mark_due(b, 49)
        self.assertEqual(self.ledger.cancel_source('pawn-instance'), 2)
        self.assertEqual(self.ledger.cancel_source('pawn-instance'), 0)
        self.assertEqual((self.ledger.state(a), self.ledger.state(b)), ('cancelled', 'cancelled'))
        self.assertEqual(self.ledger.telegraphs, (c,))

    def test_restart_can_reuse_numeric_id_with_a_new_stage_scope(self):
        old = self.create()
        restarted = EnemyAttackLedger('combat-session', 'new-stage-run')
        new = restarted.create('pawn-instance', 10, 49, ((0, 5), (2, 5)))
        self.assertEqual((old.attack_id, new.attack_id), (1, 1))
        self.assertNotEqual(old.key, new.key)
        self.assertEqual(restarted.state(old), 'unknown')
        self.assertFalse(restarted.mark_due(old, 49))
        self.assertFalse(restarted.consume(old, 'player'))
        self.assertTrue(restarted.mark_due(new, 49))
        self.assertTrue(restarted.consume(new, 'player'))

    def test_default_ledgers_receive_fresh_session_and_stage_scopes(self):
        a, b = EnemyAttackLedger(), EnemyAttackLedger()
        self.assertNotEqual(a.combat_session_id, b.combat_session_id)
        self.assertNotEqual(a.stage_instance_id, b.stage_instance_id)

    def test_unregistered_or_changed_payload_is_not_trusted(self):
        event = self.create()
        changed = replace(event, hit_tick=50)
        unknown = replace(event, attack_id=99)
        for candidate in (changed, unknown, object(), None):
            with self.subTest(candidate=candidate):
                self.assertEqual(self.ledger.state(candidate), 'unknown')
                self.assertFalse(self.ledger.mark_due(candidate, 100))
                self.assertFalse(self.ledger.cancel(candidate))
                self.assertFalse(self.ledger.consume(candidate, 'player'))

    def test_queries_or_render_repetition_do_not_consume_or_create_events(self):
        event = self.create()
        for _ in range(100):
            self.assertEqual(self.ledger.telegraphs, (event,))
            self.assertEqual(self.ledger.state(event), 'telegraph')
        self.ledger.mark_due(event, 49)
        for _ in range(100):
            self.assertEqual(self.ledger.telegraphs, ())
            self.assertEqual(self.ledger.state(event), 'due')
        self.assertTrue(self.ledger.consume(event, 'player'))
        self.assertEqual(self.create().attack_id, 2)

    def test_invalid_targets_rejected_without_consuming_attack_id(self):
        for targets in ((), ((0, 5), (0, 5)), ((-1, 5),), ((10, 0),),
                        ((True, 5),), ((1.5, 5),), ((1, 2, 3),), (1,), None):
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                self.create(targets=targets)
        self.assertEqual(self.create().attack_id, 1)

    def test_invalid_identifiers_and_times_are_rejected(self):
        for value in ('', ' ', None, 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.create(source=value)
        for start, hit in ((0, 0), (10, 9), (-1, 10)):
            with self.subTest(start=start, hit=hit), self.assertRaises(ValueError):
                self.create(start=start, hit=hit)
        for start in (True, 1.5, '1'):
            with self.subTest(start=start), self.assertRaises(TypeError):
                self.create(start=start)
        event = self.create()
        with self.assertRaises(TypeError):
            self.ledger.mark_due(event, 49.0)
        with self.assertRaises(ValueError):
            self.ledger.consume(event, '')
        with self.assertRaises(ValueError):
            EnemyAttackLedger('', 'stage')
