"""Play CHECKMATE sounds individually or verify the actual mixer on a dummy device."""
import argparse
from array import array
from ctypes import string_at
import json
from math import log10
import os
from pathlib import Path
from statistics import median
import sys
from time import perf_counter_ns, sleep

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game_audio import (AudioManager, AudioSettings, BGM_PLAYLIST, MixerAudio, PRIORITIES,
                        RENEWED_CUES, ROOT, THEMED_SFX, TRACKS, VOICES)
from presentation_events import PresentationEvents


def private_bytes():
    if sys.platform!='win32':
        return None
    import ctypes as c
    from ctypes import wintypes as w

    class Counters(c.Structure):
        _fields_=[('size',w.DWORD),('faults',w.DWORD),('values',c.c_size_t*8),('private',c.c_size_t)]

    counters=Counters()
    counters.size=c.sizeof(counters)
    query=c.windll.psapi.GetProcessMemoryInfo
    query.argtypes=[w.HANDLE,c.POINTER(Counters),w.DWORD]
    return counters.private if query(w.HANDLE(-1),c.byref(counters),counters.size) else None


def verify(backend):
    mix = backend.mix
    assert len(backend.sounds)==len(PRIORITIES) and all(backend.sounds.values())
    cold_ms={}
    initial_memory=private_bytes()
    memory_samples=[]
    loops=[]
    for name in (*BGM_PLAYLIST,'boss'):
        start=perf_counter_ns()
        backend.music(name)
        cold_ms[name]=round((perf_counter_ns()-start)/1e6,3)
        assert mix.Mix_PlayingMusic()==1 and not backend.failures
        expected=ROOT/'renewal'/(name+'.ogg')
        if expected.is_file():
            assert backend.track_paths[name]==expected
            handle=backend.tracks[name]
            assert mix.Mix_GetMusicType(handle)==mix.MUS_OGG
            duration=mix.Mix_MusicDuration(handle)
            assert duration>1 and mix.Mix_SetMusicPosition(duration-.065)==0,name
            sleep(.19)
            assert mix.Mix_PlayingMusic()==1 and 0<=mix.Mix_GetMusicPosition(handle)<2,name
            loops.append(name)
        memory=private_bytes()
        if memory is not None and initial_memory is not None:
            memory_samples.append(memory-initial_memory)
    print('First music loads and starts in ms',cold_ms)
    print('Native Vorbis loop wraps',len(loops))
    if memory_samples:
        print('Maximum sampled Windows private bytes above SFX-loaded baseline',max(memory_samples))
    backend.music(None)
    verify_sfx(backend)
    backend.clear_voices()
    assert not backend.playing(0)
    backend.music(None)
    assert not mix.Mix_PlayingMusic()
    backend.close()
    assert not backend.sounds and not backend.replacements and not backend.tracks
    print(f'Dummy SDL_mixer played {len(PRIORITIES)} shared cues, {len(THEMED_SFX)} themed cues and {len(cold_ms)} BGM paths')


def verify_sfx(backend):
    mix = backend.mix
    blocks = []

    @mix.mix_func
    def capture(_, stream, length):
        blocks.append(string_at(stream, length))

    def recorded_peak():
        samples = array('h')
        samples.frombytes(b''.join(blocks))
        return max(map(abs, samples), default=0)/32768

    backend.volume(45,75)
    mix.Mix_SetPostMix(capture,None)
    levels = {}
    try:
        for name in (*PRIORITIES, *THEMED_SFX):
            backend.clear_voices()
            blocks.clear()
            assert backend.sound(name,0) and backend.playing(0),name
            sleep(.11)
            peak = recorded_peak()
            assert .01 < peak < .25,(name,peak)
            levels[name] = round(20*log10(peak),1)
        assert all(backend.replacements.get(name) for name in (*RENEWED_CUES, *THEMED_SFX))
        assert levels['parry_perfect'] > levels['parry_normal']+1.5,levels
        backend.clear_voices()
        backend.volume(100,100)
        backend.music('boss_gothic')
        sleep(.22)
        blocks.clear()
        for channel in range(VOICES):
            assert backend.sound('parry_perfect',channel)
        sleep(.27)
        stacked_peak = recorded_peak()
        assert .25 < stacked_peak < .97,stacked_peak
        backend.clear_voices()
        blocks.clear()
        mixed = ('player_hit','parry_perfect','player_hurt','rook_impact',
                 'forest/bishop_cast','frozen/queen_fire','gothic/king_pulse','ui_select')
        for channel,name in enumerate(mixed):
            assert backend.sound(name,channel)
        sleep(.27)
        mixed_peak = recorded_peak()
        assert .20 < mixed_peak < .97,mixed_peak
        print('SFX postmix peak dBFS range', min(levels.values()), max(levels.values()))
        print('Isolated cue peaks dBFS', {name:levels[name] for name in
              ('player_swing','player_hit','parry_normal','parry_perfect','royal/queen_fire','ui_select')})
        print('Full-volume stacked / mixed postmix peaks dBFS',
              round(20*log10(stacked_peak),1),round(20*log10(mixed_peak),1))
    finally:
        mix.Mix_SetPostMix(mix.mix_func(),None)


def benchmark(backend):
    from main import _new_stage_game
    from render_motion import RenderMotion

    cases = []
    for stage in (24,25):
        game = _new_stage_game(stage)
        feed = game.encounter.ledger.presentation = PresentationEvents()
        while game.playing and game.combat.tick < 510:
            game.advance()
            batch = feed.drain()
            if any(e.kind=='attack_start' and getattr(e.payload,'attack_kind','') in
                   ('queen_diagonal','king_pulse') for e in batch):
                cases.append((game,batch))
                break
    assert len(cases)==2
    manager = AudioManager(backend,AudioSettings())
    motion = RenderMotion()
    results = {}
    for game,batch in cases:
        motion.update((game.player,*game.encounter.enemies),0,session=game.combat.combat_session_id)
        manager.update(game,0,(),motion=motion)
        samples = []
        for _ in range(400):
            # Retain the live warmed track. Reset only delivery keys to repeat
            # the same genuine frame as an isolated technical measurement.
            manager.seen.clear()
            manager.tick = -1
            manager.backend.clear_voices()
            start = perf_counter_ns()
            manager.update(game,1/180,batch,motion=motion)
            samples.append((perf_counter_ns()-start)/1e6)
        samples.sort()
        results[game.stage_number] = [round(x,4) for x in (median(samples),samples[379],samples[395])]
    print('Audio consumer median, P95, P99 in ms',results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name',nargs='*',choices=None,help='SFX or BGM names in playback order')
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--all-bgm',action='store_true',help='Play menu, five chapter/boss pairs, and ending in order')
    parser.add_argument('--combat-sfx',action='store_true',help='Play renewed combat sounds followed by all five chapter sets')
    parser.add_argument('--verify',action='store_true',help='Use the silent SDL dummy device')
    parser.add_argument('--benchmark',action='store_true',help='Time real Queen / Pulse batches on dummy SDL')
    parser.add_argument('--seconds',type=float,default=9,help='Seconds per BGM preview')
    parser.add_argument('--bgm',type=int,choices=range(101),default=45,metavar='0..100')
    parser.add_argument('--sfx',type=int,choices=range(101),default=75,metavar='0..100')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    durations = {Path(row['file']).stem:row['duration_s'] for row in manifest['files']}
    renewal = ROOT/'renewal'/'manifest.json'
    if renewal.is_file():
        for row in json.loads(renewal.read_text(encoding='utf-8'))['files']:
            durations[Path(row['file']).stem]=row['duration_s']
    combat = ROOT/'combat_sfx'/'manifest.json'
    if combat.is_file():
        for row in json.loads(combat.read_text(encoding='utf-8'))['files']:
            durations[row['file'].removesuffix('.wav')]=row['duration_s']
    durations.update({name:durations.get(name,durations['boss']) for name in BGM_PLAYLIST if name.startswith('boss_')})
    playlist = BGM_PLAYLIST if args.all_bgm else args.name
    if args.combat_sfx:
        playlist = (*playlist, *RENEWED_CUES, *THEMED_SFX)
    for name in playlist:
        if name not in durations:
            parser.error(f'Unknown audio cue: {name}')
    if args.list or not (playlist or args.verify or args.benchmark):
        print('BGM:',', '.join(BGM_PLAYLIST))
        print('SFX:',', '.join(PRIORITIES))
        print('Chapter SFX:',', '.join(THEMED_SFX))
        return
    if args.verify or args.benchmark:
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    import sdl2 as s
    from sdl2 import sdlmixer as mix
    if s.SDL_InitSubSystem(s.SDL_INIT_AUDIO):
        raise SystemExit(s.SDL_GetError().decode())
    try:
        if mix.Mix_OpenAudio(44100,mix.MIX_DEFAULT_FORMAT,2,1024):
            raise SystemExit(s.SDL_GetError().decode())
        try:
            backend = MixerAudio(mix)
            manager = AudioManager(backend,AudioSettings(bgm=args.bgm,sfx=args.sfx))
            try:
                if args.benchmark:
                    benchmark(backend)
                if args.verify:
                    verify(backend)
                elif not args.benchmark:
                    for name in playlist:
                        print(name,flush=True)
                        if name in BGM_PLAYLIST or name in TRACKS:
                            manager.set_music(name)
                            sleep(max(0,min(args.seconds,durations[name])))
                            manager.set_music(None)
                        else:
                            manager.play(name)
                            sleep(durations[name]+.15)
            finally:
                manager.close()
        finally:
            mix.Mix_CloseAudio()
    finally:
        s.SDL_QuitSubSystem(s.SDL_INIT_AUDIO)


if __name__=='__main__':
    main()
