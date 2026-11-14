"""CHECKMATE window bootstrap. Run with the project's virtual environment."""
from time import perf_counter, sleep
import os
from frame_timing import FramePacer, FrameStats
from render_motion import RenderMotion

from config import (
    FIXED_TIME_STEP,
    WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH,
)
from renderer import BoardRenderer
from combat_balance import profile_for
from display_settings import DisplaySettings, logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from player import Player, load_stage1_player
from player_renderer import PlayerRenderer
from combat import Combat
from attack_renderer import AttackRenderer
from simulation_clock import SimulationClock
from sdl_input import GameplayInput
from parry import Parry
from parry_renderer import ParryRenderer, ParryResultRenderer
from enemy import load_stage1_enemies
from enemy_behaviors import EnemyEncounter, PawnEncounter
from enemy_factory import create_stage_enemies
from stage_manager import StageCatalog
from enemy_renderer import EnemyRenderer
from enemy_attack_renderer import EnemyAttackRenderer
from combat_resolution import CombatResolver
from health_renderer import HealthRenderer
from game import GameState, StageGame, StageOneGame, SUPPORTED_STAGES
from game_renderer import GameFlowRenderer
from stage_progression import StageProgression
from upgrade_input import UpgradeInput
from upgrade_renderer import UpgradeRenderer
from upgrades import ChapterBuild, DerivedStats


def _new_game(*, stats=None):
    """Fresh Stage 1 entities/ledgers; renderers, window and display stay owned by main."""
    player = load_stage1_player()
    stats = ChapterBuild().stats if stats is None else stats
    if not isinstance(stats, DerivedStats):
        raise TypeError('Session stats must be DerivedStats')
    if player.health.max_hp != stats.max_hp:
        player = Player(*player.position, max_hp=stats.max_hp)
    combat = Combat()
    parry = Parry()
    encounter = PawnEncounter(load_stage1_enemies(), start_tick=combat.tick,
                               combat_session_id=combat.combat_session_id,
                               stage_instance_id=combat.stage_instance_id)
    resolver = CombatResolver(player, combat, encounter, parry=parry, player_damage=stats.attack_damage)
    return StageOneGame(player, combat, encounter, parry, resolver)


def _new_stage_game(stage_number, *, stats=None):
    """Construct supported sessions; catalog access alone never enables later play."""
    if type(stage_number) is not int:
        raise TypeError('Playable stage number must be an integer')
    if stage_number == 1:
        return _new_game() if stats is None else _new_game(stats=stats)
    if stage_number not in SUPPORTED_STAGES:
        raise ValueError('Only Stage 1 through Stage 17 are playable')
    definition = StageCatalog.load().get_stage(stage_number)
    stats = ChapterBuild().stats if stats is None else stats
    if not isinstance(stats, DerivedStats):
        raise TypeError('Session stats must be DerivedStats')
    player = Player(*definition.player_spawn, max_hp=stats.max_hp)
    combat, parry = Combat(), Parry()
    encounter = EnemyEncounter(create_stage_enemies(definition, profile=profile_for(definition.chapter)), start_tick=combat.tick,
                               combat_session_id=combat.combat_session_id,
                               stage_instance_id=combat.stage_instance_id, boss=definition.boss)
    resolver = CombatResolver(player, combat, encounter, parry=parry, player_damage=stats.attack_damage)
    return StageGame(player, combat, encounter, parry, resolver,
                     stage_number=definition.number, chapter=definition.chapter, boss=definition.boss)


def main(*, run=None):
    game = _new_game()
    return run_session(game, StageProgression(game, run))


def run_session(game, flow, *, game_renderer=None):
    """Shared fixed-tick window loop; preview supplies no StageGame or progression."""
    # Import here so configuration and importing this module never open a window.
    # Use the implementation module: its live window handle is set by open_canvas.
    from pico2d import pico2d as canvas

    player, combat, parry = game.player, game.combat, game.parry
    encounter, resolver = game.encounter, game.resolver
    player_renderer = PlayerRenderer()
    attack_renderer = AttackRenderer()
    parry_renderer = ParryRenderer()
    parry_result_renderer = ParryResultRenderer()
    enemy_renderer = EnemyRenderer()
    enemy_attack_renderer = EnemyAttackRenderer()
    health_renderer = HealthRenderer()
    game_renderer = GameFlowRenderer() if game_renderer is None else game_renderer
    upgrade_renderer = UpgradeRenderer()
    selection = UpgradeInput()
    clock = SimulationClock()
    pacer, stats, motion = FramePacer(), FrameStats(), RenderMotion()
    measure_frames = os.environ.get("CHECKMATE_FRAME_STATS") == "1"
    next_report = None
    canvas.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    settings_renderer = None
    try:
        if not canvas.window or not canvas.renderer:
            raise RuntimeError('Pico2D could not create a window and renderer')
        canvas.hide_lattice()
        canvas.SDL_SetWindowTitle(canvas.window, WINDOW_TITLE.encode('utf-8'))
        board_renderer = BoardRenderer(chapter=game.chapter)
        display = DisplaySettings(canvas)
        menu = SettingsMenu()
        settings_renderer = SettingsRenderer(canvas)
        controls = GameplayInput(canvas, move_interval_ticks=flow.run.stats.move_interval_ticks)
        pending_gameplay = []

        def prepare_controls(stats):
            fresh = GameplayInput(canvas, move_interval_ticks=stats.move_interval_ticks)
            fresh.prepare_session()
            selection.reconcile(canvas)
            return fresh

        def prepare_chapter(stats):
            # These are the fallible resources for entry; commit only after both succeed.
            fresh_controls = prepare_controls(stats)
            fresh_board = BoardRenderer(chapter=flow.run.chapter + 1)
            return fresh_controls, fresh_board

        def flush_gameplay(blocked=False):
            # Keep both down/up transitions in order, including quick taps
            # between ticks. Blocked draining updates latches without actions.
            queued = tuple(pending_gameplay)
            pending_gameplay.clear()
            for event in queued:
                controls.handle_key(event, player, combat, blocked=blocked, parry=parry,
                                    occupied=encounter.occupied_cells,
                                    on_attack=resolver.resolve_player_attack,
                                    on_parry=resolver.register_parry)

        previously_focused = controls.focused
        previous_frame = perf_counter()
        flow.sync_offer()
        if flow.offer is not None:
            selection.reconcile(canvas)

        motion.update((player, *encounter.enemies), 0.0, session=combat.combat_session_id)
        running = True
        while running:
            frame_start = perf_counter()
            visual_elapsed = max(0.0, frame_start - previous_frame)
            tick_before = combat.tick
            session_before = combat.combat_session_id
            offer_at_frame_start = flow.offer
            events = canvas.get_events()
            # Pico2D 1.5.1 get_events() replaces the title with its FPS counter.
            canvas.SDL_SetWindowTitle(canvas.window, WINDOW_TITLE.encode('utf-8'))
            # Window-close must survive even when a display toggle discards
            # stale mouse coordinates later in the same polled batch.
            if any(event.type == canvas.SDL_QUIT for event in events):
                break
            focused = controls.focused
            focus_changed = focused != previously_focused
            if focus_changed:
                flush_gameplay(blocked=True)
                if focused:
                    controls.reconcile_physical_keys()
                else:
                    controls.release_on_focus_loss()
                clock.reset()
                selection.reconcile(canvas)
            steps = clock.advance(frame_start - previous_frame,
                                  paused=menu.is_open or not focused or focus_changed
                                  or not game.playing)
            if pending_gameplay and steps > 1:
                # These inputs arrived in a previous zero-step frame, before
                # the first catch-up tick. Apply them there, not at the final
                # tick alongside newly polled input from this frame.
                game.advance(0)
                if game.playing:
                    combat.advance(1)
                    flush_gameplay()
                    game.resolve_current_tick()
                steps -= 1
            # Settle historical ticks before applying newly polled input. The
            # final fresh tick stays open so player attacks precede enemy AI and
            # damage (PDF p.7). Never apply present input to past hit_ticks.
            if steps:
                game.advance(steps - 1)
            if steps and game.playing:
                combat.advance(1)
            previous_frame = frame_start
            previously_focused = focused
            display_changed = False
            menu_changed = False
            restarted_this_frame = False
            if (game.playing and encounter.tick < combat.tick and focused
                    and not focus_changed and not menu.is_open):
                flush_gameplay()
            for event in events:
                transition_blocked = (menu.is_open or menu_changed or display_changed or not focused
                                      or focus_changed or restarted_this_frame)
                destination = None
                if controls.handle_restart(event, enabled=game.restart_stage_number is not None,
                                           blocked=transition_blocked):
                    destination = game.restart_stage_number
                elif controls.handle_next(event, enabled=game.next_stage_number is not None,
                                          blocked=transition_blocked):
                    destination = game.next_stage_number
                if destination is not None:
                    try:
                        if event.key == ord('n'):
                            fresh_game, (fresh_controls, fresh_board) = flow.enter_next_chapter(
                                _new_stage_game, prepare_chapter)
                        else:
                            fresh_game, fresh_controls = flow.restart(_new_stage_game, prepare_controls)
                            fresh_board = board_renderer
                    except Exception:
                        flow.error = True
                        continue
                    flush_gameplay(blocked=True)
                    game, controls = fresh_game, fresh_controls
                    board_renderer = fresh_board
                    player, combat, parry = game.player, game.combat, game.parry
                    encounter, resolver = game.encounter, game.resolver
                    if event.key == ord('n'):
                        controls.next_held = True
                    else:
                        controls.restart_held = True
                    clock.reset()
                    restarted_this_frame = True
                    continue
                blocked = (menu.blocks_gameplay() or display_changed or not focused
                           or focus_changed or not game.playing or restarted_this_frame)
                if (not blocked and encounter.tick == combat.tick
                        and controls.is_gameplay_key(event)):
                    # A settled tick cannot accept later input ahead of damage
                    # already resolved. Apply this transition at the next fresh
                    # tick, before its AI, preserving the fixed-tick ordering.
                    pending_gameplay.append(event)
                    continue
                # Gameplay releases survive modal, focus, and display transitions.
                if controls.handle_key(event, player, combat,
                                       blocked=blocked,
                                       parry=parry, occupied=encounter.occupied_cells,
                                       on_attack=resolver.resolve_player_attack,
                                       on_parry=resolver.register_parry):
                    continue
                if display_changed or not focused:
                    selection.handle(event, canvas, blocked=True)
                    continue
                action = 'consumed'
                was_open = menu.is_open
                if event.type == canvas.SDL_KEYDOWN:
                    key = ('escape' if event.key == canvas.SDLK_ESCAPE else
                           'f11' if event.key == canvas.SDLK_F11 else 'other')
                    action = menu.key(key)
                elif event.type == canvas.SDL_MOUSEBUTTONDOWN and event.button == canvas.SDL_BUTTON_LEFT:
                    action = menu.click(logical_mouse_to_canvas(event.x, event.y))
                menu_changed = menu_changed or was_open != menu.is_open
                if was_open != menu.is_open or action == 'toggle_fullscreen':
                    flush_gameplay(blocked=True)
                if action == 'quit':
                    running = False
                    break
                if action == 'toggle_fullscreen':
                    display.toggle()
                    # Discard stale mouse coordinates but keep processing key releases.
                    display_changed = True
                choice = selection.handle(event, canvas,
                    point=logical_mouse_to_canvas(event.x, event.y)
                    if event.type == canvas.SDL_MOUSEBUTTONDOWN else None,
                    blocked=(action != 'gameplay' or menu.is_open or menu_changed or display_changed
                             or not focused or focus_changed or restarted_this_frame
                             or not game.upgrade_selection_enabled or flow.offer is None
                             or flow.offer is not offer_at_frame_start))
                if choice is not None and flow.offer.options[choice].enabled:
                    try:
                        fresh_game, fresh_controls = flow.choose(
                            flow.offer, flow.offer.options[choice].kind, _new_stage_game, prepare_controls)
                    except Exception:
                        flow.error = True
                        continue
                    flush_gameplay(blocked=True)
                    game, controls = fresh_game, fresh_controls
                    player, combat, parry = game.player, game.combat, game.parry
                    encounter, resolver = game.encounter, game.resolver
                    clock.reset()
                    restarted_this_frame = True
            if not running:
                break
            # Input may have killed an enemy whose attack was due this tick.
            # Its cancellation is visible before the encounter publishes due.
            game.resolve_current_tick()
            prior_offer = flow.offer
            flow.sync_offer()
            if flow.offer is not None and flow.offer is not prior_offer:
                selection.reconcile(canvas)
            if not game.playing:
                flush_gameplay(blocked=True)
                clock.reset()
            if display_changed:
                controls.reconcile_physical_keys()
                selection.reconcile(canvas)
            if display_changed or menu_changed or focus_changed or restarted_this_frame:
                # Neither modal time nor a synchronous display switch becomes catch-up debt.
                clock.reset()
                previous_frame = perf_counter()

            visual_reset = (display_changed or menu_changed or focus_changed or restarted_this_frame
                            or menu.is_open or not focused or not game.playing or steps >= 8
                            or visual_elapsed > 0.15)
            frozen = set()
            if combat.active_attack is not None or parry.active_at(combat.tick):
                frozen.add(player.entity_instance_id)
            if encounter.pulse is not None:
                frozen.update(e.entity_instance_id for e in encounter.enemies if encounter.pulse.frozen(e))
            motion.update((player, *encounter.enemies), visual_elapsed,
                          session=combat.combat_session_id, snap=visual_reset, frozen=frozen)
            player_renderer.positions = enemy_renderer.positions = health_renderer.positions = motion.positions
            if measure_frames:
                active_sample = (not (display_changed or menu_changed or focus_changed or restarted_this_frame
                                      or menu.is_open or not focused or not game.playing)
                                 and session_before == combat.combat_session_id)
                stats.record(frame_start, max(0, combat.tick-tick_before) if active_sample else 0, active_sample)
                if next_report is None:
                    next_report = frame_start + 5.0
                    # Inspect actual SDL renderer flags; never force a VSync change.
                    import ctypes
                    import sdl2
                    info = sdl2.SDL_RendererInfo()
                    if sdl2.SDL_GetRendererInfo(canvas.renderer, ctypes.byref(info)) == 0:
                        print('CHECKMATE RENDERER', info.name, 'flags=', info.flags,
                              'vsync=', bool(info.flags & sdl2.SDL_RENDERER_PRESENTVSYNC), flush=True)
                if frame_start >= next_report:
                    stats.log()
                    next_report = frame_start + 5.0

            # RenderClear clears the whole output, including letterbox bars.
            canvas.SDL_SetRenderDrawColor(canvas.renderer, 0, 0, 0, 255)
            canvas.SDL_RenderClear(canvas.renderer)
            board_renderer.draw(canvas)
            enemy_attack_renderer.tick = combat.tick
            enemy_attack_renderer.active = game.playing
            enemy_attack_renderer.source_cells = {e.entity_instance_id: e.position for e in encounter.enemies if e.active}
            enemy_attack_renderer.draw(canvas, encounter.ledger)
            attack_renderer.draw(canvas, combat.active_attack if game.playing else None)
            enemy_renderer.draw(canvas, encounter.enemies)
            if game.playing:
                parry_renderer.draw(canvas, player, parry, combat.tick)
            player_renderer.draw(canvas, player)
            health_renderer.draw(canvas, player, encounter.enemies, combat.tick,
                                 attack_bonus=combat.pending_attack_bonus if game.playing else None,
                                 show_feedback=game.playing)
            parry_result_renderer.draw(canvas, resolver.last_parry_result if game.playing else None,
                                       combat.tick)
            game_renderer.draw_stage_label(canvas, game)
            if flow.error:
                game_renderer.draw(canvas, game, error=True)
            else:
                game_renderer.draw(canvas, game)
            if game.state is GameState.UPGRADE:
                upgrade_renderer.draw(canvas, game, flow.offer, flow.error)
            settings_renderer.draw(menu, display)
            canvas.update_canvas()
            sleep(pacer.remaining(perf_counter() - frame_start))
    finally:
        if measure_frames:
            stats.log()
        flow.run.retire()
        # Release resources on normal exit and exceptions after canvas creation.
        try:
            if settings_renderer is not None:
                settings_renderer.close()
        finally:
            canvas.close_canvas()


if __name__ == '__main__':
    main()
