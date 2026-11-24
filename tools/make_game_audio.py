"""Render original CHECKMATE WAVs and an auditable manifest with Python stdlib."""
from array import array
from hashlib import sha256
import json
from math import exp, log10, sin, tau
from pathlib import Path
from random import Random
import sys
import wave

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from game_audio import PRIORITIES

RATE = 22050
SEED = 510925
# Duration, falling/ascending partials, noise, low body and rhythmic attack count.
SFX = {
    'player_move': (.116, (595,270), .54, 102, 2),
    'player_swing': (.208, (1110,655,303), .96, 122, 1),
    'player_hit': (.23, (1317,2136,3341), .63, 91, 1),
    'player_hurt': (.31, (315,192,607), .68, 61, 1),
    'parry_normal': (.29, (1567,2231,3658), .27, 210, 1),
    'parry_perfect': (.72, (1047,1568,2093,3143), .34, 53, 2),
    'parry_failed': (.23, (493,319,178), .19, 0, 1),
    'player_death': (.77, (418,282,167), .36, 48, 3),
    'pawn_charge': (.151, (722,941), .37, 154, 1),
    'pawn_thrust': (.172, (910,457,1380), .69, 129, 1),
    'rook_charge': (.42, (152,227,287), .66, 72, 2),
    'rook_move': (.22, (109,198,351), .55, 52, 1),
    'rook_strike': (.24, (202,329,404), .86, 65, 1),
    'rook_impact': (.36, (213,126,332), .70, 41, 1),
    'knight_charge': (.186, (390,568), .52, 133, 1),
    'knight_strike': (.24, (380,693,1080), .74, 82, 2),
    'knight_land': (.29, (174,327,561), .69, 65, 2),
    'bishop_charge': (.48, (350,523,784), .16, 118, 2),
    'bishop_cast': (.58, (521,783,1241,1568), .33, 147, 3),
    'queen_charge': (.65, (277,555,830,1109), .11, 121, 3),
    'queen_fire': (.51, (880,1761,2303), .78, 96, 1),
    'king_move': (.30, (86,133,281), .59, 39, 2),
    'king_melee_charge': (.36, (128,201,434), .49, 54, 2),
    'king_charge': (.84, (137,208,415,828), .24, 40, 3),
    'king_strike': (.41, (171,245,397), .88, 36, 2),
    'king_pulse': (.85, (92,139,221,376), .61, 32, 2),
    'boss_death': (1.23, (89,177,318,490), .76, 29, 4),
    'enemy_death': (.48, (226,356,618), .48, 63, 2),
    'ui_select': (.106, (830,1245), .04, 0, 1),
    'upgrade_select': (.39, (523,659,784), .07, 131, 3),
    'stage_clear': (.67, (523,659,784,1047), .05, 131, 4),
    'boss_clear': (1.15, (392,523,659,784), .10, 65, 4),
    'game_over': (.95, (440,349,233,147), .14, 54, 4),
    'chapter_enter': (.79, (392,587,740,880), .08, 110, 4),
    'restart': (.37, (277,415,554), .10, 88, 3),
}

# Original 16-bar loops. Modes share a rhythmic vocabulary and a returning
# motif but have their own key, progression, orchestration and accompaniment.
TRACKS = {
    'menu':    (82,  (0,2,3,5,7,9,10), 57, (0,5,2,4,0,3,5,4), (0,4,6,3,2,4,1,0), 'bell','strings','soft'),
    'royal':   (107, (0,2,4,5,7,9,11), 55, (0,3,5,4,0,1,3,4), (0,2,4,7,6,4,3,2), 'brass','strings','march'),
    'forest':  (96,  (0,2,3,5,7,9,10), 62, (0,1,5,3,0,6,3,4), (4,2,0,1,3,4,6,5), 'wood','pluck','soft'),
    'frozen':  (88,  (0,2,3,5,7,8,11), 60, (0,5,2,4,0,3,1,4), (0,6,5,2,4,1,0,2), 'bell','bow','glass'),
    'caldera': (123, (0,1,3,5,7,8,10), 52, (0,1,0,4,0,5,1,6), (0,1,4,3,0,6,5,4), 'brass','reed','heavy'),
    'gothic':  (101, (0,2,3,5,7,8,11), 55, (0,5,3,4,1,5,0,4), (4,3,6,7,5,4,2,1), 'organ','bow','march'),
    'boss':    (148, (0,1,3,5,6,8,11), 51, (0,1,0,5,3,1,6,4), (0,4,1,6,3,7,5,4), 'brass','organ','heavy'),
    'ending':  (76,  (0,2,4,5,7,9,11), 57, (0,4,5,3,2,5,3,4), (2,4,7,6,4,3,2,0), 'wood','strings','glass'),
}
TIMBRES = {
    'bell': (1,.27,.11,.16,.07), 'wood': (1,.1,.23,.03,.04),
    'brass': (1,.68,.33,.21,.12), 'strings': (1,.43,.31,.14,.1),
    'pluck': (1,.39,.11,.06,.03), 'bow': (1,.36,.24,.1,.17),
    'reed': (1,.11,.73,.05,.16), 'organ': (1,.5,.26,.38,.12),
}


def sfx(name, recipe):
    duration,partials,noise,body,beats = recipe
    rng = Random(SEED+sum(map(ord,name)))
    length = round(duration*RATE)
    notes = name in ('upgrade_select','stage_clear','boss_clear','chapter_enter','restart','game_over')
    result = array('f')
    low = 0.
    for i in range(length):
        t = i/RATE
        u = t/duration
        raw = rng.uniform(-1,1)
        low += .16*(raw-low)
        attack = min(1.,t/.003)
        release = min(1.,(1-u)*12)
        pulse = (u*beats)%1
        if notes:
            offset = min(len(partials)-1,int(u*beats))
            chord = partials[offset]
            ring = (sin(tau*chord*t)+.24*sin(tau*chord*2*t))*exp(-2.2*pulse)
        else:
            upward = name.endswith('charge') or name=='parry_perfect'
            glide = t*(.80 + .26*u if upward else 1.09-.32*u)
            ring = sum(sin(tau*f*glide + .12*sin(43*t))/((j+1)**.9)
                       for j,f in enumerate(partials))*exp(-3.6*u)
        wash = noise*(.55*(raw-low)+.8*low)*exp(-5.8*pulse-2*u)
        bass = .72*sin(tau*body*t*(1-.31*u))*exp(-8.7*u) if body else 0
        if name=='parry_perfect':
            ring += .34*sin(tau*784*t)*exp(-2.4*u)
            bass *= 1.6
        result.append((.55*ring+wash+bass)*attack*release)
    level = .67 if PRIORITIES[name]>=4 else .34 if PRIORITIES[name]==1 else .50
    return result,level


def note(buffer, start, length, midi, gain, timbre):
    length = int(length*RATE)
    offset = int(start*RATE)
    hz = 440*2**((midi-69)/12)
    harmonics = TIMBRES[timbre]
    attack = .044 if timbre in ('brass','strings','bow') else .009
    tail = .14 if timbre in ('bell','strings','bow') else .065
    for i in range(length):
        t = i/RATE
        release = min(1.,(length-i)/(tail*RATE))
        env = min(1.,t/attack)*release
        if timbre in ('bell','pluck','wood'):
            env *= exp(-2.7*i/length)
        phase = tau*hz*t + .15*sin(tau*4.8*t)
        value = sum(a*sin((j+1)*phase*(1+j*.003 if timbre=='bell' else 1))
                    for j,a in enumerate(harmonics))
        buffer[(offset+i)%len(buffer)] += value*env*gain


def percussion(buffer, start, gain, rng, voice):
    offset = int(start*RATE)
    duration = .22 if voice=='low' else .11
    low = 0.
    for i in range(int(duration*RATE)):
        t = i/RATE
        raw = rng.uniform(-1,1)
        low += .16*(raw-low)
        value = (.82*sin(tau*t*(90-198*t))+.18*low if voice=='low'
                 else .68*(raw-low)+.38*sin(tau*172*t))
        buffer[(offset+i)%len(buffer)] += value*gain*min(1,t/.005)*exp(-5*t/duration)


def music(name, recipe):
    bpm, scale, root, progression, motif, lead, backing, drums = recipe
    beat = 60/bpm
    buffer = array('f',[0.]) * round(64*beat*RATE)
    rng = Random(SEED+bpm)
    def pitch(degree):
        octave,index = divmod(degree,len(scale))
        return root+12*octave+scale[index]

    for bar in range(16):
        at = 4*beat*bar
        chord = progression[bar%8]
        accent = bar//4
        pad = (.052,.041,.059,.047)[accent]
        for degree in (chord-7,chord+2,chord+4):
            note(buffer,at,beat*(3.92 if name not in ('caldera','boss') else 2.9),pitch(degree),pad,backing)
        for k in (0,2,3.5):
            divisor = 1 if k==0 else 2
            note(buffer,at+k*beat,beat*(1.65 if k==0 else .43),pitch(chord-14+(4 if k==2 else 0)),
                 .09/divisor,'organ' if name in ('boss','gothic') else 'wood')
        if bar%4!=3 or bar>=8:
            for k in range(4 if accent!=2 else 6):
                phrase = motif[(2*bar+k)%8]
                degree = phrase+7 if accent>=2 else phrase
                if k==0 or k==3:
                    degree = chord+(7 if accent>=2 else 0)+(2 if k else 0)
                when = (0,.75,1.5,2.5,3,3.5)[k]
                hold = (.65,.47,.72,.99,.36,.36)[k]
                note(buffer,at+when*beat,hold*beat,pitch(degree),.058 if accent!=1 else .048,lead)
                if name in ('frozen','menu','ending'):
                    note(buffer,at+(when+.37)*beat,hold*beat,pitch(degree),.018,lead)
        for step in (0,1.5,2,3.5):
            if step in (0,2) or drums in ('heavy','march'):
                percussion(buffer,at+step*beat,.10 if drums in ('march','heavy') else .034,
                           rng,'low' if step in (0,2) else 'high')
        if drums=='glass':
            note(buffer,at+3.5*beat,.65*beat,pitch(chord+11),.028,'bell')
    return buffer,.56


def save(root, folder, name, recipe, renderer):
    path = root/folder/(name+'.wav')
    path.parent.mkdir(parents=True,exist_ok=True)
    samples,level = renderer(name,recipe)
    peak = max(map(abs,samples))
    gain = 32767*level/peak
    pcm = array('h',(round(x*gain) for x in samples))
    if sys.byteorder!='little':
        pcm.byteswap()
    with wave.open(str(path),'wb') as stream:
        stream.setparams((1,2,RATE,len(pcm),'NONE','not compressed'))
        stream.writeframes(pcm.tobytes())
    return dict(file=f'{folder}/{path.name}', duration_s=round(len(pcm)/RATE,6),
                format='WAV PCM16 mono 22050 Hz', sha256=sha256(path.read_bytes()).hexdigest(),
                peak_dbfs=round(20*log10(level),2), parameters=recipe)


def render(root):
    assert SFX.keys()==PRIORITIES.keys()
    files = [save(root,'sfx',n,r,sfx) for n,r in sorted(SFX.items())]
    files += [save(root,'bgm',n,r,music) for n,r in TRACKS.items()]
    manifest = dict(creator='CHECKMATE project / Codex', source='tools/make_game_audio.py',
                    rights='Original project-generated synthesis, no third-party samples or compositions. '
                           'May be used and redistributed with the CHECKMATE game and exhibition builds.',
                    changes='Synthesized, dry-mixed and peak-normalized from original note and SFX recipes.',
                    seed=SEED, files=files)
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=PROJECT/'assets'/'audio')
    render(parser.parse_args().output)
