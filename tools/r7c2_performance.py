"""Windows D3D11 matched-frame benchmark and repeatable release-render workload."""
import argparse
import ast
import cProfile
from contextlib import ExitStack, nullcontext
import ctypes as ct
import hashlib
import json
import math
import os
from pathlib import Path
import pstats
import sys
import subprocess
from struct import Struct
from time import perf_counter_ns
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from actor_animation import ActorAnimation
from attack_telegraph import TelegraphRenderer
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from display_settings import DisplaySettings
from game_renderer import GameFlowRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from sprite_atlas import opted_in_catalog
from tools.stage5_art_preview import open_preview


def summary(samples):
    values = sorted(samples)
    def quantile(q):
        return round(values[math.ceil(q*len(values))-1],4)
    return dict(frames=len(values),p50=quantile(.5),p95=quantile(.95),p99=quantile(.99),
                max_ms=round(values[-1],4),over_budget=sum(t>1000/180 for t in values))


class Battle:
    def __init__(self,c,settings,menu,display):
        self.c,self.settings,self.menu,self.display = c,settings,menu,display
        self.motion = RenderMotion(improved=True)
        catalog = opted_in_catalog()
        self.anim = ActorAnimation(improved=True,enemy_attacks=True,player_actions=True,
                                   articulated=True,sprites=catalog is not None)
        self.effects = CombatVFX(layered=True)
        self.hud = GameFlowRenderer(official=True)
        self.art = LiveArenaArtPath(c,motion=self.motion,animation=self.anim,vfx=self.effects,
                                    default_enabled=True,enlarged=True,telegraph=TelegraphRenderer(),
                                    player_combat_visual=True,sprite_catalog=catalog)

    def start(self,stage):
        self.game = _new_stage_game(stage)
        self.queue = self.game.encounter.ledger.presentation = PresentationEvents()
        self.sync(0)

    def sync(self,dt,audio=None):
        g = self.game
        batch = self.queue.drain()
        frozen = {g.player.entity_instance_id} if g.parry.active_at(g.combat.tick) else set()
        if g.encounter.pulse:
            frozen.update(e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse.frozen(e))
        self.motion.update((g.player,*g.encounter.enemies),dt,session=g.combat.combat_session_id,frozen=frozen)
        self.anim.update(g,dt,batch,motion=self.motion)
        self.effects.update(g,dt,batch,motion=self.motion)
        if audio:
            audio.update(g,dt,batch,motion=self.motion)

    def advance(self):
        g = self.game
        g.advance()
        entry = 378 if g.stage_number==25 else 114 if g.stage_number==24 else None
        if g.combat.tick==entry:
            binding = g.resolver.register_parry(g.parry.request(entry))
            assert binding.adjudication_grade=='perfect'

    def draw(self):
        c,g = self.c,self.game
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        assert self.art.draw(g,self.motion.positions)
        self.hud.draw_stage_label(c,g)
        self.settings.draw(self.menu,self.display)


def window(visible=False):
    os.environ.update(SDL_VIDEODRIVER='windows',SDL_AUDIODRIVER='dummy')
    from pico2d import pico2d as c
    import sdl2 as s
    s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
    make = c.SDL_CreateRenderer
    with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:make(w,i,s.SDL_RENDERER_ACCELERATED)):
        open_preview(c,capture=not visible)
    info = s.SDL_RendererInfo()
    assert not s.SDL_GetRendererInfo(c.renderer,ct.byref(info)) and info.name==b'direct3d11'
    return c


def baseline_methods():
    """Only these two packing functions differ from the approved C1 renderer."""
    import actor_mesh
    import combat_vfx_renderer
    previous = {}
    for module,function in ((actor_mesh,'draw_actor'),(combat_vfx_renderer,'tri')):
        source = subprocess.check_output(['git','-c',f'safe.directory={ROOT}','show',
            f'f6385596ea484b47b3c0550c6cc334a8e53684c3:{module.__name__}.py'],cwd=ROOT)
        tree = ast.parse(source)
        node, = (n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==function)
        ns = {**vars(module),'_VERTEX':Struct('=ff4B8x')}
        exec(compile(ast.Module([node],[]),module.__file__,'exec'),ns)
        previous[function] = ns[function]
    def apply():
        stack = ExitStack()
        stack.enter_context(patch.object(actor_mesh,'draw_actor',previous['draw_actor']))
        stack.enter_context(patch.object(combat_vfx_renderer.Mesh,'tri',previous['tri']))
        return stack
    return apply


def benchmark(path, *, visible=False, paired=False):
    import sdl2 as s
    baseline = baseline_methods() if paired else None
    c = window(visible)
    display = DisplaySettings(c)
    settings = SettingsRenderer(c,themed=True)
    battle = Battle(c,settings,SettingsMenu(),display)
    report = {}
    try:
        for stage,ticks in ((24,(135,)),(25,(378,389))):
            battle.start(stage)
            for wanted in ticks:
                while battle.game.combat.tick<wanted:
                    battle.advance()
                    battle.sync(1/60)
                battle.draw()
                pixels = (ct.c_ubyte*(1440*900*4))()
                assert not s.SDL_RenderReadPixels(c.renderer,None,s.SDL_PIXELFORMAT_RGBA32,pixels,1440*4)
                digest = hashlib.sha256(pixels).hexdigest()
                c.update_canvas()
                if paired:
                    samples = {'before':[],'after':[]}
                    for block in range(6):
                        order = ('before','after') if block%2==0 else ('after','before')
                        for mode in order:
                            with baseline() if mode=='before' else nullcontext():
                                battle.draw()
                                assert not s.SDL_RenderReadPixels(c.renderer,None,s.SDL_PIXELFORMAT_RGBA32,pixels,1440*4)
                                assert hashlib.sha256(pixels).hexdigest()==digest
                                for i in range(110):
                                    begin=perf_counter_ns()
                                    battle.draw()
                                    c.update_canvas()
                                    if i>=10:
                                        samples[mode].append((perf_counter_ns()-begin)/1e6)
                    report[f'{stage}_{wanted}'] = dict(sha256=digest,timing={k:summary(v) for k,v in samples.items()})
                    continue
                values = []
                for i in range(420):
                    begin = perf_counter_ns()
                    battle.draw()
                    c.update_canvas()
                    if i>=60:
                        values.append((perf_counter_ns()-begin)/1e6)
                profiler = cProfile.Profile()
                with profiler:
                    for _ in range(40):
                        battle.draw()
                        c.update_canvas()
                stats = pstats.Stats(profiler).stats
                top = sorted(stats.items(),key=lambda p:-p[1][2])[:22]
                profile = [dict(function=f'{Path(key[0]).name}:{key[2]}',calls=v[1],
                                self_ms_frame=round(v[2]*25,4),total_ms_frame=round(v[3]*25,4))
                           for key,v in top]
                report[f'{stage}_{wanted}'] = dict(timing=summary(values),sha256=digest,profile=profile)
    finally:
        battle.art.close()
        settings.close()
        c.close_canvas()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    for scene,data in report.items():
        print(scene,data['timing'])


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--visible',action='store_true')
    parser.add_argument('--paired',action='store_true')
    options=parser.parse_args()
    benchmark(options.output,visible=options.visible,paired=options.paired)
