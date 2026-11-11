import unittest

from board import in_bounds
from enemy import Enemy, load_stage1_enemies
from enemy_behaviors import PawnEncounter


def pawn(name='pawn', col=4, row=4, delay=0):
    return Enemy(name, col, row, (0, -1), delay, entity_instance_id=name + '-instance')


class PawnTrackingTests(unittest.TestCase):
    def assert_first_move(self, player_cell, expected):
        enemy = pawn()
        encounter = PawnEncounter((enemy,))
        encounter.advance_to(0, player_cell)
        self.assertEqual(enemy.position, expected)
        self.assertEqual(enemy.forward, (0, -1))
        self.assertEqual(enemy.next_action_tick, 132)

    def test_moves_one_cell_up(self):
        self.assert_first_move((4, 8), (4, 5))

    def test_moves_one_cell_down(self):
        self.assert_first_move((4, 0), (4, 3))

    def test_moves_one_cell_left(self):
        self.assert_first_move((0, 4), (3, 4))

    def test_moves_one_cell_right(self):
        self.assert_first_move((8, 4), (5, 4))

    def test_one_action_never_moves_diagonally_or_multiple_cells(self):
        for col in range(10):
            for row in range(10):
                for target in ((0, 0), (0, 9), (9, 0), (9, 9)):
                    if (col, row) == target:
                        continue
                    with self.subTest(origin=(col, row), target=target):
                        enemy = pawn(col=col, row=row)
                        encounter = PawnEncounter((enemy,))
                        encounter.advance_to(0, target)
                        dx, dy = enemy.col - col, enemy.row - row
                        self.assertIn(abs(dx) + abs(dy), (0, 1))
                        self.assertTrue(in_bounds(*enemy.position))
                        self.assertNotEqual(enemy.position, target)

    def test_manhattan_ties_use_fixed_direction_priority(self):
        cases = (((7, 7), (4, 5)), ((1, 7), (4, 5)),
                 ((1, 1), (4, 3)), ((7, 1), (4, 3)))
        for player_cell, expected in cases:
            with self.subTest(player=player_cell):
                for _ in range(3):
                    self.assert_first_move(player_cell, expected)

    def test_blocked_preferred_direction_uses_other_closer_candidate(self):
        enemy, blocker = pawn(), pawn('blocker', row=5, delay=10)
        encounter = PawnEncounter((enemy, blocker))
        encounter.advance_to(0, (7, 7))
        self.assertEqual(enemy.position, (5, 4))
        self.assertEqual(blocker.position, (4, 5))
        self.assertEqual(len(encounter.occupied_cells), 2)

    def test_blocked_approaches_allow_unvisited_detour(self):
        enemy = pawn()
        blockers = (pawn('up', row=5, delay=10), pawn('right', col=5, delay=10))
        encounter = PawnEncounter((enemy, *blockers))
        encounter.advance_to(0, (7, 7))
        self.assertEqual(enemy.position, (4, 3))
        self.assertEqual(len(encounter.occupied_cells), 3)
        self.assertEqual(enemy.next_action_tick, 132)

    def test_player_occupied_cell_is_rejected_before_fallback(self):
        enemy = pawn()
        encounter = PawnEncounter((enemy,))
        encounter.advance_to(0, (4, 5))
        self.assertEqual(enemy.position, (4, 3))
        self.assertEqual(encounter.ledger.telegraphs, ())

    def test_all_neighbors_blocked_waits_without_duplicate_entities(self):
        enemy = pawn()
        blockers = tuple(pawn(str(i), col, row, delay=10)
                         for i, (col, row) in enumerate(((4, 5), (4, 3), (3, 4), (5, 4))))
        encounter = PawnEncounter((enemy, *blockers))
        for tick, next_tick in ((0, 132), (131, 132), (132, 264)):
            encounter.advance_to(tick, (0, 0))
            self.assertEqual(enemy.position, (4, 4))
            self.assertEqual(enemy.next_action_tick, next_tick)
            self.assertEqual(encounter.tick, tick)
            self.assertEqual(len(encounter.enemies), 5)
            self.assertEqual(len(encounter.occupied_cells), 5)
            self.assertEqual(encounter.ledger.telegraphs, ())

    def test_corner_fallback_stays_inside_board(self):
        cases = (((0, 9), (1, 9), (0, 8)), ((9, 9), (8, 9), (9, 8)),
                 ((0, 0), (1, 0), (0, 1)), ((9, 0), (8, 0), (9, 1)))
        for origin, target, expected in cases:
            with self.subTest(origin=origin):
                enemy = pawn(col=origin[0], row=origin[1])
                encounter = PawnEncounter((enemy,))
                encounter.advance_to(0, target)
                self.assertEqual(enemy.position, expected)
                self.assertTrue(in_bounds(*enemy.position))

    def test_static_context_never_revisits_cells_or_oscillates(self):
        enemy = pawn()
        encounter = PawnEncounter((enemy,))
        visited = {enemy.position}
        previous = enemy.position
        moves = 0
        # A player on row 9 cannot enter a downward Pawn attack diagonal.
        # This exercises detours and exhausted movement memory without attacks.
        for tick in range(0, 132 * 120, 132):
            encounter.advance_to(tick, (9, 9))
            if enemy.position != previous:
                self.assertNotIn(enemy.position, visited)
                visited.add(enemy.position)
                moves += 1
            self.assertTrue(in_bounds(*enemy.position))
            self.assertNotEqual(enemy.position, (9, 9))
            previous = enemy.position
        self.assertGreater(moves, 10)
        self.assertLessEqual(len(visited), 99)
        final_position = enemy.position
        encounter.advance_to(132 * 121, (9, 9))
        self.assertEqual(enemy.position, final_position)

    def test_changed_player_position_reopens_previously_visited_cell(self):
        enemy = pawn()
        encounter = PawnEncounter((enemy,))
        encounter.advance_to(0, (4, 8))
        self.assertEqual(enemy.position, (4, 5))
        encounter.advance_to(132, (4, 1))
        self.assertEqual(enemy.position, (4, 4))

    def test_changed_other_occupancy_reopens_previously_visited_cell(self):
        enemy = pawn()
        up = pawn('up', row=6, delay=10)
        upper_left = pawn('upper-left', col=3, row=6, delay=10)
        encounter = PawnEncounter((enemy, up, upper_left))
        encounter.advance_to(0, (4, 9))
        self.assertEqual(enemy.position, (4, 5))
        encounter.advance_to(132, (4, 9))
        self.assertEqual(enemy.position, (3, 5))
        encounter.deactivate(up.entity_instance_id)
        encounter.advance_to(264, (4, 9))
        self.assertEqual(enemy.position, (4, 5))
        self.assertEqual(len(encounter.occupied_cells), 2)

    def test_all_move_directions_preserve_downward_diagonal_attack(self):
        for first_target in ((4, 8), (4, 0), (0, 4), (8, 4)):
            with self.subTest(first_target=first_target):
                enemy = pawn()
                encounter = PawnEncounter((enemy,))
                encounter.advance_to(0, first_target)
                origin = enemy.position
                attack_target = (enemy.col + 1, enemy.row - 1)
                encounter.advance_to(132, attack_target)
                self.assertEqual(enemy.position, origin)
                self.assertEqual(enemy.forward, (0, -1))
                self.assertEqual(enemy.current_attack.target_cells, (attack_target,))
                self.assertEqual(enemy.current_attack.hit_tick, 171)

    def test_upward_movement_does_not_rotate_attack_to_up_diagonal(self):
        enemy = pawn()
        encounter = PawnEncounter((enemy,))
        encounter.advance_to(0, (4, 8))
        self.assertEqual(enemy.position, (4, 5))
        encounter.advance_to(132, (5, 6))
        self.assertEqual(encounter.ledger.telegraphs, ())
        self.assertEqual(enemy.position, (4, 6))
        self.assertEqual(enemy.forward, (0, -1))

    def test_attack_after_tracking_keeps_priority_warning_recovery_and_ids(self):
        enemy = pawn()
        encounter = PawnEncounter((enemy,))
        encounter.advance_to(0, (8, 4))
        self.assertEqual(enemy.position, (5, 4))
        encounter.advance_to(132, (6, 3))
        event = enemy.current_attack
        self.assertEqual((event.start_tick, event.telegraph_start_tick, event.hit_tick),
                         (132, 132, 171))
        self.assertEqual(encounter.advance_to(170, (7, 3)), ())
        self.assertEqual(event.target_cells, ((6, 3),))
        self.assertEqual(encounter.advance_to(171, (6, 3)), (event,))
        self.assertEqual(enemy.next_action_tick, 225)
        encounter.advance_to(224, (6, 3))
        self.assertIsNone(enemy.current_attack)
        encounter.advance_to(225, (6, 3))
        self.assertNotEqual(enemy.current_attack.attack_id, event.attack_id)
        self.assertEqual(enemy.position, (5, 4))

    def test_tracking_preserves_exact_132_tick_move_interval(self):
        enemy = pawn()
        encounter = PawnEncounter((enemy,))
        for tick, expected in ((0, (4, 5)), (131, (4, 5)), (132, (4, 6)),
                               (133, (4, 6)), (263, (4, 6)), (264, (4, 7))):
            encounter.advance_to(tick, (9, 9))
            self.assertEqual(enemy.position, expected)

    def test_eight_tick_chunks_match_individual_ticks_during_chase(self):
        def trace(ticks):
            enemies = (pawn('left', 1, 6, .8), pawn('right', 8, 6, 1.02))
            encounter = PawnEncounter(enemies, combat_session_id='combat', stage_instance_id='stage')
            due = []
            for tick in ticks:
                due.extend(encounter.advance_to(tick, (5, 1)))
            return ([(event.key, event.start_tick, event.hit_tick, event.target_cells) for event in due],
                    [(enemy.position, enemy.state, enemy.next_action_tick) for enemy in enemies])

        single_ticks = trace(range(2001))
        self.assertTrue(single_ticks[0])
        self.assertEqual(single_ticks, trace(range(0, 2001, 8)))

    def test_stage_one_pair_reaches_attack_positions_without_oscillation(self):
        encounter = PawnEncounter(load_stage1_enemies())
        visited = [{enemy.position} for enemy in encounter.enemies]
        previous = [enemy.position for enemy in encounter.enemies]
        due = []
        for tick in range(5001):
            due.extend(encounter.advance_to(tick, (5, 1)))
            self.assertEqual(len(encounter.occupied_cells), 2)
            self.assertNotIn((5, 1), encounter.occupied_cells)
            for index, enemy in enumerate(encounter.enemies):
                if enemy.position != previous[index]:
                    self.assertNotIn(enemy.position, visited[index])
                    self.assertEqual(abs(enemy.col - previous[index][0])
                                     + abs(enemy.row - previous[index][1]), 1)
                    visited[index].add(enemy.position)
                    previous[index] = enemy.position
        self.assertEqual(previous, [(4, 2), (6, 2)])
        self.assertEqual(len({event.key for event in due}), len(due))
        for enemy in encounter.enemies:
            self.assertTrue(any(event.source_entity_instance_id == enemy.entity_instance_id
                                for event in due))


if __name__ == '__main__':
    unittest.main()
