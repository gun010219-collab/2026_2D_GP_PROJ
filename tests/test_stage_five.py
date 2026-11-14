"""Playable Stage 5, terminal state, native loop policy and read-only UI."""
import unittest
from unittest.mock import Mock, patch

import main
from config import FIXED_TIME_STEP
from game import GameState
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from enemy_attack_renderer import EnemyAttackRenderer
from tests.test_stage_transition import N, R, UP, SPACE, SHIFT, F11, ESC, MENU, key, finish, run_loop
from tests.test_stage_three import play_to


class StageFiveTests(unittest.TestCase):
    def test_stage_four_n_enters_original_boss_metadata_hp_spawns_and_delays(self):
        created, snapshots, _, _, _, _=run_loop([[key(49)],[]],initial_stage=4)
        self.assertEqual([g.stage_number for g in created],[4,5])
        g=created[-1]
        self.assertTrue(g.boss)
        self.assertEqual((g.chapter,g.player.position,snapshots[0]['tick']),(1,(5,1),0))
        self.assertEqual([(e.kind,e.position,e.health.current_hp,e.initial_delay_ticks) for e in g.encounter.enemies],
                         [('king',(5,9),22,48),('rook',(2,4),6,62),('pawn',(1,6),3,75),('pawn',(8,6),3,88)])
        self.assertEqual(g.encounter.pulse.next_use_tick,240)

    def test_only_total_annihilation_clears_and_player_death_wins(self):
        for killed,dead,state in (((0,),False,GameState.PLAYING),((1,2,3),False,GameState.PLAYING),
                                  ((0,1,2,3),False,GameState.BOSS_CLEAR),((0,1,2,3),True,GameState.GAME_OVER)):
            g=main._new_stage_game(5)
            g.advance(270)
            for i in killed:
                e=g.encounter.enemies[i]
                e.health.apply_damage(e.health.current_hp,tick=g.combat.tick)
                g.encounter.deactivate(e.entity_instance_id,tick=g.combat.tick)
            if dead:
                g.player.health.apply_damage(g.player.health.current_hp,tick=g.combat.tick)
            g.update_state()
            self.assertEqual(g.state,state)
            if state is not GameState.PLAYING:
                before=(g.combat.tick,g.encounter.tick,len(g.encounter.ledger._records))
                self.assertEqual(g.advance(999),())
                self.assertEqual(before,(g.combat.tick,g.encounter.tick,len(g.encounter.ledger._records)))
                self.assertFalse(g.update_state())
                self.assertEqual(g.transition_count,1)
                self.assertEqual(g.encounter.pulse._remaining,{})

    def test_boss_clear_n_ignored_r_replays_and_game_over_r_returns_one(self):
        # Historical method name retained; Task 1-V tests N entry separately.
        for state,target in (('clear',5),('dead',1)):
            created,snapshots,_,_,_,_=run_loop([[],[key(R)]],initial_stage=5,initial=state)
            self.assertEqual([g.stage_number for g in created],[5,target])
            self.assertEqual(snapshots[0]['count'],1)
            self.assertEqual((snapshots[1]['tick'],snapshots[1]['hp']),(0,4 if state=='clear' else 3))

    def test_progress_all_five_once_then_n_never_enters_six(self):
        # Task 1-V approval replaces the old N block; preserve this method's identity.
        def clear(g,frame):
            if g.playing:
                finish(g,'clear')
        created,snapshots,_,_,_,clock=run_loop([batch for k in (49,49,50,50) for batch in ([key(k),key(k,False)], [])]+[[key(N)],[]],after_render=clear)
        self.assertEqual([g.stage_number for g in created],[1,2,3,4,5,6])
        self.assertEqual(snapshots[-1]['state'],GameState.UPGRADE)
        self.assertEqual(clock.accumulator,0)
        for n in range(18,26):
            with self.assertRaises(ValueError):
                main._new_stage_game(n)

    def test_replay_is_new_session_and_old_pulse_cannot_hit_it(self):
        old=main._new_stage_game(5)
        old.advance(270)
        event=old.encounter.pulse.event
        attempt=old.parry.request(old.combat.tick)
        old.resolver.register_parry(attempt)
        old.resolver.stop()
        fresh=main._new_stage_game(5)
        self.assertNotEqual(old.combat.combat_session_id,fresh.combat.combat_session_id)
        self.assertNotEqual(old.combat.stage_instance_id,fresh.combat.stage_instance_id)
        self.assertTrue({e.entity_instance_id for e in old.encounter.enemies}.isdisjoint(e.entity_instance_id for e in fresh.encounter.enemies))
        self.assertEqual((fresh.encounter.pulse.state,fresh.encounter.pulse._remaining,fresh.encounter.pulse.event),('NORMAL',{},None))
        for action in (lambda:fresh.resolver.resolve_enemy_attack(event),lambda:fresh.resolver.register_parry(attempt)):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(fresh.encounter.pulse.king.health.current_hp,22)

    def test_playing_n_r_and_held_inputs_cannot_restart_or_leak_into_replay(self):
        created,_,_,_,_,_=run_loop([[key(N),key(R)]],initial_stage=5,initial='playing')
        self.assertEqual(len(created),1)
        created,snapshots,_,_,_,_=run_loop([
            [key(R),key(N),key(SPACE),key(SHIFT),key(UP)],
            [key(R),key(SPACE),key(SHIFT),key(UP)],
            [key(R,False),key(SPACE,False),key(SHIFT,False),key(UP,False)],
            [key(UP),key(SPACE),key(SHIFT)]],initial_stage=5)
        self.assertEqual([g.stage_number for g in created],[5,5])
        self.assertTrue(all(s['position']==(5,1) and s['attack']==s['parry']==0 for s in snapshots[:3]))
        self.assertEqual(created[-1].player.position,(5,2))

    def test_actual_main_first_pulse_and_perfect_with_original_mixed_enemies(self):
        factory=main._new_stage_game
        seen={}
        def observe(g,t):
            pulse=g.encounter.pulse
            seen[t]=(pulse.state,g.player.health.current_hp,pulse.king.health.current_hp,
                     [(e.position,e.next_action_tick) for e in g.encounter.enemies[1:]])
        created,_,_,_,_,_=play_to(445,factory=lambda:factory(5),inputs={378:[key(SHIFT)]},
                                  samples=(239,240,264,265,377,385,414,415,444,445),observe=observe)
        g=created[-1]
        pulse=g.encounter.pulse
        self.assertEqual((pulse.event.start_tick,pulse.event.hit_tick),(265,385))
        self.assertEqual(seen[264][0],'DRAINING')
        self.assertEqual(seen[265][0],'PULSE_TELEGRAPH')
        self.assertEqual(seen[385][0],'CLEANUP')
        self.assertEqual(seen[414][0],'CLEANUP')
        self.assertEqual(seen[415][0],'NORMAL')
        self.assertEqual((g.resolver.last_parry_result.status,g.combat.pending_attack_bonus),('perfect',2))
        self.assertEqual(seen[385][2],20)
        self.assertEqual(seen[265][3],seen[414][3])
        self.assertEqual(pulse.king.stun_until_tick,445)

    def test_actual_main_normal_pulse_parry_does_not_reflect_or_reward(self):
        factory=main._new_stage_game
        created,_,_,_,_,_=play_to(385,factory=lambda:factory(5),inputs={367:[key(SHIFT)]})
        g=created[-1]
        self.assertEqual(g.resolver.last_parry_result.status,'normal')
        self.assertEqual((g.encounter.pulse.king.health.current_hp,g.combat.pending_attack_bonus,g.player.health.current_hp),(22,0,2))

    def test_menu_and_focus_pause_whole_combat_during_pulse(self):
        factory=main._new_stage_game
        def pulse_game():
            g=factory(5)
            g.advance(270)
            return g
        for batches,focus,paused in (
                ([[MENU],[],[],[key(ESC)],[]],None,(1,2,3)),
                ([[],[],[],[],[]],[512,0,0,512,512],(1,2,3))):
            created,snapshots,_,_,_,_=run_loop(batches,initial='playing',initial_factory=pulse_game,
                                               focus=focus,lengths=[8*FIXED_TIME_STEP]*5)
            self.assertEqual(snapshots[1]['tick'],snapshots[2]['tick'])
            self.assertEqual(snapshots[2]['tick'],snapshots[3]['tick'])
            self.assertEqual(created[0].encounter.pulse.state,'PULSE_TELEGRAPH')

    def test_f11_menu_escape_and_quit_remain_available_in_boss_outcomes(self):
        for state in ('clear','dead'):
            created,snapshots,_,menu,display,_=run_loop([[MENU],[key(ESC)],[key(F11)],[key(ESC)]],initial_stage=5,initial=state)
            self.assertEqual(len(created),1)
            self.assertTrue(all(s['tick']==0 for s in snapshots))
            self.assertFalse(menu.is_open)
            display.return_value.toggle.assert_called_once_with()

    def test_actual_hp_status_and_boss_clear_labels_are_read_only(self):
        g=main._new_stage_game(5)
        g.advance(270)
        pulse=g.encounter.pulse
        before=(g.combat.tick,pulse.state,tuple((e.position,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies))
        with patch.object(HealthRenderer,'_text') as text:
            for _ in range(3):
                GameFlowRenderer().draw_stage_label(Mock(),g)
                EnemyAttackRenderer().draw(Mock(),g.encounter.ledger)
        labels=[call.args[1] for call in text.call_args_list]
        self.assertIn('KING HP 22/22',labels)
        self.assertIn('CHECKMATE PULSE',labels)
        self.assertIn('PARRY THE PULSE',labels)
        self.assertEqual(before,(g.combat.tick,pulse.state,tuple((e.position,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies)))
        finish(g,'clear')
        with patch.object(HealthRenderer,'_text') as text:
            GameFlowRenderer().draw(Mock(),g)
        labels=[call.args[1] for call in text.call_args_list]
        self.assertIn('BOSS CLEAR',labels)
        self.assertIn('R TO RESTART',labels)
        self.assertNotIn('N TO CONTINUE',labels)
        self.assertFalse(any('SAVED' in s or 'UNLOCKED' in s for s in labels))


if __name__=='__main__':
    unittest.main()
