"""Render the original 44.1 kHz stereo combat effects offline (NumPy)."""
import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
import wave

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game_audio import RENEWED_CUES, SFX_PEAK_LIMIT, THEMED_SFX

RATE = 44100
SEED = 7413
STEEL = (980, 1487, 2221, 3389, 4913, 6831)


class Foley:
    def __init__(self, duration, rng):
        self.samples = np.zeros(round(duration*RATE))
        self.rng = rng

    def add(self, layer, start, gain):
        offset = round(start*RATE)
        length = min(len(layer), len(self.samples)-offset)
        self.samples[offset:offset+length] += layer[:length]*gain

    def air(self, start, length, low, high, gain, *, attack=.006, decay=.09, sweep=0):
        size = round(length*RATE)
        t = np.arange(size)/RATE
        frequency = np.fft.rfftfreq(size, 1/RATE)
        source = np.fft.rfft(self.rng.standard_normal(size))
        band = 1/(1+(low/np.maximum(frequency, 1))**6)/(1+(frequency/high)**6)
        layer = np.fft.irfft(source*band, n=size)
        layer /= max(np.sqrt(np.mean(layer**2)), 1e-8)
        if sweep:
            # Mix a darker band against the brighter one as the weapon passes.
            dark = np.fft.irfft(source*band/(1+(frequency/(high*.29))**6), n=size)
            dark /= max(np.sqrt(np.mean(dark**2)), 1e-8)
            travel = np.linspace(0, 1, size)
            if sweep < 0:
                travel = 1-travel
            layer = dark*(1-travel)+layer*travel
        envelope = (1-np.exp(-t/attack))*np.exp(-t/decay)*np.minimum((length-t)/.024, 1)
        self.add(layer*envelope, start, gain)

    def ring(self, start, length, modes, gain, *, decay=.13, bend=0):
        t = np.arange(round(length*RATE))/RATE
        bend_time = .037
        phase = t+bend*bend_time*(1-np.exp(-t/bend_time))
        layer = np.zeros_like(t)
        for index, hz in enumerate(modes):
            lifetime = decay/(1+.23*index)
            layer += np.sin(2*np.pi*hz*phase)*np.exp(-t/lifetime)/(1+.45*index)
        edge = np.minimum(t/.0015, 1)*np.minimum((length-t)/.022, 1)
        self.add(layer*edge, start, gain)

    def impact(self, start, pitch, gain, *, length=.32):
        self.air(start, length, 42, 570, gain*.56, attack=.002, decay=.074)
        self.air(start, .065, 510, 4900, gain*.31, attack=.001, decay=.016)
        self.ring(start, length, (pitch, pitch*1.62, pitch*2.73), gain*.83, decay=.08, bend=.43)

    def debris(self, start, count, spread, low, high, gain):
        times = start + self.rng.uniform(0, spread, count)
        for when in sorted(times):
            self.air(when, .038, low, high, gain*self.rng.uniform(.4, 1.2),
                     attack=.001, decay=.007)


SWIPES = {
    'player_swing': (.24, 510, 5200, .23, 1, 390),
    'pawn_thrust': (.19, 730, 7400, .14, 1, 870),
    'rook_strike': (.39, 125, 3200, .23, -1, 122),
    'knight_strike': (.30, 300, 4400, .28, 1, 210),
}
# Duration, weight, ringing material and the amount of debris.
CONTACTS = {
    'player_hit': (.28, 118, .71, (837, 1391, 2197, 3663), .31, 4),
    'player_hurt': (.32, 70, .69, (237, 436, 691), .27, 3),
    'parry_normal': (.34, 126, .63, STEEL, .63, 2),
    'parry_perfect': (.62, 92, SFX_PEAK_LIMIT, STEEL, .90, 6),
    'parry_failed': (.27, 103, .52, (452, 717, 1334), .35, 3),
    'rook_impact': (.46, 48, .76, (156, 325, 541, 1017), .50, 11),
    'knight_land': (.40, 65, .70, (207, 398, 581), .33, 7),
    'enemy_death': (.54, 57, .68, (181, 277, 526, 783), .35, 9),
    'boss_death': (.95, 43, .78, (92, 167, 351, 562), .51, 15),
}


def common(cue, rng):
    if cue in SWIPES:
        length, low, high, attack, direction, resonance = SWIPES[cue]
        sound = Foley(length, rng)
        sound.air(0, length, low, high, .77, attack=length*attack,
                  decay=length*.69, sweep=direction)
        sound.air(.008, length*.68, low*.53, high*.54, .31, attack=.016, decay=.095)
        sound.ring(.025, length*.54, (resonance, resonance*2.71), .18, decay=.045, bend=.12)
        if cue == 'rook_strike':
            sound.impact(.021, 58, .36, length=.26)
        return sound.samples, .66

    length, pitch, peak, modes, metal, debris = CONTACTS[cue]
    sound = Foley(length, rng)
    sound.impact(0, pitch, 1, length=length*.80)
    sound.ring(.003, length*.93, modes, metal, decay=length*.31, bend=.02)
    sound.debris(.027, debris, length*.53, 390, 6220, .13)
    if cue == 'player_hit':
        sound.ring(0, .18, (54, 89, 136), .87, decay=.062, bend=.15)
        sound.ring(.001, .09, (1923, 3161, 4879, 6547), .47, decay=.024, bend=.03)
        sound.air(0, .046, 1050, 8200, .52, attack=.00055, decay=.008)
    if cue == 'parry_perfect':
        sound.ring(.028, .56, (763, 1271, 2021, 3067), .49, decay=.21)
        sound.air(.019, .31, 900, 8900, .33, attack=.014, decay=.08)
        sound.impact(.042, 52, .47)
    if cue.endswith('_death') or cue in ('rook_impact', 'knight_land'):
        sound.impact(length*.32, pitch*.84, .43, length=length*.42)
    return sound.samples, peak


@dataclass(frozen=True)
class Material:
    modes: tuple
    wind_band: tuple
    weight: float
    resonance: float
    grit: int
    echo: float


MATERIALS = {
    'royal': Material((578, 1019, 1553, 2303, 4139), (940, 7700), 83, .26, 3, .21),
    'forest': Material((332, 579, 932, 1471, 2191), (180, 3900), 57, .12, 13, .15),
    'frozen': Material((907, 1607, 2377, 3547, 5693), (1200, 9700), 62, .20, 16, .23),
    'caldera': Material((171, 259, 467, 917, 1409), (74, 3300), 49, .09, 22, .12),
    'gothic': Material((114, 173, 266, 443, 769), (135, 3200), 40, .24, 9, .25),
}


@dataclass(frozen=True)
class Gesture:
    duration: float
    peak: float
    charge: bool
    pitch: float
    weight: float
    air: float


GESTURES = {
    'bishop_charge': Gesture(.50, .55, True, 1.34, .20, .47),
    'bishop_cast': Gesture(.61, .68, False, 1.12, .47, .40),
    'queen_charge': Gesture(.64, .58, True, 1.60, .23, .69),
    'queen_fire': Gesture(.58, .74, False, 1.56, .54, .97),
    'king_melee_charge': Gesture(.46, .55, True, .74, .51, .39),
    'king_strike': Gesture(.55, .79, False, .86, 1, .48),
    'king_charge': Gesture(.82, .65, True, .64, .69, .55),
    'king_pulse': Gesture(.91, .80, False, .56, 1.12, .75),
}


def themed(chapter, cue, rng):
    material, gesture = MATERIALS[chapter], GESTURES[cue]
    length = gesture.duration
    sound = Foley(length, rng)
    low, high = material.wind_band
    modes = tuple(p*gesture.pitch for p in material.modes)
    body = material.weight*(.71+.29*gesture.pitch)
    if gesture.charge:
        sound.air(0, length, low, high, gesture.air,
                  attack=.078, decay=.52*length, sweep=1)
        for step, when in enumerate((.007, length*.29, length*.53)):
            scale = (1, 1.13, 1.28)[step]
            sound.ring(when, length-when, tuple(p*scale for p in modes[:4]), .35+step*.10,
                       decay=material.resonance*.68, bend=-.10)
        sound.impact(.009, body, gesture.weight, length=length*.55)
        sound.debris(length*.18, material.grit//2, length*.52, low, high, .14)
    else:
        sound.impact(0, body, gesture.weight, length=length*.69)
        sound.air(0, length*.89, low, high, gesture.air,
                  attack=.008, decay=length*.24, sweep=-1)
        sound.ring(.003, length*.95, modes, .68, decay=material.resonance, bend=.03)
        sound.debris(.028, material.grit, length*.52, low, high, .20)
        if cue == 'king_pulse':
            sound.impact(.108, body*.88, .68, length=length*.65)
            sound.air(.14, length*.80, low*.62, high*.73, .54,
                      attack=.042, decay=.21, sweep=-1)
        if cue == 'queen_fire':
            sound.ring(.025, length*.77, modes[1:], .40,
                       decay=material.resonance*1.22, bend=-.15)
    return sound.samples, gesture.peak, material.echo


def stereo(samples, echo):
    # Early reflections give space to the centered transient and survive mono downmix.
    output = np.repeat(samples[:, None], 2, axis=1)
    for channel, reflections in enumerate((((.012, .82), (.043, .37)), ((.017, .74), (.052, .32)))):
        for delay, gain in reflections:
            frames = round(delay*RATE)
            output[frames:, channel] += samples[:-frames]*echo*gain
    fade = round(.024*RATE)
    output[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return output


def render(output, cue=None):
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Render into an empty output directory')
    rows = []
    for index, name in enumerate((*RENEWED_CUES, *THEMED_SFX)):
        if cue is not None and name != cue:
            continue
        rng = np.random.default_rng(SEED+index)
        if '/' in name:
            samples, peak, echo = themed(*name.split('/'), rng)
        else:
            samples, peak = common(name, rng)
            echo = .10
        samples = stereo(samples, echo)
        if name == 'player_hit':
            # Round the loudest transient so the low impact stays audible at the same peak.
            samples = np.tanh(samples/(.8*np.max(np.abs(samples))))
        samples *= peak/np.max(np.abs(samples))
        pcm = np.round(samples*32767).astype('<i2')
        path = output/(name+'.wav')
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), 'wb') as wav:
            wav.setparams((2, 2, RATE, len(pcm), 'NONE', 'not compressed'))
            wav.writeframes(pcm.tobytes())
        rows.append(dict(file=name+'.wav', duration_s=len(pcm)/RATE,
                         peak_dbfs=round(float(20*np.log10(np.max(np.abs(pcm))/32768)), 2),
                         rms_dbfs=round(float(10*np.log10(np.mean((pcm/32768)**2))), 2),
                         sha256=sha256(path.read_bytes()).hexdigest()))
    manifest = dict(creator='CHECKMATE project / Codex', source='tools/render_combat_sfx.py',
                    rights='Original project synthesis. No third-party samples. May be used and redistributed with CHECKMATE.',
                    format='WAV PCM16 stereo 44100 Hz', files=rows)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cue', choices=(*RENEWED_CUES, *THEMED_SFX))
    args = parser.parse_args()
    render(args.output,args.cue)
