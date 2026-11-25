
"""Compare a right-attack atlas with the mesh in real arena scenes, or generate a test atlas."""
import argparse
from contextlib import ExitStack
from ctypes import byref, c_uint32
from hashlib import sha256
import json
import os
from pathlib import Path
import pickle
from statistics import median
import struct
import sys
from time import perf_counter_ns
from unittest.mock import patch
from zlib import compress, crc32

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from actor_animation import ActorAnimation
from attack_telegraph import TelegraphRenderer
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from sprite_animation import SpriteCatalog
from sprite_atlas import SpriteAtlases
from tools.build_sprite_atlas import build
from tools.stage5_art_preview import capture_png, open_preview

LABELS = ('ready', 'draw', 'raise', 'full', 'impact', 'follow_a', 'follow_b', 'recover')
TIMINGS = (40, 40, 45, 45, 55, 60, 75, 95)


def test_fixture(destination):
    """Write eight synthetic marker frames. Independent of any player PNG."""
    source = destination / 'source'
    source.mkdir(parents=True)
    for index, name in enumerate(LABELS):
        width = 384
        pixels = bytearray(width * 4 * width)
        # A checker-coded body, shoe line, and test arm indicate pose and anchor.
        def rectangle(x, y, w, h, color):
            for row in range(y, y+h):
                start = (row * width + x) * 4
                pixels[start:start+w*4] = bytes(color)*w
        rectangle(151, 119, 82, 168, (48, 125, 172, 255))
        rectangle(142, 285, 100, 13, (17, 30, 59, 255))
        rectangle(174, 80, 37, 40, (230, 238, 255, 255))
        length = (55, 36, 26, 20, 111, 100, 85, 60)[index]
        y = (148, 140, 109, 92, 151, 173, 205, 187)[index]
        rectangle(212, y, length, 13, (238, 184, 41, 255))
        for bit in range(3):
            if index & (1 << bit):
                rectangle(164+20*bit, 207, 12, 12, (255, 240, 159, 255))

        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', crc32(tag+data))

        rows = b''.join(b'\0' + pixels[i:i+width*4] for i in range(0, len(pixels), width*4))
        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, width, 8, 6, 0, 0, 0))
               + chunk(b'IDAT', compress(rows)) + chunk(b'IEND', b''))
        (source / (name+'.png')).write_bytes(png)

    spec = dict(purpose='test', columns=4, clips=[dict(design='player', action='attack', facing='right',
                impact=4, reference_height=256, frames=[dict(file=name+'.png', ms=ms, foot=[192, 298])
                for name,ms in zip(LABELS, TIMINGS)])])
    config = source / 'player_right.json'
    config.write_text(json.dumps(spec, indent=2)+'\n', encoding='utf-8')
    return build(config, destination/'atlas')


def run(output, driver, *, manifest=None, clips=False):
    import sdl2 as s
    from pico2d import pico2d as c

    if manifest is None:
        manifest = test_fixture(output)
    else:
        output.mkdir(parents=True)
    catalog = SpriteCatalog.read(manifest, allow_test=True)
    motion = RenderMotion(improved=True)
    animation = ActorAnimation(improved=True, enemy_attacks=True, player_actions=True, articulated=True, sprites=True)
    vfx = CombatVFX(layered=True)
    warning = TelegraphRenderer()
    path = LiveArenaArtPath(c, default_enabled=True, motion=motion, animation=animation, vfx=vfx,
                           enlarged=True, telegraph=warning, player_combat_visual=True, sprite_catalog=catalog)
    timings, draw_timings, captures, sequence = {}, {}, {}, {}
    loads, released, native_formats = [], [], []
    load = SpriteAtlases._load
    drop = SpriteAtlases._drop

    def profile_load(self, atlas_path):
        start = perf_counter_ns()
        result = load(self, atlas_path)
        assert result[0]
        loads.append(round((perf_counter_ns()-start)/1e6, 3))
        pixel_format = c_uint32()
        assert not s.SDL_QueryTexture(result[0], byref(pixel_format), None, None, None)
        native_formats.append((s.SDL_GetPixelFormatName(pixel_format.value).decode(),
                               s.SDL_BYTESPERPIXEL(pixel_format.value)))
        return result

    def profile_drop(self, name):
        released.append(name)
        return drop(self, name)

    def sync(game, el=1/60):
        motion.update((game.player,*game.encounter.enemies), el, session=game.combat.combat_session_id)
        batch = game.encounter.ledger.presentation.drain()
        animation.update(game, el, batch, motion=motion)
        vfx.update(game, el, batch, motion=motion)

    def percentiles(samples):
        result = {}
        for mode, values in samples.items():
            ordered = sorted(values)
            result[mode] = [round(x, 3) for x in (median(ordered), ordered[113], ordered[118])]
        return result

    def draw(game):
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        assert path.draw(game, motion.positions)
        renderer = path.path.renderer
        assert not renderer.animation_failed and not warning.failed and not vfx.failed
        assert set(renderer.warning_cells) == {cell for event in game.resolver.live_telegraphs(game.combat.tick)
                                              for cell in event.target_cells}
        return renderer.actor_layouts[game.player.entity_instance_id]

    def capture_pair(game):
        name = f'stage{game.stage_number}_right'
        folder = output/'clips'/name
        folder.mkdir(parents=True, exist_ok=True)
        layout = draw(game)
        renderer = path.path.renderer
        atlas = renderer.sprite_atlases
        pose, _ = animation.mesh_pose(game,game.player,motion)
        sprite = atlas.controller.sample(game,game.player,'player',animation,pose)
        frame_index = sprite[0].frames.index(sprite[1]) if sprite else None
        frames = sequence.setdefault(name, [])
        frames.append(dict(tick=game.combat.tick, frame=frame_index, foot=layout['foot']))
        x,y = layout['foot']
        crop = s.SDL_Rect(max(0,min(1176,round(x-101))),max(0,min(716,round(899-y-130))),264,184)
        try:
            for suffix,bank in (('previous',None),('articulated',atlas)):
                renderer.sprite_atlases = bank
                layout = draw(game)
                assert layout['foot'] == (x,y)
                assert bool(layout.get('sprite_frame')) == (bank is not None and sprite is not None)
                capture_png(c,folder/f'{len(frames)-1:03}_{suffix}.png',crop)
        finally:
            renderer.sprite_atlases = atlas

    with patch.dict(os.environ, {'SDL_VIDEODRIVER': 'windows' if driver=='direct3d11' else 'dummy',
                                 'SDL_AUDIODRIVER': 'dummy'}), ExitStack() as stack:
        stack.enter_context(patch.object(SpriteAtlases, '_load', profile_load))
        stack.enter_context(patch.object(SpriteAtlases, '_drop', profile_drop))
        if driver == 'direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
            create = c.SDL_CreateRenderer
            with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:create(w,i,s.SDL_RENDERER_ACCELERATED)):
                open_preview(c,capture=True)
        else:
            open_preview(c,capture=True)
        info = s.SDL_RendererInfo()
        assert c.renderer and not s.SDL_GetRendererInfo(c.renderer, info) and info.name.decode() == driver
        stack.callback(c.close_canvas)
        stack.callback(path.close)
        for stage, tick in ((1,8 if clips else 0),(24,135),(25,404)):
            game = _new_stage_game(stage)
            game.encounter.ledger.presentation = PresentationEvents()
            if clips:
                sync(game)
            while game.playing and game.combat.tick < tick:
                if clips and 0 < tick-game.combat.tick <= 8 and (tick-game.combat.tick) % 2 == 0:
                    capture_pair(game)
                if stage == 25 and game.combat.tick == 367:
                    game.resolver.register_parry(game.parry.request(game.combat.tick))
                game.advance()
                sync(game)
            assert game.combat.tick == tick and game.playing, (stage, game.combat.tick, game.state)
            if stage == 25:
                assert game.resolver.last_parry_result.status == 'normal' and any(fx.name == 'king_pulse' for fx in vfx.effects)
            game.player.move('right',occupied=game.encounter.occupied_cells)
            receipt = game.combat.request_attack(game.player)
            assert receipt is not None
            game.resolver.resolve_player_attack(receipt)
            sync(game)
            before = pickle.dumps(game)
            layout = draw(game)
            assert layout['sprite_frame'] and receipt.start_tick == game.combat.tick
            swing, = (effect for effect in vfx.effects if effect.name == 'player_swing')
            assert (swing.origin, swing.cell) == (receipt.origin_cell, receipt.target_cell)
            renderer = path.path.renderer
            atlas = renderer.sprite_atlases
            samples = {mode:[] for mode in ('mesh', 'frame')}
            for mode in samples:
                renderer.sprite_atlases = atlas if mode == 'frame' else None
                layout = draw(game)
                assert bool(layout.get('sprite_frame')) == (mode=='frame')
                image = output/f'stage{stage}_{mode}.png'
                capture_png(c, image)
                captures[image.name] = sha256(image.read_bytes()).hexdigest()
            for block in range(12):
                for mode in (tuple(samples) if block % 2 == 0 else tuple(reversed(samples))):
                    renderer.sprite_atlases = atlas if mode == 'frame' else None
                    for _ in range(12):
                        start = perf_counter_ns()
                        animation.update(game, 0, (), motion=motion)
                        layout = draw(game)
                        s.SDL_RenderPresent(c.renderer)
                        if block >= 2:
                            samples[mode].append((perf_counter_ns()-start)/1e6)
            timings[stage] = percentiles(samples)
            draw_samples = {mode: [] for mode in samples}
            for index in range(120):
                for mode in (tuple(samples) if index % 2 == 0 else tuple(reversed(samples))):
                    renderer.sprite_atlases = atlas if mode == 'frame' else None
                    start = perf_counter_ns()
                    renderer.draw_actor(game, game.player, 'player', layout)
                    draw_samples[mode].append((perf_counter_ns()-start)/1e6)
                s.SDL_RenderPresent(c.renderer)
            renderer.sprite_atlases = atlas
            draw_timings[stage] = percentiles(draw_samples)
            assert pickle.dumps(game) == before
            if clips:
                capture_pair(game)
                for _ in range(14):
                    game.advance(2)
                    sync(game, 2/60)
                    assert game.player.alive
                    capture_pair(game)
                clip = catalog.clip(game.chapter,'player','attack','right','basic')
                shown = [item['frame'] for item in sequence[f'stage{stage}_right'] if item['frame'] is not None]
                assert set(shown) == set(range(clip.impact,len(clip.frames)))
        assert len(loads) == len(released)+1 == 3
    assert len(loads) == len(released)
    width,height = next(iter(catalog.atlases.values())).size
    result = dict(driver=driver, manifest=manifest.name, sequence=sequence,
                  texture_formats=native_formats, texture_pixel_bytes=width*height*native_formats[0][1],
                  texture_load_ms=loads, texture_releases=len(released),
                  p50_p95_p99_ms=timings, player_draw_cpu_p50_p95_p99_ms=draw_timings, captures=captures)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--renderer', choices=('direct3d11','software'), default='direct3d11')
    parser.add_argument('--fixture-only', action='store_true')
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--clips', action='store_true')
    args = parser.parse_args()
    if args.fixture_only:
        print(test_fixture(args.output).resolve())
    else:
        print(json.dumps(run(args.output,args.renderer,manifest=args.manifest,clips=args.clips),indent=2))
