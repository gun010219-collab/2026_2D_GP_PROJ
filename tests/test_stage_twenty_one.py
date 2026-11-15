"""Original Chapter5 seven-enemy combat; real clears separated from terminal fixtures."""
from unittest.mock import Mock,patch
import unittest
import main
from game import GameState
from renderer import BoardRenderer
from game_renderer import GameFlowRenderer
from upgrade_renderer import UpgradeRenderer
from simulation_clock import SimulationClock
from queen_behavior import queen_ray_targets
from tests.test_chapter_five_entry import entered_five,completed_four
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish,key,N,R,run_loop
from tests.balance_driver import STYLES,measure

class StageTwentyOneTests(unittest.TestCase):
    def test_exact_roster_original_delays_hp_and_theme(self):
        g=main._new_stage_game(21)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(5,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],[
            ('s21_queen_1','queen',(4,7),48,22),('s21_rook_1','rook',(2,4),62,20),('s21_rook_2','rook',(7,4),75,20),
            ('s21_knight_1','knight',(3,6),88,16),('s21_knight_2','knight',(6,6),101,16),('s21_bishop_1','bishop',(2,8),114,16),('s21_pawn_1','pawn',(1,6),128,13)])
        self.assertEqual(sum(e.health.max_hp for e in g.encounter.enemies),123)
        self.assertEqual(g.encounter.enemies[-1].forward,(0,-1))
        self.assertEqual(BoardRenderer(chapter=5).theme.name,'Gothic Throne')

    def test_clear_holds_one_offer_without_cards_or_receipt_consumption(self):
        # All ordinary stages now progress; final boss forbids a new chapter/offer.
        from tests.test_stage_twenty_five import assert_final_boundary
        assert_final_boundary(self)

    def test_boundary_keyboard_mouse_n_r_do_not_install_another_stage(self):
        # All ordinary stages now progress; final boss forbids a new chapter/offer.
        from tests.test_stage_twenty_five import assert_final_boundary
        assert_final_boundary(self)

    def test_actual_mixed_ai_snapshots_independent_cancel_and_occupancy(self):
        g=main._new_stage_game(21);g.advance(110)
        q=g.encounter.enemies[0];laser=q.current_attack
        self.assertEqual(laser.target_cells,queen_ray_targets(q.position))
        self.assertEqual(laser.hit_tick-laser.start_tick,72)
        knights=g.encounter.enemies[3:5]
        self.assertTrue(all(k.current_attack for k in knights))
        foreign=knights[1].current_attack;own=knights[0].current_attack
        knights[0].health.apply_damage(knights[0].health.current_hp,tick=110);g.encounter.deactivate(knights[0].entity_instance_id,tick=110)
        self.assertEqual(g.encounter.ledger.state(own),'cancelled');self.assertEqual(g.encounter.ledger.state(foreign),'telegraph')
        g.advance(4);b=g.encounter.enemies[5]
        self.assertEqual((len(b.current_attack.target_cells),b.current_attack.hit_tick-b.current_attack.start_tick),(50,108))
        for _ in range(150):
            cells=[e.position for e in g.encounter.enemies if e.active];self.assertEqual(len(cells),len(set(cells)));g.advance()

    def test_player_death_wins_over_last_enemy(self):
        g=main._new_stage_game(21)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state()
        self.assertEqual(g.state,GameState.GAME_OVER);self.assertTrue(g.resolver.stopped)

    def test_four_styles_actual_seven_enemy_fights(self):
        expected={'attack':('UPGRADE',432,2),'survival':('GAME_OVER',341,0),'evasion':('UPGRADE',651,2),'balanced':('UPGRADE',651,2)}
        for style in STYLES:
            row=measure(style,21)
            self.assertEqual(row['hp'],[22,20,20,16,16,16,13]);self.assertEqual((row['result'],row['ticks'],row['remaining_hp']),expected[style])
            self.assertGreater(row['hits'],0)

    def test_seven_fps_and_single_eight_tick_determinism(self):
        def trace(g):return(g.state,g.combat.tick,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.event.hit_tick,r.state,r.outcome) for r in g.encounter.ledger._records.values()])
        traces=[]
        for fps in (30,60,120,144,160,180,240):
            g=main._new_stage_game(21);c=SimulationClock()
            for _ in range(fps*4):g.advance(c.advance(1/fps))
            traces.append(trace(g))
        for stride in (1,8):
            g=main._new_stage_game(21)
            for _ in range(240//stride):g.advance(stride)
            traces.append(trace(g))
        self.assertTrue(all(t==traces[0] for t in traces))

    def test_real_queen_snapshot_normal_perfect_and_missed_parry(self):
        # Adjudication fixture isolates Queen; full seven-source battles are measured separately.
        for delta in (None,18,7):
            g=main._new_stage_game(21)
            for e in g.encounter.enemies[1:]:e.next_action_tick=1000
            g.advance(49);q=g.encounter.enemies[0];ev=q.current_attack;snapshot=ev.target_cells
            g.player.move('up',occupied=g.encounter.occupied_cells);g.player.move('up',occupied=g.encounter.occupied_cells)
            self.assertIn(g.player.position,snapshot)
            if delta:
                g.advance(ev.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.advance(ev.hit_tick-g.combat.tick)
            self.assertEqual(ev.target_cells,snapshot)
            self.assertEqual(g.player.health.current_hp,3 if delta else 2)
            self.assertEqual(g.encounter.ledger.outcome(ev),'parried_perfect' if delta==7 else 'parried_normal' if delta else 'hit')
            self.assertIsNone(g.resolver.resolve_enemy_attack(ev))
            if delta==7:self.assertEqual((q.stun_until_tick,g.combat.pending_attack_bonus),(ev.hit_tick+60,2))
