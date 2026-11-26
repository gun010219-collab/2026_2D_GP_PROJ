from dataclasses import asdict
from hashlib import sha256
import json
import os
import pickle
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from enemy import Enemy
from game_audio import (AudioManager, AudioSettings, BGM_PLAYLIST, MixerAudio, RENEWED_CUES,
                        ROOT, SFX_CHAPTERS, THEMED_SFX, VOICES)
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from settings_menu import AUDIO_ROWS, SETTINGS_BUTTON, SettingsMenu
from tests.test_bishop import battle
from tests.test_combat_resolution import pawn, setup
from tests.test_king_pulse import parry, pulse_battle
from tools.chapter_art_play import session


class FakeMixer:
    def __init__(self):
        self.calls = []
        self.live = set()

    def volume(self,bgm,sfx):
        self.calls.append(('volume',bgm,sfx))

    def music(self,name):
        self.calls.append(('music',name))

    def sound(self,name,channel):
        self.live.add(channel)
        self.calls.append(('sfx',name,channel))
        return True

    def playing(self,channel):
        return channel in self.live

    def clear_voices(self):
        self.calls.append(('halt',))
        self.live.clear()

    def close(self):
        self.clear_voices()
        self.calls.append(('close',))

    @property
    def cues(self):
        return [call[1] for call in self.calls if call[0]=='sfx']


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeMixer()
        self.audio = AudioManager(self.backend,AudioSettings())

    def test_real_swing_hit_and_duplicate(self):
        for col, expected in [(6,['player_swing']),(5,['player_swing','player_hit'])]:
            p,c,e,r = setup((pawn(col=col),))
            g = NS(player=p,combat=c,encounter=e,stage_number=1,chapter=1,state=NS(value='PLAYING'))
            q = e.ledger.presentation = PresentationEvents()
            r.resolve_player_attack(c.request_attack(p))
            batch = q.drain()
            before = pickle.dumps(g)
            self.audio.update(g,0,batch)
            self.audio.update(g,0,batch)
            self.assertEqual(self.backend.cues[-len(expected):],expected)
            self.assertEqual(pickle.dumps(g),before)
        self.assertEqual(self.backend.cues,['player_swing','player_swing','player_hit'])

    def test_real_pulse_success_failure_reflection_and_invulnerability(self):
        for grade in (18,7,19,None):
            p,c,q,e,r = parts = pulse_battle()
            feed = e.ledger.presentation = PresentationEvents()
            r.advance(1)
            if grade is None:
                r.player_invulnerable_until_tick = e.pulse.event.hit_tick+1
                r.advance(120)
            else:
                parry(parts,grade)
            g = NS(player=p,combat=c,encounter=e,stage_number=25,chapter=5,state=NS(value='PLAYING'))
            before = len(self.backend.cues)
            self.audio.update(g,0,feed.drain())
            cues = self.backend.cues[before:]
            self.assertIn('king_pulse',cues)
            self.assertEqual('parry_normal' in cues,grade==18)
            self.assertEqual('parry_perfect' in cues,grade==7)
            self.assertEqual('parry_failed' in cues,grade==19)
            self.assertEqual('player_hit' in cues,grade==7)
            self.assertEqual('player_hurt' in cues,grade==19)

    def test_two_queens_and_multitick_replay(self):
        game = _new_stage_game(24)
        feed = game.encounter.ledger.presentation = PresentationEvents()
        count = 0
        for _ in range(40):
            game.advance(4)
            batch = feed.drain()
            self.backend.live.clear()
            before = pickle.dumps(game)
            self.audio.update(game,4/60,batch)
            self.audio.update(game,0,batch)
            self.assertEqual(pickle.dumps(game),before)
            count += sum(e.kind=='attack_start' and getattr(e.payload,'attack_kind','')=='queen_diagonal'
                         for e in batch)
        self.assertGreaterEqual(count,2)
        self.assertEqual(self.backend.cues.count('queen_fire'),count)

    def test_each_chapter_routes_real_enemy_telegraphs_and_releases(self):
        class ChapterMixer(FakeMixer):
            def sound_in_chapter(self,cue,channel,chapter):
                return self.sound(f'{chapter}/{cue}',channel)

        self.backend = ChapterMixer()
        self.audio = AudioManager(self.backend,AudioSettings())
        pairs = {
            ('bishop','telegraph'): 'bishop_charge', ('bishop','attack_start'): 'bishop_cast',
            ('queen','telegraph'): 'queen_charge', ('queen','attack_start'): 'queen_fire',
            ('king','telegraph'): 'king_melee_charge', ('king','attack_start'): 'king_strike',
        }
        heard = set()
        for chapter, name in enumerate(SFX_CHAPTERS,1):
            bishop = Enemy('b',2,8,None,.10,kind='bishop')
            queen = Enemy('q',4,4,None,.10,kind='queen',max_hp=14)
            king = Enemy('k',5,2,None,.10,kind='king',boss_hp=40)
            boss = _new_stage_game(chapter*5)
            encounters = [(boss,boss.advance)]
            for enemies in ((bishop,queen),(king,)):
                p,c,_,e,r = battle(enemies=enemies)
                scenario = NS(player=p,combat=c,encounter=e,chapter=chapter,
                              stage_number=chapter*5-1,state=NS(value='PLAYING'))
                encounters.append((scenario,r.advance))
            for game, advance in encounters:
                feed = game.encounter.ledger.presentation = PresentationEvents()
                actors = {actor.entity_instance_id:actor.kind for actor in game.encounter.enemies}
                for _ in range(720):
                    advance(1)
                    batch = feed.drain()
                    offset = len(self.backend.cues)
                    self.backend.live.clear()
                    self.audio.update(game,1/60,batch)
                    self.audio.update(game,0,batch)
                    expected = []
                    for event in batch:
                        key = actors.get(event.subject),event.kind
                        if key not in pairs:
                            continue
                        cue = pairs[key]
                        if getattr(event.payload,'attack_kind','') == 'king_pulse':
                            cue = 'king_charge' if event.kind == 'telegraph' else 'king_pulse'
                        expected.append(f'{name}/{cue}')
                    delivered = [cue for cue in self.backend.cues[offset:] if '/' in cue]
                    self.assertEqual(delivered,expected)
                    heard.update(delivered)
                    if game is boss and not boss.playing:
                        break
        self.assertEqual(heard,set(THEMED_SFX))

    def test_knight_sound_follows_render_landing(self):
        game = _new_stage_game(3)
        feed = game.encounter.ledger.presentation = PresentationEvents()
        motion = RenderMotion()
        knight = game.encounter.enemies[0]
        airborne = False
        for _ in range(99):
            game.advance()
            motion.update((knight,),1/60,session=game.combat.combat_session_id)
            self.backend.live.clear()
            self.audio.update(game,1/60,feed.drain(),motion=motion)
            if motion.ground_pose(knight)[1]>1e-8:
                airborne = True
                self.assertNotIn('knight_land',self.backend.cues)
        self.assertTrue(airborne)
        self.assertEqual(self.backend.cues.count('knight_land'),1)

    def test_chapter_music_boss_terminal_and_restart(self):
        for stage in (1,2,4,5,6,7,10,11,15,16,20,21,25):
            self.audio.update(_new_stage_game(stage),0,())
        tracks = [call[1] for call in self.backend.calls if call[0]=='music']
        self.assertEqual(tracks,['royal','boss_royal','forest','boss_forest','frozen','boss_frozen',
                                 'caldera','boss_caldera','gothic','boss_gothic'])
        game,flow = session(2)
        feed = flow.enable_presentation()
        self.audio.update(game,0,())
        while game.playing:
            game.advance()
        self.audio.update(game,0,feed.drain())
        self.audio.update(game,0,())
        self.assertEqual(self.backend.cues.count('game_over'),1)
        self.assertEqual(self.audio.track,None)
        restarted,_ = flow.restart(_new_stage_game)
        self.audio.update(restarted,0,feed.drain(),ui=('restart',))
        self.assertEqual(self.audio.track,'royal')
        self.assertEqual(self.backend.cues.count('restart'),1)
        self.assertFalse(self.audio.arrivals)

    def test_volume_serialization_buttons_and_voice_priority(self):
        menu = SettingsMenu()
        center = lambda rect:(rect.left+1,rect.bottom+1)
        self.assertEqual(menu.click(center(SETTINGS_BUTTON)),'consumed')
        minus,plus,mute = AUDIO_ROWS['bgm']
        for _ in range(20):
            menu.click(center(plus))
        self.assertEqual(menu.audio.bgm,100)
        menu.click(center(minus))
        menu.click(center(mute))
        self.assertEqual(menu.audio.gains(),(0,75))
        self.assertEqual(AudioSettings(**asdict(menu.audio)),menu.audio)
        self.audio.settings = menu.audio
        for _ in range(10):
            self.audio.play('player_move')
        self.assertEqual(len(self.backend.live),4)
        for _ in range(7):
            self.audio.play('parry_perfect')
        self.assertEqual(len(self.backend.live),VOICES)
        self.assertEqual(self.backend.cues.count('parry_perfect'),7)
        menu.click(center(AUDIO_ROWS['sfx'][2]))
        self.audio.apply_settings()
        before = len(self.backend.cues)
        self.audio.play('king_pulse')
        self.assertEqual(self.backend.calls[-1],('volume',0,0))
        self.assertEqual(len(self.backend.cues),before)
        self.assertEqual(menu.key('f11'),'toggle_fullscreen')
        self.assertEqual(menu.key('escape'),'consumed')
        self.assertFalse(menu.is_open)

    def test_three_consumers_share_one_batch_and_audio_runs_alone(self):
        import main
        from actor_animation import ActorAnimation
        from combat_vfx import CombatVFX
        from stage_progression import StageProgression
        from tests.test_main import WindowLoopTests

        for value in ('0','1'):
            game = _new_stage_game(1)
            flow = StageProgression(game)
            canvas = WindowLoopTests().make_canvas()
            canvas.get_events.side_effect = [[NS(type=768,key=1073742048)],[NS(type=256)]]
            env = dict(CHECKMATE_STAGE1_ART='0',CHECKMATE_AUDIO='1',
                       CHECKMATE_ANIMATION=value,CHECKMATE_VFX=value)
            with patch.dict(os.environ,env),patch.dict(sys.modules,{'pico2d':NS(pico2d=canvas)}), \
                 patch.object(main,'DisplaySettings'),patch.object(main,'SettingsRenderer'),patch.object(main,'sleep'), \
                 patch.object(MixerAudio,'open',return_value=self.backend), \
                 patch.object(ActorAnimation,'update') as anim,patch.object(CombatVFX,'update') as vfx, \
                 patch.object(AudioManager,'update') as audio:
                main.run_session(game,flow,default_art=True)
            self.assertEqual(audio.call_count,1)
            batch = audio.call_args.args[2]
            self.assertEqual([e.kind for e in batch],['attack_start'])
            if value=='1':
                self.assertIs(batch,anim.call_args.args[2])
                self.assertIs(batch,vfx.call_args.args[2])
            else:
                anim.assert_not_called()
                vfx.assert_not_called()

    def test_no_device_and_missing_or_corrupt_handles(self):
        self.assertIsNone(MixerAudio.open(NS(audio_on=False)))
        mixer = Mock()
        mixer.Mix_LoadWAV.return_value = None
        mixer.Mix_LoadMUS.return_value = None
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        backend = MixerAudio(mixer,root=Path(directory.name))
        self.assertFalse(backend.sound('player_swing',0))
        backend.music('royal')
        mixer.Mix_FadeInMusic.assert_not_called()
        self.assertEqual(len(backend.failures),len(backend.sounds)+1)
        backend.close()
        backend.close()
        mixer.Mix_FreeMusic.assert_not_called()
        mixer.Mix_FreeChunk.assert_not_called()

    def test_corrupt_renewal_reuses_legacy_boss_music(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'renewal').mkdir()
            candidate=root/'renewal'/'boss_frozen.ogg'
            candidate.write_bytes(b'bad')
            mixer=Mock()
            mixer.Mix_LoadMUS.side_effect=[None,'legacy']
            mixer.Mix_FadeInMusic.return_value=0
            backend=MixerAudio(mixer,root)
            backend.music('boss_frozen')
            backend.music('boss_frozen')
            self.assertEqual([args.args[0].decode() for args in mixer.Mix_LoadMUS.call_args_list],
                             [str(candidate),str(root/'bgm'/'boss.wav')])
            self.assertEqual(backend.failures,[candidate])
            backend.close()
            mixer.Mix_FreeMusic.assert_called_once_with('legacy')

    def test_missing_and_corrupt_chapter_sfx_use_shared_chunk(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root/'combat_sfx'/'forest'/'queen_fire.wav'
            bad.parent.mkdir(parents=True)
            bad.write_bytes(b'bad')
            mixer = Mock()
            mixer.Mix_LoadWAV.side_effect = lambda path: None if path.decode()==str(bad) else path
            mixer.Mix_Playing.return_value = 0
            mixer.Mix_PlayChannel.return_value = 0
            backend = MixerAudio(mixer,root)
            common = str(root/'sfx'/'queen_fire.wav').encode()
            for key in ('royal/queen_fire','forest/queen_fire','forest/queen_fire'):
                self.assertTrue(backend.sound(key,0))
                mixer.Mix_PlayChannel.assert_called_with(0,common,0)
            self.assertEqual(backend.failures,[bad])
            backend.close()
            self.assertEqual(sum(call.args==(common,) for call in mixer.Mix_FreeChunk.call_args_list),1)

    def test_single_cue_gains_and_mixed_voice_headroom_preserve_ui(self):
        mixer = Mock()
        mixer.Mix_LoadWAV.side_effect = lambda path: path
        active = set()
        mixer.Mix_Playing.side_effect = lambda channel: int(channel in active)
        mixer.Mix_PlayChannel.side_effect = lambda channel,chunk,loops: (active.add(channel) or channel)
        mixer.Mix_HaltChannel.side_effect = lambda channel: active.clear() if channel==-1 else active.discard(channel)
        backend = MixerAudio(mixer)
        loaded_gains = {Path(path.decode()).stem:gain for path,gain in
                        (call.args for call in mixer.Mix_VolumeChunk.call_args_list)}
        self.assertEqual([loaded_gains[name] for name in
                          ('player_swing','player_hit','parry_perfect','ui_select')],[32,41,36,23])
        backend.volume(100,100)
        self.assertTrue(backend.sound('ui_select',0))
        self.assertEqual(backend.channel_volumes[0],128)
        names = ('player_hit','parry_perfect','player_hurt','rook_impact',
                 'forest/bishop_cast','frozen/queen_fire','gothic/king_pulse')
        for channel,cue in enumerate(names,1):
            self.assertTrue(backend.sound(cue,channel))
        self.assertEqual(backend.channel_volumes[0],58)  # Previous eight-voice limit at full BGM.
        self.assertLess(backend.channel_volumes[1],58)
        weighted = 23*backend.channel_volumes[0] + sum(
            gain*backend.channel_volumes[channel]
            for channel,gain in enumerate((41,36,32,32,32,32,32),1))
        self.assertLessEqual(.61*90/128 + .82*weighted/128**2,.97)
        backend.volume(100,0)
        self.assertEqual(set(backend.channel_volumes.values()),{0})
        backend.close()

    def test_renewed_combat_effects_have_distinct_valid_pcm_masters(self):
        import wave
        from array import array
        folder = ROOT/'combat_sfx'
        rows = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))['files']
        self.assertEqual({row['file'] for row in rows},{cue+'.wav' for cue in (*RENEWED_CUES,*THEMED_SFX)})
        hashes = set()
        for row in rows:
            path = folder/row['file']
            digest = sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest,row['sha256'],path)
            hashes.add(digest)
            with wave.open(str(path),'rb') as audio:
                self.assertEqual((audio.getnchannels(),audio.getsampwidth(),audio.getframerate()),(2,2,44100))
                self.assertEqual(audio.getnframes()/44100,row['duration_s'])
                pcm = array('h')
                pcm.frombytes(audio.readframes(audio.getnframes()))
                if sys.byteorder!='little':
                    pcm.byteswap()
            self.assertEqual(tuple(pcm[-2:]),(0,0))
            self.assertLessEqual(max(map(abs,pcm))/32768,.82)
        self.assertEqual(len(hashes),53)

    def test_renewal_masters_and_existing_wavs_match_their_manifests(self):
        sources = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))['files']
        self.assertEqual(len(sources),43)
        renewal=ROOT/'renewal'
        masters=json.loads((renewal/'manifest.json').read_text(encoding='utf-8'))['files']
        self.assertEqual({Path(row['file']).stem for row in masters},set(BGM_PLAYLIST[1:-1]))
        for row in masters:
            self.assertEqual((row['sample_rate'],row['channels']),(44100,2))
            self.assertLess(row['peak_dbfs'],-3)
            self.assertLess(row['seam_step_dbfs'],-34)
        for root,entries in ((ROOT,sources),(renewal,masters)):
            for row in entries:
                data=(root/row['file']).read_bytes()
                self.assertEqual(sha256(data).hexdigest(),row['sha256'],row['file'])

    def test_native_mixer_all_assets(self):
        result = subprocess.run([sys.executable,'tools/audio_review.py','--verify'],
                                cwd=Path(__file__).resolve().parents[1],capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
