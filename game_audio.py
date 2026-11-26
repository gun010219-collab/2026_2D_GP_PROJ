"""Session-scoped audio driven by the same presentation batch as the renderer."""
from dataclasses import dataclass
from pathlib import Path

from combat_vfx import cue_name
from config import MOTION_SECONDS, cell_center

ROOT = Path(__file__).resolve().parent / 'assets' / 'audio'
TRACKS = ('menu', 'royal', 'forest', 'frozen', 'caldera', 'gothic', 'boss', 'ending')
BOSS_TRACKS = tuple(f'boss_{name}' for name in TRACKS[1:6])
BGM_PLAYLIST = ('menu', *(name for pair in zip(TRACKS[1:6],BOSS_TRACKS) for name in pair), 'ending')
SFX_CHAPTERS = TRACKS[1:6]
THEMED_CUES = ('bishop_charge', 'bishop_cast', 'queen_charge', 'queen_fire',
               'king_melee_charge', 'king_strike', 'king_charge', 'king_pulse')
RENEWED_CUES = ('player_swing', 'player_hit', 'player_hurt', 'parry_normal', 'parry_perfect',
                'parry_failed', 'pawn_thrust', 'rook_strike', 'rook_impact', 'knight_strike',
                'knight_land', 'enemy_death', 'boss_death')
THEMED_SFX = tuple(f'{chapter}/{cue}' for chapter in SFX_CHAPTERS for cue in THEMED_CUES)
VOICES = 8
# Source WAVs are peak-normalized. Trim individual voices to leave mix headroom.
CHUNK_GAIN = 23
COMBAT_CHUNK_GAIN = 32
COMBAT_GAIN_OVERRIDES = {'player_hit': 41, 'parry_perfect': 36}
UI_CUES = frozenset(('ui_select','upgrade_select','stage_clear','boss_clear',
                     'chapter_enter','restart','game_over'))
MUSIC_GAIN = 90
# Source peak bounds used for SDL's integer mixer at maximum slider gain.
SFX_PEAK_LIMIT = .82
BGM_PEAK_LIMIT = .61
MIX_PEAK_LIMIT = .97
PRIORITIES = {
    **dict.fromkeys(('player_move','ui_select','rook_move','king_move','pawn_charge',
                     'knight_charge','king_melee_charge'), 1),
    **dict.fromkeys(('player_swing','pawn_thrust','rook_charge','rook_strike','rook_impact',
                     'knight_strike','knight_land','bishop_charge','queen_charge','parry_failed'), 2),
    **dict.fromkeys(('bishop_cast','queen_fire','king_strike','enemy_death','upgrade_select',
                     'stage_clear','chapter_enter','restart'), 3),
    **dict.fromkeys(('player_hit','player_hurt','parry_normal','king_charge'), 4),
    **dict.fromkeys(('parry_perfect','king_pulse','boss_death','player_death','boss_clear','game_over'), 5),
}
TERMINAL = {'UPGRADE':'stage_clear', 'STAGE_CLEAR':'stage_clear',
            'BOSS_CLEAR':'boss_clear', 'GAME_OVER':'game_over'}


def chunk_gain(cue):
    if cue in UI_CUES:
        return CHUNK_GAIN
    return COMBAT_GAIN_OVERRIDES.get(cue,COMBAT_CHUNK_GAIN)


@dataclass
class AudioSettings:
    bgm: int = 45
    sfx: int = 75
    bgm_mute: bool = False
    sfx_mute: bool = False

    def gains(self):
        return (0 if self.bgm_mute else self.bgm, 0 if self.sfx_mute else self.sfx)


class AudioManager:
    def __init__(self, backend, settings):
        self.backend, self.settings = backend, settings
        self.chapter_sound = getattr(backend,'sound_in_chapter',None)
        self.scope = self.track = self.state = self.gains = None
        self.tick = -1
        self.seen = set()
        self.arrivals = {}
        self.channels = {}
        self.age = 0.
        self.actor_kinds = {}

    def apply_settings(self):
        gains = self.settings.gains()
        if self.gains != gains:
            self.gains = gains
            self.backend.volume(*gains)

    def play(self, cue, *, chapter=None):
        self.apply_settings()
        if not self.gains[1]:
            return
        priority = PRIORITIES[cue.rsplit('/',1)[-1]]
        busy = {ch for ch in self.channels if self.backend.playing(ch)}
        if priority < 3 and sum(self.channels[ch] < 3 for ch in busy) >= 4:
            return
        slot = next((ch for ch in range(VOICES) if ch not in busy), None)
        if slot is None:
            slot = min(busy, key=lambda ch: (self.channels[ch],ch))
            if self.channels[slot] >= priority:
                return
        if chapter is not None and self.chapter_sound is not None:
            played = self.chapter_sound(cue,slot,chapter)
        else:
            played = self.backend.sound(cue,slot)
        if played:
            self.channels[slot] = priority

    def set_music(self, track):
        self.apply_settings()
        if track != self.track:
            self.track = track
            self.backend.music(track)

    def update(self, game, elapsed, batch, *, motion=None, paused=False, ui=()):
        scope = game.combat.combat_session_id, game.combat.stage_instance_id
        if self.scope != scope:
            self.backend.clear_voices()
            self.channels.clear()
            self.arrivals.clear()
            self.seen.clear()
            self.scope, self.state, self.tick, self.age = scope, None, -1, 0.
            self.actor_kinds = {e.entity_instance_id:e.kind for e in game.encounter.enemies}
            self.actor_kinds[game.player.entity_instance_id] = 'player'
        elif not paused and 0 <= elapsed <= .15:
            self.age += elapsed

        state = game.state.value
        music = None if state in ('BOSS_CLEAR','GAME_OVER') else (
            BOSS_TRACKS[game.chapter-1] if game.stage_number % 5 == 0 else TRACKS[game.chapter])
        self.set_music(music)
        for event in batch:
            if event.cause_key[:2] != scope or event.tick < self.tick:
                continue
            if event.tick > self.tick:
                self.tick = event.tick
                self.seen.clear()
            if event.key in self.seen:
                continue
            self.seen.add(event.key)
            kind = self.actor_kinds.get(event.subject)
            if kind is None:
                continue
            if event.kind == 'move':
                cue = kind + '_move'
            elif event.kind == 'parry_failed':
                cue = 'parry_failed'
            elif kind == 'king' and event.kind == 'telegraph' and event.payload.attack_kind != 'king_pulse':
                cue = 'king_melee_charge'
            else:
                cue = cue_name(event,kind)
            if event.kind == 'attack_move' and cue:
                remaining = max(0., MOTION_SECONDS - (game.combat.tick-event.tick)/60)
                self.arrivals[event.key] = event, cue, self.age + remaining
            elif cue in PRIORITIES:
                chapter = SFX_CHAPTERS[game.chapter-1] if cue in THEMED_CUES else None
                self.play(cue,chapter=chapter)
        if self.arrivals and not paused:
            actors = {e.entity_instance_id:e for e in game.encounter.enemies}
            for key,(event,cue,deadline) in tuple(self.arrivals.items()):
                actor = actors.get(event.subject)
                if actor is not None and actor.active and actor.position == event.destination and motion is not None:
                    arrived = motion.ground_pose(actor)[0] == cell_center(*event.destination)
                else:
                    arrived = self.age >= deadline
                if arrived:
                    del self.arrivals[key]
                    self.play(cue)
        if state != self.state:
            self.state = state
            if state in TERMINAL:
                self.play(TERMINAL[state])
        for cue in ui:
            self.play(cue)

    def close(self):
        self.backend.close()
        self.arrivals.clear()
        self.channels.clear()


class MixerAudio:
    """Use Pico2D's SDL_mixer device and explicitly own its music and chunks."""
    def __init__(self, mixer, root=ROOT):
        self.mix = mixer
        self.root = root
        self.sounds = {}
        self.replacements = {}
        self.tracks = {}
        self.track_paths = {}
        self.failures = []
        self.closed = False
        self.music_volume = self.sfx_volume = 128
        self.channel_volumes = {}
        self.voice_cues = {}
        mixer.Mix_AllocateChannels(VOICES)
        for cue in PRIORITIES:
            path = self.root/'sfx'/(cue+'.wav')
            self.sounds[cue] = self._load_sound(path,cue)

    def _load_sound(self, path, cue):
        handle = self.mix.Mix_LoadWAV(str(path).encode('utf-8'))
        if handle:
            self.mix.Mix_VolumeChunk(handle,chunk_gain(cue))
        else:
            self.failures.append(path)
        return handle

    @classmethod
    def open(cls, canvas):
        if getattr(canvas,'audio_on',False) is not True:
            return None
        import ctypes
        from sdl2 import sdlmixer
        if not sdlmixer.Mix_QuerySpec(ctypes.byref(ctypes.c_int()),
                                     ctypes.byref(ctypes.c_uint16()),ctypes.byref(ctypes.c_int())):
            return None
        return cls(sdlmixer)

    def volume(self, bgm, sfx):
        old_music_volume = self.music_volume
        self.music_volume = round(MUSIC_GAIN*bgm/100)
        self.sfx_volume = round(128*sfx/100)
        if self.music_volume < old_music_volume:
            self.mix.Mix_VolumeMusic(self.music_volume)
        self._apply_mix_headroom(self._playing_cues())
        if self.music_volume >= old_music_volume:
            self.mix.Mix_VolumeMusic(self.music_volume)

    def _playing_cues(self):
        return {channel:cue for channel,cue in self.voice_cues.items() if self.playing(channel)}

    def _apply_mix_headroom(self, voices):
        if not voices:
            return
        budget = (MIX_PEAK_LIMIT - BGM_PEAK_LIMIT*self.music_volume/128)*128**2/SFX_PEAK_LIMIT
        ui_count = sum(cue in UI_CUES for cue in voices.values())
        # Reserve the same UI gain as before the combat boost for this voice count.
        ui_volume = min(self.sfx_volume,int(budget/(len(voices)*CHUNK_GAIN)))
        combat_budget = budget - ui_count*CHUNK_GAIN*ui_volume
        combat_gain = sum(chunk_gain(cue) for cue in voices.values() if cue not in UI_CUES)
        combat_volume = min(self.sfx_volume,int(combat_budget/max(1,combat_gain)))
        for channel,cue in voices.items():
            volume = ui_volume if cue in UI_CUES else combat_volume
            if volume != self.channel_volumes.get(channel):
                self.mix.Mix_Volume(channel,volume)
                self.channel_volumes[channel] = volume

    def playing(self, channel):
        return bool(self.mix.Mix_Playing(channel))

    def sound_in_chapter(self, cue, channel, chapter):
        return self.sound(f'{chapter}/{cue}',channel)

    def sound(self, cue, channel):
        base = cue.rsplit('/',1)[-1]
        if cue in THEMED_SFX or cue in RENEWED_CUES:
            if cue not in self.replacements:
                path = self.root/'combat_sfx'/(cue+'.wav')
                self.replacements[cue] = self._load_sound(path,base) if path.is_file() else None
            handle = self.replacements[cue] or self.sounds[base]
        else:
            handle = self.sounds[base]
        if not handle:
            return False
        voices = self._playing_cues()
        if channel in voices:
            self.mix.Mix_HaltChannel(channel)
        voices[channel] = base
        self._apply_mix_headroom(voices)
        if self.mix.Mix_PlayChannel(channel,handle,0) != channel:
            return False
        self.voice_cues[channel] = base
        return True

    def music(self, track):
        self.mix.Mix_HaltMusic()
        if track is None:
            return
        if track not in self.tracks:
            legacy = 'boss' if track in BOSS_TRACKS else track
            path = self.root/'bgm'/(legacy+'.wav')
            handle = None
            if track in TRACKS[1:6] or track in BOSS_TRACKS:
                candidate = self.root/'renewal'/(track+'.ogg')
                if candidate.is_file():
                    handle = self.mix.Mix_LoadMUS(str(candidate).encode('utf-8'))
                    if handle:
                        path = candidate
                    else:
                        self.failures.append(candidate)
            if not handle:
                handle = self.mix.Mix_LoadMUS(str(path).encode('utf-8'))
                if not handle:
                    self.failures.append(path)
            self.tracks[track] = handle
            self.track_paths[track] = path
        handle = self.tracks[track]
        if handle and self.mix.Mix_FadeInMusic(handle,-1,180) != 0:
            self.failures.append(self.track_paths[track])

    def clear_voices(self):
        self.mix.Mix_HaltChannel(-1)
        self.voice_cues.clear()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.clear_voices()
        self.mix.Mix_HaltMusic()
        for chunk in (*self.sounds.values(), *self.replacements.values()):
            if chunk:
                self.mix.Mix_FreeChunk(chunk)
        for track in self.tracks.values():
            if track:
                self.mix.Mix_FreeMusic(track)
        self.sounds.clear()
        self.replacements.clear()
        self.tracks.clear()
        self.track_paths.clear()
