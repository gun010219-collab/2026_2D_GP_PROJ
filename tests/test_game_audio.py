from dataclasses import asdict
import os
import pickle
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from game_audio import AudioManager, AudioSettings, MixerAudio, VOICES
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from settings_menu import AUDIO_ROWS, SETTINGS_BUTTON, SettingsMenu
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
        for stage in (1,2,4,5,6,11,16,21):
            self.audio.update(_new_stage_game(stage),0,())
        tracks = [call[1] for call in self.backend.calls if call[0]=='music']
        self.assertEqual(tracks,['royal','boss','forest','frozen','caldera','gothic'])
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
        backend = MixerAudio(mixer)
        self.assertFalse(backend.sound('player_swing',0))
        backend.music('royal')
        mixer.Mix_FadeInMusic.assert_not_called()
        self.assertEqual(len(backend.failures),len(backend.sounds)+1)
        backend.close()
        backend.close()
        mixer.Mix_FreeMusic.assert_not_called()
        mixer.Mix_FreeChunk.assert_not_called()

    def test_native_mixer_all_wavs(self):
        result = subprocess.run([sys.executable,'tools/audio_review.py','--verify'],
                                cwd=Path(__file__).resolve().parents[1],capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
