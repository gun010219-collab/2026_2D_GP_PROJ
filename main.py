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


def main():
    # Import here so configuration and importing this module never open a window.
    # Use the implementation module: its live window handle is set by open_canvas.
    from pico2d import pico2d as canvas

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
            for event in events:
                action = 'consumed'
                if event.type == canvas.SDL_KEYDOWN:
                    key = ('escape' if event.key == canvas.SDLK_ESCAPE else
                           'f11' if event.key == canvas.SDLK_F11 else 'other')
                    action = menu.key(key)
                elif event.type == canvas.SDL_MOUSEBUTTONDOWN and event.button == canvas.SDL_BUTTON_LEFT:
                    action = menu.click(logical_mouse_to_canvas(event.x, event.y))
                if action == 'quit':
                    running = False
                    break
                if action == 'toggle_fullscreen':
                    display.toggle()
                    # Discard remaining input polled under the previous display transform.
                    break
                # Future gameplay receives only action == 'gameplay' while
                # not menu.blocks_gameplay(); modal input is never forwarded.
            if not running:
                break

            # Future fixed-step simulation updates belong before rendering.
            # This bootstrap only paces rendering; it advances no game state.
            # RenderClear clears the whole output, including letterbox bars.
            canvas.SDL_SetRenderDrawColor(canvas.renderer, 0, 0, 0, 255)
            canvas.SDL_RenderClear(canvas.renderer)
            board_renderer.draw(canvas)
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
