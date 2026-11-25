"""Capture actual ledger warning phases and compare matched hidden SDL frames."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import pickle
from statistics import median
import sys
from time import perf_counter_ns
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from actor_animation import ActorAnimation
from attack_telegraph import TelegraphRenderer, warning_frame
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from game_audio import AudioManager, AudioSettings
from game_renderer import GameFlowRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from tests.test_game_audio import FakeMixer
from tools.stage5_art_preview import capture_png, open_preview


def run(output, driver, *, baseline=None):
    import sdl2 as s
    from pico2d import pico2d as c

    if output:
        output.mkdir(parents=True,exist_ok=False)
    motion = RenderMotion(improved=True)
    anim = ActorAnimation(improved=True)
    vfx = CombatVFX(layered=True)
    overlay = TelegraphRenderer()
    prior = baseline.TelegraphRenderer() if baseline else None
    art = LiveArenaArtPath(c,motion=motion,animation=anim,vfx=vfx,enlarged=True,
                           default_enabled=True,telegraph=overlay)
    mixer = FakeMixer()
    audio = AudioManager(mixer,AudioSettings())
    hud = GameFlowRenderer(official=True)
    scenes,performance = {},{}

    def sync(g, dt):
        frozen = {g.player.entity_instance_id} if g.combat.active_attack or g.parry.active_at(g.combat.tick) else set()
        if g.encounter.pulse:
            frozen.update(e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse.frozen(e))
        motion.update((g.player,*g.encounter.enemies),dt,session=g.combat.combat_session_id,frozen=frozen)
        batch = g.encounter.ledger.presentation.drain()
        anim.update(g,dt,batch,motion=motion)
        vfx.update(g,dt,batch,motion=motion)
        mixer.live.clear()
        audio.update(g,dt,batch,motion=motion)

    def stage(number):
        g = _new_stage_game(number)
        g.encounter.ledger.presentation = PresentationEvents()
        sync(g,0)
        return g

    def advance(g, *, parry=False):
        if parry:
            g.combat.advance(1)
            binding = g.resolver.register_parry(g.parry.request(g.combat.tick))
            assert binding.adjudication_grade=='perfect'
            g.resolve_current_tick()
        else:
            g.advance()
        sync(g,1/60)

    def draw(g, *, mode='a3', label=False):
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        if art.path and art.stage==g.stage_number and art.path.renderer:
            art.path.renderer.telegraph = {'a3':overlay,'a3b':prior}.get(mode)
        assert art.draw(g,motion.positions)
        assert not overlay.failed and not art.path.renderer.animation_failed and not vfx.failed
        if label:
            hud.draw_stage_label(c,g)
        return art.path.renderer

    def capture(g, name, *, mode='a3'):
        before = pickle.dumps(g)
        read = baseline.warning_frame if mode=='a3b' else warning_frame
        cells,hint = read(g)
        renderer = draw(g,mode=mode,label=True)
        assert set(renderer.warning_cells)==set(cells)
        if mode!='a2b':
            assert len(renderer.warning_cells)==len(cells) and renderer.parry_hint==hint
        assert pickle.dumps(g)==before
        meta = dict(stage=g.stage_number,tick=g.combat.tick,mode=mode,warned=len(cells),
                    hit_ticks=sorted({r.attack.hit_tick for r in cells.values()}),
                    phase=hint.status if hint else None,
                    input_tick=hint.tick if hint else None,
                    target_id=hint.target[-1] if hint and hint.target else None,
                    fill=sorted({round(r.opacity,3) for r in cells.values()}),
                    active=[f.name for f in vfx.effects])
        if mode=='a3' and hint and hint.ring:
            meta['ring'] = dict(target_id=hint.ring.attack_key[-1],ticks_left=hint.ring.ticks_left,
                                radius=round(hint.ring.radius,4),alt=hint.status=='perfect' and bool(hint.target))
        if output:
            file = output/(name+'.png')
            capture_png(c,file)
            meta['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
        scenes[name] = meta
        if mode=='a3' and prior is not None and name in {
            'stage24_two_queen_warnings','stage24_crossing_a3','stage25_pulse_start',
            'stage25_pulse_normal','stage25_pulse_perfect_entry','stage25_pulse_resolved_a3',
        }:
            capture(g,name+'_a3b',mode='a3b')

    def compare(g, label):
        previous = 'a3b' if prior is not None else 'a2b'
        samples = {previous:[],'a3':[]}
        for block in range(12):
            modes = (previous,'a3') if block%2==0 else ('a3',previous)
            for mode in modes:
                for _ in range(12):
                    start = perf_counter_ns()
                    anim.update(g,0,(),motion=motion)
                    draw(g,mode=mode)
                    s.SDL_RenderPresent(c.renderer)
                    if block>=2:
                        samples[mode].append((perf_counter_ns()-start)/1e6)
        for mode,values in samples.items():
            values.sort()
            samples[mode] = [round(x,3) for x in (median(values),values[113],values[118])]
        performance[label] = samples

    env = {k:v for k,v in os.environ.items()
           if not (k.startswith('CHECKMATE_') and k.endswith('_ART'))}
    env.update(SDL_VIDEODRIVER='windows' if driver=='direct3d11' else 'dummy',SDL_AUDIODRIVER='dummy')
    with patch.dict(os.environ,env,clear=True):
        if driver=='direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
            make = c.SDL_CreateRenderer
            with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:make(w,i,s.SDL_RENDERER_ACCELERATED)):
                open_preview(c,capture=True)
        else:
            open_preview(c,capture=True)
        try:
            info = s.SDL_RendererInfo()
            assert s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info))==0 and info.name.decode()==driver
            for number in (4,14):
                g = stage(number)
                for _ in range(600):
                    advance(g)
                    live = tuple(g.resolver.live_telegraphs(g.combat.tick))
                    if any(len(a.target_cells)==50 and a.hit_tick-g.combat.tick==7 for a in live):
                        capture(g,f'stage{number}_bishop_perfect_entry')
                        break
                else:
                    raise AssertionError('No actual Bishop warning at perfect entry')

            for number in (9,19):
                g = stage(number)
                for _ in range(390):
                    advance(g)
                    cells,hint = warning_frame(g)
                    if cells and hint and hint.ring:
                        capture(g,f'stage{number}_targeted_warning')
                        break
                else:
                    raise AssertionError(f'No warning targeting the player on Stage {number}')

            g = stage(24)
            seen_charge = False
            for _ in range(160):
                advance(g)
                queens = [e for e in g.resolver.live_telegraphs(g.combat.tick) if e.attack_kind=='queen_diagonal']
                if not seen_charge and len(queens)==2:
                    assert set(queens[0].target_cells)&set(queens[1].target_cells)
                    capture(g,'stage24_two_queen_warnings')
                    seen_charge = True
                fx = [f for f in vfx.effects if f.name=='queen_fire']
                if len({f.key[2] for f in fx})==2:
                    assert seen_charge
                    capture(g,'stage24_crossing_a2b',mode='a2b')
                    capture(g,'stage24_crossing_a3')
                    compare(g,'stage24_crossing')
                    break
            else:
                raise AssertionError('No overlapping actual Queen attacks')

            g = stage(25)
            phases = {120:'start',60:'charge',19:'normal_next_tick',18:'normal',8:'perfect_next_tick',
                      7:'perfect_entry',1:'last_warning'}
            while g.combat.tick < 389:
                advance(g,parry=g.combat.tick==378)
                event = g.encounter.pulse.event
                if event and g.encounter.ledger.state(event)=='telegraph':
                    delta = event.hit_tick-g.combat.tick
                    if delta in phases:
                        capture(g,'stage25_pulse_'+phases[delta])
                        if delta==7:
                            capture(g,'stage25_pulse_perfect_entry_a2b',mode='a2b')
                            compare(g,'stage25_pulse_perfect_entry')
                if g.combat.tick==385:
                    assert any(f.name=='king_pulse' and len(f.cells)==100 for f in vfx.effects)
                    assert g.resolver.last_parry_result.status=='perfect'
                    assert any(f.name=='player_hit' and f.amount==2 for f in vfx.effects)
                    assert 'parry_perfect' in mixer.cues
                    capture(g,'stage25_pulse_impact_perfect')
            capture(g,'stage25_pulse_resolved_a3')
            compare(g,'stage25_pulse_resolved')

            g = stage(25)
            while g.combat.tick < 385:
                advance(g)
            assert any(f.name=='king_pulse' for f in vfx.effects)
            assert any(f.name=='player_hurt' and f.amount==1 for f in vfx.effects)
            capture(g,'stage25_unparried_impact')
        finally:
            audio.close()
            art.close()
            c.close_canvas()
            c.renderer=c.window=None
    manifest = dict(driver=driver,captures=scenes)
    if output:
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return dict(captures=len(scenes),performance_ms=performance)


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path)
    p.add_argument('--renderer',choices=('direct3d11','software'),default='direct3d11')
    args = p.parse_args()
    print(json.dumps(run(args.output,args.renderer),indent=2))
