"""CHECKMATE window bootstrap. Run with the project's virtual environment."""
from time import perf_counter, sleep

from config import (
    FIXED_TIME_STEP,
    WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH,
)
from renderer import BoardRenderer
from display_settings import DisplaySettings, logical_mouse_to_canvas
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from player import load_stage1_player
from player_renderer import PlayerRenderer
from combat import Combat
from attack_renderer import AttackRenderer
from simulation_clock import SimulationClock
from sdl_input import GameplayInput
from parry import Parry
from parry_renderer import ParryRenderer, ParryResultRenderer
from enemy import load_stage1_enemies
from enemy_behaviors import PawnEncounter
from enemy_renderer import EnemyRenderer
from enemy_attack_renderer import EnemyAttackRenderer
from combat_resolution import CombatResolver
from health_renderer import HealthRenderer
from game import StageOneGame
from game_renderer import GameFlowRenderer


def _new_game():
    """Fresh Stage 1 entities/ledgers; renderers, window and display stay owned by main."""
    player = load_stage1_player()
    combat = Combat()
    parry = Parry()
    encounter = PawnEncounter(load_stage1_enemies(), start_tick=combat.tick,
                               combat_session_id=combat.combat_session_id,
                               stage_instance_id=combat.stage_instance_id)
    resolver = CombatResolver(player, combat, encounter, parry=parry)
    return StageOneGame(player, combat, encounter, parry, resolver)


def main():
    # Import here so configuration and importing this module never open a window.
    # Use the implementation module: its live window handle is set by open_canvas.
    from pico2d import pico2d as canvas

    game = _new_game()
    player, combat, parry = game.player, game.combat, game.parry
    pawns, resolver = game.encounter, game.resolver
    player_renderer = PlayerRenderer()
    attack_renderer = AttackRenderer()
    parry_renderer = ParryRenderer()
    parry_result_renderer = ParryResultRenderer()
    enemy_renderer = EnemyRenderer()
    enemy_attack_renderer = EnemyAttackRenderer()
    health_renderer = HealthRenderer()
    game_renderer = GameFlowRenderer()
    clock = SimulationClock()
    canvas.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    settings_renderer = None
    try:
        if not canvas.window or not canvas.renderer:
            raise RuntimeError('Pico2D could not create a window and renderer')
        canvas.hide_lattice()
        canvas.SDL_SetWindowTitle(canvas.window, WINDOW_TITLE.encode('utf-8'))
        board_renderer = BoardRenderer(chapter=1)
        display = DisplaySettings(canvas)
        menu = SettingsMenu()
        settings_renderer = SettingsRenderer(canvas)
        controls = GameplayInput(canvas)
        pending_gameplay = []

        def flush_gameplay(blocked=False):
            # Keep both down/up transitions in order, including quick taps
            # between ticks. Blocked draining updates latches without actions.
            queued = tuple(pending_gameplay)
            pending_gameplay.clear()
            for event in queued:
                controls.handle_key(event, player, combat, blocked=blocked, parry=parry,
                                    occupied=pawns.occupied_cells,
                                    on_attack=resolver.resolve_player_attack,
                                    on_parry=resolver.register_parry)

        previously_focused = controls.focused
        previous_frame = perf_counter()

        running = True
        while running:
            frame_start = perf_counter()
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
            if (game.playing and pawns.tick < combat.tick and focused
                    and not focus_changed and not menu.is_open):
                flush_gameplay()
            for event in events:
                if controls.handle_restart(event, enabled=not game.playing,
                                           blocked=menu.is_open or display_changed
                                           or not focused or focus_changed):
                    flush_gameplay(blocked=True)
                    game = _new_game()
                    player, combat, parry = game.player, game.combat, game.parry
                    pawns, resolver = game.encounter, game.resolver
                    controls = GameplayInput(canvas)
                    controls.reset_after_restart()
                    clock.reset()
                    restarted_this_frame = True
                    continue
                blocked = (menu.blocks_gameplay() or display_changed or not focused
                           or focus_changed or not game.playing or restarted_this_frame)
                if (not blocked and pawns.tick == combat.tick
                        and controls.is_gameplay_key(event)):
                    # A settled tick cannot accept later input ahead of damage
                    # already resolved. Apply this transition at the next fresh
                    # tick, before its AI, preserving the fixed-tick ordering.
                    pending_gameplay.append(event)
                    continue
                # Gameplay releases survive modal, focus, and display transitions.
                if controls.handle_key(event, player, combat,
                                       blocked=blocked,
                                       parry=parry, occupied=pawns.occupied_cells,
                                       on_attack=resolver.resolve_player_attack,
                                       on_parry=resolver.register_parry):
                    continue
                if display_changed or not focused:
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
            if not running:
                break
            # Input may have killed a Pawn whose attack was due this tick.
            # Its cancellation is visible before the encounter publishes due.
            game.resolve_current_tick()
            if not game.playing:
                flush_gameplay(blocked=True)
                clock.reset()
            if display_changed:
                controls.reconcile_physical_keys()
            if display_changed or menu_changed or focus_changed or restarted_this_frame:
                # Neither modal time nor a synchronous display switch becomes catch-up debt.
                clock.reset()
                previous_frame = perf_counter()

            # RenderClear clears the whole output, including letterbox bars.
            canvas.SDL_SetRenderDrawColor(canvas.renderer, 0, 0, 0, 255)
            canvas.SDL_RenderClear(canvas.renderer)
            board_renderer.draw(canvas)
            enemy_attack_renderer.draw(canvas, pawns.ledger)
            attack_renderer.draw(canvas, combat.active_attack if game.playing else None)
            enemy_renderer.draw(canvas, pawns.enemies)
            if game.playing:
                parry_renderer.draw(canvas, player, parry, combat.tick)
            player_renderer.draw(canvas, player)
            health_renderer.draw(canvas, player, pawns.enemies, combat.tick,
                                 attack_bonus=combat.pending_attack_bonus if game.playing else None,
                                 show_feedback=game.playing)
            parry_result_renderer.draw(canvas, resolver.last_parry_result if game.playing else None,
                                       combat.tick)
            game_renderer.draw(canvas, game)
            settings_renderer.draw(menu, display)
            canvas.update_canvas()
            sleep(max(0.0, FIXED_TIME_STEP - (perf_counter() - frame_start)))
    finally:
        # Release resources on normal exit and exceptions after canvas creation.
        try:
            if settings_renderer is not None:
                settings_renderer.close()
        finally:
            canvas.close_canvas()


if __name__ == '__main__':
    main()
