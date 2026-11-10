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


def main():
    # Import here so configuration and importing this module never open a window.
    # Use the implementation module: its live window handle is set by open_canvas.
    from pico2d import pico2d as canvas

    player = load_stage1_player()
    player_renderer = PlayerRenderer()
    combat = Combat()
    attack_renderer = AttackRenderer()
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
                if focused:
                    controls.reconcile_physical_keys()
                else:
                    controls.release_on_focus_loss()
                clock.reset()
            combat.advance(clock.advance(frame_start - previous_frame,
                                         paused=menu.is_open or not focused or focus_changed))
            previous_frame = frame_start
            previously_focused = focused
            display_changed = False
            menu_changed = False
            for event in events:
                # Gameplay releases survive modal, focus, and display transitions.
                if controls.handle_key(event, player, combat,
                                       blocked=menu.blocks_gameplay() or display_changed
                                       or not focused or focus_changed):
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
                if action == 'quit':
                    running = False
                    break
                if action == 'toggle_fullscreen':
                    display.toggle()
                    # Discard stale mouse coordinates but keep processing key releases.
                    display_changed = True
            if not running:
                break
            if display_changed:
                controls.reconcile_physical_keys()
            if display_changed or menu_changed or focus_changed:
                # Neither modal time nor a synchronous display switch becomes catch-up debt.
                clock.reset()
                previous_frame = perf_counter()

            # RenderClear clears the whole output, including letterbox bars.
            canvas.SDL_SetRenderDrawColor(canvas.renderer, 0, 0, 0, 255)
            canvas.SDL_RenderClear(canvas.renderer)
            board_renderer.draw(canvas)
            attack_renderer.draw(canvas, combat.active_attack)
            player_renderer.draw(canvas, player)
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
