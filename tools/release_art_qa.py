"""Hidden SDL validation of the release default, real campaign, and facade seam."""
import argparse
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

from arena_art_profile import ProfileArtRenderer
from chapter_art_renderer import CHAPTER_PROFILES, LiveArenaArtPath
from bishop_behavior import color_targets
from game import GameState, StageGame
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from late_chapter_art import BAY_LEFT, BAY_RIGHT, DECK_EDGE, FacadeArtRenderer
from render_motion import RenderMotion
from queen_behavior import queen_ray_targets
from stage5_art_renderer import Stage5ArtRenderer
from tests.test_hp_carryover import fight
from tools.chapter_art_play import advance_campaign, session
from tools.stage5_art_preview import capture_png, open_preview


def run(driver='software', output=None):
    import sdl2 as s
    from pico2d import pico2d as c
    from main import _new_stage_game

    env = {k:v for k,v in os.environ.items() if not (k.startswith('CHECKMATE_') and k.endswith('_ART'))}
    env.update(SDL_VIDEODRIVER='windows' if driver == 'direct3d11' else 'dummy', SDL_AUDIODRIVER='dummy')
    motion = RenderMotion()
    art = LiveArenaArtPath(c, motion=motion, default_enabled=True)
    counts = dict(loads=0, releases=0, peak=0, frames=0)
    live, captures, clears, observations = set(), [], [], {}
    if output:
        output.mkdir(parents=True)

    with patch.dict(os.environ, env, clear=True):
        if driver == 'direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER, b'direct3d11')
            create = c.SDL_CreateRenderer
            with patch.object(c, 'SDL_CreateRenderer', lambda w,i,f: create(w,i,s.SDL_RENDERER_ACCELERATED)):
                open_preview(c, capture=True)
        else:
            open_preview(c, capture=True)
        info = s.SDL_RendererInfo()
        assert c.renderer and s.SDL_GetRendererInfo(c.renderer, ctypes.byref(info)) == 0
        assert info.name.decode() == driver
        load, destroy = c.load_image, c.SDL_DestroyTexture

        def acquire(name):
            image = load(name)
            key = ctypes.cast(image.texture, ctypes.c_void_p).value
            assert key and key not in live
            live.add(key)
            counts['loads'] += 1
            counts['peak'] = max(counts['peak'], len(live))
            return image

        def release(texture):
            if texture:
                live.remove(ctypes.cast(texture, ctypes.c_void_p).value)
                counts['releases'] += 1
            return destroy(texture)

        def sync(game, dt=1/60):
            frozen = {game.player.entity_instance_id} if game.combat.active_attack or game.parry.active_at(game.combat.tick) else set()
            if game.encounter.pulse:
                frozen.update(e.entity_instance_id for e in game.encounter.enemies if game.encounter.pulse.frozen(e))
            motion.update((game.player, *game.encounter.enemies), dt, session=game.combat.combat_session_id, frozen=frozen)

        def save(name):
            if name and output:
                png = output / (name + '.png')
                capture_png(c, png)
                captures.append(dict(file=png.name, sha256=hashlib.sha256(png.read_bytes()).hexdigest()))

        def draw(game, name=None):
            before = pickle.dumps((game, motion))
            c.SDL_SetRenderDrawColor(c.renderer, 0, 0, 0, 255)
            c.SDL_RenderClear(c.renderer)
            assert art.draw(game, motion.positions), game.stage_number
            active = art.path.renderer
            kinds = {e.kind for e in game.encounter.enemies}
            assert active.files == CHAPTER_PROFILES[game.chapter].files_for(kinds), game.stage_number
            armor_mesh = art.player_armor.appearance is not None
            assert len(live) == len(active.files) + armor_mesh
            expected = [cell for attack in game.encounter.ledger.telegraphs for cell in attack.target_cells] if game.playing else []
            assert active.warning_cells == expected
            if game.chapter >= 4:
                actors = [e for e in (game.player, *game.encounter.enemies)
                          if e.alive and getattr(e, 'active', True)]
                actors.sort(key=lambda e: (-motion.ground_pose(e)[0][1], motion.ground_pose(e)[0][0],
                                           e.entity_instance_id))
                assert active.order == [e.entity_instance_id for e in actors]
            hud = GameFlowRenderer()
            hud.draw_stage_label(c, game)
            hud.draw(c, game)
            assert before == pickle.dumps((game, motion))
            save(name)
            counts['frames'] += 1

        def pixels(x, y, width, height):
            rect = s.SDL_Rect(x, y, width, height)
            result = (ctypes.c_ubyte * (width * height * 4))()
            assert s.SDL_RenderReadPixels(c.renderer, ctypes.byref(rect), s.SDL_PIXELFORMAT_RGBA32, result, width*4) == 0
            return bytes(result)

        try:
            with patch.object(c, 'load_image', acquire), patch.object(c, 'SDL_DestroyTexture', release):
                try:
                    for stage in range(1, 26):
                        game = _new_stage_game(stage)
                        sync(game, 0)
                        draw(game)
                        if stage in (16, 21):
                            # Compare the same live state, with only the frame pass switched.
                            with patch.object(FacadeArtRenderer, 'draw_frame', Stage5ArtRenderer.draw_frame):
                                draw(game, f'stage{stage}_facade_before')
                                above = pixels(0, 0, 1440, int(899-DECK_EDGE))
                                joint = pixels(BAY_LEFT, 766, BAY_RIGHT-BAY_LEFT, 100)
                            draw(game, f'stage{stage}_facade_after')
                            assert above == pixels(0, 0, 1440, int(899-DECK_EDGE))
                            assert joint != pixels(BAY_LEFT, 766, BAY_RIGHT-BAY_LEFT, 100)
                    art.close()
                    if output:
                        for chapter in (4, 5):
                            profile = CHAPTER_PROFILES[chapter]
                            sheet = ProfileArtRenderer(c, profile=profile)
                            try:
                                c.SDL_SetRenderDrawColor(c.renderer, 40, 42, 47, 255)
                                c.SDL_RenderClear(c.renderer)
                                for i, kind in enumerate(('pawn','rook','knight','bishop','queen','king')):
                                    x = 170 + 220 * i
                                    slot = profile.layout(kind, 5, 0)
                                    size = slot['height'] * 1.6
                                    sheet.image(kind, x, 480, size, size)
                                    HealthRenderer._text(c, kind.upper(), x-36, 320)
                                save(f'chapter{chapter}_roster')
                            finally:
                                sheet.close()

                    game, flow = session(1)
                    event_feed = flow.enable_presentation()
                    original = StageGame.resolve_current_tick

                    def observe(current):
                        result = original(current)
                        sync(current)
                        events = current.encounter.ledger.telegraphs
                        actors = {e.entity_instance_id:e for e in current.encounter.enemies}
                        active = {key:e.kind for key,e in actors.items()}
                        kinds = {active[e.source_entity_instance_id] for e in events}
                        stage = current.stage_number
                        state = observations.setdefault(stage, dict(kinds=set(), reflect=0, paired_queens=False,
                                                                    king_attacks=set(), pulse_keys=set()))
                        state['kinds'].update(kinds)
                        queens = [e for e in events if active[e.source_entity_instance_id] == 'queen']
                        for e in queens:
                            assert e.target_cells == queen_ray_targets(actors[e.source_entity_instance_id].position)
                        bishops = [e for e in events if active[e.source_entity_instance_id] == 'bishop']
                        assert len({sum(actors[e.source_entity_instance_id].position) % 2 for e in bishops}) <= 1
                        for e in bishops:
                            assert e.target_cells == color_targets(actors[e.source_entity_instance_id].position)
                        paired = len({e.source_entity_instance_id for e in queens}) > 1
                        pulse = [e for e in events if e.attack_kind == 'king_pulse']
                        state['pulse_keys'].update(e.key for e in pulse)
                        state['king_attacks'].update(e.attack_kind for e in events
                                                     if active[e.source_entity_instance_id] == 'king')
                        reflected = [e for e in event_feed.drain() if e.kind == 'hurt'
                                     and e.payload.source_entity_instance_id == current.player.entity_instance_id
                                     and e.payload.amount == 2 and e.payload.attack_key in state['pulse_keys']]
                        state['reflect'] += len(reflected)
                        if stage == 16:
                            lift = max(motion.ground_pose(e)[1] for e in current.encounter.enemies if e.kind == 'knight')
                            if lift > 17.9 and not state.get('knight_peak'):
                                draw(current, 'stage16_knight_peak')
                                state['knight_peak'] = round(lift, 3)
                        if stage == 24 and paired and not state['paired_queens']:
                            draw(current, 'stage24_two_queens')
                        state['paired_queens'] |= paired
                        if stage in (20, 25) and pulse and not state.get('pulse'):
                            draw(current, f'stage{stage}_pulse')
                            state['pulse'] = True
                        if current.combat.tick % 72 == 0 or not current.playing:
                            draw(current)
                        return result

                    with patch.object(StageGame, 'resolve_current_tick', observe):
                        for stage in range(1, 26):
                            assert game.stage_number == stage
                            sync(game, 0)
                            draw(game)
                            result = fight(flow)
                            clears.append(result)
                            assert result[1] == ('BOSS_CLEAR' if game.boss else 'UPGRADE')
                            if stage < 25:
                                advance_campaign(flow, result)
                                game = flow.game
                        draw(game, 'stage25_boss_clear')
                    assert len(clears) == 25 and game.state is GameState.BOSS_CLEAR
                    assert observations[16].get('knight_peak')
                    assert observations[24]['paired_queens']
                    for stage in (20, 25):
                        assert observations[stage]['king_attacks'] == {'basic', 'king_pulse'}
                    assert observations[25]['reflect']
                    replay, _ = flow.restart(_new_stage_game)
                    sync(replay, 0)
                    draw(replay)
                    assert replay.stage_number == 25 and len(flow.run.receipts) == 4
                    replay.advance(1800)
                    assert replay.state is GameState.GAME_OVER
                    restarted, _ = flow.restart(_new_stage_game)
                    sync(restarted, 0)
                    draw(restarted)
                    assert restarted.stage_number == 21 and not flow.run.receipts
                    for boss_stage in (20, 25):
                        for delta, grade in ((18, 'normal'), (7, 'perfect')):
                            boss = _new_stage_game(boss_stage)
                            boss.advance(265)
                            pulse = boss.encounter.pulse.event
                            assert pulse and len(pulse.target_cells) == 100
                            boss.advance(pulse.hit_tick - boss.combat.tick - delta)
                            boss.resolver.register_parry(boss.parry.request(boss.combat.tick))
                            player_hp = boss.player.health.current_hp
                            king = boss.encounter.pulse.king
                            initial = king.health.current_hp
                            boss.advance(delta)
                            result = boss.resolver.last_parry_result
                            assert result.enemy_event_key == pulse.key and result.status == grade
                            assert boss.player.health.current_hp == player_hp
                            assert king.health.current_hp == initial - (2 if grade == 'perfect' else 0)
                            sync(boss, 0)
                            draw(boss, f'stage{boss_stage}_reflect' if grade == 'perfect' else None)
                        observations[boss_stage]['isolated_pulse_grades'] = ['normal', 'perfect']
                    art.close()
                    game = _new_stage_game(25)
                    with patch.object(c, 'load_image', side_effect=lambda name: (
                        acquire(name) if not name.endswith('ch5_king.png') else _missing(name))) as loader:
                        assert not art.draw(game, {}) and not art.draw(game, {})
                        assert not live and loader.call_count == 7
                    assert counts['loads'] == counts['releases']
                finally:
                    art.close()
        finally:
            c.close_canvas()
            c.window = c.renderer = None
    for state in observations.values():
        state['kinds'] = sorted(state['kinds'])
        state['king_attacks'] = sorted(state['king_attacks'])
        state.pop('pulse_keys')
    report = dict(driver=driver, resources=counts, campaign=clears, attacks=observations, captures=captures)
    if output:
        (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    return report


def _missing(name):
    raise FileNotFoundError(name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', choices=('software', 'direct3d11'), default='software')
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    print(json.dumps(run(options.renderer, options.output), indent=2))
