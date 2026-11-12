"""King model/factory and approved one-step geometry/timing baselines."""
from dataclasses import replace
import unittest

from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from enemy_factory import create_enemy, create_stage_enemies, UnsupportedEnemyError
from king_behavior import KING_STEPS, choose_move, melee_target, move_candidates
from stage_manager import StageCatalog


def king(name='k', col=5, row=2, delay=0, hp=8):
    return Enemy(name, col, row, None, delay, kind='king', boss_hp=hp)


class KingDefinitionTests(unittest.TestCase):
    def test_explicit_hp_only_lives_in_health_and_runtime_ids_are_fresh(self):
        first, second = king(), king()
        self.assertEqual((first.kind, first.forward, first.health.current_hp, first.health.max_hp),
                         ('king', None, 8, 8))
        self.assertNotIn('boss_hp', vars(first))
        self.assertNotEqual(first.entity_instance_id, second.entity_instance_id)
        self.assertNotEqual(first.data_id, first.entity_instance_id)
        self.assertIsNot(first.health, second.health)

    def test_boss_hp_is_required_and_invalid_values_never_default_to_eight(self):
        definition = StageCatalog.load().get_stage(5).enemies[0]
        for bad in (None, True, False, 0, -1, 8.0, '8', float('inf')):
            with self.subTest(hp=bad):
                with self.assertRaises(ValueError):
                    king(hp=bad)
                with self.assertRaises(ValueError):
                    create_enemy(definition, boss_hp=bad)
        with self.assertRaises(ValueError):
            create_enemy(definition)

    def test_every_boss_definition_supplies_its_own_hp_to_king(self):
        catalog = StageCatalog.load()
        for number, hp in ((5, 8), (10, 10), (15, 12), (20, 14), (25, 16)):
            stage = catalog.get_stage(number)
            definition = next(e for e in stage.enemies if e.kind == 'king')
            source = create_enemy(definition, boss_hp=stage.boss_hp)
            self.assertEqual((source.health.max_hp, source.health.current_hp), (hp, hp))
            self.assertEqual(source.position, (5, 9))
            self.assertEqual(source.initial_delay_ticks, 48)
            if all(e.kind != 'queen' for e in stage.enemies):
                whole_stage = create_stage_enemies(stage)
                self.assertEqual(next(e for e in whole_stage if e.kind == 'king').health.max_hp, hp)

    def test_stage_five_factory_preserves_original_order_positions_hp_and_delay(self):
        stage = StageCatalog.load().get_stage(5)
        enemies = create_stage_enemies(stage)
        self.assertEqual((stage.boss, stage.boss_hp, stage.chapter, stage.player_spawn), (True, 8, 1, (5, 1)))
        self.assertEqual([(e.data_id, e.kind, e.position, e.health.current_hp, e.initial_delay_ticks) for e in enemies],
                         [('s5_king_1', 'king', (5, 9), 8, 48),
                          ('s5_rook_1', 'rook', (2, 4), 4, 62),
                          ('s5_pawn_1', 'pawn', (1, 6), 2, 75),
                          ('s5_pawn_2', 'pawn', (8, 6), 2, 88)])
        self.assertEqual(enemies[2].forward, (0, -1))

    def test_factory_rejects_inconsistent_boss_metadata_before_spawning(self):
        catalog = StageCatalog.load()
        stage = catalog.get_stage(5)
        for change in ({'boss': False}, {'boss': 1}, {'boss_hp': None}, {'boss_hp': True},
                       {'boss_hp': 0}, {'boss_hp': 8.5}, {'enemies': stage.enemies[1:]},
                       {'enemies': (stage.enemies[0], stage.enemies[0])}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                create_stage_enemies(replace(stage, **change))
        with self.assertRaises(ValueError):
            create_stage_enemies(replace(catalog.get_stage(2), boss_hp=8))

    def test_general_enemy_factories_keep_original_hp_and_reject_boss_override(self):
        catalog = StageCatalog.load()
        for kind, hp in (('pawn', 2), ('rook', 4), ('knight', 3), ('bishop', 3)):
            definition = next(e for stage in catalog.stages for e in stage.enemies if e.kind == kind)
            self.assertEqual(create_enemy(definition).health.current_hp, hp)
            with self.assertRaises(ValueError):
                create_enemy(definition, boss_hp=8)

    def test_definitions_remain_read_only_and_repeated_creation_has_no_state_alias(self):
        stage = StageCatalog.load().get_stage(5)
        a, b = create_stage_enemies(stage), create_stage_enemies(stage)
        a[0].health.apply_damage(3, tick=0)
        a[0].col = 4
        self.assertEqual((stage.enemies[0].position, stage.boss_hp, b[0].position, b[0].health.current_hp),
                         ((5, 9), 8, (5, 9), 8))
        self.assertTrue({e.entity_instance_id for e in a}.isdisjoint(e.entity_instance_id for e in b))
        self.assertFalse(hasattr(stage.enemies[0], 'health'))

    def test_queen_options_and_unsupported_rosters_are_still_rejected(self):
        catalog = StageCatalog.load()
        with self.assertRaises(UnsupportedEnemyError):
            create_enemy(replace(catalog.get_stage(5).enemies[0], options={'forward': (0, -1)}), boss_hp=8)
        for number in (13, 15, 20, 25):
            with self.assertRaisesRegex(UnsupportedEnemyError, 'queen'):
                create_stage_enemies(catalog.get_stage(number))


class KingGeometryTests(unittest.TestCase):
    def test_exact_eight_candidates_in_approved_tie_order(self):
        self.assertEqual(KING_STEPS, ((0, 1), (0, -1), (-1, 0), (1, 0),
                                     (-1, 1), (1, 1), (-1, -1), (1, -1)))
        self.assertEqual(move_candidates((4, 4), (9, 9), set()),
                         tuple((4 + dx, 4 + dy) for dx, dy in KING_STEPS))

    def test_all_origins_are_in_bounds_distinct_and_one_cell_only(self):
        for col in range(10):
            for row in range(10):
                cells = move_candidates((col, row), (9, 9), set())
                self.assertEqual(len(cells), len(set(cells)))
                self.assertNotIn((9, 9), cells)
                for x, y in cells:
                    self.assertTrue(0 <= x < 10 and 0 <= y < 10)
                    self.assertEqual(max(abs(x - col), abs(y - row)), 1)
        self.assertEqual(set(move_candidates((0, 0), (9, 9), set())), {(0, 1), (1, 0), (1, 1)})

    def test_player_and_active_enemy_cells_are_excluded(self):
        cells = move_candidates((4, 4), (5, 5), {(4, 5), (3, 4)})
        self.assertNotIn((5, 5), cells)
        self.assertNotIn((4, 5), cells)
        self.assertNotIn((3, 4), cells)

    def test_nearest_chebyshev_candidate_and_fixed_ties_are_deterministic(self):
        self.assertEqual(choose_move((4, 4), (6, 6), set()), (5, 5))
        self.assertEqual(choose_move((4, 4), (4, 8), set()), (4, 5))
        self.assertEqual(choose_move((4, 4), (6, 4), set()), (5, 4))
        self.assertEqual(choose_move((4, 4), (6, 4), {(5, 4)}), (5, 5))
        self.assertEqual(choose_move((0, 0), (9, 9), {(0, 1), (1, 0), (1, 1)}), (0, 0))

    def test_melee_targets_player_single_adjacent_cell_in_all_eight_directions(self):
        for dx, dy in KING_STEPS:
            self.assertEqual(melee_target((4, 4), (4 + dx, 4 + dy)), (4 + dx, 4 + dy))
        for cell in ((4, 4), (4, 6), (6, 6), (4, 9)):
            self.assertIsNone(melee_target((4, 4), cell))


class KingScheduleTests(unittest.TestCase):
    def test_original_initial_delay_and_exact_72_tick_movement_interval(self):
        source = king(col=5, row=9, delay=.8)
        encounter = EnemyEncounter((source,))
        encounter.advance_to(47, (5, 1))
        self.assertEqual(source.position, (5, 9))
        encounter.advance_to(48, (5, 1))
        self.assertEqual((source.position, source.next_action_tick), ((5, 8), 120))
        encounter.advance_to(119, (5, 1))
        self.assertEqual(source.position, (5, 8))
        encounter.advance_to(120, (5, 1))
        self.assertEqual((source.position, source.next_action_tick), ((5, 7), 192))

    def test_adjacent_attack_precedes_movement_and_target_never_retracks(self):
        for dx, dy in KING_STEPS:
            source = king(col=4, row=4)
            encounter = EnemyEncounter((source,))
            encounter.advance_to(0, (4 + dx, 4 + dy))
            event = source.current_attack
            self.assertEqual((event.start_tick, event.hit_tick, event.target_cells),
                             (0, 48, ((4 + dx, 4 + dy),)))
            encounter.advance_to(47, (9, 9))
            self.assertEqual(source.position, (4, 4))
            self.assertEqual(event.target_cells, ((4 + dx, 4 + dy),))
            self.assertEqual(encounter.advance_to(48, (9, 9)), (event,))
            self.assertEqual(encounter.advance_to(48, (9, 9)), ())

    def test_no_legal_candidate_waits_72_then_retries_released_cell(self):
        source = king(col=4, row=4)
        blockers = tuple(Enemy(str(i), 4 + dx, 4 + dy, (0, -1), 10)
                         for i, (dx, dy) in enumerate(KING_STEPS))
        encounter = EnemyEncounter((source, *blockers))
        encounter.advance_to(0, (9, 9))
        self.assertEqual((source.position, source.next_action_tick, source.current_attack), ((4, 4), 72, None))
        blockers[0].health.apply_damage(2, tick=1)
        encounter.deactivate(blockers[0].entity_instance_id)
        encounter.advance_to(71, (9, 9))
        self.assertEqual(source.position, (4, 4))
        encounter.advance_to(72, (9, 9))
        self.assertEqual(source.position, (4, 5))

    def test_stun_and_death_suspend_movement_without_reusing_an_old_action(self):
        source = king(col=4, row=4)
        encounter = EnemyEncounter((source,))
        encounter.advance_to(0, (9, 9))
        origin = source.position
        encounter.stun(source.entity_instance_id, 0)
        encounter.advance_to(59, (9, 9))
        self.assertEqual(source.position, origin)
        encounter.advance_to(60, (9, 9))
        self.assertNotEqual(source.position, origin)
        source.health.apply_damage(8, tick=60)
        encounter.deactivate(source.entity_instance_id)
        origin = source.position
        encounter.advance_to(500, (9, 9))
        self.assertEqual(source.position, origin)
        self.assertNotIn(origin, encounter.occupied_cells)


if __name__ == '__main__':
    unittest.main()
