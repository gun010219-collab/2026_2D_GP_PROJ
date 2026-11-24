"""Play CHECKMATE sounds individually or verify the actual mixer on a dummy device."""
import argparse
import json
import os
from pathlib import Path
from statistics import median
import sys
from time import perf_counter_ns, sleep

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game_audio import AudioManager, AudioSettings, MixerAudio, PRIORITIES, ROOT, TRACKS
from presentation_events import PresentationEvents


def verify(backend):
    mix = backend.mix
    assert len(backend.sounds)==len(PRIORITIES) and all(backend.sounds.values())
    for name in TRACKS:
        backend.music(name)
        assert mix.Mix_PlayingMusic()==1 and not backend.failures
    for name in PRIORITIES:
        assert backend.sound(name,0) and backend.playing(0),name
    backend.clear_voices()
    assert not backend.playing(0)
    backend.music(None)
    assert not mix.Mix_PlayingMusic()
    backend.close()
    assert not backend.sounds and not backend.tracks
    print(f'Dummy SDL_mixer loaded, played and released {len(PRIORITIES)} SFX and {len(TRACKS)} BGM')


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
    parser.add_argument('--verify',action='store_true',help='Use the silent SDL dummy device')
    parser.add_argument('--benchmark',action='store_true',help='Time real Queen / Pulse batches on dummy SDL')
    parser.add_argument('--seconds',type=float,default=9,help='Seconds per BGM preview')
    parser.add_argument('--bgm',type=int,choices=range(101),default=45,metavar='0..100')
    parser.add_argument('--sfx',type=int,choices=range(101),default=75,metavar='0..100')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    durations = {Path(row['file']).stem:row['duration_s'] for row in manifest['files']}
    for name in args.name:
        if name not in durations:
            parser.error(f'Unknown audio cue: {name}')
    if args.list or not (args.name or args.verify or args.benchmark):
        print('BGM:',', '.join(TRACKS))
        print('SFX:',', '.join(PRIORITIES))
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
                    for name in args.name:
                        print(name,flush=True)
                        if name in TRACKS:
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
