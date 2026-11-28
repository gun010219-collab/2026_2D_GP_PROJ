"""Capture armor/stride combinations and compare matched Direct3D11 frame loads."""
import argparse
from contextlib import ExitStack, nullcontext
import ctypes as ct
import json
import os
from pathlib import Path
import sys
from time import perf_counter, sleep
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sdl2 as s
from sdl2 import sdlimage
from chapter_run import ChapterRun
from combat_vfx import MAX_EFFECTS, MAX_PARTICLES
from frame_timing import FramePacer
from input_controller import InputController
from main import _new_stage_game, run_session
import movement_vfx
from presentation_events import PresentationEvents
from stage5_art_renderer import Stage5ArtRenderer
from stage_progression import StageProgression
from sdl_input import poll_ready_events
from tests.test_hp_carryover import fight
from tools.blade_growth_qa import crop, pixels, sheet
from tools.player_armor_qa import play, tap
from tools.r7c1_review import pixel_delta
from tools.r7c2_performance import Battle, DisplaySettings, SettingsMenu, SettingsRenderer, summary, window
from tools.r7c2_soak import MemoryMonitor, Owners
from tools.r7c2_window_qa import focus
from tools.stage5_art_preview import capture_png
from upgrade_renderer import UpgradeRenderer
from upgrades import ChapterBuild


def prepare(battle, stage, hp, level, tick=0):
    stats = ChapterBuild(hp_level=hp-3, move_level=level).stats
    game = battle.game = _new_stage_game(stage, stats=stats)
    battle.queue = game.encounter.ledger.presentation = PresentationEvents()
    battle.sync(0)
    while game.combat.tick < tick:
        battle.advance()
        battle.sync(1/60)
    assert game.playing
    directions = InputController(move_interval_ticks=stats.move_interval_ticks)
    for direction in ('right', 'left', 'up', 'down'):
        moved = directions.key_down(direction, game.player, occupied=game.encounter.occupied_cells, tick=tick)
        directions.key_up(direction)
        if moved:
            break
    assert moved
    for elapsed in (0, .038):
        battle.motion.update((game.player, *game.encounter.enemies), elapsed, session=game.combat.combat_session_id,
                             player_interval=directions.move_interval_ticks)
    battle.anim.update(game, .038, (), motion=battle.motion)
    trail = battle.motion.player_trail(game.player)
    assert (trail is None) == (level == 0)


def paired_pixels(battle):
    battle.draw()
    post = pixels(battle.c)
    with patch.object(Stage5ArtRenderer, 'draw_movement'):
        battle.draw()
        baseline = pixels(battle.c)
    count, bounds = pixel_delta(post, baseline, 1440)
    battle.draw()
    if bounds:
        layout = battle.art.path.renderer.actor_layouts[battle.game.player.entity_instance_id]
        x, y = layout['foot']
        assert x-115 <= bounds[0] <= bounds[2] <= x+115
        assert 899-y-114 <= bounds[1] <= bounds[3] <= 899-y+38
    return dict(pixels=count, bounds=bounds)


def captures(battle, output):
    cells, compare = [], []
    try:
        for hp in (3, 4, 5, 6):
            for level in (0, 1, 2):
                prepare(battle, 5, hp, level)
                delta = paired_pixels(battle)
                assert bool(delta['pixels']) == bool(level)
                layout = battle.art.path.renderer.actor_layouts[battle.game.player.entity_instance_id]
                cells.append((crop(battle.c, *layout['foot']), f'HP {hp}   /   {battle.motion.player_interval} ticks'))
                compare.append(dict(hp=hp, interval=battle.motion.player_interval, **delta))
        sheet(battle.c, output/'movement.png', cells, 3)
    finally:
        for surface, _ in cells:
            s.SDL_FreeSurface(surface)
    for level in (0, 1, 2):
        run = ChapterRun(entry_build=ChapterBuild(move_level=level))
        flow = StageProgression(_new_stage_game(1, stats=run.stats), run)
        assert fight(flow)[1] == 'UPGRADE'
        battle.game = flow.game
        battle.queue = flow.enable_presentation()
        battle.sync(0)
        battle.draw()
        UpgradeRenderer().draw(battle.c, flow.game, flow.sync_offer())
        capture_png(battle.c, output/f'card-{level}.png')
    return compare


def sample(battle, monitor, *, enabled):
    times, work = [], []
    clock = FramePacer()
    switch = nullcontext() if enabled else patch.object(Stage5ArtRenderer, 'draw_movement')
    with switch:
        for frame in range(264):
            start = perf_counter()
            s.SDL_PumpEvents()
            battle.draw()
            s.SDL_RenderPresent(battle.c.renderer)
            elapsed = perf_counter() - start
            if frame >= 24:
                times.append(start)
                work.append(elapsed*1000)
            sleep(clock.remaining(elapsed, start))
    gaps = [(b-a)*1000 for a,b in zip(times,times[1:])]
    return dict(fps=round(1000*len(gaps)/sum(gaps),2), interval_ms=summary(gaps),
                work_ms=summary(work), memory_bytes=monitor.read())


def measure(battle, monitor):
    results = {}
    for stage, tick in ((24, 136), (25, 401)):
        prepare(battle, stage, 6, 2, tick=tick)
        effects = battle.effects.effects
        assert effects and len(effects)+1 <= MAX_EFFECTS and sum(f.particles for f in effects)+5 <= MAX_PARTICLES
        delta = paired_pixels(battle)
        assert delta['pixels']
        before = sample(battle, monitor, enabled=False)
        after = sample(battle, monitor, enabled=True)
        results[stage] = dict(tick=tick, combat_effects=[f.name for f in effects],
                              effects=len(effects)+1, particles=sum(f.particles for f in effects)+5,
                              before=before, after=after, **delta)
    return results


def run(output, benchmark):
    output.mkdir(parents=True, exist_ok=True)
    canvas = window(visible=benchmark)
    owners = Owners()
    monitor = MemoryMonitor() if benchmark else None
    try:
        with ExitStack() as stack:
            owners.watch(stack, canvas, 'load_image', 'texture', member='texture')
            owners.watch(stack, sdlimage, 'IMG_LoadTexture', 'texture')
            owners.watch(stack, canvas, 'SDL_CreateTextureFromSurface', 'texture')
            owners.watch(stack, canvas, 'SDL_DestroyTexture', 'texture', release=True)
            settings = SettingsRenderer(canvas, themed=True)
            battle = Battle(canvas, settings, SettingsMenu(), DisplaySettings(canvas))
            try:
                result = measure(battle, monitor) if benchmark else captures(battle, output)
            finally:
                battle.art.close()
                settings.close()
            assert owners.created == owners.freed
        name = 'performance.json' if benchmark else 'captures.json'
        report = dict(renderer='direct3d11', result=result, loads=owners.created, releases=owners.freed)
        (output/name).write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    finally:
        if monitor is not None:
            monitor.close()
        canvas.close_canvas()


def smoke(output):
    from pico2d import pico2d as canvas

    output.mkdir(parents=True, exist_ok=True)
    os.environ.update(SDL_VIDEODRIVER='windows', SDL_AUDIODRIVER='dummy')
    report = {}

    def drive(game, flow, **kwargs):
        focus(canvas.window)
        interval = flow.run.stats.move_interval_ticks
        origin = game.player.position
        observations = []
        sent = None
        original = movement_vfx.draw

        def observe(*args):
            observations.append(game.combat.tick)
            return original(*args)

        def poll(current_canvas):
            nonlocal sent
            tick = game.combat.tick
            if tick >= 4 and sent is None:
                tap(canvas, s.SDLK_RIGHT)
                sent = tick
            if tick >= 26:
                event = s.SDL_Event()
                event.type = s.SDL_QUIT
                assert s.SDL_PushEvent(ct.byref(event)) == 1
            return poll_ready_events(current_canvas)

        with patch.object(movement_vfx, 'draw', observe):
            assert run_session(game, flow, poll_events=poll, **kwargs) == 'exit'
        assert game.player.position == (origin[0]+1, origin[1])
        assert bool(observations) == (interval < 18)
        assert all(sent <= tick <= sent+8 for tick in observations), (sent, observations)
        report[interval] = dict(start_cell=origin, end_cell=game.player.position,
                                input_tick=sent, trail_ticks=observations)

    for level in range(3):
        s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER, b'direct3d11')
        play(5, move_level=level, drive=drive)
    (output/'release-smoke.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--play', choices=(18, 15, 12), type=int)
    mode.add_argument('--capture', type=Path)
    mode.add_argument('--benchmark', type=Path)
    mode.add_argument('--smoke', type=Path)
    parser.add_argument('--hp', choices=(3, 4, 5, 6), type=int, default=6)
    args = parser.parse_args()
    if args.play:
        play(args.hp, move_level=(18, 15, 12).index(args.play))
    elif args.smoke:
        smoke(args.smoke)
    else:
        run(args.capture or args.benchmark, bool(args.benchmark))
