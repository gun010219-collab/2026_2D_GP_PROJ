"""Owned Chapter 1 completion and atomic Chapter 2 session preparation."""
import unittest
from types import SimpleNamespace
import sys
from unittest.mock import Mock,patch

import main
from chapter_run import ChapterRun
from game import GameState
from stage_progression import StageProgression
from tests.test_stage_transition import finish
from tests.test_upgrade_flow import flow_at_boss
from tests import test_main as canvas_tests
from tests.test_stage_transition import key,N,R,MENU,ESC,F11,run_loop
from renderer import BoardRenderer
from sdl_input import GameplayInput
from config import FIXED_TIME_STEP
from upgrades import ChapterBuild


def completed_boss():
    flow=flow_at_boss()
    finish(flow.game,'clear')
    return flow


def snapshot(flow):
    return (flow.run,flow.game,flow.run.run_id,flow.run.build,flow.run.receipts,
            flow.run.active_offer,flow.run.retired,flow.game.state)


class ChapterTwoEntryTests(unittest.TestCase):
    def test_four_real_upgrade_receipts_then_entry_resets_new_chapter(self):
        flow=completed_boss();old_run,old_game=flow.run,flow.game
        self.assertEqual(len(old_run.receipts),4)
        self.assertNotEqual(old_run.build,ChapterBuild())
        self.assertIsNone(flow.offer)
        g,prepared=flow.enter_next_chapter(main._new_stage_game)
        self.assertIsNone(prepared)
        self.assertIs(flow.game,g)
        self.assertTrue(old_run.retired)
        self.assertEqual((flow.run.chapter,flow.run.current_stage,flow.run.build,flow.run.receipts),
                         (2,6,ChapterBuild(),()))
        self.assertEqual((g.chapter,g.stage_number,g.player.health.current_hp,g.player.health.max_hp,
                          g.resolver.player_damage,g.combat.tick,g.encounter.tick),(2,6,3,3,1,0,-1))
        self.assertIsNone(g.encounter.pulse)
        self.assertNotEqual(old_run.run_id,flow.run.run_id)
        self.assertNotEqual(old_game.combat.stage_instance_id,g.combat.stage_instance_id)
        self.assertNotEqual(old_game.player.entity_instance_id,g.player.entity_instance_id)

    def test_preparation_observes_old_live_owner_and_returns_prepared_objects(self):
        flow=completed_boss();old_run,old_game=flow.run,flow.game
        marker=object()
        def prepare(stats):
            self.assertIs(flow.game,old_game)
            self.assertIs(flow.run,old_run)
            self.assertFalse(old_run.retired)
            self.assertEqual(stats,ChapterBuild().stats)
            return marker
        g,prepared=flow.enter_next_chapter(main._new_stage_game,prepare)
        self.assertIs(prepared,marker)
        self.assertEqual(g.stage_number,6)

    def test_factory_failure_preserves_completed_run_and_replay_then_retry(self):
        flow=completed_boss();before=snapshot(flow)
        factory=Mock(side_effect=RuntimeError('session generation failure'))
        with self.assertRaises(RuntimeError):flow.enter_next_chapter(factory)
        self.assertEqual(snapshot(flow),before)
        self.assertEqual(flow.run.boss_replay_stats(),before[3].stats)
        flow.enter_next_chapter(main._new_stage_game)
        self.assertEqual((flow.run.chapter,flow.game.stage_number),(2,6))

    def test_input_and_board_preparation_failures_do_not_retire_old_run(self):
        for kind in ('input','board'):
            with self.subTest(kind=kind):
                flow=completed_boss();before=snapshot(flow)
                def fail(stats):raise RuntimeError(kind+' preparation failed')
                with self.assertRaises(RuntimeError):
                    flow.enter_next_chapter(main._new_stage_game,fail)
                self.assertEqual(snapshot(flow),before)
                self.assertEqual(flow.game.restart_stage_number,5)
                self.assertIsNone(flow.offer)

    def test_new_chapter_run_failure_preserves_boss_clear_and_four_receipts(self):
        flow = completed_boss()
        before = snapshot(flow)
        factory = Mock()
        # Preserve the ChapterRun type used by the initial ownership check.
        with patch.object(ChapterRun, '__init__', side_effect=RuntimeError('run creation failed')):
            with self.assertRaises(RuntimeError):
                flow.enter_next_chapter(factory)
        factory.assert_not_called()
        self.assertEqual(snapshot(flow), before)
        self.assertEqual(len(flow.run.receipts), 4)

    def test_prepared_resolver_must_own_all_candidate_runtime_objects(self):
        for component in ('player', 'combat', 'parry', 'encounter'):
            with self.subTest(component=component):
                flow = completed_boss()
                before = snapshot(flow)
                prepare = Mock()
                def broken(number, *, stats):
                    candidate = main._new_stage_game(number, stats=stats)
                    foreign = main._new_stage_game(number, stats=stats)
                    setattr(candidate.resolver, component, getattr(foreign, component))
                    return candidate
                with self.assertRaises(ValueError):
                    flow.enter_next_chapter(broken, prepare)
                prepare.assert_not_called()
                self.assertEqual(snapshot(flow), before)

    def test_invalid_prepared_stats_destination_and_enemy_state_are_rejected(self):
        for change in ('destination','damage','hp','enemy','clock','old_game'):
            with self.subTest(change=change):
                flow=completed_boss();before=snapshot(flow)
                def broken(n,stats):
                    if change=='old_game':return flow.game
                    g=main._new_stage_game(5 if change=='destination' else n,stats=stats)
                    if change=='damage':g.resolver.player_damage=3
                    if change=='hp':g.player.health.apply_damage(1,tick=0)
                    if change=='enemy':g.encounter.enemies[0].health.apply_damage(1,tick=0)
                    if change=='clock':g.combat.advance()
                    return g
                with self.assertRaises(ValueError):flow.enter_next_chapter(broken)
                self.assertEqual(snapshot(flow),before)

    def test_playing_boss_and_ordinary_upgrade_cannot_enter_chapter_two(self):
        flows=[flow_at_boss(),StageProgression(main._new_game())]
        finish(flows[1].game,'clear')
        flows[1].sync_offer()
        for flow in flows:
            before=snapshot(flow);factory=Mock()
            with self.assertRaises(ValueError):flow.enter_next_chapter(factory)
            factory.assert_not_called()
            self.assertEqual(snapshot(flow),before)

    def test_king_death_alone_and_game_over_never_unlock_entry(self):
        for dead_player in (False,True):
            flow=flow_at_boss();g=flow.game
            king=g.encounter.pulse.king
            king.health.apply_damage(king.health.current_hp,tick=0)
            g.encounter.deactivate(king.entity_instance_id,tick=0)
            if dead_player:g.player.health.apply_damage(g.player.health.current_hp,tick=0)
            g.update_state()
            self.assertEqual(g.state,GameState.GAME_OVER if dead_player else GameState.PLAYING)
            before=snapshot(flow)
            with self.assertRaises(ValueError):flow.enter_next_chapter(main._new_stage_game)
            self.assertEqual(snapshot(flow),before)

    def test_external_completed_game_cannot_replace_bound_boss_instance(self):
        flow=completed_boss()
        foreign=main._new_stage_game(5,stats=flow.run.stats)
        finish(foreign,'clear')
        flow.game=foreign
        factory=Mock()
        with self.assertRaises(ValueError):flow.enter_next_chapter(factory)
        factory.assert_not_called()
        self.assertFalse(flow.run.retired)

    def test_retired_or_foreign_run_cannot_authorize_entry(self):
        flow=completed_boss()
        foreign=ChapterRun()
        for i,kind in enumerate(('attack','hp','move','hp'),1):
            foreign.select(foreign.offer_after_clear(i,'foreign-'+str(i)),kind)
        flow.run=foreign
        with self.assertRaises(ValueError):flow.enter_next_chapter(main._new_stage_game)
        own=completed_boss();own.run.retire()
        with self.assertRaises(ValueError):own.enter_next_chapter(main._new_stage_game)

    def test_old_receipts_attacks_and_parries_do_not_leak_into_stage_six(self):
        flow=flow_at_boss();old=flow.game
        old.advance(270)
        enemy_event=old.encounter.ledger.pending[0]
        attack=old.combat.request_attack(old.player)
        attempt=old.parry.request(old.combat.tick)
        old.resolver.register_parry(attempt)
        old.combat.grant_perfect_counter()
        receipt=flow.run.receipts[0]
        finish(old,'clear')
        fresh,_=flow.enter_next_chapter(main._new_stage_game)
        with self.assertRaises(ValueError):fresh.resolver.resolve_enemy_attack(enemy_event)
        with self.assertRaises(ValueError):fresh.resolver.resolve_player_attack(attack)
        with self.assertRaises(ValueError):fresh.resolver.register_parry(attempt)
        self.assertIsNone(fresh.parry.last_attempt)
        self.assertEqual(fresh.combat.pending_attack_bonus,0)
        self.assertEqual(fresh.resolver.player_invulnerable_until_tick,0)
        self.assertEqual(fresh.encounter.ledger.pending,())
        with self.assertRaises(ValueError):flow.run.verify_receipt(receipt)
        with self.assertRaises(ValueError):flow.run.select(receipt.offer,'hp')

    def test_entry_can_only_commit_once_and_does_not_make_stage_seven(self):
        flow=completed_boss()
        factory=Mock(side_effect=main._new_stage_game)
        flow.enter_next_chapter(factory)
        with self.assertRaises(ValueError):flow.enter_next_chapter(factory)
        self.assertEqual(factory.call_count,1)
        self.assertEqual(flow.run.current_stage,6)
        with self.assertRaises(ValueError):main._new_stage_game(11)

    def test_stage_six_game_over_restarts_six_with_new_baseline_run(self):
        flow=completed_boss();flow.enter_next_chapter(main._new_stage_game)
        old_run,old_game=flow.run,flow.game
        finish(old_game,'dead')
        before=snapshot(flow)
        with self.assertRaises(RuntimeError):
            flow.restart(Mock(side_effect=RuntimeError('failed restart')))
        self.assertEqual(snapshot(flow),before)
        fresh,_=flow.restart(main._new_stage_game)
        self.assertEqual((fresh.stage_number,flow.run.chapter,flow.run.current_stage),(6,2,6))
        self.assertEqual((fresh.player.health.current_hp,fresh.resolver.player_damage),(3,1))
        self.assertEqual(flow.run.build,ChapterBuild())
        self.assertTrue(old_run.retired)
        self.assertNotEqual(old_game.combat.stage_instance_id,fresh.combat.stage_instance_id)

    def test_stage_six_restart_input_preparation_failure_keeps_dead_run_for_retry(self):
        flow = completed_boss()
        flow.enter_next_chapter(main._new_stage_game)
        finish(flow.game, 'dead')
        before = snapshot(flow)
        with self.assertRaises(RuntimeError):
            flow.restart(main._new_stage_game, Mock(side_effect=RuntimeError('input failed')))
        self.assertEqual(snapshot(flow), before)
        fresh, controls = flow.restart(main._new_stage_game)
        self.assertIsNone(controls)
        self.assertEqual((fresh.stage_number, fresh.player.health.current_hp), (6, 3))
        self.assertTrue(before[0].retired)

    def test_main_actual_session_input_and_board_failures_keep_old_screen_until_retry(self):
        for failure in ('factory','input','board'):
            with self.subTest(failure=failure):
                flow=completed_boss();old_run,old_game=flow.run,flow.game
                canvas=canvas_tests.WindowLoopTests().make_canvas()
                canvas.SDL_SCANCODE_N=17
                events=iter([[key(N)],[key(N,repeat=True)],[key(N,False)],[key(N)],
                             [SimpleNamespace(type=256)]])
                def poll():
                    batch=next(events)
                    for event in batch:
                        if event.type in (768,769) and event.key==N:
                            canvas.SDL_GetKeyboardState.return_value[17]=int(event.type==768)
                    return batch
                canvas.get_events.side_effect=poll
                now=[0.0];seen=[];themes=[];failed=[False]
                original_factory=main._new_stage_game
                original_prepare=GameplayInput.prepare_session
                original_draw=BoardRenderer.draw
                def fail_once(kind):
                    if kind==failure and not failed[0]:
                        failed[0]=True
                        raise RuntimeError(kind+' creation failed')
                def factory(n,**kwargs):
                    fail_once('factory')
                    return original_factory(n,**kwargs)
                def prepare(self):
                    fail_once('input')
                    original_prepare(self)
                def board(chapter):
                    if chapter==2:fail_once('board')
                    return BoardRenderer(chapter)
                def draw(self,*args,**kwargs):
                    themes.append(self.theme.chapter)
                    original_draw(self,*args,**kwargs)
                def render():
                    seen.append((flow.game,flow.run,flow.run.build,old_run.retired,flow.error))
                    now[0]+=FIXED_TIME_STEP
                canvas.update_canvas.side_effect=render
                with patch.dict(sys.modules,{'pico2d':SimpleNamespace(pico2d=canvas)}), \
                     patch.object(main,'_new_game',return_value=old_game), \
                     patch.object(main,'StageProgression',return_value=flow), \
                     patch.object(main,'_new_stage_game',side_effect=factory), \
                     patch.object(main,'BoardRenderer',side_effect=board), \
                     patch.object(BoardRenderer,'draw',draw), \
                     patch.object(GameplayInput,'prepare_session',prepare), \
                     patch.object(main,'DisplaySettings'), \
                     patch.object(main,'SettingsRenderer'), \
                     patch.object(main,'perf_counter',side_effect=lambda:now[0]), \
                     patch.object(main,'sleep'):
                    main.main(run=old_run)
                self.assertTrue(failed[0])
                self.assertEqual(len(seen),4)
                self.assertEqual(themes,[1,1,1,2])
                for game,run,build,retired,error in seen[:3]:
                    self.assertIs(game,old_game)
                    self.assertIs(run,old_run)
                    self.assertEqual(build,old_run.build)
                    self.assertFalse(retired)
                    self.assertTrue(error)
                self.assertEqual(seen[-1][0].stage_number,6)
                self.assertEqual(seen[-1][2],ChapterBuild())
                self.assertTrue(seen[-1][3])
                self.assertFalse(seen[-1][4])
                canvas.close_canvas.assert_called_once_with()

    def test_main_next_requires_release_after_disabled_hold_or_repeat(self):
        def clear_after_first(game,frame):
            if frame==0:finish(game,'clear')
        created,snapshots,*_=run_loop([[key(N)],[key(N)],
            [key(N,repeat=True)],[key(N,False)],[key(N)]],
            initial_stage=5,initial='playing',after_render=clear_after_first)
        self.assertEqual([g.stage_number for g in created],[5,6])
        self.assertEqual([s['count'] for s in snapshots],[1,1,1,1,2])
        self.assertEqual(snapshots[-1]['tick'],0)

    def test_main_settings_f11_and_focus_block_next_until_release_and_fresh_press(self):
        cases=(
            ([[MENU,key(N)],[key(ESC),key(N)],[key(N,False)],[key(N)]],None),
            ([[key(F11),key(N)],[key(N)],[key(N,False)],[key(N)]],None),
            ([[],[key(N)],[key(N)],[key(N,False)],[key(N)]],[512,0,512,512,512]),
        )
        for batches,focus in cases:
            with self.subTest(batches=batches,focus=focus):
                created,snapshots,_,menu,_,_=run_loop(batches,initial_stage=5,focus=focus)
                self.assertEqual([g.stage_number for g in created],[5,6])
                self.assertTrue(all(s['stage']==5 and s['tick']==0 for s in snapshots[:-1]))
                self.assertEqual((snapshots[-1]['stage'],snapshots[-1]['tick']),(6,0))
                self.assertFalse(menu.is_open)

    def test_main_next_and_replay_orders_allow_only_one_successful_transition(self):
        for keys,target in (((N,R,N),6),((R,N,R),5)):
            with self.subTest(keys=keys):
                created,snapshots,*_=run_loop([[key(k) for k in keys]],initial_stage=5)
                self.assertEqual([g.stage_number for g in created],[5,target])
                self.assertEqual(snapshots[0]['tick'],0)
                if target==5:
                    self.assertEqual((created[-1].player.health.current_hp,
                                      created[-1].resolver.player_damage),(4,2))
                else:
                    self.assertEqual((created[-1].player.health.current_hp,
                                      created[-1].resolver.player_damage),(3,1))

    def test_main_failed_next_can_replay_in_same_batch_then_enter_on_new_press(self):
        original=main._new_stage_game;calls=[]
        def flaky(n,**kwargs):
            calls.append(n)
            if n==6 and calls.count(6)==1:raise RuntimeError('failed chapter entry')
            return original(n,**kwargs)
        def clear_replayed_boss(game,frame):
            if frame==0:finish(game,'clear')
        with patch.object(main,'_new_stage_game',side_effect=flaky):
            created,snapshots,*_=run_loop([[key(N),key(R)],
                [key(R,False),key(N,repeat=True)],[key(N,False)],[key(N)]],
                initial_stage=5,after_render=clear_replayed_boss)
        # The first 5 is only the harness bootstrap. Failed 6 is never active.
        self.assertEqual(calls,[5,6,5,6])
        self.assertEqual([g.stage_number for g in created],[5,5,6])
        self.assertEqual([s['stage'] for s in snapshots],[5,5,5,6])
        self.assertEqual((created[1].player.health.current_hp,created[1].resolver.player_damage),(4,2))
        self.assertEqual((created[-1].player.health.current_hp,created[-1].resolver.player_damage),(3,1))


if __name__=='__main__':unittest.main()
