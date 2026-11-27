"""Time-bounded D3D11 campaign-scene soak with native ownership and WDDM telemetry."""
import argparse
from collections import Counter
from contextlib import ExitStack
import ctypes as ct
from ctypes import wintypes as w
import json
import os
from pathlib import Path
from time import monotonic, perf_counter_ns, sleep
from unittest.mock import patch

from r7c2_performance import Battle, DisplaySettings, SettingsMenu, SettingsRenderer, window
from game_audio import AudioManager, AudioSettings, MixerAudio


class Memory(ct.Structure):
    _fields_ = [('size',w.DWORD),('faults',w.DWORD)] + [
        (name,ct.c_size_t) for name in ('peak_ws','working_set','peak_paged','paged','peak_nonpaged',
                                        'nonpaged','pagefile','peak_pagefile','private')]


class CounterValue(ct.Structure):
    _fields_ = [('status',w.DWORD),('value',ct.c_double)]


class CounterItem(ct.Structure):
    _fields_ = [('instance',w.LPWSTR),('data',CounterValue)]


class MemoryMonitor:
    def __init__(self):
        self.pdh = ct.windll.pdh
        self.query = w.HANDLE()
        assert self.pdh.PdhOpenQueryW(None,0,ct.byref(self.query))==0
        self.counters = {}
        for kind in ('Dedicated','Shared'):
            counter = w.HANDLE()
            name = rf'\GPU Process Memory(*)\{kind} Usage'
            result = self.pdh.PdhAddEnglishCounterW(self.query,name,0,ct.byref(counter))
            if result==0:
                self.counters[kind] = counter

    def read(self):
        mem = Memory()
        mem.size = ct.sizeof(mem)
        assert ct.windll.psapi.GetProcessMemoryInfo(w.HANDLE(-1),ct.byref(mem),mem.size)
        result = dict(private=mem.private,working_set=mem.working_set)
        assert self.pdh.PdhCollectQueryData(self.query)==0
        for kind,counter in self.counters.items():
            length,count = w.DWORD(),w.DWORD()
            self.pdh.PdhGetFormattedCounterArrayW(counter,0x200,ct.byref(length),ct.byref(count),None)
            if length.value:
                buffer = ct.create_string_buffer(length.value)
                status = self.pdh.PdhGetFormattedCounterArrayW(counter,0x200,ct.byref(length),ct.byref(count),buffer)
                assert status==0,status
                items = ct.cast(buffer,ct.POINTER(CounterItem))
                values = [items[i].data.value for i in range(count.value)
                          if items[i].instance.startswith(f'pid_{os.getpid()}_') and items[i].data.status in (0,1)]
                result[kind.lower()] = round(sum(values)) if values else None
        return result

    def close(self):
        self.pdh.PdhCloseQuery(self.query)


class Owners:
    def __init__(self):
        self.live = {}
        self.created,self.freed = Counter(),Counter()

    def watch(self,stack,module,method,kind,*,release=False,member=None):
        native = getattr(module,method)
        live = self.live.setdefault(kind,set())
        def call(*args):
            if release and args[0]:
                address = ct.cast(args[0],ct.c_void_p).value
                live.remove(address)
                self.freed[kind] += 1
            value = native(*args)
            if not release and value:
                ptr = getattr(value,member) if member else value
                address = ct.cast(ptr,ct.c_void_p).value
                assert address and address not in live,(kind,address)
                live.add(address)
                self.created[kind] += 1
            return value
        stack.enter_context(patch.object(module,method,call))


def soak(output,seconds):
    from sdl2 import sdlimage, sdlmixer as mix
    import sdl2 as s
    c = window()
    display = DisplaySettings(c)
    assert not s.SDL_InitSubSystem(s.SDL_INIT_AUDIO)
    assert not mix.Mix_OpenAudio(44100,mix.MIX_DEFAULT_FORMAT,2,1024)
    c.audio_on=True
    monitor,owners = MemoryMonitor(),Owners()
    start = monotonic()
    output.parent.mkdir(parents=True,exist_ok=True)
    rows,frames,transitions = [],0,0
    stages = ((24,150),(25,400),(5,130),(10,130),(15,130),(20,130))
    def record(phase):
        entry = dict(seconds=round(monotonic()-start,3),phase=phase,frames=frames,transitions=transitions,
                     memory_bytes=monitor.read(),live={k:len(v) for k,v in owners.live.items()})
        rows.append(entry)
        output.write_text(json.dumps(dict(pid=os.getpid(),samples=rows,created=dict(owners.created),
                                          freed=dict(owners.freed)),indent=2)+'\n',encoding='utf8')
    try:
        with ExitStack() as stack:
            for module,create,free,kind,member in (
                (c,'load_image','SDL_DestroyTexture','texture','texture'),
                (c,'load_font','TTF_CloseFont','font','font'),
                (mix,'Mix_LoadWAV','Mix_FreeChunk','chunk',None),
                (mix,'Mix_LoadMUS','Mix_FreeMusic','music',None)):
                owners.watch(stack,module,create,kind,member=member)
                owners.watch(stack,module,free,kind,release=True)
            owners.watch(stack,c,'SDL_CreateTextureFromSurface','texture')
            owners.watch(stack,sdlimage,'IMG_LoadTexture','texture')
            settings = SettingsRenderer(c,themed=True)
            audio = AudioManager(MixerAudio.open(c),AudioSettings())
            battle = Battle(c,settings,SettingsMenu(),display)
            try:
                record('open')
                deadline = perf_counter_ns()
                while monotonic()-start<seconds or transitions%len(stages):
                    stage,ticks = stages[transitions%len(stages)]
                    battle.start(stage)
                    for frame in range(ticks*3):
                        if frame%3==0:
                            battle.advance()
                        battle.sync(1/180,audio)
                        battle.draw()
                        c.update_canvas()
                        frames += 1
                        deadline += round(1e9/180)
                        now = perf_counter_ns()
                        if deadline>now:
                            sleep((deadline-now)/1e9)
                        elif now-deadline>100_000_000:
                            deadline=now
                    transitions += 1
                    if stage==25 or transitions%len(stages)==0:
                        record(f'stage{stage}')
            finally:
                battle.art.close()
                audio.close()
                settings.close()
            assert owners.created==owners.freed,(owners.created,owners.freed)
            record('released')
    finally:
        c.close_canvas()
        monitor.close()


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--seconds',type=float,default=1800.)
    args=parser.parse_args()
    assert args.seconds>0
    soak(args.output,args.seconds)
