"""Rook source baselines, geometry and definition/live-instance boundaries."""
from dataclasses import replace
import unittest

from enemy import Enemy, load_stage1_enemies
from enemy_behaviors import EnemyEncounter, PawnEncounter
from enemy_factory import create_enemy, create_stage_enemies, UnsupportedEnemyError
from rook_behavior import attack_path, choose_move
from stage_manager import StageCatalog


def rook(name='rook', col=2, row=4, delay=0):
    return Enemy(name, col, row, None, delay, kind='rook')


class RookDataTests(unittest.TestCase):
    def test_rook_has_real_kind_hp_no_pawn_direction_and_fresh_ids(self):
        a, b = rook(), rook()
        self.assertEqual((a.kind, a.position, a.forward, a.health.max_hp, a.health.current_hp),
                         ('rook', (2, 4), None, 4, 4))
        self.assertTrue(a.alive and a.active)
        self.assertNotEqual(a.data_id, a.entity_instance_id)
        self.assertNotEqual(a.entity_instance_id, b.entity_instance_id)
        self.assertIsNot(a.health, b.health)

    def test_initial_delay_uses_existing_ceil_to_ticks(self):
        self.assertEqual(rook(delay=0).initial_delay_ticks, 0)
        self.assertEqual(rook(delay=.8).initial_delay_ticks, 48)
        self.assertEqual(rook(delay=1.02).initial_delay_ticks, 62)

    def test_invalid_rook_input_rejected(self):
        for change in ({'col': True}, {'row': 10}, {'forward': (0, -1)}, {'data_id': ''},
                       {'entity_instance_id': ''}, {'initial_delay': -1},
                       {'initial_delay': float('nan')}, {'initial_delay': True}, {'kind': 'king'}):
            values = dict(data_id='r', col=2, row=4, forward=None, initial_delay=0, kind='rook')
            values.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                Enemy(**values)

    def test_stage_two_spawns_rook_then_two_pawns_with_correct_delays(self):
        stage = StageCatalog.load().get_stage(2)
        enemies = create_stage_enemies(stage)
        self.assertEqual([(e.data_id, e.kind, e.position, e.health.current_hp, e.initial_delay_ticks)
                          for e in enemies],
                         [('s2_rook_1', 'rook', (2, 4), 4, 48),
                          ('s2_pawn_1', 'pawn', (1, 6), 2, 62),
                          ('s2_pawn_2', 'pawn', (8, 6), 2, 75)])
        self.assertIsNone(enemies[0].forward)
        self.assertEqual(enemies[1].forward, (0, -1))

    def test_stage_one_factory_matches_legacy_loader(self):
        actual = create_stage_enemies(StageCatalog.load().get_stage(1))
        expected = load_stage1_enemies()
        def values(enemies):
            return [(e.data_id, e.kind, e.position, e.forward, e.initial_delay_ticks,
                     e.health.current_hp) for e in enemies]
        self.assertEqual(values(actual), values(expected))

    def test_factory_does_not_mutate_definition_or_share_runtime_state(self):
        stage = StageCatalog.load().get_stage(2)
        first, second = create_stage_enemies(stage), create_stage_enemies(stage)
        first[0].health.apply_damage(3, tick=1)
        first[0].col = 3
        self.assertEqual((stage.enemies[0].position, second[0].position, second[0].health.current_hp),
                         ((2, 4), (2, 4), 4))
        self.assertTrue({e.entity_instance_id for e in first}.isdisjoint(
            e.entity_instance_id for e in second))
        self.assertFalse(hasattr(stage.enemies[0], 'health'))
        self.assertFalse(hasattr(stage.enemies[0], 'entity_instance_id'))

    def test_unsupported_pieces_are_never_skipped_or_replaced(self):
        catalog = StageCatalog.load()
        for kind in ('queen',):
            definition = next(e for s in catalog.stages for e in s.enemies if e.kind == kind)
            with self.subTest(kind=kind), self.assertRaisesRegex(UnsupportedEnemyError, kind):
                create_enemy(definition)
        with self.assertRaises(UnsupportedEnemyError):
            create_stage_enemies(catalog.get_stage(15))

    def test_factory_rejects_wrong_object_and_unknown_options(self):
        with self.assertRaises(TypeError):
            create_enemy(rook())
        with self.assertRaises(TypeError):
            create_stage_enemies(2)
        definition = StageCatalog.load().get_stage(2).enemies[0]
        with self.assertRaises(UnsupportedEnemyError):
            create_enemy(replace(definition, options={'forward': (0, -1)}))

    def test_factory_rejects_duplicate_or_player_overlapping_spawns(self):
        stage = StageCatalog.load().get_stage(2)
        for enemies in ((stage.enemies[0], stage.enemies[0]),
                        (replace(stage.enemies[0], col=5, row=1),)):
            with self.subTest(enemies=enemies), self.assertRaises(ValueError):
                create_stage_enemies(replace(stage, enemies=enemies))

    def test_pawn_compatibility_entry_rejects_rook(self):
        with self.assertRaises(ValueError):
            PawnEncounter((rook(),))
        with self.assertRaises(ValueError):
            EnemyEncounter((object(),))


class RookGeometryTests(unittest.TestCase):
    def test_all_four_straight_attack_paths(self):
        for target, expected in [((4, 7), ((4, 5), (4, 6), (4, 7))),
                                 ((4, 1), ((4, 3), (4, 2), (4, 1))),
                                 ((1, 4), ((3, 4), (2, 4), (1, 4))),
                                 ((7, 4), ((5, 4), (6, 4), (7, 4)))]:
            with self.subTest(target=target):
                self.assertEqual(attack_path((4, 4), target, set()), expected)

    def test_unaligned_or_overlapping_player_has_no_attack(self):
        self.assertEqual(attack_path((4, 4), (5, 5), set()), ())
        self.assertEqual(attack_path((4, 4), (4, 4), set()), ())

    def test_dash_is_not_limited_by_three_cell_reposition_range(self):
        self.assertEqual(attack_path((0, 0), (9, 0), set()), tuple((c, 0) for c in range(1, 10)))

    def test_other_piece_blocks_entire_attack_line(self):
        for blocker in ((2, 0), (5, 0), (9, 0)):
            with self.subTest(blocker=blocker):
                self.assertEqual(attack_path((0, 0), (9, 0), {blocker}), ())

    def test_blocker_behind_target_does_not_extend_or_block_attack(self):
        self.assertEqual(attack_path((0, 0), (2, 0), {(3, 0)}), ((1, 0), (2, 0)))

    def test_reposition_prefers_clear_alignment_up_down_left_right_ties(self):
        self.assertEqual(choose_move((4, 4), (6, 6), set()), (4, 6))
        self.assertEqual(choose_move((4, 4), (6, 2), set()), (4, 2))
        self.assertEqual(choose_move((4, 4), (8, 8), set()), (4, 7))

    def test_reposition_never_passes_through_or_lands_on_piece(self):
        occupied = {(4, 5), (4, 3), (3, 4)}
        self.assertEqual(choose_move((4, 4), (6, 6), occupied), (6, 4))
        self.assertEqual(choose_move((4, 4), (6, 6), occupied | {(5, 4)}), (4, 4))

    def test_reposition_stops_before_player_and_board_edges(self):
        self.assertNotEqual(choose_move((4, 4), (4, 5), set()), (4, 5))
        for origin in ((0, 0), (9, 9), (0, 9), (9, 0)):
            target = choose_move(origin, (5, 5), set())
            self.assertTrue(all(0 <= v < 10 for v in target))
            self.assertLessEqual(abs(target[0]-origin[0]) + abs(target[1]-origin[1]), 3)
            self.assertTrue(target[0] == origin[0] or target[1] == origin[1])


class RookScheduleTests(unittest.TestCase):
    def test_initial_wait_and_reposition_72_tick_boundary(self):
        enemy = rook(delay=.8)
        encounter = EnemyEncounter((enemy,))
        encounter.advance_to(47, (5, 1))
        self.assertEqual(enemy.position, (2, 4))
        encounter.advance_to(48, (5, 1))
        self.assertEqual((enemy.position, enemy.next_action_tick), ((2, 1), 120))
        encounter.advance_to(119, (5, 1))
        self.assertIsNone(enemy.current_attack)
        encounter.advance_to(120, (5, 1))
        self.assertEqual((enemy.state, enemy.current_attack.hit_tick), ('telegraph', 168))

    def test_fixed_path_48_tick_telegraph_due_once_recovery_90(self):
        enemy = rook(col=1, row=1)
        encounter = EnemyEncounter((enemy,))
        encounter.advance_to(0, (7, 1))
        event = enemy.current_attack
        self.assertEqual(event.target_cells, tuple((c, 1) for c in range(2, 8)))
        self.assertEqual(event.hit_tick, 48)
        self.assertEqual(encounter.advance_to(47, (7, 2)), ())
        self.assertEqual(event.target_cells[-1], (7, 1))
        self.assertEqual(encounter.advance_to(48, (7, 2)), (event,))
        self.assertEqual((enemy.state, enemy.next_action_tick), ('recovering', 138))
        self.assertEqual(encounter.advance_to(48, (7, 2)), ())
        self.assertEqual(enemy.position, (1, 1))  # Damage/parry adjudication owns dash completion.

    def test_stun_cancels_rook_attack_and_only_stuns_source(self):
        a, b = rook('a', 1, 1), rook('b', 1, 3)
        encounter = EnemyEncounter((a, b))
        encounter.advance_to(0, (7, 1))
        event = a.current_attack
        encounter.stun(a.entity_instance_id, 0)
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertEqual((a.state, a.stun_until_tick), ('stunned', 60))
        self.assertNotEqual(b.state, 'stunned')
        encounter.advance_to(59, (7, 1))
        self.assertEqual(a.position, (1, 1))
        encounter.advance_to(60, (7, 1))
        self.assertEqual((a.state, a.current_attack.start_tick), ('telegraph', 60))

    def test_dead_rook_releases_occupancy_cancels_without_stopping_pawn(self):
        enemy = rook(col=1, row=1)
        pawn = Enemy('p', 8, 6, (0, -1), .8)
        encounter = EnemyEncounter((enemy, pawn))
        encounter.advance_to(0, (7, 1))
        event = enemy.current_attack
        enemy.health.apply_damage(4, tick=1)
        encounter.advance_to(48, (7, 1))
        self.assertFalse(enemy.active)
        self.assertNotIn((1, 1), encounter.occupied_cells)
        self.assertEqual(encounter.ledger.state(event), 'cancelled')
        self.assertNotEqual(pawn.position, (8, 6))


if __name__ == '__main__':
    unittest.main()
