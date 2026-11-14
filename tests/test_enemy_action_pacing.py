"""Controlled, process-local pacing candidates; shipped constants stay unchanged."""
import unittest
import config
import main
from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from simulation_clock import SimulationClock
from tools.action_pacing_experiment import candidate,observe,run,risks
from tests.balance_driver import measure


class EnemyActionPacingTests(unittest.TestCase):
    def test_candidate_ticks_and_all_protected_timings(self):
        for name,pawn,rook in (('baseline',132,72),('A',126,72),('B',132,69),('C',126,69)):
            with candidate(name):
                e=main._new_stage_game(20).encounter
                self.assertEqual((e.move_ticks,e.rook_move_ticks,e.king_move_ticks),(pawn,rook,72))
                self.assertEqual((e.telegraph_ticks,e.rook_telegraph_ticks,e.knight_telegraph_ticks,e.bishop_telegraph_ticks,e.queen_telegraph_ticks,e.king_telegraph_ticks),(39,48,36,108,72,48))
                self.assertEqual((e.recovery_ticks,e.rook_recovery_ticks,e.knight_recovery_ticks,e.bishop_recovery_ticks,e.queen_recovery_ticks,e.king_recovery_ticks),(54,90,72,240,180,90))
        self.assertEqual((config.PAWN_MOVE_INTERVAL_SECONDS,config.ROOK_MOVE_INTERVAL_SECONDS),(2.2,1.2))

    def test_pawn_initial_delay_and_second_move_exact_boundary(self):
        for name,interval in (('baseline',132),('A',126),('B',132),('C',126)):
            with candidate(name):
                p=Enemy('p',1,6,(0,-1),.8);e=EnemyEncounter((p,))
                e.advance_to(47,(8,1));self.assertEqual(p.position,(1,6))
                e.advance_to(48,(8,1));first=p.position
                self.assertNotEqual(first,(1,6));self.assertEqual(p.next_action_tick,48+interval)
                e.advance_to(47+interval,(8,1));self.assertEqual(p.position,first)
                e.advance_to(48+interval,(8,1));self.assertNotEqual(p.position,first)
                snapshot=(p.position,p.next_action_tick);e.advance_to(48+interval,(8,1));self.assertEqual((p.position,p.next_action_tick),snapshot)

    def test_rook_reposition_then_attack_at_changed_ready_tick(self):
        for name,interval in (('baseline',72),('A',72),('B',69),('C',69)):
            with candidate(name):
                r=Enemy('r',2,4,None,.8,kind='rook');e=EnemyEncounter((r,))
                e.advance_to(48,(8,1));self.assertEqual(r.next_action_tick,48+interval)
                position=r.position;e.advance_to(47+interval,(8,1));self.assertIsNone(r.current_attack)
                e.advance_to(48+interval,(8,1));ev=r.current_attack
                self.assertIsNotNone(ev);self.assertEqual(ev.hit_tick-ev.start_tick,48)
                e.advance_to(ev.hit_tick-1,(8,1));self.assertEqual(r.position,position)
                e.stun(r.entity_instance_id,ev.hit_tick-1)
                self.assertEqual(e.ledger.state(ev),'cancelled')
                self.assertEqual(r.stun_until_tick,ev.hit_tick-1+60)

    def test_all_original_initial_delays_and_hp_remain_unchanged(self):
        for name in ('A','B','C'):
            for n in range(1,21):
                baseline=main._new_stage_game(n)
                with candidate(name):trial=main._new_stage_game(n)
                snapshot=lambda g:[(e.data_id,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies]
                self.assertEqual(snapshot(baseline),snapshot(trial))

    def test_observer_cannot_change_combat_result(self):
        for name in ('baseline','A','B','C'):
            with candidate(name):
                expected=measure('survival',19)
                with observe():actual=measure('survival',19)
                self.assertEqual(expected,actual)

    def test_four_profiles_keep_measured_failures_and_risk_decisions(self):
        base=run('baseline')
        self.assertEqual(sum(r['result']!='GAME_OVER' for r in base['independent']),77)
        for name,clears in (('A',76),('B',77),('C',76)):
            trial=run(name)
            self.assertEqual(sum(r['result']!='GAME_OVER' for r in trial['independent']),clears)
            self.assertEqual([(r['stage'],r['result']) for r in trial['campaigns']],[(20,'BOSS_CLEAR'),(16,'GAME_OVER'),(18,'GAME_OVER'),(19,'GAME_OVER')])
            self.assertEqual(bool(risks(base,trial)),name!='B')
            failures={(r['stage'],r['style']):r['ticks'] for r in trial['independent'] if r['result']=='GAME_OVER'}
            for pair,tick in (((16,'survival'),408),((19,'evasion'),395),((20,'survival'),838)):
                self.assertEqual(failures[pair],tick)
            if name!='B':self.assertIn((18,'evasion'),failures)

    def test_pulse_freezes_and_restores_deadlines_for_all_candidates(self):
        from tests.test_king_pulse import PulseFreezeTests
        for name in ('A','B','C'):
            with candidate(name):PulseFreezeTests().test_s200_h320_r350_deadlines_and_historical_damage_are_preserved()

    def test_seven_fps_and_single_eight_tick_determinism_all_candidates(self):
        def snapshot(g):
            return (g.state,g.combat.tick,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.event.hit_tick,r.state,r.outcome) for r in g.encounter.ledger._records.values()])
        for name in ('baseline','A','B','C'):
            with candidate(name):
                traces=[]
                for fps in (30,60,120,144,160,180,240):
                    g=main._new_stage_game(19);clock=SimulationClock()
                    for _ in range(fps*4):g.advance(clock.advance(1/fps))
                    traces.append(snapshot(g))
                for stride in (1,8):
                    g=main._new_stage_game(19)
                    for _ in range(240//stride):g.advance(stride)
                    traces.append(snapshot(g))
                self.assertTrue(all(t==traces[0] for t in traces))

    def test_game_over_stops_all_ai_and_unsupported_stages_stay_blocked(self):
        for name in ('A','B','C'):
            with candidate(name):
                g=main._new_stage_game(20);g.advance(1000)
                self.assertFalse(g.playing);before=(g.combat.tick,[(e.position,e.next_action_tick) for e in g.encounter.enemies])
                g.advance(1000);self.assertEqual((g.combat.tick,[(e.position,e.next_action_tick) for e in g.encounter.enemies]),before)
                for n in range(22,26):
                    with self.assertRaises(ValueError):main._new_stage_game(n)
