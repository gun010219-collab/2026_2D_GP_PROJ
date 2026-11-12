"""Opt-in movement deadlines use Combat.tick; legacy API remains unrestricted."""
import unittest

from combat import Combat
from input_controller import InputController
from player import Player
from simulation_clock import SimulationClock
from upgrades import ChapterBuild


class MoveCooldownTests(unittest.TestCase):
    def test_first_press_and_all_three_exact_deadline_boundaries(self):
        for level,interval in enumerate((18,15,12)):
            p,c=Player(5,1),Combat()
            controls=InputController(move_interval_ticks=ChapterBuild(move_level=level).stats.move_interval_ticks)
            self.assertTrue(controls.key_down('up',p,tick=c.tick))
            self.assertEqual(controls.next_move_tick,interval)
            controls.key_up('up')
            c.advance(interval-1)
            self.assertFalse(controls.key_down('right',p,tick=c.tick))
            self.assertEqual((p.position,p.facing),((5,2),'up'))
            controls.key_up('right')
            c.advance(1)
            self.assertTrue(controls.key_down('right',p,tick=c.tick))
            self.assertEqual((p.position,controls.next_move_tick),((6,2),interval*2))

    def test_first_move_is_ready_even_if_session_starts_at_nonzero_tick(self):
        controls=InputController(move_interval_ticks=18)
        p,c=Player(5,1),Combat()
        c.advance(500)
        self.assertTrue(controls.key_down('up',p,tick=c.tick))
        self.assertEqual(controls.next_move_tick,518)

    def test_wall_failure_updates_facing_but_never_spends_cooldown(self):
        controls=InputController(move_interval_ticks=18)
        p=Player(0,0)
        self.assertFalse(controls.key_down('left',p,tick=0))
        self.assertEqual((p.position,p.facing,controls.next_move_tick),((0,0),'left',0))
        controls.key_up('left')
        self.assertTrue(controls.key_down('up',p,tick=0))

    def test_occupied_failure_is_free_and_next_released_press_can_move(self):
        controls=InputController(move_interval_ticks=15)
        p=Player(5,1)
        self.assertFalse(controls.key_down('right',p,occupied={(6,1)},tick=0))
        self.assertEqual((p.facing,controls.next_move_tick),('right',0))
        controls.key_up('right')
        self.assertTrue(controls.key_down('up',p,tick=0))

    def test_fast_press_is_discarded_and_holding_cannot_execute_at_expiry(self):
        controls=InputController(move_interval_ticks=18)
        p=Player(5,1)
        controls.key_down('up',p,tick=0); controls.key_up('up')
        self.assertFalse(controls.key_down('right',p,tick=1))
        for tick in (17,18,100):
            self.assertFalse(controls.key_down('right',p,tick=tick))
        self.assertEqual((p.position,p.facing),((5,2),'up'))
        controls.key_up('right')
        self.assertTrue(controls.key_down('right',p,tick=100))

    def test_chords_keep_first_key_rule_even_when_deadline_has_elapsed(self):
        controls=InputController(move_interval_ticks=12)
        p=Player(5,1)
        self.assertTrue(controls.key_down('up',p,tick=0))
        self.assertFalse(controls.key_down('right',p,tick=12))
        controls.key_up('up')
        self.assertFalse(controls.key_down('left',p,tick=12))
        controls.key_up('right'); controls.key_up('left')
        self.assertTrue(controls.key_down('right',p,tick=12))

    def test_blocked_menu_input_has_no_facing_change_or_later_replay(self):
        controls=InputController(move_interval_ticks=18)
        p=Player(5,1)
        self.assertFalse(controls.key_down('right',p,blocked=True,tick=0))
        self.assertEqual((p.position,p.facing,controls.next_move_tick),((5,1),'up',0))
        self.assertFalse(controls.key_down('right',p,tick=100))
        controls.key_up('right')
        self.assertTrue(controls.key_down('right',p,tick=100))

    def test_focus_reconcile_does_not_bypass_deadline_or_emit_ghost_move(self):
        controls=InputController(move_interval_ticks=18)
        p=Player(5,1)
        controls.key_down('up',p,tick=0)
        controls.reconcile(())
        controls.reconcile(('up',))
        self.assertFalse(controls.key_down('up',p,tick=18))
        self.assertEqual(p.position,(5,2))
        controls.key_up('up')
        self.assertTrue(controls.key_down('up',p,tick=18))
        controls.reconcile(())
        self.assertFalse(controls.key_down('right',p,tick=19))

    def test_paused_wall_time_does_not_advance_combat_movement_deadline(self):
        p,c,clock=Player(5,1),Combat(),SimulationClock()
        controls=InputController(move_interval_ticks=18)
        controls.key_down('up',p,tick=c.tick); controls.key_up('up')
        for _ in range(5):
            c.advance(clock.advance(100,paused=True))
        self.assertEqual(c.tick,0)
        self.assertFalse(controls.key_down('right',p,tick=c.tick))
        controls.key_up('right')
        c.advance(18)
        self.assertTrue(controls.key_down('right',p,tick=c.tick))

    def test_new_session_controller_has_no_old_deadline_or_held_keys(self):
        p,c=Player(5,1),Combat()
        old=InputController(move_interval_ticks=18)
        old.key_down('up',p,tick=c.tick)
        fresh=InputController(move_interval_ticks=18)
        self.assertEqual(fresh.next_move_tick,0)
        self.assertTrue(fresh.key_down('up',Player(5,1),tick=0))
        self.assertEqual(old.next_move_tick,18)

    def test_bad_intervals_and_nonmonotonic_ticks_do_not_mutate_input_state(self):
        for bad in (True,False,0,-1,18.0,'18',[]):
            with self.assertRaises(ValueError):
                InputController(move_interval_ticks=bad)
        controls=InputController(move_interval_ticks=18)
        p=Player(5,1)
        for bad in (None,True,-1,1.0,'0'):
            with self.assertRaises(ValueError):
                controls.key_down('up',p,tick=bad)
        self.assertTrue(controls.key_down('up',p,tick=0))
        controls.key_up('up')
        controls.key_down('right',p,blocked=True,tick=10)
        controls.key_up('right')
        with self.assertRaises(ValueError):
            controls.key_down('left',p,tick=9)
        self.assertTrue(controls.key_down('left',p,tick=18))

    def test_unconfigured_legacy_and_direct_player_movement_remain_unrestricted(self):
        p=Player(5,1)
        controls=InputController()
        for _ in range(3):
            self.assertTrue(controls.key_down('up',p))
            controls.key_up('up')
        self.assertEqual(p.position,(5,4))
        self.assertIsNone(controls.move_interval_ticks)
        self.assertTrue(p.move('right'))
        self.assertTrue(p.move('right'))

    def test_dead_player_cannot_move_or_spend_a_cooldown(self):
        p=Player(5,1)
        p.health.apply_damage(3,tick=0)
        controls=InputController(move_interval_ticks=18)
        self.assertFalse(controls.key_down('up',p,tick=0))
        self.assertEqual(controls.next_move_tick,0)

    def test_one_and_eight_tick_catchup_use_the_same_input_schedule(self):
        def simulate(chunk):
            p,c=Player(5,1),Combat()
            controls=InputController(move_interval_ticks=18)
            actions={0:'up',3:'right',18:'right',19:'up',36:'down',54:'left'}
            rows=[]
            while c.tick<=64:
                stop=min(c.tick+chunk,65)
                for t in range(c.tick,stop):
                    if t in actions:
                        direction=actions[t]
                        rows.append((t,controls.key_down(direction,p,tick=c.tick),p.position,controls.next_move_tick))
                        controls.key_up(direction)
                    c.advance()
            return rows
        self.assertEqual(simulate(1),simulate(8))


if __name__=='__main__':
    unittest.main()
