import unittest

from enemy import Enemy, load_stage1_enemies
from enemy_behaviors import PawnEncounter
from player import Player


def pawn(name='pawn', col=4, row=4, delay=0):
    return Enemy(name, col, row, (0, -1), delay, entity_instance_id=name + '-instance')


class PawnBehaviorTests(unittest.TestCase):
    def test_initial_wait_boundaries_from_json(self):
        encounter = PawnEncounter(load_stage1_enemies())
        encounter.advance_to(47, (5, 1))
        self.assertEqual([e.position for e in encounter.enemies], [(1, 6), (8, 6)])
        encounter.advance_to(48, (5, 1))
        self.assertEqual([e.position for e in encounter.enemies], [(1, 5), (8, 6)])
        encounter.advance_to(61, (5, 1))
        self.assertEqual(encounter.enemies[1].state, 'initial_wait')
        encounter.advance_to(62, (5, 1))
        self.assertEqual([e.position for e in encounter.enemies], [(1, 5), (8, 5)])

    def test_move_interval_and_blocked_last_row(self):
        # The bottom edge blocks downward movement, not all movement anymore.
        e = pawn(row=0)
        encounter = PawnEncounter((e,))
        encounter.advance_to(0, (9, 9))
        self.assertEqual(e.position, (4, 1))
        self.assertEqual(e.next_action_tick, 132)
        encounter.advance_to(131, (9, 9))
        self.assertEqual(e.position, (4, 1))
        encounter.advance_to(132, (9, 9))
        self.assertEqual(e.position, (4, 2))
        encounter.advance_to(1056, (9, 9))
        self.assertEqual(e.position, (4, 9))
        encounter.advance_to(1188, (9, 9))
        self.assertEqual(e.position, (5, 9))

    def test_attack_one_player_diagonal_not_both_cells(self):
        for target in ((3, 3), (5, 3)):
            encounter = PawnEncounter((pawn(),))
            encounter.advance_to(0, target)
            event = encounter.ledger.telegraphs[0]
            self.assertEqual(event.target_cells, (target,))
            self.assertEqual((event.start_tick, event.telegraph_start_tick, event.hit_tick), (0, 0, 39))
            self.assertEqual(encounter.enemies[0].position, (4, 4))

    def test_forward_player_blocks_move_and_is_not_attack_target(self):
        e = pawn()
        encounter = PawnEncounter((e,))
        encounter.advance_to(0, (4, 3))
        self.assertEqual(e.position, (4, 4))
        self.assertNotEqual(e.position, (4, 3))
        event, = encounter.ledger.telegraphs
        self.assertEqual((event.attack_kind, event.target_cells), ('pawn_contact', ((4, 3),)))
        self.assertEqual(e.next_action_tick, 39)

    def test_telegraph_fixed_target_and_due_once_without_auto_consume(self):
        encounter = PawnEncounter((pawn(),))
        encounter.advance_to(0, (3, 3))
        event = encounter.ledger.telegraphs[0]
        self.assertEqual(encounter.advance_to(38, (5, 3)), ())
        self.assertEqual(event.target_cells, ((3, 3),))
        self.assertEqual(encounter.advance_to(39, (5, 3)), (event,))
        self.assertEqual(encounter.advance_to(39, (5, 3)), ())
        self.assertEqual(encounter.advance_to(40, (5, 3)), ())
        self.assertEqual(encounter.ledger.telegraphs, ())
        self.assertTrue(encounter.ledger.consume(event, 'future-player-instance'))
        self.assertFalse(encounter.ledger.consume(event, 'future-player-instance'))

    def test_recovery_boundary_and_new_attack_id(self):
        e = pawn()
        encounter = PawnEncounter((e,))
        encounter.advance_to(0, (3, 3))
        first = e.current_attack
        encounter.advance_to(39, (3, 3))
        self.assertEqual(e.state, 'recovering')
        self.assertEqual(e.next_action_tick, 93)
        encounter.advance_to(92, (3, 3))
        self.assertIsNone(e.current_attack)
        encounter.advance_to(93, (3, 3))
        self.assertEqual(e.state, 'telegraph')
        self.assertNotEqual(e.current_attack.attack_id, first.attack_id)

    def test_enemy_occupancy_uses_stable_order_and_no_overlap(self):
        back, front = pawn('back', row=4), pawn('front', row=3)
        encounter = PawnEncounter((back, front))
        encounter.advance_to(0, (9, 9))
        self.assertEqual(back.position, (4, 5))
        self.assertEqual(front.position, (4, 4))
        for tick in (132, 264, 396):
            encounter.advance_to(tick, (9, 9))
            self.assertEqual(len(encounter.occupied_cells), 2)

    def test_reject_duplicate_occupancy_ids_and_player_overlap(self):
        with self.assertRaises(ValueError):
            PawnEncounter((pawn('a'), pawn('b')))
        with self.assertRaises(ValueError):
            PawnEncounter((pawn('a'), pawn('a', col=5)))
        encounter = PawnEncounter((pawn(),))
        with self.assertRaises(ValueError):
            encounter.advance_to(0, (4, 4))

    def test_deactivation_cancels_warning_and_due_delivery(self):
        e = pawn()
        encounter = PawnEncounter((e,))
        encounter.advance_to(0, (3, 3))
        event = e.current_attack
        encounter.deactivate(e.entity_instance_id)
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertEqual(encounter.advance_to(100, (3, 3)), ())
        self.assertEqual(e.state, 'inactive')
        self.assertEqual(encounter.occupied_cells, frozenset())

    def test_explicit_attack_cancel_removes_warning_and_prevents_due(self):
        encounter = PawnEncounter((pawn(),))
        encounter.advance_to(0, (3, 3))
        event = encounter.ledger.telegraphs[0]
        encounter.ledger.cancel(event)
        self.assertEqual(encounter.advance_to(40, (9, 9)), ())
        self.assertFalse(encounter.ledger.consume(event, 'player'))

    def test_chunked_ticks_match_single_tick_updates(self):
        def trace(chunks):
            e = pawn()
            encounter = PawnEncounter((e,), combat_session_id='session', stage_instance_id='stage')
            due = []
            for tick in chunks:
                due.extend(encounter.advance_to(tick, (3, 3)))
            return [(a.key, a.start_tick, a.hit_tick, a.target_cells) for a in due], e.state, e.position
        self.assertEqual(trace(range(201)), trace([0, 8, 40, 93, 200]))

    def test_enemy_blocks_player_but_turning_and_input_policy_are_preserved(self):
        player = Player(5, 1)
        self.assertFalse(player.move('right', occupied={(6, 1)}))
        self.assertEqual((player.position, player.facing), ((5, 1), 'right'))
        self.assertTrue(player.move('up', occupied={(6, 1)}))

    def test_invalid_time_and_repeated_update(self):
        encounter = PawnEncounter((pawn(),))
        encounter.advance_to(1, (9, 9))
        before = encounter.enemies[0].position
        self.assertEqual(encounter.advance_to(1, (9, 9)), ())
        self.assertEqual(encounter.enemies[0].position, before)
        for tick in (-1, True, 1.5, 0):
            with self.assertRaises(ValueError):
                encounter.advance_to(tick, (9, 9))
