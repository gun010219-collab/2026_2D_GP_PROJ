import math
import unittest

from combat import Combat
from config import FIXED_TIME_STEP, MAX_SIMULATION_STEPS_PER_FRAME
from player import Player
from simulation_clock import SimulationClock


class SimulationClockTests(unittest.TestCase):
    def test_cooldown_has_same_boundary_at_different_render_rates(self):
        for fps in (30, 60, 120, 144):
            with self.subTest(fps=fps):
                clock, combat, player = SimulationClock(), Combat(), Player(5, 1)
                combat.request_attack(player)
                frames = math.floor(0.6 * fps)
                for _ in range(frames):
                    combat.advance(clock.advance(1 / fps))
                remainder = max(0.0, 0.6 - frames / fps)
                combat.advance(clock.advance(remainder))
                self.assertEqual(combat.tick, 36)
                self.assertEqual(combat.request_attack(player).attack_id, 2)

    def test_fractional_time_is_accumulated_not_counted_as_frames(self):
        clock = SimulationClock()
        self.assertEqual(clock.advance(FIXED_TIME_STEP / 4), 0)
        self.assertEqual(clock.advance(FIXED_TIME_STEP / 4), 0)
        self.assertEqual(clock.advance(FIXED_TIME_STEP / 2), 1)
        self.assertAlmostEqual(clock.accumulator, 0.0)
        self.assertEqual(clock.advance(FIXED_TIME_STEP * 2.5), 2)
        self.assertEqual(clock.advance(FIXED_TIME_STEP / 2), 1)

    def test_pause_drops_elapsed_and_fraction_without_catchup(self):
        clock, combat = SimulationClock(), Combat()
        combat.advance(clock.advance(FIXED_TIME_STEP / 2))
        combat.advance(clock.advance(10.0, paused=True))
        self.assertEqual(combat.tick, 0)
        self.assertEqual(clock.accumulator, 0.0)
        self.assertEqual(clock.advance(FIXED_TIME_STEP / 2), 0)
        self.assertEqual(clock.advance(FIXED_TIME_STEP / 2), 1)

    def test_menu_pause_freezes_cooldown_and_effect(self):
        clock, combat, player = SimulationClock(), Combat(), Player(5, 1)
        event = combat.request_attack(player)
        combat.advance(clock.advance(FIXED_TIME_STEP * 3))
        for _ in range(100):
            combat.advance(clock.advance(0.1, paused=True))
        self.assertEqual(combat.tick, 3)
        self.assertIs(combat.active_attack, event)
        self.assertIsNone(combat.request_attack(player))
        combat.advance(clock.advance(FIXED_TIME_STEP))
        self.assertEqual(combat.tick, 4)

    def test_large_delay_is_capped_and_backlog_discarded(self):
        clock = SimulationClock()
        self.assertEqual(clock.advance(1000.0), MAX_SIMULATION_STEPS_PER_FRAME)
        self.assertEqual(MAX_SIMULATION_STEPS_PER_FRAME, 8)
        self.assertEqual(clock.advance(0), 0)
        self.assertEqual(clock.advance(FIXED_TIME_STEP), 1)

    def test_reset_drops_only_fractional_pending_time(self):
        clock = SimulationClock()
        clock.advance(FIXED_TIME_STEP / 2)
        clock.reset()
        self.assertEqual(clock.accumulator, 0.0)
        self.assertEqual(clock.advance(FIXED_TIME_STEP / 2), 0)

    def test_invalid_elapsed_does_not_change_accumulator(self):
        clock = SimulationClock()
        for elapsed in (-0.1, float('nan'), float('inf')):
            with self.subTest(elapsed=elapsed), self.assertRaises(ValueError):
                clock.advance(elapsed)
        self.assertEqual(clock.accumulator, 0.0)

    def test_parry_shares_combat_time_through_modal_pause(self):
        from parry import Parry
        parry, combat, clock = Parry(), Combat(), SimulationClock()
        parry.request(combat.tick)
        combat.advance(clock.advance(FIXED_TIME_STEP * 3))
        for _ in range(100):
            combat.advance(clock.advance(0.1, paused=True))
        self.assertEqual(parry.state_at(combat.tick), 'perfect_window')
        self.assertEqual(combat.tick, 3)
        combat.advance(clock.advance(FIXED_TIME_STEP * 5))
        self.assertEqual(parry.state_at(combat.tick), 'normal_window')
        combat.advance(clock.advance(FIXED_TIME_STEP * 8))
        combat.advance(clock.advance(FIXED_TIME_STEP * 2))
        self.assertEqual(parry.state_at(combat.tick), 'inactive')

    def test_parry_can_cross_visual_phase_during_capped_stall(self):
        from parry import Parry
        parry, combat, clock = Parry(), Combat(), SimulationClock()
        parry.request(0)
        combat.advance(clock.advance(5.0))
        self.assertEqual(combat.tick, 8)
        self.assertEqual(parry.state_at(combat.tick), 'normal_window')
        self.assertEqual(clock.advance(0), 0)
