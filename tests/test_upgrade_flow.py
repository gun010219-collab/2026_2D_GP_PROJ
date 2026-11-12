"""Real progression ownership, precommit preparation, input and renderer contracts."""
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import main
from chapter_run import ChapterRun
from game import GameState
from health_renderer import HealthRenderer
from stage_progression import StageProgression
from upgrade_input import UpgradeInput
from upgrade_renderer import UpgradeRenderer, CARD_RECTS
from upgrades import ChapterBuild
from tests.test_stage_transition import run_loop, key, N,R,UP,SPACE,SHIFT,MENU,ESC,F11,finish
from tests import test_main as canvas_tests


def clear(flow):
    finish(flow.game,'clear')
    return flow.sync_offer()


def flow_at_boss(choices=('attack','hp','move','hp')):
    flow=StageProgression(main._new_game())
    for kind in choices:
        o=clear(flow)
        flow.choose(o,kind,main._new_stage_game)
    return flow


class UpgradeFlowTests(unittest.TestCase):
    def test_real_ordinary_clear_has_upgrade_state_and_no_n_or_r(self):
        flow=StageProgression(main._new_game())
        offer=clear(flow)
        g=flow.game
        self.assertEqual(g.state,GameState.UPGRADE)
        self.assertIsNone(g.next_stage_number)
        self.assertIsNone(g.restart_stage_number)
        self.assertIs(flow.sync_offer(),offer)
        before=(g.combat.tick,g.encounter.tick,g.transition_count,len(g.encounter.ledger._records))
        g.advance(1000)
        self.assertEqual(before,(g.combat.tick,g.encounter.tick,g.transition_count,len(g.encounter.ledger._records)))

    def test_offer_requires_actual_own_live_player_clear_and_correct_run(self):
        flow=StageProgression(main._new_game())
        self.assertIsNone(flow.sync_offer())
        with self.assertRaises(ValueError):
            flow.choose(None,'attack',main._new_stage_game)
        flow.game.player.health.apply_damage(3,tick=0)
        finish(flow.game,'clear')
        self.assertEqual(flow.game.state,GameState.GAME_OVER)
        self.assertIsNone(flow.sync_offer())
        with self.assertRaises(ValueError):
            StageProgression(main._new_stage_game(2))

    def test_all_four_real_choices_propagate_stats_and_fresh_sessions(self):
        flow=StageProgression(main._new_game())
        stages=[]
        for i,kind in enumerate(('attack','hp','move','hp'),1):
            old=flow.game
            stages.append(old.stage_number)
            o=clear(flow)
            candidate,_=flow.choose(o,kind,main._new_stage_game)
            self.assertEqual(candidate.stage_number,i+1)
            self.assertEqual((candidate.player.health.max_hp,candidate.player.health.current_hp),
                             (flow.run.stats.max_hp,flow.run.stats.max_hp))
            self.assertEqual(candidate.resolver.player_damage,flow.run.stats.attack_damage)
            self.assertNotEqual(old.combat.stage_instance_id,candidate.combat.stage_instance_id)
            self.assertEqual(candidate.combat.tick,0)
            self.assertEqual(sum((flow.run.build.attack_level,flow.run.build.hp_level,flow.run.build.move_level)),i)
        self.assertEqual(stages+[flow.game.stage_number],[1,2,3,4,5])
        self.assertEqual(flow.run.build,ChapterBuild(1,2,1))
        self.assertEqual([e.health.max_hp for e in flow.game.encounter.enemies],[22,6,3,3])

    def test_factory_failure_does_not_consume_then_retry_commits_once(self):
        flow=StageProgression(main._new_game());o=clear(flow)
        def fail(*args,**kwargs):raise RuntimeError('generation failed')
        with self.assertRaises(RuntimeError):flow.choose(o,'hp',fail)
        self.assertEqual((flow.run.build,flow.run.receipts,flow.game.state),(ChapterBuild(),(),GameState.UPGRADE))
        self.assertIs(flow.offer,o)
        flow.choose(o,'hp',main._new_stage_game)
        self.assertEqual((len(flow.run.receipts),flow.game.stage_number),(1,2))
        with self.assertRaises(ValueError):flow.choose(o,'attack',main._new_stage_game)

    def test_input_preparation_failure_also_preserves_offer(self):
        flow=StageProgression(main._new_game());o=clear(flow)
        def fail(stats):raise RuntimeError('input failure')
        with self.assertRaises(RuntimeError):flow.choose(o,'move',main._new_stage_game,fail)
        self.assertIs(flow.offer,o)
        self.assertEqual(flow.run.build,ChapterBuild())

    def test_wrong_destination_stats_health_and_enemy_data_are_rejected_precommit(self):
        for change in ('stage','damage','hp','enemy','clock','shared_health'):
            flow=StageProgression(main._new_game());o=clear(flow)
            def broken(n,stats):
                g=main._new_stage_game(n if change!='stage' else 3,stats=stats)
                if change=='damage':g.resolver.player_damage=99
                if change=='hp':g.player.health.apply_damage(1,tick=0)
                if change=='enemy':g.encounter.enemies[0].health.apply_damage(1,tick=0)
                if change=='clock':g.combat.advance()
                if change=='shared_health':g.player.health=flow.game.player.health
                return g
            with self.assertRaises(ValueError):flow.choose(o,'attack',broken)
            self.assertEqual(flow.run.build,ChapterBuild())
            self.assertIs(flow.offer,o)

    def test_copied_foreign_stale_and_max_choices_do_not_build_a_session(self):
        flow=StageProgression(main._new_game());o=clear(flow)
        factory=Mock()
        for fake in (replace(o),ChapterRun().offer_after_clear(1,'foreign'),None):
            with self.assertRaises(ValueError):flow.choose(fake,'hp',factory)
        factory.assert_not_called()
        flow.choose(o,'move',main._new_stage_game)
        flow.choose(clear(flow),'move',main._new_stage_game)
        o=clear(flow)
        self.assertTrue(o.options[2].is_max)
        with self.assertRaises(ValueError):flow.choose(o,'move',factory)
        factory.assert_not_called()

    def test_boss_clear_replay_retains_build_without_a_fifth_offer(self):
        flow=flow_at_boss();run=flow.run;build=run.build
        clear(flow)
        self.assertEqual(flow.game.state,GameState.BOSS_CLEAR)
        self.assertIsNone(flow.offer)
        old=flow.game
        g,_=flow.restart(main._new_stage_game)
        self.assertIs(flow.run,run)
        self.assertEqual(flow.run.build,build)
        self.assertEqual((g.player.health.current_hp,g.resolver.player_damage),(5,2))
        self.assertEqual(len(run.receipts),4)
        self.assertNotEqual(g.combat.stage_instance_id,old.combat.stage_instance_id)

    def test_game_over_resets_after_prepare_and_retires_previous_run(self):
        flow=flow_at_boss();old=flow.run
        finish(flow.game,'dead')
        def fail(*args,**kwargs):raise RuntimeError('failed restart')
        with self.assertRaises(RuntimeError):flow.restart(fail)
        self.assertFalse(old.retired)
        g,_=flow.restart(main._new_stage_game)
        self.assertTrue(old.retired)
        self.assertEqual((flow.run.build,g.stage_number,g.player.health.current_hp), (ChapterBuild(),1,3))

    def test_boss_restart_failure_does_not_discard_terminal_state(self):
        flow=flow_at_boss();clear(flow);old=flow.game
        with self.assertRaises(ValueError):flow.restart(lambda n,stats:old)
        self.assertIs(flow.game,old)
        self.assertEqual(len(flow.run.receipts),4)

    def test_keyboard_repeat_blocking_mouse_and_max_do_not_mutate_view(self):
        c=canvas_tests.WindowLoopTests().make_canvas();inputs=UpgradeInput()
        self.assertIsNone(inputs.handle(key(49),c,blocked=True))
        self.assertIsNone(inputs.handle(key(49),c))
        inputs.handle(key(49,False),c)
        self.assertEqual(inputs.handle(key(49),c),0)
        self.assertIsNone(inputs.handle(key(49,repeat=True),c))
        click=SimpleNamespace(type=1025,button=1)
        self.assertEqual(inputs.handle(click,c,point=(730,400)),1)
        self.assertIsNone(inputs.handle(click,c,point=(990,400)))
        inputs.handle(SimpleNamespace(type=1026,button=1),c)
        self.assertEqual(inputs.handle(click,c,point=(990,400)),2)
        inputs.handle(SimpleNamespace(type=1026,button=1),c)
        self.assertIsNone(inputs.handle(click,c,point=None))

    def test_renderer_reads_real_values_and_max_without_consuming(self):
        flow=StageProgression(main._new_game())
        for _ in range(2):flow.choose(clear(flow),'move',main._new_stage_game)
        o=clear(flow);before=(flow.run.build,flow.run.receipts,flow.game.combat.tick)
        with patch.object(UpgradeRenderer,'_text') as text:
            for _ in range(3):UpgradeRenderer().draw(Mock(),flow.game,o)
        labels=[x.args[1] for x in text.call_args_list]
        for value in ('UPGRADE','1 ATTACK','2 MAX HP','3 MOVE','MAX','NOW 12','NEXT 4','NEXT 2'):
            self.assertIn(value,labels)
        self.assertEqual(before,(flow.run.build,flow.run.receipts,flow.game.combat.tick))

    def test_main_keyboard_and_mouse_and_same_batch_select_only_once(self):
        click=SimpleNamespace(type=1025,button=1,x=730,y=500)
        for batch in ([key(49),key(50),key(SPACE),key(UP)],[click,key(49)]):
            created,snapshots,*_=run_loop([batch,[]])
            self.assertEqual([g.stage_number for g in created],[1,2])
            self.assertEqual(snapshots[0]['tick'],0)
            self.assertEqual(created[-1].player.position,(5,1))
        self.assertEqual(created[-1].player.health.max_hp,4)

    def test_main_r_n_cannot_escape_upgrade_and_menu_has_input_priority(self):
        created,snapshots,*_=run_loop([[key(N),key(R)],[MENU,key(49)],
            [key(ESC),key(49,False)],[key(49)]])
        self.assertEqual([s['count'] for s in snapshots],[1,1,1,2])
        self.assertEqual(created[-1].resolver.player_damage,2)

    def test_main_max_keys_are_ignored_while_other_cards_can_advance(self):
        def terminal(g,frame):
            if g.playing:finish(g,'clear')
        created,_,*_=run_loop([[key(51),key(51,False)],[],[key(51),key(51,False)],[],
                                [key(51),key(51,False)],[key(50)]],after_render=terminal)
        self.assertEqual([g.stage_number for g in created],[1,2,3,4])
        self.assertEqual(created[-1].player.health.max_hp,4)

    def test_actual_gameplay_input_activates_all_three_deadlines(self):
        from sdl_input import GameplayInput
        for interval in (18,15,12):
            c=canvas_tests.WindowLoopTests().make_canvas();g=main._new_game()
            controls=GameplayInput(c,move_interval_ticks=interval)
            controls.handle_key(key(UP),g.player,g.combat)
            controls.handle_key(key(UP,False),g.player,g.combat)
            g.combat.advance(interval-1)
            controls.handle_key(key(1073741903),g.player,g.combat)
            self.assertEqual(g.player.position,(5,2))
            controls.handle_key(key(1073741903,False),g.player,g.combat)
            g.combat.advance()
            controls.handle_key(key(1073741903),g.player,g.combat)
            self.assertEqual(g.player.position,(6,2))
            controls.handle_key(key(SPACE),g.player,g.combat)
            controls.handle_key(key(SHIFT),g.player,g.combat,parry=g.parry)
            self.assertIsNotNone(g.combat.active_attack)
            self.assertIsNotNone(g.parry.last_attempt)

    def test_application_exit_retires_pending_offer_and_rejects_late_choice(self):
        flow=StageProgression(main._new_game());o=clear(flow)
        self.assertTrue(flow.run.retire())
        self.assertFalse(flow.run.retire())
        self.assertIsNone(flow.offer)
        with self.assertRaises(ValueError):flow.run.select(o,'hp')
        with self.assertRaises(ValueError):flow.choose(o,'hp',main._new_stage_game)
        self.assertEqual(flow.run.build,ChapterBuild())

    def test_main_all_hp_levels_and_both_attack_levels_enter_real_sessions(self):
        def terminal(g,frame):
            if g.playing:finish(g,'clear')
        for kinds,expected in (((50,50,50,49),((3,1),(4,1),(5,1),(6,1),(6,2))),
                               ((49,49,50,50),((3,1),(3,2),(3,3),(4,3),(5,3)))):
            batches=[batch for k in kinds for batch in ([key(k),key(k,False)],[])]
            created,_,*_=run_loop(batches,after_render=terminal)
            self.assertEqual([(g.player.health.max_hp,g.resolver.player_damage) for g in created],list(expected))
            self.assertEqual([g.stage_number for g in created],[1,2,3,4,5])
            self.assertEqual(created[-1].encounter.pulse.king.health.max_hp,22)

    def test_same_movement_schedule_is_identical_with_one_or_eight_tick_frames(self):
        schedule={0:[key(UP),key(UP,False)],17:[key(1073741903),key(1073741903,False)],
                  18:[key(1073741903),key(1073741903,False)],36:[key(SPACE)]}
        results=[]
        for stride in (1,8):
            ticks=sorted(set(range(0,41,stride))|set(schedule)|{40})
            lengths=[(b-a)/60 for a,b in zip(ticks,ticks[1:])]+[1/60]
            created,_,*_=run_loop([schedule.get(t,[]) for t in ticks],initial='playing',lengths=lengths)
            g=created[-1]
            results.append((g.combat.tick,g.player.position,g.player.facing,g.combat.active_attack.start_tick,
                            tuple((e.position,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies)))
        self.assertEqual(results[0],results[1])
        self.assertEqual(results[0][:4],(40,(6,2),'right',36))

    def test_main_factory_failure_keeps_offer_until_a_new_successful_press(self):
        original=main._new_stage_game
        calls=[]
        def flaky(n,**kwargs):
            calls.append(n)
            if len(calls)==1:raise RuntimeError('candidate failure')
            return original(n,**kwargs)
        with patch.object(main,'_new_stage_game',side_effect=flaky):
            created,snapshots,*_=run_loop([[key(50)],[key(50,repeat=True)],
                                         [key(50,False)],[key(50)]])
        self.assertEqual([s['count'] for s in snapshots],[1,1,1,2])
        self.assertEqual(calls,[2,2])
        self.assertEqual(created[-1].player.health.current_hp,4)

    def test_main_uses_upgraded_movement_intervals_when_replacing_input(self):
        from sdl_input import GameplayInput
        intervals=[]
        def controls(canvas,**kwargs):
            intervals.append(kwargs['move_interval_ticks'])
            return GameplayInput(canvas,**kwargs)
        def terminal(g,frame):
            if g.playing:finish(g,'clear')
        with patch.object(main,'GameplayInput',side_effect=controls):
            created,_,*_=run_loop([batch for k in (51,51,50,50)
                                  for batch in ([key(k),key(k,False)],[])],after_render=terminal)
        self.assertEqual(intervals,[18,15,12,12,12])
        self.assertEqual(created[-1].stage_number,5)

    def test_shared_card_bounds_and_logical_letterbox_coordinates(self):
        from display_settings import logical_mouse_to_canvas
        from upgrade_renderer import card_at
        for i,r in enumerate(CARD_RECTS):
            self.assertEqual(card_at(logical_mouse_to_canvas(r.left,899-r.bottom)),i)
            self.assertEqual(card_at((r.left+r.width-1,r.bottom+r.height-1)),i)
            self.assertIsNone(card_at((r.left+r.width,r.bottom)))
        for x,y in ((-1,300),(1440,300),(700,-1),(700,900)):
            self.assertIsNone(card_at(logical_mouse_to_canvas(x,y)))


if __name__=='__main__':unittest.main()
