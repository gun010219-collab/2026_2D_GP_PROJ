"""Run the royal and frozen art through real combat on hidden SDL."""
import argparse
from contextlib import ExitStack
import ctypes
import hashlib
import json
import os
from pathlib import Path
import pickle
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_art_common import CAMERA
from board import is_light_tile
from chapter_art_renderer import LiveArenaArtPath
from game import GameState, StageGame
from game_renderer import GameFlowRenderer
from input_controller import InputController
from main import _new_stage_game
from queen_behavior import queen_ray_targets
from render_motion import RenderMotion
from renderer import BoardRenderer
from tests.test_hp_carryover import fight
from tools.chapter_art_play import UPGRADES, session
from tools.stage5_art_preview import capture_png, open_preview


def mixed_warnings(game, update=lambda: None):
    controls = InputController()
    moves = {0: 'left', 18: 'left', 36: 'left', 54: 'up'}
    while game.combat.tick <= 75:
        tick = game.combat.tick
        if tick in moves:
            direction = moves[tick]
            assert controls.key_down(direction, game.player, occupied=game.encounter.occupied_cells, tick=tick)
            controls.key_up(direction)
        game.resolve_current_tick()
        update()
        if tick == 75:
            break
        game.combat.advance()
    enemies = {e.entity_instance_id: e for e in game.encounter.enemies}
    events = {enemies[e.source_entity_instance_id].kind: e for e in game.encounter.ledger.telegraphs}
    assert events.keys() == {'queen', 'rook', 'bishop'}
    assert events['queen'].target_cells == queen_ray_targets(enemies[events['queen'].source_entity_instance_id].position)
    bishop = enemies[events['bishop'].source_entity_instance_id]
    assert set(events['bishop'].target_cells) == {
        (x, y) for x in range(10) for y in range(10) if is_light_tile(x, y) == is_light_tile(*bishop.position)}
    rook = enemies[events['rook'].source_entity_instance_id]
    assert all(x == rook.position[0] for x, _ in events['rook'].target_cells)
    return events


def run(driver, output=None):
    import sdl2 as s
    from pico2d import pico2d as canvas

    counts = dict(loads=0, releases=0, peak=0, frames=0)
    captures, trips = [], {}
    textures = set()
    motion = RenderMotion()
    art = LiveArenaArtPath(canvas, motion=motion)
    hud = GameFlowRenderer()
    art_env = {f'CHECKMATE_CHAPTER{n}_ART': '1' for n in (1, 2, 3)}
    art_env.update(SDL_VIDEODRIVER='windows' if driver == 'direct3d11' else 'dummy',
                   SDL_AUDIODRIVER='dummy')
    if output is not None:
        output.mkdir(parents=True)
    with patch.dict(os.environ, art_env), ExitStack() as stack:
        for stage in range(1, 16):
            os.environ.pop(f'CHECKMATE_STAGE{stage}_ART', None)
        try:
            if driver == 'direct3d11':
                s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER, b'direct3d11')
                create = canvas.SDL_CreateRenderer
                with patch.object(canvas, 'SDL_CreateRenderer',
                                  lambda w, i, flags: create(w, i, s.SDL_RENDERER_ACCELERATED)):
                    open_preview(canvas, capture=True)
            else:
                open_preview(canvas, capture=True)
            info = s.SDL_RendererInfo()
            assert canvas.renderer and s.SDL_GetRendererInfo(canvas.renderer, ctypes.byref(info)) == 0
            assert info.name.decode() == driver
            load, destroy = canvas.load_image, canvas.SDL_DestroyTexture

            def tracked_load(name):
                sprite = load(name)
                handle = ctypes.cast(sprite.texture, ctypes.c_void_p).value
                assert handle and handle not in textures
                textures.add(handle)
                counts['loads'] += 1
                counts['peak'] = max(counts['peak'], len(textures))
                return sprite

            def tracked_destroy(texture):
                if texture:
                    textures.remove(ctypes.cast(texture, ctypes.c_void_p).value)
                    counts['releases'] += 1
                return destroy(texture)

            stack.enter_context(patch.object(canvas, 'load_image', tracked_load))
            stack.enter_context(patch.object(canvas, 'SDL_DestroyTexture', tracked_destroy))

            def draw(game, name=None, *, expected=None):
                before = pickle.dumps((game, motion))
                canvas.SDL_SetRenderDrawColor(canvas.renderer, 0, 0, 0, 255)
                canvas.SDL_RenderClear(canvas.renderer)
                applied = art.draw(game, motion.positions)
                assert applied == (game.stage_number <= 15 if expected is None else expected)
                ids = {enemy.entity_instance_id: enemy.kind for enemy in game.encounter.enemies}
                events = game.encounter.ledger.telegraphs
                if applied and game.stage_number in art.paths:
                    renderer = art.path.renderer
                    assert len(textures) == len(set(ids.values())) + 5
                    assert renderer.warning_cells == [cell for event in events for cell in event.target_cells]
                    actors = [e for e in (game.player, *game.encounter.enemies)
                              if e.alive and getattr(e, 'active', True)]
                    actors.sort(key=lambda e: (-motion.ground_pose(e)[0][1], motion.ground_pose(e)[0][0],
                                               e.entity_instance_id))
                    assert renderer.order == [e.entity_instance_id for e in actors]
                if not applied:
                    assert not textures
                    BoardRenderer(chapter=game.chapter).draw(canvas)
                hud.draw_stage_label(canvas, game)
                hud.draw(canvas, game)
                assert pickle.dumps((game, motion)) == before
                if name and output:
                    png = output / (name + '.png')
                    capture_png(canvas, png)
                    captures.append(dict(file=png.name, stage=game.stage_number, tick=game.combat.tick,
                                         state=game.state.value, hp=game.player.health.current_hp,
                                         warnings=[dict(kind=ids[e.source_entity_instance_id], hit=e.hit_tick,
                                                        cells=len(e.target_cells)) for e in events],
                                         sha256=hashlib.sha256(png.read_bytes()).hexdigest()))
                canvas.update_canvas()
                counts['frames'] += 1

            def sync(game, elapsed=1/60):
                frozen = set()
                if game.combat.active_attack or game.parry.active_at(game.combat.tick):
                    frozen.add(game.player.entity_instance_id)
                if game.encounter.pulse:
                    frozen.update(e.entity_instance_id for e in game.encounter.enemies
                                  if game.encounter.pulse.frozen(e))
                motion.update((game.player, *game.encounter.enemies), elapsed,
                              session=game.combat.combat_session_id, frozen=frozen)

            for stage in range(1, 17):
                game = session(stage)[0] if stage in (13, 15) else _new_stage_game(stage)
                sync(game, 0)
                draw(game, {1: 'royal_start', 13: 'queen_start', 15: 'ice_king_start'}.get(stage))

            for first in (1, 11):
                game, flow = session(first)
                records = []
                original = StageGame.resolve_current_tick

                def observe(current):
                    result = original(current)
                    if current is game:
                        sync(current)
                        if current.combat.tick % 12 == 0 or not current.playing:
                            draw(current)
                        if current.boss and not current.encounter.pulse.king.alive and current.playing:
                            king_fell_early.add(current.stage_number)
                    return result

                king_fell_early = set()
                with patch.object(StageGame, 'resolve_current_tick', observe):
                    for kind in UPGRADES[game.chapter]:
                        sync(game, 0)
                        draw(game)
                        result = fight(flow)
                        assert result[1] == 'UPGRADE'
                        records.append(result)
                        game, _ = flow.choose(flow.sync_offer(), kind, _new_stage_game)
                    sync(game, 0)
                    draw(game)
                    result = fight(flow)
                    assert result[1] == 'BOSS_CLEAR' and len(flow.run.receipts) == 4
                    records.append(result)
                    if first == 11:
                        assert 15 in king_fell_early
                        draw(game, 'ice_boss_clear')
                    game, _ = flow.restart(_new_stage_game)
                    assert game.playing and len(flow.run.receipts) == 4
                    sync(game, 0)
                    draw(game)
                    replay = fight(flow)
                    assert replay[1] == 'BOSS_CLEAR'
                    game, _ = flow.enter_next_chapter(_new_stage_game)
                    assert game.stage_number == first + 5 and not flow.run.receipts
                    sync(game, 0)
                    draw(game)
                trips[first] = dict(clears=records, replay=replay, next_stage=game.stage_number)

            game, _ = session(3)
            sync(game, 0)
            knight = game.encounter.enemies[0]
            for _ in range(84):
                game.advance()
                sync(game)
            sync(game, motion.duration / 2)
            draw(game, 'royal_knight_peak')
            pose = art.path.renderer.actor_layouts[knight.entity_instance_id]
            u, v, lift = art.path.renderer.pose(knight, motion.positions)
            base = art.path.renderer.layout('knight', u, v)
            assert abs(lift - 18) < 1e-8 and pose['foot'] == CAMERA.project(u + .5, v + .25)
            assert abs(pose['hp_y'] - base['hp_y'] - 18) < 1e-8

            game, _ = session(4)
            game.advance(48)
            sync(game, 0)
            assert any(len(e.target_cells) == 50 for e in game.encounter.ledger.telegraphs)
            draw(game, 'royal_bishop_warning')

            game, _ = session(14)
            sync(game, 0)
            mixed = mixed_warnings(game, lambda: sync(game))
            draw(game, 'ice_mixed_warning')
            mixed_summary = {kind: len(event.target_cells) for kind, event in mixed.items()}
            mixed_outcomes = {}
            for kind, expected in (('rook', 'hit'), ('queen', 'invulnerable'), ('bishop', 'hit')):
                event = mixed[kind]
                before = game.player.health.current_hp
                game.advance(event.hit_tick - game.combat.tick)
                outcome = game.encounter.ledger.outcome(event)
                assert outcome == expected
                assert before - game.player.health.current_hp == int(outcome == 'hit')
                mixed_outcomes[kind] = outcome

            for stage, delta in ((5, 7), (15, 18), (15, 7)):
                game, _ = session(stage)
                sync(game, 0)
                game.advance(265)
                sync(game)
                event = game.encounter.pulse.event
                assert event and len(event.target_cells) == 100 and event.hit_tick == 385
                if delta == 7:
                    draw(game, 'royal_pulse' if stage == 5 else 'ice_pulse')
                game.advance(event.hit_tick - delta - game.combat.tick)
                game.resolver.register_parry(game.parry.request(game.combat.tick))
                king = game.encounter.pulse.king
                hp = (game.player.health.current_hp, king.health.current_hp)
                game.advance(delta)
                grade = 'perfect' if delta == 7 else 'normal'
                assert game.resolver.last_parry_result.enemy_event_key == event.key
                assert game.resolver.last_parry_result.status == grade
                assert game.player.health.current_hp == hp[0] and king.health.current_hp == hp[1] - (2 if delta == 7 else 0)
                if stage == 15 and delta == 7:
                    sync(game)
                    draw(game, 'ice_perfect_reflect')

            game, flow = session(14)
            game.advance(1800)
            assert game.state is GameState.GAME_OVER
            sync(game, 0)
            draw(game)
            game, _ = flow.restart(_new_stage_game)
            assert game.stage_number == 11 and not flow.run.receipts
            sync(game, 0)
            draw(game)

            game, _ = session(15)
            sync(game, 0)
            draw(game)
            art.close()
            failed_loads = counts['loads']
            with patch.object(canvas, 'load_image') as fail:
                def damaged(name):
                    if Path(name).name == 'ch3_king.png':
                        raise OSError('intentional failed Ice King decode')
                    return tracked_load(name)
                fail.side_effect = damaged
                draw(game, expected=False)
                draw(game, expected=False)
                assert fail.call_count == 9
            assert counts['loads'] - failed_loads == 8
            art.close()
            assert not textures and counts['loads'] == counts['releases'] and counts['peak'] == 9
            report = dict(renderer=driver, resources=counts, routes=trips,
                          stage14=dict(cells=mixed_summary, outcomes=mixed_outcomes),
                          captures=captures, forced_decode_fallback=True)
            if output:
                (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            return report
        finally:
            art.close()
            if canvas.window:
                canvas.close_canvas()
                canvas.window = canvas.renderer = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', choices=('software', 'direct3d11'), default='software')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.renderer, args.output), indent=2))
