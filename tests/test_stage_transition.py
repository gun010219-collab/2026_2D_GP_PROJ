"""Supported stage sessions and main flow using deterministic fake SDL/time."""
from chapter_run import ChapterRun
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

import main
from config import FIXED_TIME_STEP
from game import GameState, StageGame, StageOneGame
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from sdl_input import GameplayInput
from simulation_clock import SimulationClock
from stage_manager import StageCatalog
from tests import test_main as canvas_tests


N, R, UP, LEFT, SPACE, SHIFT, F11, ESC = (110, 114, 1073741906, 1073741904,
                                       32, 1073742049, 1073741892, 27)
MENU = SimpleNamespace(type=1025, button=1, x=1295, y=41)


def key(value, down=True, repeat=False):
    return SimpleNamespace(type=768 if down else 769, key=value, repeat=repeat)


def finish(game, state):
    if state == 'dead':
        game.player.health.apply_damage(game.player.health.current_hp, tick=game.combat.tick)
    elif state == 'clear':
        for enemy in game.encounter.enemies:
            if enemy.alive:
                enemy.health.apply_damage(enemy.health.current_hp, tick=game.combat.tick)
            game.encounter.deactivate(enemy.entity_instance_id)
    game.update_state()


def run_loop(batches, *, initial_stage=1, initial='clear', focus=None, lengths=None,
             after_render=None, initial_factory=None):
    """Use actual factories/loop/renderers; replace only the desktop and time."""
    canvas = canvas_tests.WindowLoopTests().make_canvas()
    canvas.SDL_SCANCODE_R, canvas.SDL_SCANCODE_N = 21, 17
    scans = {49:30,50:31,51:32,N: 17, R: 21, UP: 82, LEFT: 80, SPACE: 44, SHIFT: 225}
    flags = focus if focus is not None else [512] * len(batches)
    queued = iter(zip(batches + [[SimpleNamespace(type=256)]], flags + [flags[-1]]))

    def poll():
        events, flag = next(queued)
        canvas.SDL_GetWindowFlags.return_value = flag
        for event in events:
            if event.type in (768, 769) and event.key in scans:
                canvas.SDL_GetKeyboardState.return_value[scans[event.key]] = int(event.type == 768)
        return events

    canvas.get_events.side_effect = poll
    created, snapshots = [], []
    run = ChapterRun(2 if initial_stage >= 6 else 1)
    original_one, original_stage = main._new_game, main._new_stage_game

    def register(game):
        nonlocal run
        if not created:
            finish(game, initial)
        if not created:
            if game.chapter != run.chapter:
                run = ChapterRun(game.chapter)
            for stage in range((game.chapter-1)*5+1,game.stage_number):
                o=run.offer_after_clear(stage,f"fixture-{stage}")
                run.select(o,("move","move","attack","hp")[(stage-1)%5])
        created.append(game)
        return game

    def create_one(**kwargs):
        if not created:
            if initial_factory is not None:
                return register(initial_factory())
            if initial_stage in range(2, 10):
                return register(original_stage(initial_stage))
        return register(original_one(**kwargs))

    def create_stage(number, **kwargs):
        return create_one(**kwargs) if number == 1 else register(original_stage(number, **kwargs))

    now = [0.0]
    elapsed = iter(lengths or [FIXED_TIME_STEP] * len(batches))

    def rendered():
        game = created[-1]
        snapshots.append(dict(stage=game.stage_number, state=game.state, tick=game.combat.tick,
                              position=game.player.position, hp=game.player.health.current_hp,
                              attack=game.combat.next_attack_tick, parry=game.parry.next_parry_tick,
                              count=len(created)))
        if after_render is not None:
            after_render(game, len(snapshots) - 1)
        now[0] += next(elapsed)

    canvas.update_canvas.side_effect = rendered
    menu, clock = main.SettingsMenu(), SimulationClock()
    with patch.dict(sys.modules, {'pico2d': SimpleNamespace(pico2d=canvas)}), \
            patch.object(main, '_new_game', side_effect=create_one), \
            patch.object(main, '_new_stage_game', side_effect=create_stage), \
            patch.object(main, 'DisplaySettings') as display, \
            patch.object(main, 'SettingsRenderer') as settings, \
            patch.object(main, 'BoardRenderer') as board, \
            patch.object(main, 'SettingsMenu', return_value=menu), \
            patch.object(main, 'SimulationClock', return_value=clock), \
            patch.object(main, 'perf_counter', side_effect=lambda: now[0]), \
            patch.object(main, 'sleep'):
        main.main(run=run)
    canvas.open_canvas.assert_called_once_with(1440, 900)
    canvas.close_canvas.assert_called_once_with()
    expected_chapters = [created[0].chapter]
    if created[0].chapter == 1 and any(g.chapter == 2 for g in created):
        expected_chapters.append(2)
    assert [c.kwargs['chapter'] for c in board.call_args_list] == expected_chapters
    display.assert_called_once_with(canvas)
    settings.assert_called_once_with(canvas)
    settings.return_value.close.assert_called_once_with()
    return created, snapshots, canvas, menu, display, clock


class StageSessionTests(unittest.TestCase):
    def test_legacy_stage_one_factory_and_constructor_are_preserved(self):
        game = main._new_game()
        self.assertIsInstance(game, StageOneGame)
        self.assertIsInstance(game, StageGame)
        self.assertEqual((game.stage_number, game.chapter, game.player.position), (1, 1, (5, 1)))
        self.assertEqual([(e.kind, e.position, e.health.current_hp) for e in game.encounter.enemies],
                         [('pawn', (1, 6), 2), ('pawn', (8, 6), 2)])
        with patch.object(main, '_new_game', return_value=game) as legacy:
            self.assertIs(main._new_stage_game(1), game)
            legacy.assert_called_once_with()

    def test_stage_two_is_created_from_catalog_with_exact_hp_position_delay_and_scope(self):
        game = main._new_stage_game(2)
        definition = StageCatalog.load().get_stage(2)
        self.assertEqual((game.stage_number, game.chapter, game.player.position, game.player.facing,
                          game.player.health.current_hp, game.combat.tick), (2, 1, (5, 1), 'up', 3, 0))
        self.assertEqual([(e.data_id, e.kind, e.position, e.initial_delay) for e in game.encounter.enemies],
                         [(e.data_id, e.kind, e.position, e.initial_delay) for e in definition.enemies])
        self.assertEqual([e.health.current_hp for e in game.encounter.enemies], [4, 2, 2])
        self.assertEqual([e.initial_delay_ticks for e in game.encounter.enemies], [48, 62, 75])
        self.assertIsNone(game.encounter.enemies[0].forward)
        self.assertEqual(game.encounter.ledger.combat_session_id, game.combat.combat_session_id)
        self.assertEqual(game.encounter.ledger.stage_instance_id, game.combat.stage_instance_id)

    def test_supported_clear_can_continue_and_restart_destinations_are_explicit(self):
        for number in (1, 2, 3, 4):
            for state in ('playing', 'dead', 'clear'):
                with self.subTest(number=number, state=state):
                    game = main._new_stage_game(number)
                    finish(game, state)
                    self.assertEqual(game.next_stage_number,
                                     None)
                    self.assertEqual(game.restart_stage_number,
                                     None if state in ('playing','clear') else 1)

    def test_stage_two_requires_all_three_deaths_and_death_wins_ties(self):
        game = main._new_stage_game(2)
        for enemy in game.encounter.enemies[:2]:
            enemy.health.apply_damage(enemy.health.max_hp, tick=0)
            game.encounter.deactivate(enemy.entity_instance_id)
        self.assertFalse(game.update_state())
        last = game.encounter.enemies[-1]
        last.health.apply_damage(2, tick=0)
        game.player.health.apply_damage(3, tick=0)
        self.assertTrue(game.update_state())
        self.assertEqual((game.state, game.transition_count), (GameState.GAME_OVER, 1))
        self.assertFalse(game.update_state())

    def test_unsupported_stage_and_invalid_metadata_fail_before_creating_entities(self):
        for number in (0, *range(10, 26), -1):
            with self.subTest(number=number), self.assertRaises(ValueError):
                main._new_stage_game(number)
        for number in (True, 2.0, '2', None):
            with self.subTest(number=number), self.assertRaises(TypeError):
                main._new_stage_game(number)
        game = main._new_game()
        args = (game.player, game.combat, game.encounter, game.parry, game.resolver)
        for metadata in ({'stage_number': 5}, {'stage_number': True}, {'chapter': 2}, {'chapter': True}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                StageGame(*args, **metadata)

    def test_new_sessions_reset_all_runtime_state_and_reject_old_attacks_and_parries(self):
        for number in (1, 2):
            old = main._new_stage_game(number)
            old.advance(120)
            attack = old.combat.request_attack(old.player)
            attempt = old.parry.request(old.combat.tick)
            old.resolver.register_parry(attempt)
            enemy_event = old.encounter.ledger.telegraphs[0] if number == 2 else None
            old.combat.grant_perfect_counter()
            old.resolver.player_invulnerable_until_tick = old.combat.tick + 48
            old.encounter.stun(old.encounter.enemies[0].entity_instance_id, old.combat.tick)
            old.resolver.stop()
            fresh = main._new_stage_game(2)
            self.assertEqual((fresh.combat.tick, fresh.combat.next_attack_tick,
                              fresh.parry.next_parry_tick, fresh.combat.pending_attack_bonus,
                              fresh.resolver.player_invulnerable_until_tick), (0, 0, 0, 0, 0))
            self.assertIsNone(fresh.player.health.last_damage_tick)
            self.assertIsNone(fresh.parry.last_attempt)
            self.assertIsNone(fresh.resolver.last_parry_result)
            self.assertEqual(fresh.encounter.ledger.telegraphs, ())
            self.assertTrue(all(e.stun_until_tick == 0 and e.current_attack is None
                                for e in fresh.encounter.enemies))
            self.assertNotEqual(old.combat.combat_session_id, fresh.combat.combat_session_id)
            self.assertNotEqual(old.combat.stage_instance_id, fresh.combat.stage_instance_id)
            self.assertTrue({e.entity_instance_id for e in old.encounter.enemies}.isdisjoint(
                e.entity_instance_id for e in fresh.encounter.enemies))
            with self.assertRaises(ValueError):
                fresh.resolver.resolve_player_attack(attack)
            with self.assertRaises(ValueError):
                fresh.resolver.register_parry(attempt)
            if enemy_event is not None:
                with self.assertRaises(ValueError):
                    fresh.resolver.resolve_enemy_attack(enemy_event)

    def test_stage_two_terminal_states_freeze_ai_ticks_damage_rewards_and_plans(self):
        for state in ('dead', 'clear'):
            game = main._new_stage_game(2)
            game.advance(120)
            event = game.encounter.enemies[0].current_attack
            finish(game, state)
            before = (game.combat.tick, game.encounter.tick, game.player.health.current_hp,
                      tuple(e.position for e in game.encounter.enemies), game.combat.pending_attack_bonus)
            for _ in range(5):
                self.assertEqual(game.advance(1000), ())
                self.assertIsNone(game.resolver.resolve_enemy_attack(event))
                self.assertFalse(game.encounter.complete_attack(event, game.player.position))
            self.assertEqual(before, (game.combat.tick, game.encounter.tick, game.player.health.current_hp,
                                     tuple(e.position for e in game.encounter.enemies), game.combat.pending_attack_bonus))
            self.assertEqual(game.encounter.ledger.state(event), 'cancelled')


class StageFlowInputTests(unittest.TestCase):
    def setUp(self):
        self.canvas = canvas_tests.WindowLoopTests().make_canvas()
        self.canvas.SDL_SCANCODE_R, self.canvas.SDL_SCANCODE_N = 21, 17
        self.controls = GameplayInput(self.canvas)

    def test_n_is_immediate_edge_triggered_and_not_a_gameplay_key(self):
        self.assertFalse(self.controls.is_gameplay_key(key(N)))
        self.assertTrue(self.controls.handle_next(key(N), enabled=True))
        self.assertFalse(self.controls.handle_next(key(N), enabled=True))
        self.assertFalse(self.controls.handle_next(key(N, False), enabled=True))
        self.assertTrue(self.controls.handle_next(key(N), enabled=True))

    def test_blocked_disabled_or_repeat_n_needs_release_and_new_press(self):
        for kwargs in ({'blocked': True, 'enabled': True}, {'enabled': False}):
            controls = GameplayInput(self.canvas)
            self.assertFalse(controls.handle_next(key(N), **kwargs))
            self.assertFalse(controls.handle_next(key(N), enabled=True))
            controls.handle_next(key(N, False))
            self.assertTrue(controls.handle_next(key(N), enabled=True))
        controls = GameplayInput(self.canvas)
        self.assertFalse(controls.handle_next(key(N, repeat=True), enabled=True))

    def test_physical_reconciliation_never_emits_n_and_r_commands(self):
        self.canvas.SDL_GetKeyboardState.return_value[17] = 1
        self.canvas.SDL_GetKeyboardState.return_value[21] = 1
        self.controls.reset_after_transition(N)
        self.assertFalse(self.controls.handle_next(key(N), enabled=True))
        self.assertFalse(self.controls.handle_restart(key(R), enabled=True))
        self.controls.release_on_focus_loss()
        self.controls.reconcile_physical_keys()
        self.assertFalse(self.controls.handle_next(key(N), enabled=True))


class StageFlowMainTests(unittest.TestCase):
    def test_final_stage_one_kill_and_n_in_same_batch_wait_for_fresh_n_after_clear(self):
        original_factory = main._new_game
        def almost_clear():
            game = original_factory()
            first, second = game.encounter.enemies
            first.col, first.row = 5, 2
            first.health.apply_damage(1, tick=0)
            second.health.apply_damage(2, tick=0)
            game.encounter.deactivate(second.entity_instance_id)
            return game
        created, snapshots, _, _, _, _ = run_loop(
            [[key(SPACE), key(49)], [key(49)], [key(49, False), key(49)]],
            initial='playing', initial_factory=almost_clear)
        self.assertEqual([s['count'] for s in snapshots], [1, 1, 2])
        self.assertEqual(snapshots[0]['state'], GameState.UPGRADE)
        self.assertEqual(created[-1].stage_number, 2)

    def test_stage_two_final_space_kill_clears_all_enemies_then_r_replays_two(self):
        original_factory = main._new_stage_game
        def almost_clear_two():
            game = original_factory(2)
            for enemy in game.encounter.enemies[:2]:
                enemy.health.apply_damage(enemy.health.max_hp, tick=0)
                game.encounter.deactivate(enemy.entity_instance_id)
            last = game.encounter.enemies[-1]
            last.col, last.row = 5, 2
            last.health.apply_damage(1, tick=0)
            return game
        created, snapshots, _, _, _, _ = run_loop(
            [[key(SPACE)], [], [key(R)]], initial_stage=2, initial='playing',
            initial_factory=almost_clear_two)
        self.assertEqual([g.stage_number for g in created], [2])
        self.assertEqual(snapshots[0]['state'], GameState.UPGRADE)
        self.assertTrue(created[0].resolver.stopped)
        self.assertTrue(all(not e.alive for e in created[-1].encounter.enemies))

    def test_real_stage_two_death_stops_at_444_and_r_returns_to_chapter_start(self):
        created, snapshots, _, _, _, _ = run_loop(
            [[] for _ in range(57)] + [[key(49)], [key(R)]],
            initial_stage=2, initial='playing', lengths=[8 * FIXED_TIME_STEP] * 59)
        dead, fresh = created
        self.assertEqual((dead.state, dead.combat.tick, dead.player.health.current_hp),
                         (GameState.GAME_OVER, 444, 0))
        self.assertEqual(snapshots[-2]['count'], 1)
        self.assertEqual((fresh.stage_number, snapshots[-1]['tick'], fresh.player.health.current_hp), (1, 0, 3))

    def test_other_active_enemy_path_entry_cancels_in_main_with_90_tick_recovery(self):
        event = []
        def obstruct(game, frame):
            if frame == 15:  # Rook books its path at combat tick120.
                event.append(game.encounter.enemies[0].current_attack)
                pawn = game.encounter.enemies[1]
                pawn.col, pawn.row = 4, 1
        created, _, _, _, _, _ = run_loop(
            [[key(49)]] + [[] for _ in range(16)],
            lengths=[8 * FIXED_TIME_STEP] * 15 + [FIXED_TIME_STEP] * 2,
            after_render=obstruct)
        game = created[-1]
        source = game.encounter.enemies[0]
        self.assertEqual((game.combat.tick, source.state, source.next_action_tick), (121, 'recovering', 211))
        self.assertEqual(event[0].target_cells, ((3, 1), (4, 1), (5, 1)))
        self.assertEqual(game.encounter.ledger.state(event[0]), 'cancelled')
        self.assertEqual(game.player.health.current_hp, 3)

    def test_pending_old_stage_input_queue_is_discarded_during_n_transition(self):
        def clear_after_queued_input(game, frame):
            if frame == 1:
                finish(game, 'clear')
        created, snapshots, _, _, _, _ = run_loop(
            [[], [key(SPACE)], [], [key(49)], [key(SPACE)], [key(SPACE, False)], [key(SPACE)]],
            initial='playing', lengths=[0, 0, 0, FIXED_TIME_STEP, FIXED_TIME_STEP,
                                         FIXED_TIME_STEP, FIXED_TIME_STEP],
            after_render=clear_after_queued_input)
        self.assertEqual(len(created), 2)
        self.assertIsNone(created[0].combat.active_attack)
        self.assertTrue(all(s['attack'] == 0 for s in snapshots[:5]))
        self.assertEqual((created[-1].combat.active_attack.attack_id,
                          created[-1].combat.active_attack.start_tick), (1, 3))

    def test_n_after_stage_one_clear_creates_real_stage_two_at_zero_without_new_window(self):
        created, snapshots, _, _, _, clock = run_loop([[key(49)], []])
        self.assertEqual([g.stage_number for g in created], [1, 2])
        self.assertEqual((snapshots[0]['tick'], snapshots[0]['stage'], snapshots[0]['hp']), (0, 2, 3))
        self.assertTrue(created[0].resolver.stopped)
        self.assertEqual([e.kind for e in created[1].encounter.enemies], ['rook', 'pawn', 'pawn'])
        self.assertLess(clock.accumulator, FIXED_TIME_STEP)

    def test_n_is_ignored_in_playing_game_over_and_stage_four_clear(self):
        for number, state in ((1, 'playing'), (1, 'dead'), (2, 'playing'), (2, 'dead'),
                              (3, 'playing'), (3, 'dead'), (4, 'playing'), (4, 'dead'), (5, 'clear')):
            with self.subTest(number=number, state=state):
                created, _, _, _, _, _ = run_loop([[key(N)], [], [key(N, False), key(N)]],
                                                 initial_stage=number, initial=state)
                self.assertEqual(len(created), 2 if number==5 and state=='clear' else 1)
                if number==5 and state=='clear':
                    self.assertEqual(created[-1].stage_number,6)

    def test_r_replays_stage_two_clear_but_game_over_returns_to_stage_one(self):
        for state in ('clear','dead'):
            created,snapshots,_,_,_,_=run_loop([[key(R)],[]],initial_stage=2,initial=state)
            self.assertEqual([g.stage_number for g in created],[2] if state=='clear' else [2,1])
            self.assertEqual(snapshots[0]['tick'],0)
            if state=='clear':
                self.assertEqual(created[0].state,GameState.UPGRADE)
                self.assertIsNone(created[0].next_stage_number)
                self.assertIsNone(created[0].restart_stage_number)
            else:
                self.assertEqual(created[-1].player.health.current_hp,3)
                self.assertTrue(created[-1].playing)

    def test_stage_one_clear_r_still_replays_stage_one(self):
        created,snapshots,_,_,_,_=run_loop([[key(R)],[key(R,False),key(R),key(N)]])
        self.assertEqual([g.stage_number for g in created],[1])
        self.assertTrue(all(s['state'] is GameState.UPGRADE and s['tick']==0 for s in snapshots))
        self.assertEqual(created[0].transition_count,1)

    def test_transition_blocks_tail_actions_and_physical_holds_until_release(self):
        created, snapshots, _, _, _, _ = run_loop([
            [key(49), key(UP), key(SPACE), key(SHIFT), key(R)],
            [key(49), key(UP), key(SPACE), key(SHIFT)],
            [key(49, False), key(R, False), key(UP, False), key(SPACE, False), key(SHIFT, False)],
            [key(UP), key(SPACE), key(SHIFT)],
        ])
        self.assertEqual(len(created), 2)
        self.assertTrue(all(s['position'] == (5, 1) and s['attack'] == s['parry'] == 0
                            for s in snapshots[:3]))
        game = created[-1]
        self.assertEqual(game.player.position, (5, 2))
        self.assertEqual((game.combat.active_attack.attack_id, game.parry.last_attempt.parry_id), (1, 1))
        self.assertEqual((game.combat.active_attack.start_tick, game.parry.last_attempt.start_tick), (3, 3))

    def test_only_one_transition_per_batch_in_both_n_r_orders(self):
        for keys, expected in (([49, R, R], 2), ([R, 49, 49], 2)):
            with self.subTest(keys=keys):
                created, _, _, _, _, _ = run_loop([[key(value) for value in keys]])
                self.assertEqual([g.stage_number for g in created], [1, expected])

    def test_held_n_from_playing_is_not_buffered_for_later_clear(self):
        def clear_after_first(game, frame):
            if frame == 0:
                finish(game, 'clear')
        created, snapshots, _, _, _, _ = run_loop(
            [[key(49)], [key(49)], [key(49, False)], [key(49)]], initial='playing',
            after_render=clear_after_first)
        self.assertEqual([s['count'] for s in snapshots], [1, 1, 1, 2])

    def test_settings_block_n_until_menu_closed_release_and_new_press(self):
        created, snapshots, _, menu, _, _ = run_loop(
            [[MENU, key(49)], [key(ESC), key(49)], [key(49, False)], [key(49)]])
        self.assertEqual([s['count'] for s in snapshots], [1, 1, 1, 2])
        self.assertFalse(menu.is_open)

    def test_focus_loss_and_regained_hold_cannot_advance(self):
        created, snapshots, _, _, _, _ = run_loop(
            [[], [key(49)], [], [key(49)], [key(49, False)], [key(49)]],
            focus=[512, 0, 0, 512, 512, 512])
        self.assertEqual([s['count'] for s in snapshots], [1, 1, 1, 1, 1, 2])

    def test_f11_order_and_stage_two_settings_reuse_existing_adapters(self):
        created, snapshots, _, menu, display, _ = run_loop(
            [[key(F11), key(49)], [key(49, False)], [key(49), key(F11)], [MENU], [key(ESC)]])
        self.assertEqual([s['count'] for s in snapshots], [1, 1, 2, 2, 2])
        self.assertEqual(display.return_value.toggle.call_count, 2)
        self.assertFalse(menu.is_open)
        self.assertEqual(created[-1].stage_number, 2)

    def test_repeated_stage_two_clear_replays_have_zero_clock_debt_and_unique_sessions(self):
        created,snapshots,_,_,_,clock=run_loop([[key(R),key(R,False)] for _ in range(6)],initial_stage=2,lengths=[20]*6)
        self.assertEqual(len(created),1)
        self.assertTrue(all(s['tick']==0 and s['state'] is GameState.UPGRADE for s in snapshots))
        self.assertEqual(created[0].transition_count,1)
        self.assertEqual(clock.accumulator,0)
        self.assertIsNone(created[0].restart_stage_number)

    def test_real_mixed_main_loop_renders_warns_and_applies_rook_damage(self):
        seen, warnings = [], []
        enemy_draw, warning_draw = main.EnemyRenderer.draw, main.EnemyAttackRenderer.draw
        def draw_enemies(renderer, canvas, enemies):
            seen.append(tuple(e.kind for e in enemies if e.active))
            enemy_draw(renderer, canvas, enemies)
        def draw_warnings(renderer, canvas, ledger):
            warnings.extend(event.target_cells for event in ledger.telegraphs)
            warning_draw(renderer, canvas, ledger)
        with patch.object(main.EnemyRenderer, 'draw', draw_enemies), \
                patch.object(main.EnemyAttackRenderer, 'draw', draw_warnings):
            created, snapshots, _, _, _, _ = run_loop(
                [[key(49)]] + [[] for _ in range(22)], lengths=[8 * FIXED_TIME_STEP] * 23)
        game = created[-1]
        self.assertEqual(game.stage_number, 2)
        self.assertIn(('rook', 'pawn', 'pawn'), seen)
        self.assertIn(((3, 1), (4, 1), (5, 1)), warnings)
        self.assertEqual(game.player.health.current_hp, 2)
        self.assertEqual(game.encounter.enemies[0].position, (4, 1))
        self.assertEqual(game.player.health.last_damage_tick, 168)

    def test_stage_two_main_loop_normal_and_perfect_parry_against_real_rook(self):
        for grade in ('normal', 'perfect'):
            if grade == 'perfect':
                batches = [[key(49)]] + [[] for _ in range(20)] + [[key(SHIFT)], []]
                lengths = [8 * FIXED_TIME_STEP] * 20 + [FIXED_TIME_STEP, 7 * FIXED_TIME_STEP, FIXED_TIME_STEP]
            else:
                batches = [[key(49)]] + [[] for _ in range(18)] + [[key(SHIFT)], [], [], []]
                lengths = [8 * FIXED_TIME_STEP] * 18 + [6 * FIXED_TIME_STEP, 8 * FIXED_TIME_STEP,
                                                       8 * FIXED_TIME_STEP, 2 * FIXED_TIME_STEP, FIXED_TIME_STEP]
            with self.subTest(grade=grade):
                created, _, _, _, _, _ = run_loop(batches, lengths=lengths)
                game = created[-1]
                self.assertEqual(game.resolver.last_parry_result.status, grade)
                self.assertEqual(game.player.health.current_hp, 3)
                source = game.encounter.enemies[0]
                self.assertEqual(source.position, (2, 1) if grade == 'perfect' else (4, 1))
                self.assertEqual(game.combat.pending_attack_bonus, 2 if grade == 'perfect' else 0)
                if grade == 'perfect':
                    self.assertEqual((source.state, source.stun_until_tick), ('stunned', 228))

    def test_hit_tick_move_evades_real_rook_in_main_loop(self):
        batches = [[key(49)]] + [[] for _ in range(20)] + [[key(UP)]]
        created, _, _, _, _, _ = run_loop(batches, lengths=[8 * FIXED_TIME_STEP] * 22)
        game = created[-1]
        self.assertEqual((game.combat.tick, game.player.position, game.player.health.current_hp),
                         (168, (5, 2), 3))
        self.assertEqual(game.encounter.enemies[0].position, (5, 1))

    def test_space_kills_rook_and_cancels_its_pending_attack_in_main(self):
        from tests.test_stage_three import play_to
        def expose(game,tick):
            if tick==144:
                game.encounter.enemies[0].health.apply_damage(3,tick=tick)
        created,_,_,_,_,_=play_to(170,factory=lambda: main._new_stage_game(2),
            inputs={150:[key(LEFT),key(LEFT,False)],168:[key(LEFT),key(SPACE)]},
            samples=(144,),observe=expose)
        game=created[-1]
        self.assertFalse(game.encounter.enemies[0].active)
        self.assertEqual((game.player.position,game.player.health.current_hp),((3,1),3))
        self.assertEqual(game.encounter.ledger.telegraphs,())

    def test_stage_two_terminal_menu_f11_esc_and_window_close_remain_available(self):
        for state in ('dead', 'clear'):
            created, snapshots, _, menu, display, _ = run_loop(
                [[MENU], [key(ESC)], [key(F11)], [key(ESC)]], initial_stage=2, initial=state)
            self.assertEqual(len(snapshots), 3)
            self.assertEqual(len(created), 1)
            self.assertTrue(all(s['tick'] == 0 for s in snapshots))
            self.assertFalse(menu.is_open)
            display.return_value.toggle.assert_called_once_with()
        created, snapshots, _, _, _, _ = run_loop(
            [[key(49), SimpleNamespace(type=256)]])
        self.assertEqual(len(created), 1)
        self.assertEqual(snapshots, [])


class StageFlowRendererTests(unittest.TestCase):
    def test_stage_two_health_labels_read_actual_rook_and_pawn_hp(self):
        game = main._new_stage_game(2)
        with patch.object(HealthRenderer, '_text') as text:
            HealthRenderer().draw(Mock(), game.player, game.encounter.enemies, 0)
        labels = [call.args[1] for call in text.call_args_list]
        self.assertEqual(labels.count('4/4'), 1)
        self.assertEqual(labels.count('2/2'), 2)
        game.encounter.enemies[0].health.apply_damage(1, tick=0)
        with patch.object(HealthRenderer, '_text') as text:
            HealthRenderer().draw(Mock(), game.player, game.encounter.enemies, 0)
        self.assertIn('3/4', [call.args[1] for call in text.call_args_list])

    def labels(self, game):
        with patch.object(HealthRenderer, '_text') as text:
            GameFlowRenderer().draw(Mock(), game)
        return [call.args[1] for call in text.call_args_list]

    def test_stage_one_clear_has_continue_hint_but_game_over_does_not(self):
        game = main._new_game()
        finish(game, 'clear')
        self.assertIn('UPGRADE', self.labels(game))
        self.assertNotIn('N TO CONTINUE', self.labels(game))
        dead = main._new_game()
        finish(dead, 'dead')
        self.assertNotIn('N TO CONTINUE', self.labels(dead))

    def test_stage_two_shows_actual_stage_all_enemies_and_correct_restart_destination(self):
        for state, expected in (('dead', 'R TO STAGE 1'), ('clear', 'UPGRADE')):
            game = main._new_stage_game(2)
            finish(game, state)
            labels = self.labels(game)
            self.assertIn('STAGE 2', labels)
            self.assertIn(f'ENEMIES LEFT {3 if state == "dead" else 0}/3', labels)
            self.assertIn(expected, labels)
            self.assertNotIn('N TO CONTINUE', labels)
            self.assertNotIn('STAGE 3', labels)

    def test_stage_labels_and_terminal_glyphs_fit_existing_layout_without_mutation(self):
        for number in (1, 2):
            game = main._new_stage_game(number)
            canvas = Mock()
            GameFlowRenderer().draw_stage_label(canvas, game)
            for call in canvas.draw_rectangle.call_args_list:
                x1, y1, x2, y2 = call.args[:4]
                self.assertTrue(0 <= x1 <= x2 < 300 and 0 <= y1 <= y2 < 900)
            finish(game, 'clear')
            before = (game.state, game.combat.tick, game.transition_count, game.player.health.current_hp)
            for _ in range(3):
                canvas = Mock()
                GameFlowRenderer().draw(canvas, game)
                for call in canvas.draw_rectangle.call_args_list:
                    x1, y1, x2, y2 = call.args[:4]
                    self.assertTrue(300 <= x1 <= x2 < 1140 and 30 <= y1 <= y2 < 870)
            self.assertEqual(before, (game.state, game.combat.tick, game.transition_count, game.player.health.current_hp))


if __name__ == '__main__':
    unittest.main()
