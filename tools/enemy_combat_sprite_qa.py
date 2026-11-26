
"""Compare enemy sprite groups with their previous catalogs on real combat ticks."""
import argparse
from contextlib import ExitStack
from ctypes import byref, c_uint32
from hashlib import sha256
import json
import os
from pathlib import Path
import pickle
import sys
from time import perf_counter_ns
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from actor_animation import ActorAnimation, State
from attack_telegraph import TelegraphRenderer
from chapter_art_renderer import LiveArenaArtPath
from combat_vfx import CombatVFX
from input_controller import InputController
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from sprite_animation import SpriteCatalog, SpriteController, cardinal
from sprite_atlas import DEFAULT_CATALOG, SpriteAtlases
from tools.player_combat_sprite_qa import percentiles
from tools.stage5_art_preview import capture_png, open_preview

# Real input paths, source ids and observed release ticks on the current campaign.
CASES=(
    (1,'pawn','LLLL',615),(2,'rook','',168),(3,'knight','',84),
    (7,'pawn','LLLL',642),(6,'rook','',208),(7,'knight','',84),
    (13,'pawn','LLLL',642),(11,'rook','',168),(11,'knight','',111),
    (17,'pawn','LLLLUUU',285),(16,'rook','',168),(16,'knight','',111),
    (21,'pawn','LLLLUUU',299),(21,'rook','',182),(21,'knight','',124),
)
CLIPS=frozenset({'ch1_pawn','ch2_rook','ch3_knight'})
DIRECTION_CASES=(
    (2,'rook','LLLLLL',234,'left'),(2,'rook','UUUULLLL',306,'up'),
    (3,'knight','UUUULLLL',192,'left'),(3,'knight','LLLLLL',408,'up'),
)

CASTER_CASES=(
    (4,'bishop','',156), (8,'bishop','',156), (12,'bishop','',156),
    (16,'bishop','',209), (21,'bishop','',222),
    (13,'queen','',121), (18,'queen','',121), (24,'queen','',121),
    (5,'king','UUUUU',240,'down','basic',(164,224)),
    (10,'king','UUUUU',240,'right','basic',(222,)),
    (15,'king','UUUUU',463,'right','basic',(117,177,367,445)),
    (20,'king','UUUUR',463,'down','basic',(117,367,445)),
    (25,'king','UUUUR',463,'down','basic',(117,190,367,445)),
    *((stage,'king','',385,'neutral','king_pulse',(367,)) for stage in (5,10,15,20,25)),
)
CASTER_CLIPS=frozenset({'ch3_bishop','ch5_queen','ch1_king_melee','ch5_king_pulse'})


def run(output, *, benchmark_only=False, group='martial'):
    import sdl2 as s
    from pico2d import pico2d as c

    output.mkdir(parents=True)
    caster=group=='caster'
    martial=DEFAULT_CATALOG.with_name('manifest_martial.json')
    production=SpriteCatalog.read(DEFAULT_CATALOG if caster else martial)
    previous_file=martial if caster else DEFAULT_CATALOG.with_name('manifest_player_only.json')
    previous=SpriteController(SpriteCatalog.read(previous_file))
    report=dict(driver='direct3d11',group=group,scenes={},textures={},loads=0,releases=0,peak=0)
    if caster:
        report['boss_performance']={}
    load,drop=SpriteAtlases._load, SpriteAtlases._drop

    def measure_load(bank,path):
        t=perf_counter_ns()
        texture,size=load(bank,path)
        assert texture,path
        elapsed=(perf_counter_ns()-t)/1e6
        fmt=c_uint32()
        assert s.SDL_QueryTexture(texture,byref(fmt),None,None,None)==0
        info=report['textures'].setdefault(path.name,dict(size=size,ms=[],
                      pixel_bytes=size[0]*size[1]*s.SDL_BYTESPERPIXEL(fmt.value)))
        info['ms'].append(round(elapsed,3))
        report['loads']+=1
        report['peak']=max(report['peak'],report['loads']-report['releases'])
        return texture,size

    def measure_drop(bank,name):
        drop(bank,name)
        report['releases']+=1

    def scene(stage,kind,steps,hit_tick,expected_facing=None,attack_kind=None,parries=()):
        game=_new_stage_game(stage)
        source_id=f's{stage}_{kind}_1'
        actor=next(e for e in game.encounter.enemies if e.data_id==source_id)
        name=f'ch{game.chapter}_{kind}'
        if caster and kind=='king':
            name+='_pulse' if attack_kind=='king_pulse' else '_melee'
        elif expected_facing is not None:
            name+=f'_{expected_facing}'
        record=report['scenes'][name]=dict(stage=stage,source=source_id,hit_tick=hit_tick,phases={})
        observed=set()
        feed=game.encounter.ledger.presentation=PresentationEvents()
        controls=InputController()
        motion=RenderMotion(improved=True)
        animation=ActorAnimation(improved=True,enemy_attacks=True,player_actions=True,articulated=True,sprites=True)
        vfx=CombatVFX(layered=True)
        warning=TelegraphRenderer()
        art=LiveArenaArtPath(c,motion=motion,animation=animation,vfx=vfx,telegraph=warning,default_enabled=True,
                             enlarged=True,player_combat_visual=True,sprite_catalog=production)
        clip_names=CASTER_CLIPS if caster else CLIPS
        clip_folder=output/'clips'/name if name in clip_names and not benchmark_only else None
        if clip_folder is not None:
            clip_folder.mkdir(parents=True)

        def draw():
            c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
            c.SDL_RenderClear(c.renderer)
            assert art.draw(game,motion.positions)
            renderer=art.path.renderer
            assert not renderer.animation_failed and not vfx.failed and not warning.failed
            return renderer

        def pair(folder,index,*,full=False):
            before=pickle.dumps(game)
            renderer=draw()
            foot=renderer.actor_layouts[actor.entity_instance_id]['foot']
            x,y=foot
            region=None if full else s.SDL_Rect(max(0,min(1176,round(x-132))),
                                                 max(0,min(716,round(899-y-148))),264,184)
            capture_png(c,folder/f'{index}_articulated.png',region)
            cells=tuple(renderer.warning_cells)
            hint=renderer.parry_hint
            bank=renderer.sprite_atlases
            selected=bank.controller
            try:
                bank.controller=previous
                draw()
                layout=renderer.actor_layouts[actor.entity_instance_id]
                assert not layout.get('sprite_frame') and layout['foot']==foot
                assert tuple(renderer.warning_cells)==cells and renderer.parry_hint==hint
                capture_png(c,folder/f'{index}_previous.png',region)
            finally:
                bank.controller=selected
            assert pickle.dumps(game)==before

        def benchmark(phase, label=None):
            before=pickle.dumps(game)
            renderer=draw()
            bank=renderer.sprite_atlases
            selected=bank.controller
            baseline='martial' if caster else 'player_only'
            timings={baseline:[],'enemy_sprite':[]}
            try:
                for block in range(12):
                    keys=tuple(timings) if block%2==0 else tuple(reversed(timings))
                    for mode in keys:
                        bank.controller=selected if mode=='enemy_sprite' else previous
                        for _ in range(12):
                            t=perf_counter_ns()
                            animation.update(game,0,(),motion=motion)
                            renderer=draw()
                            assert bool(renderer.actor_layouts[actor.entity_instance_id].get('sprite_frame'))==(mode=='enemy_sprite')
                            s.SDL_RenderPresent(c.renderer)
                            if block>=2:
                                timings[mode].append((perf_counter_ns()-t)/1e6)
            finally:
                bank.controller=selected
            assert pickle.dumps(game)==before
            destination=report['boss_performance'] if label else record
            destination[label or 'performance']=dict(phase=phase,tick=game.combat.tick,
                                    frame_ms={mode:percentiles(values) for mode,values in timings.items()})

        try:
            animation.update(game,0,(),motion=motion)
            if not benchmark_only:
                (output/'poses').mkdir(exist_ok=True)
            index=0
            # Warm the actual arena first so its texture-loading time is recorded separately.
            draw()
            controller=art.path.renderer.sprite_atlases.controller
            end_tick=hit_tick+(42 if caster else 28)
            while game.combat.tick<end_tick:
                tick=game.combat.tick
                if tick%18==0 and tick//18<len(steps):
                    direction={'L':'left','U':'up','R':'right'}[steps[tick//18]]
                    controls.key_down(direction,game.player,occupied=game.encounter.occupied_cells,tick=tick)
                    controls.key_up(direction)
                if tick+1 in parries:
                    game.combat.advance(1)
                    attempt=game.parry.request(game.combat.tick)
                    assert attempt is not None,(name,tick+1)
                    result=game.resolver.register_parry(attempt)
                    assert result.adjudication_grade=='normal',(name,tick+1,result)
                    game.resolve_current_tick()
                else:
                    game.advance()
                tick=game.combat.tick
                assert game.playing,(name,tick,game.state)
                frozen=() if game.encounter.pulse is None else tuple(
                    enemy.entity_instance_id for enemy in game.encounter.enemies if game.encounter.pulse.frozen(enemy))
                motion.update((game.player,*game.encounter.enemies),1/60,session=game.combat.combat_session_id,frozen=frozen)
                events=feed.drain()
                animation.update(game,1/60,events,motion=motion)
                vfx.update(game,1/60,events,motion=motion)
                pose=animation.mesh_pose(game,actor,motion)[0]
                selected=controller.sample(game,actor,kind,animation,pose)
                if selected and animation.sprite_source(game,actor,pose)[1].hit_tick==hit_tick:
                    clip,frame=selected
                    observed.add(clip.frames.index(frame))
                    assert clip.facing==cardinal(pose.direction,pose.depth_direction)
                    phase=pose.attack_motion
                    first_release = pose.state is State.ATTACK and 'release' not in record['phases']
                    if first_release:
                        onset=next((event for event in events if event.kind=='attack_start'
                                    and event.subject==actor.entity_instance_id),None)
                        start_frame=clip.contact if phase=='arrival' else clip.impact
                        assert onset and onset.tick==hit_tick and frame is clip.frames[start_frame],name
                        if expected_facing is not None:
                            assert clip.facing==expected_facing,name
                        record['phases']['release']=dict(tick=tick,frame=start_frame,origin=onset.origin,
                                                         target=onset.payload.target_cells[0],
                                                         attack_kind=onset.payload.attack_kind)
                    phases=record['phases']
                    first_arrival = phase=='arrival' and phase not in phases
                    if phase not in phases:
                        _,lift=motion.ground_pose(actor)
                        assert draw().actor_layouts[actor.entity_instance_id].get('sprite_frame')
                        phases[phase]=dict(tick=tick,frame=clip.frames.index(frame),
                                            facing=clip.facing,elevation=lift)
                        if phase=='arrival':
                            effect='rook_impact' if kind=='rook' else 'knight_land'
                            assert frame is clip.frames[clip.contact] and abs(lift)<1e-6
                            assert any(fx.name==effect and fx.landed is not None and fx.key[2]==actor.entity_instance_id
                                       for fx in vfx.effects),(name,tick)
                    if first_arrival or first_release and (caster or kind=='pawn'):
                        if not caster and (name in CLIPS or name=='ch5_rook'):
                            benchmark(phase)
                        if not benchmark_only:
                            gallery=output/'poses'
                            gallery.mkdir(exist_ok=True)
                            pair(gallery,name)
                if caster and stage==24 and tick==135:
                    queens=[actor for actor in game.encounter.enemies if actor.kind=='queen']
                    assert len({fx.key[2] for fx in vfx.effects if fx.name=='queen_fire'})==2
                    frames=[controller.sample(game,q,'queen',animation,animation.mesh_pose(game,q,motion)[0]) for q in queens]
                    assert all(frames) and frames[0][1]!=frames[1][1]
                    benchmark('crossing','stage24_queen')
                    if not benchmark_only:
                        pair(output/'poses','stage24_queen_crossing',full=True)
                if name=='ch5_king_pulse' and tick in (378,389):
                    if tick==378:
                        assert len(draw().warning_cells)==100
                    else:
                        assert game.resolver.last_parry_result.status=='normal'
                    benchmark('charge' if tick==378 else 'release',f'stage25_pulse_{tick}')
                    if not benchmark_only:
                        pair(output/'poses',f'stage25_pulse_{tick}',full=True)
                clip_start=hit_tick-(36 if kind=='rook' or caster else 28)
                if clip_folder is not None and tick>=clip_start and (tick-clip_start)%2==0:
                    pair(clip_folder,f'{index:03}')
                    index+=1
            required={'anticipation','release'}
            if kind in ('rook','knight'):
                required.add('arrival')
                if record['phases'].get('arrival',{}).get('tick')!=hit_tick:
                    required.add('travel')
            assert required<=set(record['phases']),(name,record)
            if caster:
                assert observed=={0,1,2,3},(name,observed)
            record['observed_frames']=sorted(observed)
            record['clip_frames']=index
        finally:
            art.close()

    with patch.dict(os.environ,{'SDL_VIDEODRIVER':'windows','SDL_AUDIODRIVER':'dummy'}), ExitStack() as stack:
        stack.enter_context(patch.object(SpriteAtlases,'_load',measure_load))
        stack.enter_context(patch.object(SpriteAtlases,'_drop',measure_drop))
        s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
        create=c.SDL_CreateRenderer
        with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:create(w,i,s.SDL_RENDERER_ACCELERATED)):
            open_preview(c,capture=True)
        stack.callback(c.close_canvas)
        info=s.SDL_RendererInfo()
        assert c.renderer and not s.SDL_GetRendererInfo(c.renderer,info) and info.name==b'direct3d11'
        for case in (CASTER_CASES if caster else (*CASES, *DIRECTION_CASES)):
            scene(*case)
    assert report['loads']==report['releases']
    report['capture_sha256']={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted((output/'poses').glob('*.png'))}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--benchmark-only',action='store_true')
    parser.add_argument('--group', choices=('martial','caster'), default='martial')
    args=parser.parse_args()
    result=run(args.output,benchmark_only=args.benchmark_only,group=args.group)
    print(json.dumps(dict(scenes=len(result['scenes']),
                          loads=result['loads'],releases=result['releases']),indent=2))
