import unittest

from config import PAWN_INITIAL_HP, PLAYER_INITIAL_HP
from enemy import load_stage1_enemies
from health import Health
from player import load_stage1_player


class HealthTests(unittest.TestCase):
    def test_pdf_initial_values_are_actual_independent_health(self):
        player = load_stage1_player()
        pawns = load_stage1_enemies()
        self.assertEqual(PLAYER_INITIAL_HP, 3)
        self.assertEqual(PAWN_INITIAL_HP, 2)
        self.assertEqual((player.health.current_hp, player.health.max_hp), (3, 3))
        self.assertEqual([(e.health.current_hp, e.health.max_hp) for e in pawns], [(3, 3), (3, 3)])
        self.assertIsNot(pawns[0].health, pawns[1].health)
        self.assertIsNone(player.health.last_damage_tick)
        self.assertTrue(player.alive)

    def test_damage_reduces_hp_and_records_only_actual_hit(self):
        health = Health(3)
        self.assertEqual(health.apply_damage(1, tick=39), 1)
        self.assertEqual((health.current_hp, health.max_hp, health.alive), (2, 3, True))
        self.assertEqual((health.last_damage_tick, health.last_damage_amount), (39, 1))

    def test_overkill_clamps_to_zero_and_dead_damage_does_not_update_feedback(self):
        health = Health(2)
        self.assertEqual(health.apply_damage(100, tick=10), 2)
        self.assertEqual((health.current_hp, health.alive), (0, False))
        self.assertEqual(health.apply_damage(1, tick=20), 0)
        self.assertEqual((health.last_damage_tick, health.last_damage_amount), (10, 2))

    def test_invalid_max_hp(self):
        for value in (True, False, 1.5, '3', None, float('inf'), float('nan')):
            with self.subTest(value=value), self.assertRaises(TypeError):
                Health(value)
        for value in (0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Health(value)

    def test_invalid_damage_is_rejected_without_mutation(self):
        health = Health(3)
        for value in (True, False, 1.0, '1', None, float('inf'), float('nan')):
            with self.subTest(value=value), self.assertRaises(TypeError):
                health.apply_damage(value, tick=0)
        for value in (0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                health.apply_damage(value, tick=0)
        self.assertEqual(health.current_hp, 3)
        self.assertIsNone(health.last_damage_tick)

    def test_invalid_tick_is_rejected_before_damage(self):
        health = Health(3)
        for value in (True, 1.5, '1'):
            with self.subTest(value=value), self.assertRaises(TypeError):
                health.apply_damage(1, tick=value)
        with self.assertRaises(ValueError):
            health.apply_damage(1, tick=-1)
        self.assertEqual(health.current_hp, 3)

    def test_hp_properties_cannot_be_assigned(self):
        health = Health(3)
        for name in ('max_hp', 'current_hp', 'alive', 'last_damage_tick'):
            with self.subTest(name=name), self.assertRaises(AttributeError):
                setattr(health, name, 100)

    def test_reloaded_player_has_unique_instance_identity(self):
        first, second = load_stage1_player(), load_stage1_player()
        self.assertNotEqual(first.entity_instance_id, second.entity_instance_id)
        self.assertIsNot(first.health, second.health)

    def test_dead_player_cannot_move_or_turn(self):
        player = load_stage1_player()
        player.health.apply_damage(player.health.max_hp, tick=0)
        before = player.position, player.facing
        self.assertFalse(player.move('right'))
        self.assertEqual((player.position, player.facing), before)


if __name__ == '__main__':
    unittest.main()
