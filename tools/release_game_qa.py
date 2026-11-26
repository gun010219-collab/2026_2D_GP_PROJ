"""Run the shipping shell and an actual 25-stage run against an isolated save."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace as Event
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from chapter_art_renderer import LiveArenaArtPath
from front_menu import FrontRenderer,buttons
from game_renderer import GameFlowRenderer
from game_audio import AudioManager, BOSS_TRACKS
import main
from release_game import ReleaseGame,launch
from save_manager import SaveData,SaveStore
from settings_menu import AUDIO_ROWS
from settings_renderer import SettingsRenderer
from tests.test_hp_carryover import fight
from tools.chapter_art_play import advance_campaign,session
from tools.stage5_art_preview import capture_png,open_preview


def run(driver,output,isolated):
    import sdl2 as s
    from sdl2 import sdlimage, sdlmixer as mix
    from pico2d import pico2d as c

    if output:
        output.mkdir(parents=True,exist_ok=False)
    save = Path(isolated)/'save.json'
    records,frames,views,play_calls,tracks = [],{}, {}, [],[]
    live = set()
    counts = dict(loads=0,frees=0,peak=0,opens=0,closes=0)
    view, combat_frames = '',0
    save_defaults = SaveData()
    def snap(name):
        if name not in frames:
            frames[name] = None
            if output:
                png = output/(name+'.png')
                capture_png(c,png)
                frames[name] = hashlib.sha256(png.read_bytes()).hexdigest()

    def window(width,height):
        counts['opens']+=1
        if driver=='direct3d11':
            s.SDL_SetHint(s.SDL_HINT_RENDER_DRIVER,b'direct3d11')
        create = c.SDL_CreateRenderer
        if driver=='direct3d11':
            with patch.object(c,'SDL_CreateRenderer',lambda w,i,f:create(w,i,s.SDL_RENDERER_ACCELERATED)):
                open_preview(c,capture=True)
        else:
            open_preview(c,capture=True)
        info=s.SDL_RendererInfo()
        assert s.SDL_GetRendererInfo(c.renderer,ctypes.byref(info))==0 and info.name.decode()==driver
        assert s.SDL_InitSubSystem(s.SDL_INIT_AUDIO)==0
        assert mix.Mix_OpenAudio(44100,mix.MIX_DEFAULT_FORMAT,2,1024)==0
        c.audio_on=True

    old_close = c.close_canvas
    def close():
        assert not live,live
        counts['closes']+=1
        old_close()
        c.window=c.renderer=None

    old_image,old_texture,old_destroy = c.load_image,c.SDL_CreateTextureFromSurface,c.SDL_DestroyTexture
    old_atlas = sdlimage.IMG_LoadTexture
    def acquire(tex):
        ptr=ctypes.cast(tex,ctypes.c_void_p).value
        if ptr and ptr not in live:
            live.add(ptr)
            counts['loads']+=1
            counts['peak']=max(counts['peak'],len(live))
        return tex
    def load_image(name):
        image=old_image(name)
        acquire(image.texture)
        return image
    def load_texture(*args):
        return acquire(old_texture(*args))
    def load_atlas(*args):
        return acquire(old_atlas(*args))
    def destroy(tex):
        if tex:
            key=ctypes.cast(tex,ctypes.c_void_p).value
            assert key in live,key
            live.remove(key)
            counts['frees']+=1
        return old_destroy(tex)

    loop = ReleaseGame.front_loop
    def observe_front(app,screen,replay):
        nonlocal view
        views[screen]=views.get(screen,0)+1
        view=f'{screen}{views[screen]}'
        polls[view]=0
        return loop(app,screen,replay)

    old_music = AudioManager.set_music
    def music(audio,key):
        changed=audio.track!=key
        old_music(audio,key)
        if changed:
            assert bool(mix.Mix_PlayingMusic()) == bool(key)
            tracks.append(key)

    draw = FrontRenderer.draw_screen
    def observe_draw(front,screen,data,notice,selection,ending,replay):
        draw(front,screen,data,notice,selection,ending,replay)
        if view=='main1':
            assert data.continue_chapter is None
            snap('main_menu')
        elif view=='chapters1':
            assert data.unlocked==(1,)
            snap('chapter_select_initial' if selection==0 else 'chapter_locked')
        elif view=='chapters2':
            assert data.unlocked==(1,2,3,4,5)
            snap('chapters_all_unlocked')
        elif view=='ending1':
            assert ending and replay
            snap('ending')
        elif view=='credits1':
            snap('credits')

    draw_settings = SettingsRenderer.draw
    def observe_settings(renderer,menu,display):
        draw_settings(renderer,menu,display)
        if menu.is_open and menu.audio.bgm==50 and menu.audio.sfx_mute:
            snap('settings')

    def key(code):
        return Event(type=s.SDL_KEYDOWN,key=code,repeat=0)
    def click(rect):
        return Event(type=s.SDL_MOUSEBUTTONDOWN,button=s.SDL_BUTTON_LEFT,
                     x=rect.left+rect.width//2,y=899-(rect.bottom+rect.height//2))
    def select(screen,index,replay=False):
        return click(buttons(screen,save_defaults,replay)[index].rect)

    escape=key(s.SDLK_ESCAPE)
    polls={}
    plans={
        'main1':[[],[key(s.SDLK_DOWN)],[key(s.SDLK_RETURN)]],
        'chapters1':[[],[select('chapters',4)],[escape]],
        'main2':[[],[select('main',3)],[click(AUDIO_ROWS['bgm'][1])],
                 [click(AUDIO_ROWS['sfx'][2])],[escape],[select('main',0)]],
        'main3':[[],[select('main',1)]],
        'ending1':[[],[select('ending',1,True)]],
        'ending2':[[],[select('ending',0,True)]],
        'credits1':[[],[key(s.SDLK_RETURN)]],
        'ending3':[[],[select('ending',2,True)]],
        'main4':[[],[select('main',2)]],
        'chapters2':[[],[escape]],
        'main5':[[],[select('main',4)]],
    }
    def poll():
        nonlocal combat_frames
        if view=='intro':
            combat_frames+=1
            return [] if combat_frames<5 else [escape]
        if view=='terminal':
            combat_frames+=1
            assert combat_frames<35,'Ending animation hold did not finish'
            return []
        i=polls[view]
        polls[view]+=1
        return plans[view][i]

    def battle_capture(game,name):
        c.SDL_SetRenderDrawColor(c.renderer,0,0,0,255)
        c.SDL_RenderClear(c.renderer)
        art = LiveArenaArtPath(c,default_enabled=True)
        try:
            assert art.draw(game,{})
            GameFlowRenderer(official=True).draw(c,game)
            snap(name)
        finally:
            art.close()

    def play(game,flow,*,default_art,app):
        nonlocal view,combat_frames
        play_calls.append(game.stage_number)
        if len(play_calls)==1:
            view='intro'
            combat_frames=0
            assert main.run_session(game,flow,default_art=True,app=app)=='main'
            return 'main'
        if len(play_calls)==2:
            _,loss=session(2)
            while loss.game.playing:
                loss.game.advance()
            assert loss.game.state.value=='GAME_OVER'
            battle_capture(loss.game,'game_over')
            for stage in range(1,26):
                app.audio.update(flow.game,0,())
                if stage==25:
                    flow.enable_presentation()
                result=fight(flow)
                records.append(list(result))
                if stage<25 and stage%5==0:
                    from campaign_save import record_clear
                    record_clear(app.store,flow)
                    if stage==5:
                        battle_capture(flow.game,'boss_clear')
                if stage<25:
                    advance_campaign(flow,result)
        else:
            assert game.stage_number==25 and len(flow.run.receipts)==4
            app.audio.update(game,0,())
            flow.enable_presentation()
            assert fight(flow)[1]=='BOSS_CLEAR'
        view='terminal'
        combat_frames=0
        real_clock = [0.]
        def time():
            real_clock[0]+=.04
            return real_clock[0]
        with patch.object(main,'perf_counter',time):
            outcome=main.run_session(flow.game,flow,default_art=True,app=app)
        assert outcome=='ending' and combat_frames>=10
        return outcome

    env = dict(SDL_VIDEODRIVER='windows' if driver=='direct3d11' else 'dummy',SDL_AUDIODRIVER='dummy',
               CHECKMATE_AUDIO='1')
    flags = c.SDL_GetWindowFlags
    with patch.dict(os.environ,env),patch.object(c,'open_canvas',window),patch.object(c,'close_canvas',close), \
         patch.object(c,'SDL_GetWindowFlags',lambda w:flags(w)|s.SDL_WINDOW_INPUT_FOCUS), \
         patch.object(c,'get_events',poll),patch.object(c,'load_image',load_image), \
         patch.object(c,'SDL_CreateTextureFromSurface',load_texture),patch.object(c,'SDL_DestroyTexture',destroy), \
         patch.object(sdlimage,'IMG_LoadTexture',load_atlas), \
         patch.object(ReleaseGame,'front_loop',observe_front),patch.object(AudioManager,'set_music',music), \
         patch.object(FrontRenderer,'draw_screen',observe_draw),patch.object(SettingsRenderer,'draw',observe_settings):
        launch(main._new_stage_game,play,path=save)
    baseline=json.loads((ROOT/'artifacts/combat_vfx_r4/manifest.json').read_text())['campaign']
    assert records==baseline
    restored=SaveStore(save).data
    assert restored.unlocked==restored.cleared==(1,2,3,4,5)
    assert restored.continue_chapter==5 and restored.final_clear
    assert restored.bgm==50 and restored.sfx_mute
    from campaign_save import start_chapter
    continued=start_chapter(SaveStore(save),restored.continue_chapter,main._new_stage_game)
    assert continued.game.stage_number==21 and continued.run.entry_attack_level==restored.entry_attack[-1]
    assert tracks.count('ending')==2 and tracks[0]=='menu',tracks
    assert tuple(track for track in tracks if track is not None and track.startswith('boss'))==(
        *BOSS_TRACKS,BOSS_TRACKS[-1]),tracks
    assert set(tracks) >= {'royal','forest','frozen','caldera','gothic'},tracks
    assert counts['opens']==counts['closes']==1 and counts['loads']==counts['frees']
    assert len(frames)==9,frames
    report=dict(driver=driver,render_resources=counts,campaign=records,frames=frames,tracks=tracks,
                continue_stage=continued.game.stage_number,entry_attack=restored.entry_attack)
    if output:
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--renderer',choices=('direct3d11','software'),default='direct3d11')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    with TemporaryDirectory(prefix='checkmate-r6-save-') as folder:
        print(json.dumps(run(args.renderer,args.output,folder),indent=2))
