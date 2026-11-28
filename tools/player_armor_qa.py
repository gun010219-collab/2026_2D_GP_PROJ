"""Review live armor events, measure the Windows release loop, or play with a temporary save."""
import argparse
from contextlib import nullcontext
import ctypes as ct
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sdl2 as s
from campaign_save import start_chapter
from chapter_art_renderer import LiveArenaArtPath
from main import _new_stage_game, run_session
from player_armor import PlayerArmor
from presentation_events import PresentationEvents
from release_game import ReleaseGame
from sdl_input import poll_ready_events
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from tools.blade_growth_qa import crop, position_for_contact, sheet
from tools.chapter_art_play import session
from tools.r7c2_performance import Battle, DisplaySettings, summary, window
from tools.r7c2_soak import MemoryMonitor
from tools.r7c2_window_qa import focus
from tools.stage5_art_preview import capture_png
from upgrades import ChapterBuild


def capture(output):
    """Use actual animation cues on the normal arena path at the native projection."""
    canvas = window()
    settings = SettingsRenderer(canvas, themed=True)
    battle = Battle(canvas, settings, SettingsMenu(), DisplaySettings(canvas))
    cells = []
    rows = []

    def take(tier, expected, *, sprite=False, full=False):
        battle.draw()
        game = battle.game
        renderer = battle.art.path.renderer
        layout = renderer.actor_layouts[game.player.entity_instance_id]
        assert layout['animation'] == expected and layout.get('sprite_frame', False) == sprite, layout
        assert layout.get('armor_hp', 3) == tier
        cells.append((crop(canvas, *layout['foot']), f'HP {tier}   {expected.replace("_", " ")}'))
        rows.append(dict(stage=game.stage_number, tick=game.combat.tick,
                         hp=game.player.health.current_hp, armor=tier, **layout))
        if full:
            capture_png(canvas, output / f'hp{tier}-{expected}.png')

    def begin(stage, tier, *, hp=None):
        battle.game = _new_stage_game(stage, stats=ChapterBuild(attack_level=15, hp_level=tier-3).stats,
                                      initial_hp=hp)
        battle.queue = battle.game.encounter.ledger.presentation = PresentationEvents()
        battle.sync(0)
        return battle.game

    try:
        for tier in (3, 4, 5, 6):
            game = begin(5, tier, hp=2)
            take(tier, 'idle')
            game.player.move('right')
            battle.sync(1/180)
            take(tier, 'move')
            rook = next(enemy for enemy in game.encounter.enemies if enemy.kind == 'rook')
            position_for_contact(game, rook.position)
            battle.motion.update((game.player, *game.encounter.enemies), 0,
                                 session=game.combat.combat_session_id, snap=True)
            receipt = game.resolver.resolve_player_attack(game.combat.request_attack(game.player))
            assert receipt is not None and receipt.amount > 0
            battle.sync(0)
            assert {('player_hit', 5), ('player_swing', 5)} <= {
                (effect.name, effect.blade_tier) for effect in battle.effects.effects}
            take(tier, 'attack', sprite=True, full=True)

            for delta, result in ((18, 'normal'), (7, 'perfect')):
                game = begin(25, tier)
                for _ in range(385 - delta):
                    game.advance()
                    battle.sync(1/60)
                game.resolver.register_parry(game.parry.request(game.combat.tick))
                battle.sync(0)
                if result == 'normal':
                    take(tier, 'parry_ready', sprite=True)
                for _ in range(delta):
                    game.advance()
                    battle.sync(1/60)
                assert game.resolver.last_parry_result.status == result
                take(tier, f'parry_{result}', sprite=True)

            game = begin(5, tier)
            game.resolver.register_parry(game.parry.request(game.combat.tick))
            battle.sync(0)
            take(tier, 'parry_failed', sprite=True)

            for hp, expected in ((2, 'hit'), (1, 'death')):
                game = begin(25, tier, hp=hp)
                while game.player.health.current_hp == hp:
                    assert game.combat.tick < 385
                    game.advance()
                    battle.sync(1/60)
                take(tier, expected)
        sheet(canvas, output / 'live-states.png', cells, 9)
        (output / 'live-states.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
    finally:
        for surface, _ in cells:
            s.SDL_FreeSurface(surface)
        battle.art.close()
        settings.close()
        canvas.close_canvas()


def tap(canvas, key):
    for event_type in (s.SDL_KEYDOWN, s.SDL_KEYUP):
        event = s.SDL_Event()
        event.type = event_type
        event.key.windowID = s.SDL_GetWindowID(canvas.window)
        event.key.keysym.sym = key
        assert s.SDL_PushEvent(ct.byref(event)) == 1


def benchmark_round(canvas, monitor, stage, parry_tick, swing_tick, target_kind, *, enabled):
    game, flow = session(stage)
    assert game.player.health.max_hp == 6
    snapshots = {}
    stamps, ticks, work = [], [], []
    measured = set()
    sent = set()

    def poll(current_canvas):
        assert s.SDL_GetWindowFlags(current_canvas.window) & s.SDL_WINDOW_INPUT_FOCUS
        tick = game.combat.tick
        stamps.append(perf_counter_ns())
        ticks.append(tick)
        for label, sample_tick in (('active', 45), ('impact', swing_tick + 2)):
            if tick >= sample_tick and label not in snapshots:
                snapshots[label] = monitor.read()
                measured.add(len(stamps)-1)
        if tick >= parry_tick and 'parry' not in sent:
            tap(canvas, s.SDLK_LALT)
            sent.add('parry')
        if tick >= swing_tick and 'swing' not in sent:
            target = next(e for e in game.encounter.enemies if e.kind == target_kind and e.active)
            position_for_contact(game, target.position)
            tap(canvas, s.SDLK_LCTRL)
            sent.add('swing')
        if tick >= swing_tick + 36:
            event = s.SDL_Event()
            event.type = s.SDL_QUIT
            assert s.SDL_PushEvent(ct.byref(event)) == 1
        assert game.playing and len(stamps) < 4000
        return poll_ready_events(current_canvas)

    from frame_timing import FramePacer

    original = FramePacer.remaining

    def remaining(pacer, elapsed, *args, **kwargs):
        work.append(elapsed * 1000)
        return original(pacer, elapsed, *args, **kwargs)

    snapshots['before'] = monitor.read()
    with TemporaryDirectory() as directory:
        app = ReleaseGame(canvas, Path(directory) / 'save.json', _new_stage_game)
        try:
            armor = nullcontext() if enabled else patch.object(PlayerArmor, 'select', return_value=None)
            with armor, patch.object(FramePacer, 'remaining', remaining):
                assert run_session(game, flow, default_art=True, app=app, poll_events=poll) == 'exit'
        finally:
            app.close()
    snapshots['released'] = monitor.read()
    assert game.resolver.last_parry_result.status == 'perfect'
    assert 'swing' in sent
    outcome = (game.player.health.current_hp, tuple(enemy.health.current_hp for enemy in game.encounter.enemies))

    def measure(indices):
        gaps = [(stamps[i+1] - stamps[i]) / 1e6 for i in indices]
        return dict(fps=round(1000 * len(gaps) / sum(gaps), 2),
                    interval_ms=summary(gaps), work_ms=summary([work[i] for i in indices]))

    valid = [i for i in range(len(work)) if ticks[i] >= 5 and i not in measured]
    hot = [i for i in valid if parry_tick - 4 <= ticks[i] <= swing_tick + 24]
    return dict(active=measure(valid), impact=measure(hot), cold_ms=round(work[0], 4),
                memory_bytes=snapshots, outcome=outcome)


def benchmark(output):
    from pico2d import pico2d as canvas

    os.environ.update(SDL_VIDEODRIVER='windows', SDL_AUDIODRIVER='dummy')
    s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER, b'direct3d11')
    canvas.open_canvas(1440, 900)
    monitor = None
    try:
        focus(canvas.window)
        info = s.SDL_RendererInfo()
        assert not s.SDL_GetRendererInfo(canvas.renderer, ct.byref(info)) and info.name == b'direct3d11'
        monitor = MemoryMonitor()
        report = {}
        for params in ((24, 114, 135, 'queen'), (25, 378, 389, 'king')):
            rows = [benchmark_round(canvas, monitor, *params, enabled=mode) for mode in (False, True)]
            assert rows[0]['outcome'] == rows[1]['outcome']
            report[params[0]] = dict(zip(('before', 'after'), rows))
        (output / 'paced.json').write_text(json.dumps(dict(renderer='direct3d11', stages=report), indent=2) + '\n',
                                          encoding='utf-8')
    finally:
        if monitor is not None:
            monitor.close()
        canvas.close_canvas()


def play(tier, *, move_level=0, drive=run_session):
    """Run the release loop with an isolated early-chapter checkpoint."""
    from pico2d import pico2d as canvas

    with TemporaryDirectory() as directory:
        canvas.open_canvas(1440, 900)
        app = None
        try:
            app = ReleaseGame(canvas, Path(directory) / 'save.json', _new_stage_game)
            entry = ChapterBuild(hp_level=tier-3, move_level=move_level)
            checkpoints = (ChapterBuild(), entry)
            if entry.hp_level + entry.move_level > 4:
                checkpoints = (ChapterBuild(), ChapterBuild(hp_level=3, move_level=1), entry)
            chapter = len(checkpoints)
            app.store.remember(replace(app.store.data, unlocked=tuple(range(1, chapter+1)),
                                       cleared=tuple(range(1, chapter)), entry_builds=checkpoints))
            flow = start_chapter(app.store, chapter, _new_stage_game)
            drive(flow.game, flow, default_art=True, app=app)
        finally:
            if app is not None:
                app.close()
            canvas.close_canvas()


def flicker(output):
    from tools import r7c1_review

    stats = ChapterBuild(hp_level=3).stats

    def upgraded(stage):
        return _new_stage_game(stage, stats=stats)

    with patch.object(r7c1_review, '_new_stage_game', upgraded):
        r7c1_review.run(output, enforce=True, desktop=True)


def smoke(output):
    import pico2d.pico2d as canvas

    os.environ.update(SDL_VIDEODRIVER='windows', SDL_AUDIODRIVER='dummy')
    report = {}
    original_draw = LiveArenaArtPath.draw

    def drive(game, flow, **kwargs):
        focus(canvas.window)
        info = s.SDL_RendererInfo()
        assert not s.SDL_GetRendererInfo(canvas.renderer, ct.byref(info)) and info.name == b'direct3d11'
        tier = game.player.health.max_hp
        spawn = game.player.position
        seen = set()
        sent = set()

        def poll(current_canvas):
            assert s.SDL_GetWindowFlags(current_canvas.window) & s.SDL_WINDOW_INPUT_FOCUS
            tick = game.combat.tick
            for action, due, key in (('move', 3, s.SDLK_RIGHT), ('attack', 8, s.SDLK_LCTRL)):
                if tick >= due and action not in sent:
                    tap(canvas, key)
                    sent.add(action)
            if tick >= 24:
                event = s.SDL_Event()
                event.type = s.SDL_QUIT
                assert s.SDL_PushEvent(ct.byref(event)) == 1
            return poll_ready_events(current_canvas)

        def observe(art, current, positions):
            assert original_draw(art, current, positions)
            layout = art.path.renderer.actor_layouts[current.player.entity_instance_id]
            assert layout.get('armor_hp', 3) == tier
            pose = layout['animation']
            seen.add(pose)
            if pose == 'attack':
                assert layout['sprite_frame']
            return True

        with patch.object(LiveArenaArtPath, 'draw', observe):
            assert run_session(game, flow, poll_events=poll, **kwargs) == 'exit'
        assert {'idle', 'move', 'attack'} <= seen and game.player.position != spawn
        report[tier] = dict(stage=game.stage_number, states=sorted(seen), tick=game.combat.tick,
                            start_cell=spawn, end_cell=game.player.position)

    for tier in (3, 4, 5, 6):
        s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER, b'direct3d11')
        play(tier, drive=drive)
    (output / 'release-smoke.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--capture', type=Path)
    mode.add_argument('--benchmark', type=Path)
    mode.add_argument('--flicker', type=Path)
    mode.add_argument('--smoke', type=Path)
    mode.add_argument('--play', type=int, choices=(3, 4, 5, 6), metavar='MAX_HP')
    args = parser.parse_args()
    if args.play is not None:
        play(args.play)
    for operation, output in ((capture, args.capture), (benchmark, args.benchmark),
                              (flicker, args.flicker), (smoke, args.smoke)):
        if output is not None:
            output.mkdir(parents=True, exist_ok=True)
            operation(output)
