"""Measure the paced release combat loop with a real clock, SDL poll, mixer and D3D11."""
import argparse
from contextlib import nullcontext
import ctypes as ct
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from unittest.mock import patch

from r7c2_performance import baseline_methods, summary, window
import main
from release_game import ReleaseGame
from sdl_input import poll_ready_events
from tools.chapter_art_play import session


def measure(path, *, desktop=False):
    import sdl2 as s
    from sdl2 import sdlmixer as mix
    if desktop:
        from pico2d import pico2d as c
        from config import WINDOW_WIDTH, WINDOW_HEIGHT
        from r7c2_window_qa import focus as focus_window
        os.environ.update(SDL_VIDEODRIVER='windows',SDL_AUDIODRIVER='dummy')
        s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
        c.open_canvas(WINDOW_WIDTH,WINDOW_HEIGHT)
        c.hide_lattice()
        focus_window(c.window)
        info = s.SDL_RendererInfo()
        assert not s.SDL_GetRendererInfo(c.renderer,ct.byref(info))
        assert info.name==b'direct3d11' and c.audio_on
    else:
        c = window()
        assert not s.SDL_InitSubSystem(s.SDL_INIT_AUDIO)
        assert not mix.Mix_OpenAudio(44100,mix.MIX_DEFAULT_FORMAT,2,1024)
        c.audio_on=True
    flags = c.SDL_GetWindowFlags
    original = c.get_events
    legacy = baseline_methods()
    results = {}
    try:
        for stage,end in ((24,160),(25,414)):
            for mode in ('before','after'):
                with TemporaryDirectory() as folder:
                    app = ReleaseGame(c,Path(folder)/'save.json',main._new_stage_game)
                    try:
                        game,flow = session(stage)
                        key_at = 114 if stage==24 else 378
                        sent = False
                        stamps,ticks,work,poll_cost = [],[],[],[]
                        def poll():
                            nonlocal sent
                            now=perf_counter_ns()
                            if desktop and not flags(c.window)&s.SDL_WINDOW_INPUT_FOCUS:
                                raise RuntimeError('Desktop window lost input focus during measurement')
                            if not sent and key_at<=game.combat.tick<key_at+4:
                                for kind in (s.SDL_KEYDOWN,s.SDL_KEYUP):
                                    event=s.SDL_Event()
                                    event.type=kind
                                    event.key.windowID=s.SDL_GetWindowID(c.window)
                                    event.key.keysym.sym=s.SDLK_LALT
                                    assert s.SDL_PushEvent(ct.byref(event))==1
                                sent=True
                            if game.combat.tick>=end:
                                event=s.SDL_Event()
                                event.type=s.SDL_QUIT
                                assert s.SDL_PushEvent(ct.byref(event))==1
                            assert game.playing and len(stamps)<4000
                            events=original() if mode=='before' else poll_ready_events(c)
                            poll_cost.append((perf_counter_ns()-now)/1e6)
                            stamps.append(now)
                            ticks.append(game.combat.tick)
                            return events
                        pacer = main.FramePacer.remaining
                        def remaining(self,elapsed,*args,**kwargs):
                            work.append(elapsed*1000)
                            return pacer(self,elapsed) if mode=='before' else pacer(self,elapsed,*args,**kwargs)
                        focus = nullcontext() if desktop else patch.object(
                            c,'SDL_GetWindowFlags',lambda w:flags(w)|s.SDL_WINDOW_INPUT_FOCUS)
                        with legacy() if mode=='before' else nullcontext(), focus, \
                             patch.object(main.FramePacer,'remaining',remaining):
                            assert main.run_session(game,flow,default_art=True,app=app,poll_events=lambda _:poll())=='exit'
                        assert game.resolver.last_parry_result.status=='perfect'
                        observed=[i for i in range(1,len(work)) if ticks[i]>=5]
                        hot=[i for i in observed if key_at-4<=ticks[i]<=key_at+32]
                        def stats(indices):
                            gaps=[(stamps[i+1]-stamps[i])/1e6 for i in indices]
                            seconds=sum(gaps)/1000
                            return dict(paced_interval_ms=summary(gaps),work_ms=summary([work[i] for i in indices]),
                                        poll_ms=summary([poll_cost[i] for i in indices]),
                                        actual_fps=round(len(gaps)/seconds,2),
                                        simulation_hz=round((ticks[indices[-1]+1]-ticks[indices[0]])/seconds,2))
                        results[f'{stage}_{mode}']=dict(cold_first_ms=round(work[0],3),
                                                    active=stats(observed),impact=stats(hot))
                    finally:
                        app.close()
    finally:
        c.close_canvas()
    path.write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--desktop',action='store_true',help='Use the release canvas and require native focus')
    args = parser.parse_args()
    measure(args.output,desktop=args.desktop)
