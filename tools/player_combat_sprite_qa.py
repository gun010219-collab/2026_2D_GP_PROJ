
"""Compare R7-A3E-2A and 2B on the same real attack and parry events."""
import argparse
from contextlib import ExitStack
from ctypes import byref, c_uint32
import json
from pathlib import Path
import pickle
from statistics import median
import sys
from time import perf_counter_ns
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from actor_animation import ActorAnimation
from attack_telegraph import TelegraphRenderer
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from health_renderer import HealthRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from sprite_animation import SpriteCatalog, SpriteController
from sprite_atlas import DEFAULT_CATALOG, SpriteAtlases
from tools.stage5_art_preview import capture_png, open_preview

CASES = (('left',1,12),('down',1,12),('up',24,135),
         ('normal',25,367),('perfect',25,378),('failed',1,12))


def percentiles(values):
    values.sort()
    return [round(n,3) for n in (median(values),values[113],values[118])]


def run(output, *, benchmark_only=False):
    import sdl2 as s
    from pico2d import pico2d as c

    output.mkdir(parents=True)
    full = SpriteCatalog.read(DEFAULT_CATALOG)
    previous = SpriteController(SpriteCatalog.read(DEFAULT_CATALOG.with_name('manifest_right_only.json')))
    report = dict(driver='direct3d11', samples={}, texture_loads={}, atlas_count=0, atlas_releases=0)
    old_load = SpriteAtlases._load
    old_drop = SpriteAtlases._drop

    def load_texture(self, name):
        start = perf_counter_ns()
        texture,size = old_load(self,name)
        assert texture,name
        latency = (perf_counter_ns()-start)/1e6
        fmt = c_uint32()
        assert not s.SDL_QueryTexture(texture,byref(fmt),None,None,None)
        info = report['texture_loads'].setdefault(name.name,dict(size=size,
            bytes=size[0]*size[1]*s.SDL_BYTESPERPIXEL(fmt.value),ms=[]))
        info['ms'].append(round(latency,3))
        report['atlas_count']+=1
        return texture,size

    def drop_texture(self, name):
        old_drop(self,name)
        report['atlas_releases']+=1

    def scenario(name, stage, input_tick):
        game = _new_stage_game(stage)
        feed = game.encounter.ledger.presentation = PresentationEvents()
        animation = ActorAnimation(improved=True,enemy_attacks=True,player_actions=True,articulated=True,sprites=True)
        motion = RenderMotion(improved=True)
        vfx = CombatVFX(layered=True)
        warning = TelegraphRenderer()
        art = LiveArenaArtPath(c,motion=motion,animation=animation,vfx=vfx,telegraph=warning,
                              default_enabled=True,enlarged=True,player_combat_visual=True,sprite_catalog=full)
        sample = report['samples'][name] = dict(stage=stage, input_tick=input_tick,drawn=[])
        folder = output/'clips'/f'stage{stage}_{name}'
        if not benchmark_only:
            folder.mkdir(parents=True)

        def sync(elapsed):
            motion.update((game.player,*game.encounter.enemies),elapsed,session=game.combat.combat_session_id)
            batch = feed.drain()
            animation.update(game,elapsed,batch,motion=motion)
            vfx.update(game,elapsed,batch,motion=motion)

        def draw():
            c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
            c.SDL_RenderClear(c.renderer)
            assert art.draw(game,motion.positions)
            renderer = art.path.renderer
            assert not renderer.animation_failed and not warning.failed and not vfx.failed
            return renderer

        def placement(renderer):
            return renderer.actor_layouts[game.player.entity_instance_id]

        def compare():
            renderer = draw()
            bank = renderer.sprite_atlases
            selected = bank.controller.sample(game,game.player,'player',animation,
                                               animation.mesh_pose(game,game.player,motion)[0])
            full_hint = renderer.parry_hint
            full_warning = tuple(renderer.warning_cells)
            layout = placement(renderer)
            foot = layout['foot']
            frame = len(sample['drawn'])
            if selected:
                clip,sprite = selected
                sample['drawn'].append([game.combat.tick,clip.action,clip.facing,clip.frames.index(sprite)])
            else:
                sample['drawn'].append([game.combat.tick,None,None,None])
            assert bool(layout.get('sprite_frame')) == (selected is not None)
            x,y = foot
            region = s.SDL_Rect(max(0,min(1176,round(x-132))),max(0,min(716,round(899-y-130))),264,184)
            capture_png(c,folder/f'{frame:03}_articulated.png',region)
            chosen = bank.controller
            try:
                bank.controller = previous
                assert draw() is renderer
                assert placement(renderer)['foot']==foot
                assert renderer.parry_hint==full_hint and tuple(renderer.warning_cells)==full_warning
                capture_png(c,folder/f'{frame:03}_previous.png',region)
            finally:
                bank.controller = chosen

        def benchmark(destination, *, expect_sprite=True):
            renderer = draw()
            bank = renderer.sprite_atlases
            full_controller = bank.controller
            assert bool(placement(renderer).get('sprite_frame')) == expect_sprite
            hint = renderer.parry_hint
            expected = tuple(renderer.warning_cells)
            values = {'right_only': [], 'all_combat': []}
            actors = {'right_only': [], 'all_combat': []}
            try:
                for block in range(12):
                    order = tuple(values) if block%2==0 else tuple(reversed(values))
                    for key in order:
                        bank.controller = full_controller if key=='all_combat' else previous
                        for _ in range(12):
                            start = perf_counter_ns()
                            animation.update(game,0,(),motion=motion)
                            draw()
                            s.SDL_RenderPresent(c.renderer)
                            if block>=2:
                                values[key].append((perf_counter_ns()-start)/1e6)
                        assert renderer.parry_hint==hint and tuple(renderer.warning_cells)==expected
                for index in range(120):
                    order = tuple(values) if index%2==0 else tuple(reversed(values))
                    for key in order:
                        bank.controller = full_controller if key=='all_combat' else previous
                        start = perf_counter_ns()
                        renderer.draw_actor(game,game.player,'player',placement(renderer))
                        actors[key].append((perf_counter_ns()-start)/1e6)
                    s.SDL_RenderPresent(c.renderer)
            finally:
                bank.controller = full_controller
            destination.update(full_ms={k:percentiles(v) for k,v in values.items()},
                               player_draw_ms={k:percentiles(v) for k,v in actors.items()})
            destination['benchmark_tick'] = game.combat.tick

        with ExitStack() as cleanup:
            cleanup.callback(art.close)
            sync(0)
            if name=='down':
                assert game.player.move('up')
                sync(0)
            while game.playing and game.combat.tick<input_tick:
                if not benchmark_only and 0<input_tick-game.combat.tick<=8 and (input_tick-game.combat.tick)%2==0:
                    compare()
                game.advance()
                sync(1/60)
            assert game.combat.tick==input_tick and game.playing
            if name=='perfect':
                with patch.object(HealthRenderer,'_text',wraps=HealthRenderer._text) as text:
                    entry = draw()
                strings = {call.args[1] for call in text.call_args_list}
                assert {'ALT','NEXT INPUT','L ALT  PERFECT'} <= strings, strings
                hint = entry.parry_hint
                assert hint.status=='perfect' and hint.ring and len(entry.warning_cells)==100
                entry_sample = sample['perfect_entry'] = dict(hint=hint.status,
                    ticks_left=hint.ring.ticks_left,warning_cells=len(entry.warning_cells),
                    display=['ALT','NEXT INPUT','L ALT  PERFECT'])
                capture_png(c,output/'stage25_perfect_entry.png')
                benchmark(entry_sample,expect_sprite=False)
            attack = name in ('left','up','down')
            if attack:
                game.player.move(name,occupied=game.encounter.occupied_cells)
                event = game.combat.request_attack(game.player)
                assert event.facing==name
                game.resolver.resolve_player_attack(event)
            else:
                attempt = game.parry.request(game.combat.tick)
                assert attempt is not None
                game.resolver.register_parry(attempt)
            sync(0)
            draw()
            if name in ('normal','perfect'):
                assert art.path.renderer.parry_hint.ring is not None
            release = 385 if name in ('normal','perfect') else input_tick
            end = release + (28 if attack else 25)
            for tick in range(input_tick,end+1):
                assert game.combat.tick==tick
                if tick==release:
                    before = pickle.dumps(game)
                    if name in ('left','up','normal','perfect'):
                        benchmark(sample)
                    assert pickle.dumps(game)==before
                    if not attack:
                        actual = game.resolver.parry_result(attempt).status
                        assert actual==('unbound' if name=='failed' else name),actual
                if not benchmark_only and (tick-input_tick)%2==0:
                    compare()
                if tick!=end:
                    game.advance()
                    sync(1/60)
                    assert game.player.alive
            if not benchmark_only:
                shown = {row[1] for row in sample['drawn']}
                expected = 'attack' if attack else f'parry_{name}'
                assert expected in shown,(name,shown)
                if name in ('normal','perfect'):
                    assert 'parry_ready' in shown

    with patch.dict('os.environ',{'SDL_VIDEODRIVER':'windows','SDL_AUDIODRIVER':'dummy'}), ExitStack() as stack:
        stack.enter_context(patch.object(SpriteAtlases,'_load',load_texture))
        stack.enter_context(patch.object(SpriteAtlases,'_drop',drop_texture))
        s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
        create = c.SDL_CreateRenderer
        with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:create(w,i,s.SDL_RENDERER_ACCELERATED)):
            open_preview(c,capture=True)
        stack.callback(c.close_canvas)
        info = s.SDL_RendererInfo()
        assert c.renderer and not s.SDL_GetRendererInfo(c.renderer,info) and info.name==b'direct3d11'
        for case in CASES:
            scenario(*case)
    assert report['atlas_count']==report['atlas_releases']==3*len(CASES)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--benchmark-only',action='store_true')
    options = parser.parse_args()
    print(json.dumps(run(options.output,benchmark_only=options.benchmark_only),indent=2))
