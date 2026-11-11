"""Stage 4 flow, mixed combat and UI through the existing main loop."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main
from config import FIXED_TIME_STEP
from game import GameState
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from tests.test_stage_transition import N,R,UP,SPACE,SHIFT,F11,ESC,MENU,key,finish,run_loop
from tests.test_stage_three import play_to
from tests.test_bishop import battle,bishop
from enemy import Enemy


def play_four(end,**kwargs):
    factory=main._new_stage_game
    return play_to(end,factory=lambda:factory(4),**kwargs)


class StageFourFlowTests(unittest.TestCase):
    def test_stage_three_clear_n_creates_four_with_zero_clock_and_original_data(self):
        created,snapshots,_,_,_,clock=run_loop([[key(N)],[]],initial_stage=3)
        self.assertEqual([g.stage_number for g in created],[3,4])
        g=created[-1]
        self.assertEqual((snapshots[0]['tick'],g.player.position,g.player.health.current_hp),(0,(5,1),3))
        self.assertEqual([(e.kind,e.position,e.health.current_hp) for e in g.encounter.enemies],
                         [('bishop',(2,8),3),('rook',(2,4),4),('pawn',(1,6),2),('pawn',(8,6),2)])
        self.assertLess(clock.accumulator,FIXED_TIME_STEP)

    def test_clear_r_replays_four_death_r_returns_one_and_n_never_reaches_five(self):
        for state,target in (('clear',4),('dead',1)):
            created,snapshots,_,_,_,_=run_loop([[key(N)],[key(R)]],initial_stage=4,initial=state)
            self.assertEqual([g.stage_number for g in created],[4,target])
            self.assertEqual(snapshots[0]['count'],1)
            self.assertEqual((snapshots[1]['tick'],snapshots[1]['hp']),(0,3))
        with self.assertRaises(ValueError):
            main._new_stage_game(5)

    def test_playing_n_and_r_do_not_restart_four(self):
        created,_,_,_,_,_=run_loop([[key(N),key(R)]],initial_stage=4,initial='playing')
        self.assertEqual(len(created),1)

    def test_four_requires_all_deaths_and_player_death_has_priority(self):
        for dead in (False,True):
            g=main._new_stage_game(4)
            for enemy in g.encounter.enemies[:3]:
                enemy.health.apply_damage(enemy.health.current_hp,tick=0)
                g.encounter.deactivate(enemy.entity_instance_id)
            self.assertFalse(g.update_state())
            g.encounter.enemies[-1].health.apply_damage(2,tick=0)
            if dead:
                g.player.health.apply_damage(3,tick=0)
            g.update_state()
            self.assertEqual(g.state,GameState.GAME_OVER if dead else GameState.STAGE_CLEAR)
            self.assertFalse(g.update_state())

    def test_session_replacement_resets_all_state_and_rejects_previous_events(self):
        for before,after in ((3,4),(4,4),(4,1)):
            old=main._new_stage_game(before)
            old.advance(140)
            events=old.encounter.ledger.telegraphs
            attack=old.combat.request_attack(old.player)
            attempt=old.parry.request(old.combat.tick)
            old.resolver.register_parry(attempt)
            old.combat.grant_perfect_counter()
            old.resolver.player_invulnerable_until_tick=old.combat.tick+48
            old.encounter.stun(old.encounter.enemies[0].entity_instance_id,old.combat.tick)
            old.resolver.stop()
            fresh=main._new_stage_game(after)
            self.assertEqual((fresh.combat.tick,fresh.combat.next_attack_tick,fresh.parry.next_parry_tick,
                              fresh.combat.pending_attack_bonus,fresh.resolver.player_invulnerable_until_tick),(0,0,0,0,0))
            self.assertEqual(fresh.player.position,(5,1))
            self.assertEqual(fresh.player.health.current_hp,3)
            self.assertIsNone(fresh.player.health.last_damage_tick)
            self.assertIsNone(fresh.parry.last_attempt)
            self.assertIsNone(fresh.resolver.last_parry_result)
            self.assertEqual(fresh.encounter.ledger.telegraphs,())
            self.assertEqual(fresh.encounter._attack_moves,{})
            self.assertEqual(fresh.encounter._bishop_closed_tick,{})
            self.assertNotEqual(old.combat.combat_session_id,fresh.combat.combat_session_id)
            self.assertNotEqual(old.combat.stage_instance_id,fresh.combat.stage_instance_id)
            self.assertNotEqual(old.player.entity_instance_id,fresh.player.entity_instance_id)
            self.assertTrue({e.entity_instance_id for e in old.encounter.enemies}.isdisjoint(
                e.entity_instance_id for e in fresh.encounter.enemies))
            self.assertTrue(all(e.current_attack is None and e.stun_until_tick==0 for e in fresh.encounter.enemies))
            with self.assertRaises(ValueError):
                fresh.resolver.resolve_player_attack(attack)
            with self.assertRaises(ValueError):
                fresh.resolver.register_parry(attempt)
            for event in events:
                with self.assertRaises(ValueError):
                    fresh.resolver.resolve_enemy_attack(event)

    def test_held_flow_and_combat_keys_cannot_generate_ghost_actions_after_transition(self):
        created,snapshots,_,_,_,_=run_loop([
            [key(N),key(SPACE),key(SHIFT),key(UP),key(R)],
            [key(N),key(SPACE),key(SHIFT),key(UP)],
            [key(N,False),key(R,False),key(SPACE,False),key(SHIFT,False),key(UP,False)],
            [key(UP),key(SPACE),key(SHIFT)]],initial_stage=3)
        self.assertEqual([g.stage_number for g in created],[3,4])
        self.assertTrue(all(s['position']==(5,1) and s['attack']==s['parry']==0 for s in snapshots[:3]))
        self.assertEqual(created[-1].player.position,(5,2))
        self.assertEqual(created[-1].combat.active_attack.start_tick,3)

    def test_same_frame_flow_order_and_repeated_restart_have_no_clock_debt(self):
        for keys,target in (([N,R,N],4),([R,N,R],3)):
            created,_,_,_,_,_=run_loop([[key(k) for k in keys]],initial_stage=3)
            self.assertEqual([g.stage_number for g in created],[3,target])
        def clear_again(g,frame):
            finish(g,'clear')
        created,snapshots,_,_,_,clock=run_loop([[key(R),key(R,False)] for _ in range(5)],
            initial_stage=4,after_render=clear_again,lengths=[20]*5)
        self.assertEqual(len({g.combat.stage_instance_id for g in created}),6)
        self.assertTrue(all(s['tick']==0 for s in snapshots))
        self.assertEqual(clock.accumulator,0)

    def test_menu_focus_and_f11_block_stage_three_progress_until_fresh_press(self):
        for batches,focus in (([[MENU,key(N)],[key(ESC),key(N)],[key(N,False)],[key(N)]],None),
                              ([[key(F11),key(N)],[key(N)],[key(N,False)],[key(N)]],None),
                              ([[],[key(N)],[key(N)],[key(N,False)],[key(N)]],[512,0,512,512,512])):
            created,snapshots,_,_,_,_=run_loop(batches,initial_stage=3,focus=focus)
            self.assertTrue(all(s['stage']==3 for s in snapshots[:-1]))
            self.assertEqual(created[-1].stage_number,4)

    def test_terminal_menu_display_escape_and_close_remain_available(self):
        for state in ('clear','dead'):
            created,snapshots,_,menu,display,_=run_loop([[MENU],[key(ESC)],[key(F11)],[key(ESC)]],
                                                     initial_stage=4,initial=state)
            self.assertEqual(len(created),1)
            self.assertTrue(all(s['tick']==0 for s in snapshots))
            self.assertFalse(menu.is_open)
            display.return_value.toggle.assert_called_once_with()
        created,snapshots,_,_,_,_=run_loop([[key(R),SimpleNamespace(type=256)]],initial_stage=4)
        self.assertEqual((len(created),len(snapshots)),(1,0))


class StageFourMainCombatTests(unittest.TestCase):
    def test_original_108_tick_warning_hit_and_no_position_change_in_actual_main(self):
        seen={}
        def record(g,t):
            source=g.encounter.enemies[0]
            seen[t]=(source.position,g.player.health.current_hp,source.current_attack)
            cells=[g.player.position]+[e.position for e in g.encounter.enemies if e.active]
            self.assertEqual(len(cells),len(set(cells)))
        created,_,_,_,_,_=play_four(156,samples=(48,155),observe=record)
        self.assertEqual((seen[48][2].start_tick,seen[48][2].hit_tick,len(seen[48][2].target_cells)),(48,156,50))
        self.assertEqual(seen[155][:2],((2,8),3))
        self.assertEqual(seen[156][:2],((2,8),2))
        self.assertEqual(created[-1].player.health.last_damage_tick,156)

    def test_cardinal_step_evades_board_color_and_reentry_is_damage_not_cancellation(self):
        for inputs,hp in (({155:[key(UP)]},3),
                          ({140:[key(UP),key(UP,False)],155:[key(1073741905)]},2)):
            created,_,_,_,_,_=play_four(156,inputs=inputs)
            self.assertEqual(created[-1].player.health.current_hp,hp)
            self.assertEqual(created[-1].encounter.enemies[0].position,(2,8))

    def test_normal_and_perfect_parry_with_other_attackers_independent(self):
        for delta,grade in ((18,'normal'),(7,'perfect')):
            created,_,_,_,_,_=play_four(156,inputs={156-delta:[key(SHIFT)]})
            g=created[-1]
            self.assertEqual(g.resolver.last_parry_result.status,grade)
            self.assertEqual(g.player.health.current_hp,3)
            self.assertEqual(g.combat.pending_attack_bonus,2 if grade=='perfect' else 0)
            self.assertEqual(g.encounter.enemies[0].position,(2,8))
            self.assertTrue(all(e.state!='stunned' for e in g.encounter.enemies[1:]))

    def test_perfect_stun_boundary_and_counter_cooldown_reset_in_main(self):
        seen={}
        def record(g,t):
            if t in (156,215,216):
                seen[t]=(g.encounter.enemies[0].state,g.encounter.enemies[0].current_attack,g.combat.next_attack_tick)
        created,_,_,_,_,_=play_four(216,inputs={140:[key(SPACE)],149:[key(SHIFT)]},
                                    samples=(156,215),observe=record)
        self.assertEqual(seen[156][0],'stunned')
        self.assertEqual(seen[156][2],156)
        self.assertEqual(seen[215][0],'stunned')
        self.assertEqual(seen[216][1].start_tick,216)

    def test_settings_and_focus_pause_bishop_telegraph_and_time(self):
        factory=main._new_stage_game
        def warned():
            g=factory(4)
            g.advance(48)
            return g
        for batches,focus in (([[MENU],[],[key(ESC)],[]],None),([[],[],[],[]],[512,0,512,512])):
            created,snapshots,_,_,_,_=run_loop(batches,initial='playing',initial_factory=warned,
                focus=focus,lengths=[8*FIXED_TIME_STEP]*4)
            self.assertTrue(all(s['tick']==48 for s in snapshots[:3]))
            self.assertEqual(snapshots[-1]['tick'],56)
            self.assertEqual(created[-1].encounter.enemies[0].current_attack.hit_tick,156)

    def test_actual_death_freezes_at_458_and_r_returns_to_stage_one(self):
        created,snapshots,_,_,_,_=play_four(480,inputs={480:[key(R)]},samples=(458,472))
        dead,fresh=created
        self.assertEqual((dead.state,dead.combat.tick,dead.player.health.current_hp),(GameState.GAME_OVER,458,0))
        self.assertEqual((fresh.stage_number,fresh.combat.tick,fresh.player.health.current_hp),(1,0,3))

    def test_final_bishop_space_kill_clears_four_and_r_replays_same_stage(self):
        factory=main._new_stage_game
        def almost_clear():
            g=factory(4)
            b=g.encounter.enemies[0]
            b.col,b.row=5,2
            b.health.apply_damage(2,tick=0)
            for e in g.encounter.enemies[1:]:
                e.health.apply_damage(e.health.current_hp,tick=0)
                g.encounter.deactivate(e.entity_instance_id)
            return g
        created,snapshots,_,_,_,_=run_loop([[key(SPACE),key(N)],[key(N,False),key(N)],[key(R)]],
            initial='playing',initial_factory=almost_clear)
        self.assertEqual([g.stage_number for g in created],[4,4])
        self.assertEqual(snapshots[0]['state'],GameState.STAGE_CLEAR)
        self.assertEqual([e.health.current_hp for e in created[-1].encounter.enemies],[3,4,2,2])

    def test_bishop_rook_knight_pawn_same_tick_share_ledger_and_invulnerability(self):
        enemies=(bishop(),Enemy('r',2,1,None,1.0,kind='rook'),
                 Enemy('k',4,3,None,1.2,kind='knight'),Enemy('p',4,2,(0,-1),1.15))
        p,c,q,e,r=battle(enemies)
        r.advance(107)
        events=[x.current_attack for x in e.enemies]
        self.assertTrue(all(x.hit_tick==108 for x in events))
        r.advance(1)
        self.assertEqual([e.ledger.outcome(x) for x in events],['hit','invulnerable','invulnerable','invulnerable'])
        self.assertEqual(p.health.current_hp,2)
        self.assertEqual(e.enemies[0].position,(2,8))

    def test_repeated_stage_four_simulations_are_deterministic_and_collision_free(self):
        traces=[]
        for _ in range(2):
            g=main._new_stage_game(4)
            rows=[]
            for step in range(601):
                cells=[g.player.position]+[e.position for e in g.encounter.enemies if e.active]
                self.assertEqual(len(cells),len(set(cells)))
                rows.append((g.combat.tick,g.player.health.current_hp,
                             [(e.kind,e.position,e.state,e.next_action_tick) for e in g.encounter.enemies]))
                g.advance(1)
            traces.append(rows)
        self.assertEqual(traces[0],traces[1])
        self.assertEqual(traces[0][-1][0],458)


class StageFourRendererTests(unittest.TestCase):
    def test_actual_hp_and_terminal_prompts_do_not_claim_chapter_clear(self):
        for state in ('playing','clear','dead'):
            g=main._new_stage_game(4)
            if state!='playing':
                finish(g,state)
            with patch.object(HealthRenderer,'_text') as text:
                GameFlowRenderer().draw_stage_label(Mock(),g)
                GameFlowRenderer().draw(Mock(),g)
                HealthRenderer().draw(Mock(),g.player,g.encounter.enemies,g.combat.tick)
            labels=[call.args[1] for call in text.call_args_list]
            self.assertIn('STAGE 4',labels)
            self.assertNotIn('N TO CONTINUE',labels)
            self.assertFalse(any('CHAPTER CLEAR' in s or 'ENDING' in s or 'STAGE 5' in s for s in labels))
            if state=='playing':
                self.assertEqual(labels.count('3/3'),2)
                self.assertEqual(labels.count('4/4'),1)
                self.assertEqual(labels.count('2/2'),2)
            elif state=='clear':
                self.assertIn('R TO RESTART',labels)
            else:
                self.assertIn('R TO STAGE 1',labels)


if __name__=='__main__':
    unittest.main()
