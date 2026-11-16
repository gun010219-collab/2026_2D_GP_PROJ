"""Separate Chapter2 QA runner. Reuses the unchanged battle driver and live APIs."""
import argparse
from contextlib import nullcontext
import ctypes
import json
import os
from pathlib import Path
import pickle
import sys
from unittest import TestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import main
from combat_balance import profile_for
from game import StageGame
from render_motion import RenderMotion
from stage_manager import StageCatalog
from tests.balance_driver import STYLES
from tests.test_hp_carryover import fight
from tools.campaign_qa import trace_damage
from tools.stage6_play import session


def roster(g):
    d = StageCatalog.load().get_stage(g.stage_number)
    assert [(e.data_id, e.kind, e.position) for e in g.encounter.enemies] == [(e.data_id, e.kind, (e.col, e.row)) for e in d.enemies]
    assert [e.health.max_hp for e in g.encounter.enemies] == [profile_for(d.chapter).hp(e.kind) for e in d.enemies]
    return [dict(id=e.data_id, kind=e.kind, cell=e.position, hp=e.health.max_hp) for e in g.encounter.enemies]


def campaign(style, audit=None):
    g, flow = session()  # Real fresh Stage6, Receipt0; no synthetic prior-stage offers.
    assert not flow.run.receipts and flow.run.current_stage == 6
    seen = set(); rows = []; upgrades = []; owner = flow.run

    def fresh(new, old=None):
        ids = (new.combat.combat_session_id, new.combat.stage_instance_id)
        assert all(i not in seen for i in ids); seen.update(ids)
        if old is not None:
            for attr in ('player', 'health', 'combat', 'parry', 'encounter', 'resolver'):
                if attr == 'health': assert new.player.health is not old.player.health
                else: assert getattr(new, attr) is not getattr(old, attr)
            assert new.encounter.ledger is not old.encounter.ledger
        if audit: audit.draw(new)

    fresh(g)
    with trace_damage() as traces:
        for index in range(5):
            g = flow.game; original = roster(g); start_hp = g.player.health.current_hp
            stats = flow.run.stats
            result = fight(flow)  # Original 3600-tick BFS/movement/attack/parry policy.
            rows.append(dict(stage=g.stage_number, roster=original, start_hp=start_hp,
                             attack=stats.attack_damage, max_hp=stats.max_hp, move_ticks=stats.move_interval_ticks,
                             receipts=len(flow.run.receipts), result=result[1], ticks=result[2], remaining_hp=result[3],
                             damage_trace=traces.get(g.combat.stage_instance_id, [])))
            for receipt in flow.run.receipts: flow.run.verify_receipt(receipt)
            if not g.player.alive or g.playing: break  # Preserve death/timeout; never skip onward.
            assert g.resolver.stopped and not g.encounter.ledger.pending
            if g.boss: break
            offer = flow.sync_offer(); assert flow.sync_offer() is offer
            kind = STYLES[style][index]; old = g
            g, _ = flow.choose(offer, kind, main._new_stage_game)
            assert flow.run is owner and g.player.health.current_hp == result[3]+int(kind == 'hp')
            assert len(flow.run.receipts) == index+1 and flow.run.active_offer is None
            try: flow.choose(offer, kind, main._new_stage_game)
            except ValueError: pass
            else: raise AssertionError('Duplicate offer accepted')
            upgrades.append(dict(after_stage=old.stage_number, kind=kind, next_hp=g.player.health.current_hp,
                                 next_attack=flow.run.stats.attack_damage, receipts=len(flow.run.receipts)))
            fresh(g, old)
    terminal = flow.game
    completed = terminal.stage_number == 10 and terminal.state.value == 'BOSS_CLEAR'
    post = {}
    if completed:
        assert len(owner.receipts) == 4 and flow.sync_offer() is None
        old = terminal; g, _ = flow.restart(main._new_stage_game)
        assert flow.run is owner and len(owner.receipts) == 4
        assert g.player.health.current_hp == owner.stats.max_hp and g.encounter.pulse.king.health.current_hp == 50
        assert g.encounter.pulse is not old.encounter.pulse; fresh(g, old)
        replay = fight(flow)  # Separate real replay, not substituted for original campaign results.
        post['boss_replay'] = list(replay)
        if g.state.value == 'BOSS_CLEAR':
            old = g; g, _ = flow.enter_next_chapter(main._new_stage_game)
            assert owner.retired and flow.run is not owner
            assert (g.stage_number, flow.run.chapter, len(flow.run.receipts), g.player.health.current_hp, flow.run.stats.move_interval_ticks) == (11, 3, 0, 3, 18)
            assert flow.run.entry_attack_level == owner.build.attack_level
            fresh(g, old)
            post['chapter3'] = dict(stage=11, hp=3, receipts=0, attack=flow.run.stats.attack_damage, legacy_display=True)
    elif terminal.state.value == 'GAME_OVER':
        g, _ = flow.restart(main._new_stage_game); fresh(g, terminal)
        assert g.stage_number == 6 and not flow.run.receipts and g.player.health.current_hp == 3
        post['restart_only_not_continued'] = 6
    if audit: audit.release()
    flow.run.retire()
    return dict(style=style, scope='fresh_Chapter2_Stage6_Receipt0_entry_attack_level1',
                completed_to_boss_clear=completed, rows=rows, upgrades=upgrades, post_checks=post,
                unique_sessions=len(seen)//2)


class NativeAudit:
    """Hidden renderer/lifetime instrumentation; no real-time FPS or RAM claim."""
    def __init__(self, driver):
        self.driver = driver; self.live = set(); self.loads = self.destroys = self.peak = self.frames = 0
        self.max_lift = 0; self.warning_kinds = set(); self.last = None; self.patches = []

    def __enter__(self):
        from pico2d import pico2d as c
        import sdl2 as s
        from tools.stage5_art_preview import open_preview
        from stage10_art_renderer import LiveArenaArtPath
        self.c = c; self.s = s
        if self.driver == 'direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER, b'direct3d11'); create = c.SDL_CreateRenderer
            with patch.object(c, 'SDL_CreateRenderer', lambda w, i, flags: create(w, i, s.SDL_RENDERER_ACCELERATED)):
                open_preview(c, capture=True)
        else: open_preview(c, capture=True)
        info = s.SDL_RendererInfo(); assert s.SDL_GetRendererInfo(c.renderer, info) == 0
        self.renderer = info.name.decode(); assert self.renderer == self.driver
        self.vsync = bool(info.flags & s.SDL_RENDERER_PRESENTVSYNC)
        load, destroy = c.load_image, c.SDL_DestroyTexture
        def loading(path):
            image = load(path); key = ctypes.cast(image.texture, ctypes.c_void_p).value
            assert key not in self.live; self.live.add(key); self.loads += 1; self.peak = max(self.peak, len(self.live))
            return image
        def destroying(texture):
            key = ctypes.cast(texture, ctypes.c_void_p).value
            # Pico2D Image.__del__ calls SDL_DestroyTexture(None) after an explicit close.
            # This is a native no-op, not another owned texture destruction.
            if key is None: return destroy(texture)
            assert key in self.live; self.live.remove(key); self.destroys += 1; return destroy(texture)
        self.patches = [patch.object(c, 'load_image', loading), patch.object(c, 'SDL_DestroyTexture', destroying)]
        for p in self.patches: p.start()
        self.motion = RenderMotion(); self.path = LiveArenaArtPath(c, motion=self.motion)
        native = StageGame.resolve_current_tick
        def resolve(g):
            result = native(g)
            if g.chapter == 2: self.draw(g)
            return result
        self.observer = patch.object(StageGame, 'resolve_current_tick', resolve); self.observer.start()
        return self

    def paths(self):
        p = self.path; result = []
        while p is not None:
            result.extend(getattr(p, 'stage'+str(n)) for n in range(5, 11) if hasattr(p, 'stage'+str(n)))
            p = getattr(p, 'previous', None)
        return result

    def draw(self, g):
        key = (g.combat.combat_session_id, g.combat.tick)
        frozen = {e.entity_instance_id for e in g.encounter.enemies if g.encounter.pulse and g.encounter.pulse.frozen(e)}
        if g.combat.active_attack or g.parry.active_at(g.combat.tick): frozen.add(g.player.entity_instance_id)
        self.motion.update((g.player, *g.encounter.enemies), 0 if key == self.last else 1/60,
                           session=g.combat.combat_session_id, frozen=frozen)
        self.last = key; before = pickle.dumps((g, self.motion)); active = self.path.draw(g, self.motion.positions)
        assert pickle.dumps((g, self.motion)) == before
        residents = [p for p in self.paths() if p.renderer is not None]
        assert active == (6 <= g.stage_number <= 10)
        assert len(residents) == int(active)
        if active:
            r = residents[0].renderer; expected = [tuple(c) for e in g.encounter.ledger.telegraphs for c in e.target_cells] if g.playing else []
            assert r.warning_cells == expected
            assert len(self.live) == {6: 7, 7: 7, 8: 9, 9: 9, 10: 9}[g.stage_number]
            for e in g.encounter.enemies:
                if not e.active or not e.alive: assert e.entity_instance_id not in r.order
            self.max_lift = max(self.max_lift, *[v.get('elevation', 0) for v in r.actor_layouts.values()], 0)
            for event in g.encounter.ledger.telegraphs:
                self.warning_kinds.add('pulse' if event.attack_kind == 'king_pulse' else next(e.kind for e in g.encounter.enemies if e.entity_instance_id == event.source_entity_instance_id))
        else: assert not self.live
        self.frames += 1

    def release(self):
        self.path.close(); assert not self.live

    def faults(self):
        from arena_art_common import ArenaArtError
        from stage6_art_renderer import Stage6ArtPath, Stage6ArtRenderer
        self.release(); g, flow = session(); before = pickle.dumps(g); checks = []
        for error in (FileNotFoundError('expected missing asset QA fixture'), ArenaArtError('expected SDL QA fixture')):
            renderer = None
            if isinstance(error, ArenaArtError): renderer = Stage6ArtRenderer(self.c)
            def factory(c):
                if renderer is None: raise error
                return renderer
            path = Stage6ArtPath(self.c, factory)
            cm = patch.object(renderer, 'draw', side_effect=error) if renderer else nullcontext()
            with cm, TestCase().assertLogs('stage6_art_renderer', level='ERROR') as logs:
                assert not path.draw(g, {})
            assert len(logs.records) == 1 and path.failed
            assert not path.draw(g, {}) and not self.live and pickle.dumps(g) == before
            path.close(); checks.append(type(error).__name__)
        flow.run.retire(); return checks

    def __exit__(self, *exc):
        try:
            self.observer.stop(); self.release(); assert self.loads == self.destroys and not self.live
        finally:
            for p in reversed(self.patches): p.stop()
            self.c.close_canvas(); self.c.window = self.c.renderer = None


def run(driver=None):
    env = {f'CHECKMATE_STAGE{n}_ART': '1' for n in range(6, 11)}
    if driver: env.update(SDL_VIDEODRIVER='windows' if driver == 'direct3d11' else 'dummy', SDL_AUDIODRIVER='dummy')
    with patch.dict(os.environ, env), NativeAudit(driver) if driver else nullcontext() as audit:
        campaigns = [campaign(style, audit) for style in STYLES]
        g, flow = session(); old = g; g.advance(3600)
        assert g.state.value == 'GAME_OVER'
        death_tick = g.end_tick; g, _ = flow.restart(main._new_stage_game)
        assert (g.stage_number, len(flow.run.receipts), g.player.health.current_hp) == (6, 0, 3)
        assert g.combat.combat_session_id != old.combat.combat_session_id
        if audit: audit.draw(g); audit.release()
        flow.run.retire()
        native = None
        if audit:
            faults = audit.faults()
            native = dict(renderer=audit.renderer, vsync=audit.vsync, observed_frames=audit.frames,
                          texture_loads=audit.loads, texture_destroys=audit.destroys, peak_live_textures=audit.peak,
                          live_after_close=len(audit.live), max_knight_lift=audit.max_lift,
                          warning_sources=sorted(audit.warning_kinds), fallback_fixtures=faults,
                          performance_measured=False, long_running_process_memory_measured=False)
    return dict(scope='Fresh Chapter2 Stage6 start; no prior receipts or forced clears; not Chapter1/human-clear evidence',
                driver='Unchanged tests.test_hp_carryover.fight /3600 ticks per battle', campaigns=campaigns,
                no_input_game_over=dict(stage=6, death_tick=death_tick, restart_stage=6, hp=3, receipts=0),
                native_audit=native, human_stage6_gui='pending', human_chapter2_continuous='pending', windows_performance='unmeasured')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native', choices=('software', 'direct3d11'))
    args = parser.parse_args(); result = run(args.native)
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    for row in result['campaigns']: print(row['style'], [(r['stage'], r['result'], r['ticks'], r['remaining_hp']) for r in row['rows']])
    print('Native audit:', result['native_audit']); print('Human GUI/performance remain pending; this is not a frame-rate benchmark.')
