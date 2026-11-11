"""Knight PDF baselines, pure L-jump geometry and live definition adapters."""
from dataclasses import replace
import unittest

from enemy import Enemy
from enemy_behaviors import EnemyEncounter, PawnEncounter
from enemy_factory import create_enemy, create_stage_enemies, UnsupportedEnemyError
from knight_behavior import KNIGHT_STEPS, choose_landing, landing_candidates
from stage_manager import StageCatalog


def knight(name='k', col=4, row=3, delay=0):
    return Enemy(name, col, row, None, delay, kind='knight')


class KnightDefinitionTests(unittest.TestCase):
    def test_actual_knight_has_hp_three_no_pawn_direction_and_fresh_runtime_ids(self):
        a, b = knight(), knight()
        self.assertEqual((a.kind, a.position, a.forward, a.health.max_hp, a.health.current_hp),
                         ('knight', (4, 3), None, 3, 3))
        self.assertTrue(a.active and a.alive)
        self.assertNotEqual(a.data_id, a.entity_instance_id)
        self.assertNotEqual(a.entity_instance_id, b.entity_instance_id)
        self.assertIsNot(a.health, b.health)

    def test_delay_uses_common_ceil_tick_conversion(self):
        self.assertEqual(knight(delay=.8).initial_delay_ticks, 48)
        self.assertEqual(knight(delay=1.02).initial_delay_ticks, 62)
        self.assertEqual(knight(delay=0).initial_delay_ticks, 0)

    def test_invalid_knight_model_fields_are_rejected(self):
        for change in ({'col': True}, {'row': 10}, {'forward': (0, -1)}, {'data_id': ''},
                       {'entity_instance_id': ''}, {'initial_delay': -1},
                       {'initial_delay': float('inf')}, {'initial_delay': True}, {'kind': 'bishop'}):
            values = dict(data_id='k', col=4, row=3, forward=None, initial_delay=0, kind='knight')
            values.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                Enemy(**values)

    def test_stage_three_original_order_positions_hp_and_delay(self):
        stage = StageCatalog.load().get_stage(3)
        enemies = create_stage_enemies(stage)
        self.assertEqual(stage.player_spawn, (5, 1))
        self.assertEqual([(e.data_id, e.kind, e.position, e.health.current_hp, e.initial_delay_ticks)
                          for e in enemies],
                         [('s3_knight_1', 'knight', (3, 6), 3, 48),
                          ('s3_pawn_1', 'pawn', (1, 6), 2, 62),
                          ('s3_pawn_2', 'pawn', (8, 6), 2, 75)])
        self.assertNotIn('forward', stage.enemies[0].options)
        self.assertIsNone(enemies[0].forward)

    def test_factory_reloads_without_definition_or_runtime_state_aliases(self):
        stage = StageCatalog.load().get_stage(3)
        first, second = create_stage_enemies(stage), create_stage_enemies(stage)
        first[0].health.apply_damage(2, tick=0)
        first[0].col = 4
        self.assertEqual((stage.enemies[0].position, second[0].position, second[0].health.current_hp),
                         ((3, 6), (3, 6), 3))
        self.assertTrue({e.entity_instance_id for e in first}.isdisjoint(e.entity_instance_id for e in second))
        self.assertFalse(hasattr(stage.enemies[0], 'health'))

    def test_bishop_queen_king_and_unknown_knight_options_are_still_rejected(self):
        catalog = StageCatalog.load()
        for kind in ('bishop', 'queen', 'king'):
            definition = next(e for s in catalog.stages for e in s.enemies if e.kind == kind)
            with self.subTest(kind=kind), self.assertRaises(UnsupportedEnemyError):
                create_enemy(definition)
        definition = catalog.get_stage(3).enemies[0]
        with self.assertRaises(UnsupportedEnemyError):
            create_enemy(replace(definition, options={'forward': (0, -1)}))

    def test_pawn_compatibility_entry_never_silently_runs_knight_as_pawn(self):
        with self.assertRaises(ValueError):
            PawnEncounter((knight(),))


class KnightGeometryTests(unittest.TestCase):
    def test_exact_eight_l_offsets_in_all_directions(self):
        self.assertEqual(set(KNIGHT_STEPS), {(dx, dy) for dx in (-2, -1, 1, 2)
                                           for dy in (-2, -1, 1, 2) if abs(dx) + abs(dy) == 3})
        cells = landing_candidates((4, 4), set())
        self.assertEqual(len(cells), 8)
        self.assertEqual(set(cells), {(4 + dx, 4 + dy) for dx, dy in KNIGHT_STEPS})

    def test_all_board_origins_return_only_distinct_in_bounds_l_landings(self):
        for col in range(10):
            for row in range(10):
                cells = landing_candidates((col, row), set())
                self.assertEqual(len(cells), len(set(cells)))
                for x, y in cells:
                    self.assertTrue(0 <= x < 10 and 0 <= y < 10)
                    self.assertEqual(sorted((abs(x - col), abs(y - row))), [1, 2])
        self.assertEqual(set(landing_candidates((0, 0), set())), {(1, 2), (2, 1)})

    def test_intermediate_pieces_do_not_block_a_jump(self):
        around = {(3, 3), (3, 4), (3, 5), (4, 3), (4, 5), (5, 3), (5, 4), (5, 5)}
        self.assertEqual(landing_candidates((4, 4), around), landing_candidates((4, 4), set()))
        self.assertEqual(choose_landing((4, 4), (5, 6), around), (5, 6))

    def test_active_enemy_occupied_landings_are_excluded(self):
        cells = landing_candidates((4, 4), {(5, 6), (6, 5)})
        self.assertNotIn((5, 6), cells)
        self.assertNotIn((6, 5), cells)
        self.assertEqual(len(cells), 6)

    def test_player_landing_is_preferred_and_ties_use_stable_clockwise_order(self):
        for dx, dy in KNIGHT_STEPS:
            target = 4 + dx, 4 + dy
            self.assertEqual(choose_landing((4, 4), target, set()), target)
        self.assertEqual(choose_landing((4, 4), (9, 9), set()), (5, 6))

    def test_no_legal_landing_returns_none_without_fabricated_target(self):
        self.assertIsNone(choose_landing((0, 0), (9, 9), {(1, 2), (2, 1)}))


class KnightScheduleTests(unittest.TestCase):
    def test_original_stage_three_wait_then_single_cell_36_tick_telegraph(self):
        encounter = EnemyEncounter(create_stage_enemies(StageCatalog.load().get_stage(3)))
        source = encounter.enemies[0]
        encounter.advance_to(47, (5, 1))
        self.assertEqual((source.position, source.state), ((3, 6), 'initial_wait'))
        encounter.advance_to(48, (5, 1))
        event = source.current_attack
        self.assertEqual((event.start_tick, event.hit_tick, event.target_cells), (48, 84, ((5, 5),)))
        self.assertEqual(source.position, (3, 6))

    def test_target_is_frozen_even_if_player_moves_and_due_is_published_once(self):
        source = knight()
        encounter = EnemyEncounter((source,))
        encounter.advance_to(0, (5, 1))
        event = source.current_attack
        self.assertEqual(event.target_cells, ((5, 1),))
        self.assertEqual(encounter.advance_to(35, (9, 9)), ())
        self.assertEqual(event.target_cells, ((5, 1),))
        self.assertEqual(encounter.advance_to(36, (9, 9)), (event,))
        self.assertEqual(encounter.advance_to(36, (9, 9)), ())
        self.assertEqual((source.state, source.next_action_tick, source.position), ('recovering', 108, (4, 3)))

    def test_surrounded_knight_waits_and_retries_using_existing_recovery_duration(self):
        source = knight(col=0, row=0)
        blockers = (Enemy('a', 1, 2, (0, -1), 10), Enemy('b', 2, 1, (0, -1), 10))
        encounter = EnemyEncounter((source, *blockers))
        encounter.advance_to(0, (9, 9))
        self.assertEqual((source.state, source.next_action_tick, source.current_attack), ('waiting', 72, None))
        blockers[0].health.apply_damage(2, tick=1)
        encounter.deactivate(blockers[0].entity_instance_id)
        encounter.advance_to(71, (9, 9))
        self.assertIsNone(source.current_attack)
        encounter.advance_to(72, (9, 9))
        self.assertEqual(source.current_attack.target_cells, ((1, 2),))


if __name__ == '__main__':
    unittest.main()
