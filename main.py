"""CHECKMATE window bootstrap. Run with the project's virtual environment."""
from time import perf_counter, sleep

from config import (
    BOARD_BOTTOM, BOARD_LEFT, BOARD_PIXEL_SIZE, FIXED_TIME_STEP,
    HUD_BOTTOM, HUD_HEIGHT, HUD_LEFT, HUD_WIDTH,
    WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH,
)


def main():
    # Import here so configuration and importing this module never open a window.
    # Use the implementation module: its live window handle is set by open_canvas.
    from pico2d import pico2d as canvas

    canvas.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        if not canvas.window or not canvas.renderer:
            raise RuntimeError('Pico2D could not create a window and renderer')
        canvas.hide_lattice()
        canvas.SDL_SetWindowTitle(canvas.window, WINDOW_TITLE.encode('utf-8'))

        running = True
        while running:
            frame_start = perf_counter()
            events = canvas.get_events()
            # Pico2D 1.5.1 get_events() replaces the title with its FPS counter.
            canvas.SDL_SetWindowTitle(canvas.window, WINDOW_TITLE.encode('utf-8'))
            for event in events:
                if event.type == canvas.SDL_QUIT or (
                    event.type == canvas.SDL_KEYDOWN and event.key == canvas.SDLK_ESCAPE
                ):
                    running = False
            if not running:
                break

            # Future fixed-step simulation updates belong before rendering.
            # This bootstrap only paces rendering; it advances no game state.
            canvas.clear_canvas()
            canvas.draw_rectangle(
                BOARD_LEFT, BOARD_BOTTOM,
                BOARD_LEFT + BOARD_PIXEL_SIZE, BOARD_BOTTOM + BOARD_PIXEL_SIZE,
                50, 60, 70,
            )
            canvas.draw_rectangle(
                HUD_LEFT, HUD_BOTTOM, HUD_LEFT + HUD_WIDTH, HUD_BOTTOM + HUD_HEIGHT,
                100, 110, 120,
            )
            canvas.update_canvas()
            sleep(max(0.0, FIXED_TIME_STEP - (perf_counter() - frame_start)))
    finally:
        # Release resources on normal exit and exceptions after canvas creation.
        canvas.close_canvas()


if __name__ == '__main__':
    main()
