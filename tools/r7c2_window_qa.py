"""Exercise the Windows release loop, two owned windows and an isolated save."""
import argparse
import ctypes as ct
from ctypes import wintypes as w
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, perf_counter_ns, sleep
from unittest.mock import patch

from r7c2_performance import summary, window
import main
from release_game import ReleaseGame
from settings_menu import SETTINGS_BUTTON
from sdl_input import poll_ready_events
from tools.chapter_art_play import session
from tests.test_hp_carryover import fight


def window_handle(win):
    import sdl2 as s
    from sdl2 import syswm
    info = syswm.SDL_SysWMinfo()
    s.SDL_VERSION(info.version)
    assert syswm.SDL_GetWindowWMInfo(win,ct.byref(info))
    return info.info.win.window


def focus(win):
    import sdl2 as s
    user = ct.windll.user32
    user.GetForegroundWindow.restype = w.HWND
    target = window_handle(win)
    s.SDL_RaiseWindow(win)
    own_thread = ct.windll.kernel32.GetCurrentThreadId()
    foreground = user.GetForegroundWindow()
    other_thread = user.GetWindowThreadProcessId(w.HWND(foreground),None) if foreground else 0
    attached = other_thread!=own_thread and other_thread and user.AttachThreadInput(own_thread,other_thread,True)
    try:
        user.SetForegroundWindow(w.HWND(target))
    finally:
        if attached:
            user.AttachThreadInput(own_thread,other_thread,False)
    until = monotonic()+1
    while monotonic()<until:
        s.SDL_PumpEvents()
        if user.GetForegroundWindow()==target and s.SDL_GetWindowFlags(win)&s.SDL_WINDOW_INPUT_FOCUS:
            return
        sleep(.01)
    raise RuntimeError(f'Windows foreground activation unavailable ({user.GetForegroundWindow()})')


def run(output):
    import sdl2 as s
    c = window(visible=True)
    user = ct.windll.user32
    user.GetForegroundWindow.restype = w.HWND
    user.WindowFromPoint.argtypes=[w.POINT]
    user.WindowFromPoint.restype=w.HWND
    previous_cursor=w.POINT()
    assert user.GetCursorPos(ct.byref(previous_cursor))
    helper = s.SDL_CreateWindow(b'CHECKMATE focus test',80,80,300,120,s.SDL_WINDOW_SHOWN)
    assert helper
    game_hwnd,helper_hwnd = window_handle(c.window),window_handle(helper)

    def alt_tab(from_hwnd):
        assert user.GetForegroundWindow()==from_hwnd
        # Release both keys even if the second key fails.
        user.keybd_event(0x12,0,0,0)
        try:
            user.keybd_event(0x09,0,0,0)
        finally:
            user.keybd_event(0x09,0,2,0)
            user.keybd_event(0x12,0,2,0)

    def tap(key):
        for kind in (s.SDL_KEYDOWN,s.SDL_KEYUP):
            event = s.SDL_Event()
            event.type = kind
            event.key.windowID = s.SDL_GetWindowID(c.window)
            event.key.keysym.sym = key
            assert s.SDL_PushEvent(ct.byref(event))==1

    trace = {}
    try:
        focus(helper)
        focus(c.window)
        with TemporaryDirectory() as folder:
            app = ReleaseGame(c,Path(folder)/'save.json',main._new_stage_game)
            try:
                game,flow = session(5)
                assert fight(flow)[1]=='BOSS_CLEAR'
                frame = 0
                flags, input_log = [], []
                active, gaps = [],[]
                measuring = False
                previous = lost_tick = None
                def until(condition, label):
                    deadline=monotonic()+3
                    while not condition():
                        if monotonic()>deadline:
                            raise RuntimeError(f'{label}: foreground={user.GetForegroundWindow()}, '
                                               f'focus={bool(s.SDL_GetWindowFlags(c.window)&s.SDL_WINDOW_INPUT_FOCUS)}, '
                                               f'fullscreen={app.display.fullscreen}, flips={len(flags)}, '
                                               f'game={game_hwnd}, helper={helper_hwnd}, log={input_log[-12:]}')
                        yield
                def actions():
                    nonlocal measuring,lost_tick
                    for toggle in range(8):
                        focus(c.window)
                        yield from range(5)
                        target=not app.display.fullscreen
                        tap(s.SDLK_F11)
                        yield
                        yield from until(lambda: app.display.fullscreen==target,'F11')
                        flags.append(target)
                    focus(c.window)
                    s.SDL_SetWindowSize(c.window,1060,710)
                    yield from until(lambda:app.display._bounds()[2:]==(1060,710),'resize')
                    yield from range(8)
                    x,y=ct.c_int(),ct.c_int()
                    target=SETTINGS_BUTTON
                    s.SDL_RenderLogicalToWindow(c.renderer,target.left+target.width/2,
                        899-target.bottom-target.height/2,ct.byref(x),ct.byref(y))
                    point=w.POINT(x.value,y.value)
                    assert user.ClientToScreen(w.HWND(game_hwnd),ct.byref(point))
                    assert user.GetForegroundWindow()==game_hwnd and user.WindowFromPoint(point)==game_hwnd
                    user.SetCursorPos(point.x,point.y)
                    user.mouse_event(2,0,0,0,0)
                    user.mouse_event(4,0,0,0,0)
                    yield from until(lambda:app.menu.is_open,'settings click')
                    tap(s.SDLK_ESCAPE)
                    yield from until(lambda:not app.menu.is_open,'close settings')
                    tap(ord('r'))
                    yield from until(lambda:flow.game is not game and flow.game.playing,'boss replay')
                    assert flow.game.stage_number==5 and fight(flow)[1]=='BOSS_CLEAR'
                    yield from range(4)
                    tap(ord('n'))
                    yield from until(lambda:flow.game.stage_number==6,'chapter transition')
                    initial_position=flow.game.player.position
                    # Put the helper directly behind the game in Windows' Alt+Tab order.
                    focus(helper)
                    yield from range(3)
                    focus(c.window)
                    yield from range(6)
                    alt_tab(game_hwnd)
                    yield from until(lambda:user.GetForegroundWindow()==helper_hwnd,'physical Alt+Tab out')
                    yield from until(lambda:not s.SDL_GetWindowFlags(c.window)&s.SDL_WINDOW_INPUT_FOCUS,'focus loss')
                    yield from range(4)
                    lost_tick=flow.game.combat.tick
                    tap(s.SDLK_LEFT)
                    yield from range(15)
                    assert flow.game.combat.tick==lost_tick and flow.game.player.position==initial_position
                    alt_tab(helper_hwnd)
                    yield from until(lambda:user.GetForegroundWindow()==game_hwnd,'physical Alt+Tab back')
                    yield from until(lambda:flow.game.combat.tick>lost_tick,'resume simulation')
                    assert flow.game.player.position==initial_position
                    tap(s.SDLK_RIGHT)
                    yield from until(lambda:flow.game.player.position==(initial_position[0]+1,initial_position[1]),'fresh move')
                    measuring=True
                    yield from range(300)
                    measuring=False
                    event=s.SDL_Event()
                    event.type=s.SDL_QUIT
                    assert s.SDL_PushEvent(ct.byref(event))==1
                    yield
                steps=actions()
                def poll():
                    nonlocal frame,previous
                    frame+=1
                    s.SDL_PumpEvents()
                    next(steps)
                    if measuring:
                        now=perf_counter_ns()
                        if previous is not None:
                            gaps.append((now-previous)/1e6)
                        previous=now
                    events = poll_ready_events(c)
                    for event in events:
                        if event.type in (s.SDL_KEYDOWN,s.SDL_MOUSEBUTTONDOWN):
                            input_log.append((frame,event.type,event.key,event.x,event.y,app.display.fullscreen,
                                              bool(s.SDL_GetWindowFlags(c.window)&s.SDL_WINDOW_INPUT_FOCUS)))
                    return events
                def work_time(elapsed,started):
                    if measuring:
                        active.append(elapsed*1000)
                    return pacer(elapsed,started)
                pacer = main.FramePacer().remaining
                with patch.object(main.FramePacer,'remaining',staticmethod(work_time)):
                    outcome=main.run_session(game,flow,default_art=True,app=app,poll_events=lambda _:poll())
                assert outcome=='exit' and not flow.error
                trace=dict(f11_states=flags,resized=[1060,710],settings_click=True,restart=5,
                           next_stage=6,alt_tab_owned_windows=True,paused_tick=lost_tick,
                           fresh_move=flow.game.player.position,quit=outcome,frames=frame-1,
                           stage6_work_ms=summary(active),stage6_paced_ms=summary(gaps))
            finally:
                app.close()
    finally:
        user.SetCursorPos(previous_cursor.x,previous_cursor.y)
        s.SDL_DestroyWindow(helper)
        c.close_canvas()
    output.write_text(json.dumps(trace,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    run(parser.parse_args().output)
