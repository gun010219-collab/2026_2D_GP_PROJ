"""Replay two actual parries, capture consecutive frames and isolate the success VFX."""
import argparse
import ctypes as ct
import json
import os
from pathlib import Path
import sys
from time import perf_counter_ns
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from actor_animation import ActorAnimation
from attack_telegraph import TelegraphRenderer
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from display_settings import DisplaySettings, logical_mouse_to_canvas
from game_renderer import GameFlowRenderer
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from sprite_atlas import opted_in_catalog
from tools.stage5_art_preview import capture_png, open_preview
from upgrade_renderer import CARD_RECTS, card_at
from arena_art_common import CAMERA


def release_loop(c, s, display, settings):
    """Exercise SDL left-Alt through the release loop across three separate attacks."""
    import main
    from tools.chapter_art_play import session

    game, flow = session(24)
    app = SimpleNamespace(display=display,menu=SettingsMenu(),settings_renderer=settings,
                          audio=None,store=SimpleNamespace(notice=''))
    sent, outcomes = set(), {}
    clock = 0.
    frames = clears = 0
    previous = None
    clear, present = c.SDL_RenderClear, c.update_canvas
    flags = c.SDL_GetWindowFlags
    x,y = ct.c_int(),ct.c_int()
    s.SDL_RenderLogicalToWindow(c.renderer,0,0,ct.byref(x),ct.byref(y))
    region = s.SDL_Rect(x.value,y.value,8,100)
    sample = (ct.c_ubyte * 3200)()

    def now():
        nonlocal clock
        clock += 1/360
        return clock

    def poll():
        tick = game.combat.tick
        assert frames < 1500 and game.playing
        if len(outcomes)>=3 and tick>max(outcomes)+31:
            return [SimpleNamespace(type=c.SDL_KEYDOWN,key=c.SDLK_ESCAPE)]
        for attack in game.encounter.ledger.telegraphs:
            if (attack.key not in sent and game.player.position in attack.target_cells
                    and attack.hit_tick-tick==7):
                sent.add(attack.key)
                return [SimpleNamespace(type=kind,key=c.SDLK_LALT)
                        for kind in (c.SDL_KEYDOWN,c.SDL_KEYUP)]
        return []

    def clear_once(renderer):
        nonlocal clears
        clears += 1
        return clear(renderer)

    def check_present():
        nonlocal previous,frames
        frames += 1
        assert clears==frames
        assert not s.SDL_RenderReadPixels(c.renderer,ct.byref(region),s.SDL_PIXELFORMAT_RGBA32,sample,32)
        pixels = bytes(sample)
        assert previous is None or pixels==previous, (
            frames,game.combat.tick,game.state.value,game.resolver.last_parry_result,
            pixel_delta(pixels,previous,8))
        previous = pixels
        result = game.resolver.last_parry_result
        if result and result.status=='perfect':
            outcomes[result.tick] = result.parry_id
        present()

    with patch.object(c,'get_events',poll),patch.object(main,'perf_counter',now), \
         patch.object(main,'sleep',lambda _:None),patch.object(c,'update_canvas',check_present), \
         patch.object(c,'SDL_RenderClear',clear_once), \
         patch.object(c,'SDL_GetWindowFlags',lambda w:flags(w)|s.SDL_WINDOW_INPUT_FOCUS):
        assert main.run_session(game,flow,default_art=True,app=app)=='main'
    return dict(perfect_ticks=list(outcomes),clears=clears,presents=frames,corner_changes=0)


def pixel_delta(a, b, width):
    """Count changed RGBA pixels and bound them in native framebuffer coordinates."""
    stride = 4 * width
    lane = int.from_bytes(b'\x01\0\0\0' * width, 'little')
    left, right, top, bottom, count = width, -1, None, None, 0
    for offset in range(0, len(a), stride):
        row = int.from_bytes(a[offset:offset+stride], 'little') ^ int.from_bytes(b[offset:offset+stride], 'little')
        if not row:
            continue
        for shift in (16, 8, 4, 2, 1):
            row |= row >> shift
        pixels = row & lane
        left = min(left, ((pixels & -pixels).bit_length()-1)//32)
        right = max(right, (pixels.bit_length()-1)//32)
        y = offset//stride
        top = y if top is None else top
        bottom = y
        count += pixels.bit_count()
    return count, ([left, top, right, bottom] if count else None)


def run(output, *, enforce=False, desktop=False):
    os.environ.update(SDL_VIDEODRIVER='windows', SDL_AUDIODRIVER='dummy')
    import sdl2 as s
    from pico2d import pico2d as c

    output.mkdir(parents=True, exist_ok=True)
    s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER, b'direct3d11')
    make = c.SDL_CreateRenderer
    with patch.object(c, 'SDL_CreateRenderer', lambda w,i,f: make(w,i,s.SDL_RENDERER_ACCELERATED)):
        open_preview(c, capture=not desktop)
    display = DisplaySettings(c)
    settings = SettingsRenderer(c, themed=True)
    menu = SettingsMenu()
    hud = GameFlowRenderer(official=True)
    report = {}
    try:
        info = s.SDL_RendererInfo()
        assert s.SDL_GetRendererInfo(c.renderer, ct.byref(info)) == 0 and info.name == b'direct3d11'
        for mode in ('window', 'fullscreen'):
            if mode == 'fullscreen':
                assert display.toggle() and display.fullscreen
            s.SDL_PumpEvents()
            w, h = ct.c_int(), ct.c_int()
            assert not s.SDL_GetRendererOutputSize(c.renderer, ct.byref(w), ct.byref(h))
            width, height = w.value, h.value
            raw = (ct.c_ubyte * (width*height*4))()
            screen = s.SDL_Rect(0,0,width,height)

            def read():
                # NULL packs the active viewport at (0,0), omitting letterbox offsets.
                assert not s.SDL_RenderReadPixels(c.renderer, ct.byref(screen), s.SDL_PIXELFORMAT_RGBA32, raw, width*4)
                return bytes(raw)

            def window_point(x,y):
                px, py = ct.c_int(), ct.c_int()
                s.SDL_RenderLogicalToWindow(c.renderer, x, y, ct.byref(px), ct.byref(py))
                return px.value, py.value

            origin_x,origin_y = window_point(0,0)
            edge_start = 4*(origin_y*width+origin_x)

            for i, rect in enumerate(CARD_RECTS):
                x,y = window_point(rect.left+rect.width/2, 899-rect.bottom-rect.height/2)
                lx,ly = ct.c_float(),ct.c_float()
                s.SDL_RenderWindowToLogical(c.renderer,x,y,ct.byref(lx),ct.byref(ly))
                assert card_at(logical_mouse_to_canvas(lx.value,ly.value)) == i

            for number, impact in ((24,121),(25,385)):
                game = _new_stage_game(number)
                queue = game.encounter.ledger.presentation = PresentationEvents()
                motion = RenderMotion(improved=True)
                catalog = opted_in_catalog()
                anim = ActorAnimation(improved=True, enemy_attacks=True, player_actions=True,
                                      articulated=True, sprites=catalog is not None)
                effects = CombatVFX(layered=True)
                art = LiveArenaArtPath(c, motion=motion, animation=anim, vfx=effects,
                                       default_enabled=True, enlarged=True, telegraph=TelegraphRenderer(),
                                       player_combat_visual=True, sprite_catalog=catalog)

                def draw():
                    c.SDL_SetRenderDrawColor(c.renderer, 0,0,0,255)
                    c.SDL_RenderClear(c.renderer)
                    assert art.draw(game, motion.positions)
                    hud.draw_stage_label(c, game)
                    settings.draw(menu, display)

                records, previous = [], None
                try:
                    for tick in range(impact+(32 if enforce else 21)):
                        if tick:
                            game.advance()
                        if tick == impact-7:
                            binding = game.resolver.register_parry(game.parry.request(tick))
                            assert binding.adjudication_grade == 'perfect'
                        batch = queue.drain()
                        dt = 1/60 if tick else 0
                        frozen = {game.player.entity_instance_id} if game.parry.active_at(tick) else set()
                        if game.encounter.pulse:
                            frozen.update(e.entity_instance_id for e in game.encounter.enemies
                                          if game.encounter.pulse.frozen(e))
                        motion.update((game.player,*game.encounter.enemies),dt,
                                      session=game.combat.combat_session_id,frozen=frozen)
                        anim.update(game,dt,batch,motion=motion)
                        effects.update(game,dt,batch,motion=motion)
                        if tick < impact-2:
                            continue
                        draw()
                        frame = read()
                        # Diagonal Queen fire can reach the lower part of the left edge.
                        edge = b''.join(frame[j:j+32] for j in range(edge_start,len(frame),width*4))
                        changes = pixel_delta(edge,previous,8)[0] if previous else 0
                        corner_changes = pixel_delta(edge[:3200],previous[:3200],8)[0] if previous else 0
                        previous = edge
                        parries = [f for f in effects.effects if f.name=='parry_perfect']
                        assert len(parries) <= 1
                        if tick == impact:
                            assert len(parries)==1 and game.resolver.last_parry_result.status=='perfect'
                        if not desktop and mode=='window' and tick-impact in (-1,0,1,2,3,4,5,6,7):
                            assert (width,height)==(1440,900)
                            capture_png(c,output/f's{number}_{tick-impact:+03}.png')
                        c.update_canvas()
                        changed, bounds = 0,None
                        if parries:
                            with patch.object(effects,'effects',[f for f in effects.effects if f not in parries]):
                                draw()
                                changed,bounds = pixel_delta(frame,read(),width)
                            if enforce and bounds:
                                x,y = CAMERA.center(*game.player.position)
                                x1,y1 = window_point(x-95,899-y-115)
                                x2,y2 = window_point(x+95,899-y+90)
                                assert x1<=bounds[0]<=bounds[2]<=x2 and y1<=bounds[1]<=bounds[3]<=y2, (
                                    mode,width,height,display._bounds(),window_point(0,0),bounds,(x1,y1,x2,y2))
                        if enforce:
                            assert corner_changes==0,(mode,number,tick,corner_changes)
                        records.append(dict(tick=tick,edge_pixels=changes,corner_pixels=corner_changes,
                                            vfx_pixels=changed,bounds=bounds))
                        if tick == (135 if number == 24 else impact+4):
                            samples = []
                            for i in range(110):
                                start = perf_counter_ns()
                                draw()
                                c.update_canvas()
                                if i>=20:
                                    samples.append((perf_counter_ns()-start)/1e6)
                            samples.sort()
                            timing = dict(p50_ms=round(samples[44],3),p95_ms=round(samples[85],3))
                    if enforce:
                        assert not parries
                    report[f'{mode}_{number}'] = dict(output=[width,height],timing=timing,frames=records)
                finally:
                    art.close()
            if enforce:
                report[mode+'_release_loop'] = release_loop(c,s,display,settings)
        assert display.toggle() and not display.fullscreen
        (output/'frames.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    finally:
        settings.close()
        c.close_canvas()


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--enforce',action='store_true')
    parser.add_argument('--desktop',action='store_true',help='Use a visible Windows desktop window')
    args = parser.parse_args()
    run(args.output,enforce=args.enforce,desktop=args.desktop)
