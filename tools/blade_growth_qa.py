"""Capture production blade receipts and benchmark paired D3D11 frames at the same tick."""
import argparse
from collections import deque
import ctypes as ct
import json
import os
from pathlib import Path
import sys
from time import perf_counter_ns
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sdl2 as s
from sdl2.sdlimage import IMG_SavePNG
from arena_art_common import CAMERA
from display_settings import DisplaySettings
from main import _new_stage_game
from player import DIRECTIONS
from presentation_events import PresentationEvents
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from tools.r7c1_review import pixel_delta
from tools.r7c2_performance import Battle, summary, window
from tools.stage5_art_preview import capture_png
from upgrades import ChapterBuild


def position_for_contact(game, target):
    """Arrange only the QA player's starting position using legal adjacent moves."""
    occupied = game.encounter.occupied_cells
    queue = deque([(game.player.position, ())])
    seen = {game.player.position}
    while queue:
        (x,y), path = queue.popleft()
        for facing,(dx,dy) in DIRECTIONS.items():
            cell = x+dx,y+dy
            if cell == target:
                for direction in path:
                    assert game.player.move(direction, occupied)
                assert not game.player.move(facing, occupied)
                return
            if cell not in seen and cell not in occupied and min(cell)>=0 and max(cell)<10:
                seen.add(cell)
                queue.append((cell, (*path,facing)))
    raise AssertionError('No path to the requested target')


def scene(battle, damage, stage, tick):
    game = battle.game = _new_stage_game(stage, stats=ChapterBuild(attack_level=damage-1).stats)
    battle.queue = game.encounter.ledger.presentation = PresentationEvents()
    battle.sync(0)
    while game.combat.tick < tick:
        battle.advance()
        battle.sync(1/60)
    kind = 'king' if stage==25 else 'queen' if tick else 'rook'
    target = next(e for e in game.encounter.enemies if e.kind==kind and e.active)
    position_for_contact(game, target.position)
    battle.motion.update((game.player,*game.encounter.enemies),0,
                         session=game.combat.combat_session_id,snap=True)
    battle.sync(0)
    result = game.resolver.resolve_player_attack(game.combat.request_attack(game.player))
    assert result and result.amount > 0
    battle.sync(0)
    owned = [fx for fx in battle.effects.effects if fx.key[0] == result.attack_key]
    assert [fx.name for fx in owned] == ['player_swing','player_hit']
    return owned


def pixels(canvas):
    raw = (ct.c_ubyte*(1440*900*4))()
    assert not s.SDL_RenderReadPixels(canvas.renderer,None,s.SDL_PIXELFORMAT_RGBA32,raw,1440*4)
    return bytes(raw)


def crop(canvas, x, y):
    surface = s.SDL_CreateRGBSurfaceWithFormat(0,224,180,32,s.SDL_PIXELFORMAT_RGBA32)
    assert surface
    rect = s.SDL_Rect(round(x)-112,899-round(y)-108,224,180)
    assert not s.SDL_RenderReadPixels(canvas.renderer,ct.byref(rect),s.SDL_PIXELFORMAT_RGBA32,
                                      surface.contents.pixels,surface.contents.pitch)
    return surface


def sheet(canvas, out, cells, columns):
    """Label native-resolution crops; no pixel rescaling or redraw of the effects."""
    rows = (len(cells)+columns-1)//columns
    page = s.SDL_CreateRGBSurfaceWithFormat(0,columns*228,rows*208,32,s.SDL_PIXELFORMAT_RGBA32)
    assert page
    font = canvas.load_font(str(ROOT/'assets/ui/fonts/SourceSans3-Regular.ttf'),17)
    try:
        s.SDL_FillRect(page,None,s.SDL_MapRGB(page.contents.format,18,21,29))
        for i,(image,title) in enumerate(cells):
            x,y = (i%columns)*228,(i//columns)*208
            rect = s.SDL_Rect(x+2,y+25,224,180)
            assert not s.SDL_BlitSurface(image,None,page,ct.byref(rect))
            label = canvas.TTF_RenderUTF8_Blended(font.font,title.encode(),s.SDL_Color(224,231,247))
            assert label
            try:
                rect = s.SDL_Rect(x+5,y+2,0,0)
                assert not s.SDL_BlitSurface(label,None,page,ct.byref(rect))
            finally:
                s.SDL_FreeSurface(label)
        assert not IMG_SavePNG(page,str(out).encode())
    finally:
        canvas.TTF_CloseFont(font.font)
        s.SDL_FreeSurface(page)


def capture(battle, out):
    comparison = []
    captures = []
    try:
        for tier,damage in enumerate((1,4,7,10,16),1):
            owned = scene(battle,damage,24,0)
            px,py = CAMERA.center(*owned[0].origin)
            tx,ty = CAMERA.center(*owned[0].cell)
            frames, bounds = [], []
            try:
                for tick in range(24):
                    if tick:
                        battle.game.advance()
                        battle.sync(1/60)
                    battle.draw()
                    image = crop(battle.c,(px+tx)/2,(py+ty)/2+16)
                    frames.append((image,f'ATK {damage}   +{tick:02} ticks'))
                    active = [fx for fx in owned if fx in battle.effects.effects]
                    before = pixels(battle.c)
                    for fx in active:
                        fx.blade_tier = 1
                    battle.draw()
                    count, box = pixel_delta(before,pixels(battle.c),1440)
                    for fx in active:
                        fx.blade_tier = tier
                    if box:
                        assert box[0]>=min(px,tx)-85 and box[2]<=max(px,tx)+85
                        assert box[1]>=899-max(py,ty)-110 and box[3]<=899-min(py,ty)+65
                    bounds.append((count,box))
                    if tick==3:
                        battle.draw()
                        comparison.append((crop(battle.c,(px+tx)/2,(py+ty)/2+16),
                                           f'Tier {tier}   /   ATK {damage}'))
                        capture_png(battle.c,out/f'tier-{tier}.png')
                assert any(n for n,_ in bounds) == (tier>1) and bounds[-1]==(0,None)
                sheet(battle.c,out/f'tier-{tier}-sequence.png',frames,6)
                captures.append(dict(tier=tier,base_attack=damage,origin=owned[0].origin,
                                     target=owned[0].cell,delta_from_basic=bounds))
            finally:
                for image,_ in frames:
                    s.SDL_FreeSurface(image)
        sheet(battle.c,out/'comparison.png',comparison,5)
        return captures
    finally:
        for image,_ in comparison:
            s.SDL_FreeSurface(image)


def benchmark(battle, out):
    results = {}
    for stage,tick,required in ((24,0,None),(24,135,'queen_fire'),(25,389,'king_pulse')):
        owned = scene(battle,16,stage,tick)
        battle.game.advance(2)
        battle.sync(2/60)
        cues = [fx.name for fx in battle.effects.effects]
        assert not required or required in cues
        battle.draw()
        capture_png(battle.c,out/f'stage-{stage}-tick-{tick+2}.png')
        samples = {1:[],5:[]}
        for block in range(6):
            for tier in ((1,5) if block%2==0 else (5,1)):
                for fx in owned:
                    fx.blade_tier = tier
                for frame in range(110):
                    start = perf_counter_ns()
                    battle.draw()
                    battle.c.update_canvas()
                    if frame>=10:
                        samples[tier].append((perf_counter_ns()-start)/1e6)
        r = battle.art.path.renderer
        expected = {cell for event in battle.game.resolver.live_telegraphs(battle.game.combat.tick)
                    for cell in event.target_cells}
        assert set(r.warning_cells)==expected and not battle.effects.failed and not r.vfx.atlas.failed
        results[f'{stage}_{tick+2}'] = dict(cues=cues,warnings=len(expected),
            basic=summary(samples[1]),royal=summary(samples[5]))
    return results


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    canvas = window()
    settings = SettingsRenderer(canvas,themed=True)
    battle = Battle(canvas,settings,SettingsMenu(),DisplaySettings(canvas))
    try:
        report = dict(driver='direct3d11',resolution=[1440,900],
                      captures=capture(battle,out),timing=benchmark(battle,out))
        (out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(json.dumps(report['timing'],indent=2))
    finally:
        battle.art.close()
        settings.close()
        canvas.close_canvas()


def live(out):
    """Time the shipping paced loop, including SDL input, simulation, present and wait."""
    from pico2d import pico2d as c
    import main
    from combat_vfx import CombatVFX
    from release_game import ReleaseGame
    from sdl_input import poll_ready_events
    from tools.chapter_art_play import session
    from r7c2_window_qa import focus

    os.environ.update(SDL_VIDEODRIVER='windows', SDL_AUDIODRIVER='dummy')
    s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
    c.open_canvas(1440,900)
    c.hide_lattice()
    report = {}
    def tap(key):
        for kind in (s.SDL_KEYDOWN,s.SDL_KEYUP):
            event = s.SDL_Event()
            event.type, event.key.windowID, event.key.keysym.sym = kind,s.SDL_GetWindowID(c.window),key
            assert s.SDL_PushEvent(ct.byref(event))==1
    try:
        focus(c.window)
        info = s.SDL_RendererInfo()
        assert not s.SDL_GetRendererInfo(c.renderer,ct.byref(info)) and info.name==b'direct3d11'
        for stage,parry_tick,swing_tick,kind,enemy_cue in (
                (24,114,135,'queen','queen_fire'), (25,378,389,'king','king_pulse')):
            game, flow = session(stage)
            assert flow.run.stats.attack_damage>=13
            stamps,ticks,work,overlap = [],[],[],[]
            sent = set()
            def poll(canvas):
                assert s.SDL_GetWindowFlags(canvas.window)&s.SDL_WINDOW_INPUT_FOCUS
                stamps.append(perf_counter_ns())
                tick = game.combat.tick
                ticks.append(tick)
                if tick>=parry_tick and 'parry' not in sent:
                    tap(s.SDLK_LALT)
                    sent.add('parry')
                if tick>=swing_tick and 'attack' not in sent:
                    target = next(e for e in game.encounter.enemies if e.kind==kind and e.active)
                    position_for_contact(game,target.position)
                    tap(s.SDLK_LCTRL)
                    sent.add('attack')
                if tick>=swing_tick+30:
                    quit_event = s.SDL_Event()
                    quit_event.type = s.SDL_QUIT
                    assert s.SDL_PushEvent(ct.byref(quit_event))==1
                assert game.playing and len(stamps)<3000
                return poll_ready_events(canvas)
            original_update = CombatVFX.update
            def observe(manager,*args,**kwargs):
                original_update(manager,*args,**kwargs)
                if swing_tick<=game.combat.tick<=swing_tick+15:
                    active = {(f.name,f.blade_tier) for f in manager.effects}
                    if {('player_hit',5),('player_swing',5),(enemy_cue,1)}<=active:
                        overlap.append(len(stamps)-1)
            original_remaining = main.FramePacer.remaining
            def remaining(pacer,elapsed,*args,**kwargs):
                work.append(elapsed*1000)
                return original_remaining(pacer,elapsed,*args,**kwargs)
            with TemporaryDirectory() as folder:
                app = ReleaseGame(c,Path(folder)/'save.json',main._new_stage_game)
                try:
                    with patch.object(CombatVFX,'update',observe), patch.object(main.FramePacer,'remaining',remaining):
                        assert main.run_session(game,flow,default_art=True,app=app,poll_events=poll)=='exit'
                finally:
                    app.close()
            assert overlap and game.resolver.last_parry_result.status=='perfect'
            def measure(indices):
                gaps = [(stamps[i+1]-stamps[i])/1e6 for i in indices]
                return dict(fps=round(1000*len(gaps)/sum(gaps),2),interval_ms=summary(gaps),
                            work_ms=summary([work[i] for i in indices]))
            report[stage] = dict(attack=flow.run.stats.attack_damage,
                active=measure([i for i in range(len(work)) if ticks[i]>=5]),
                overlap=measure(overlap))
        (out/'paced.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(report)
    finally:
        c.close_canvas()


def campaign(out):
    from sprite_atlas import opted_in_catalog
    from tools.combat_vfx_qa import run as campaign_review
    with TemporaryDirectory() as folder:
        work = Path(folder)/'campaign'
        campaign_review('software',work,layered=True,telegraph=True,attack_motion=True,
                        player_combat=True,articulation=True,sprite_catalog=opted_in_catalog())
        result = json.loads((work/'manifest.json').read_text())
    from tools.campaign_qa import release_campaign_rows
    assert result['campaign']==release_campaign_rows()
    keys = ('driver','campaign','resources','coverage','peak_effects','peak_particles')
    (out/'campaign.json').write_text(json.dumps({k:result[k] for k in keys},indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--live',action='store_true')
    mode.add_argument('--campaign',action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    if args.live:
        live(args.output)
    elif args.campaign:
        campaign(args.output)
    else:
        run(args.output)
