"""Original CHECKMATE scores. Write expanded General MIDI without runtime dependencies."""
from dataclasses import dataclass
from random import Random
from struct import pack

PPQ = 480
RATE = 44100
MAJOR = (0,2,4,5,7,9,11)
MINOR = (0,2,3,5,7,8,10)
DORIAN = (0,2,3,5,7,9,10)
PHRYGIAN = (0,1,3,5,7,8,10)
HARMONIC = (0,2,3,5,7,8,11)
LYDIAN = (0,2,4,6,7,9,11)


@dataclass(frozen=True)
class Score:
    title: str
    tempo: int
    beats: int
    tonic: int
    scale: tuple
    harmony: tuple
    phrase: tuple
    ensemble: tuple
    pulse: tuple
    hall: float
    lufs_goal: float  # Used as an RMS mixing reference, not an LUFS measurement.


# Degrees are zero-indexed. A dot leaves room for the accompaniment.
SCORES = {
    'royal': Score('Crown of Dawn',84,4,60,MAJOR,
        ((0,4,5,3,0,1,3,4),(5,2,3,0,1,5,3,4)),
        ('0:1 2:.5 4:.5 6:1 7:1','9:1 8:.5 7:.5 6:1 4:1','2:1 .:.5 4:.5 5:2','4:1 3:1 2:1 1:1',
         '0:1 4:1 7:1 9:1','8:1 7:1 6:1 4:1','5:2 2:1 1:1','0:2 .:2'),
        (60,48,42,52,46,14), (0,2.5), .66,-23),
    'boss_royal': Score('Judgment of the Crown',112,4,60,MINOR,
        ((0,5,3,4,0,5,1,4),(3,5,0,6,3,1,5,4)),
        ('0:.75 4:.75 7:1 6:.5 4:1','5:1 3:.5 2:.5 5:2','7:.5 6:.5 5:1 3:1 4:1','4:1 1:1 6:1 4:1',
         '7:1 8:.5 9:.5 7:1 6:1','5:.75 2:.75 5:.5 6:2','4:1 3:.5 2:.5 1:2','1:.5 2:.5 4:1 6:1 .:1'),
        (61,48,43,52,47,14), (0,1.5,2.5,3.5), .67,-21),
    'forest': Score('Where the Canopy Breathes',74,3,62,DORIAN,
        ((0,3,0,6,1,3,4,0),(3,1,6,0,3,5,6,0)),
        ('4:.5 6:.5 7:1 5:1','4:1 2:.5 .:.5 1:1','0:1 2:.5 4:.5 6:1','5:.5 4:.5 3:1 .:1',
         '2:.5 4:.5 7:.5 9:.5 8:1','7:1 5:.5 4:.5 2:1','1:1 3:1 4:.5 .:.5','0:2 .:1'),
        (73,49,42,48,46,71), (), .55,-24),
    'boss_forest': Score('The Antlered Sentinel',106,3,62,DORIAN,
        ((0,6,0,3,1,6,3,4),(5,3,0,6,5,1,3,4)),
        ('4:.5 5:.5 7:.75 5:.25 4:1','2:.5 1:.5 0:1 2:1','4:.5 6:.5 7:1 9:1','8:.5 7:.5 5:1 4:1',
         '2:.5 4:.5 5:.5 7:.5 9:1','8:.75 7:.25 6:.5 4:.5 5:1','4:1 3:.5 2:.5 1:1','1:.5 3:.5 4:1 .:1'),
        (73,49,42,None,46,68), (0,1.5,2.5), .50,-22),
    'frozen': Score('Crystal Ramparts',76,3,57,LYDIAN,
        ((0,2,4,1,0,5,1,4),(5,4,1,0,2,5,1,4)),
        ('7:1 9:.5 11:.5 10:1','8:1 .:.5 7:.5 6:1','5:.5 7:.5 9:1 6:1','4:1 3:1 .:1',
         '7:.5 10:.5 11:1 12:1','11:1 9:.5 7:.5 5:1','3:.75 2:.25 4:1 6:1','7:2 .:1'),
        (8,49,42,53,46,98), (), .84,-24),
    'boss_frozen': Score('Glass Throne at Midnight',98,4,57,HARMONIC,
        ((0,5,2,4,0,3,1,4),(2,6,0,5,3,1,5,4)),
        ('7:.5 8:.5 11:1 13:1 11:1','10:.75 9:.25 8:1 7:2','4:.5 5:.5 7:1 9:.5 8:.5 6:1','6:1 4:1 2:1 .:1',
         '7:1 10:1 12:.5 11:.5 9:1','8:.5 7:.5 6:1 9:1 7:1','5:1 4:.5 2:.5 3:1 1:1','6:2 4:1 .:1'),
        (9,48,42,52,45,14), (0,2.5,3.5), .81,-22),
    'caldera': Score('The Furnace Below',116,4,50,PHRYGIAN,
        ((0,1,0,5,0,6,1,0),(3,1,5,0,6,1,3,0)),
        ('0:.75 1:.75 4:.5 1:1 0:1','-1:1 0:.5 1:.5 3:1 1:1','0:.5 0:.5 4:.75 5:.25 3:1 1:1','0:2 .:2',
         '4:.75 5:.75 7:.5 5:1 4:1','3:1 1:.5 0:.5 -1:2','0:.5 1:.5 3:.5 4:.5 5:1 4:1','1:1 -1:1 0:1 .:1'),
        (61,48,43,None,47,57), (0,.75,1.5,2.5,3.25), .53,-22),
    'boss_caldera': Score('The Mountain Unchained',136,4,50,PHRYGIAN,
        ((0,1,0,3,5,1,0,6),(0,5,3,6,1,3,1,0)),
        ('0:.5 0:.25 1:.25 4:.75 5:.25 7:1 4:1','1:.5 3:.5 4:.5 5:.5 4:1 1:1','0:.5 -1:.5 0:.5 1:.5 4:2','3:1 5:1 4:1 1:1',
         '5:.75 7:.75 8:.5 7:1 5:1','4:1 3:.5 1:.5 0:1 -1:1','0:.5 1:.5 4:1 7:1 6:1','4:1 1:.5 0:.5 -1:1 .:1'),
        (61,48,43,52,47,57), (0,.5,1.25,2,2.75,3.5), .58,-20),
    'gothic': Score('Procession of Ash',86,4,55,HARMONIC,
        ((0,5,2,4,0,3,5,4),(5,2,6,0,1,3,5,4)),
        ('0:1 2:1 4:.75 6:.25 7:1','8:1 7:1 6:1 4:1','3:1 5:1 8:1 7:1','6:2 4:1 .:1',
         '9:1 8:.5 7:.5 6:2','5:1 7:1 6:.5 5:.5 3:1','2:1 4:1 1:1 6:1','0:2 .:2'),
        (52,48,42,53,19,14), (0,2.5), .86,-23),
    'boss_gothic': Score('Opera of the Last King',108,4,55,HARMONIC,
        ((0,5,2,4,0,1,3,4),(5,1,6,0,3,5,1,4)),
        ('0:.75 2:.75 4:.5 6:1 7:1','9:1 8:.5 7:.5 6:1 4:1','3:.5 5:.5 7:1 9:1 8:1','6:1 4:1 2:.5 4:.5 6:1',
         '9:.5 10:.5 11:1 13:1 11:1','9:1 8:.5 7:.5 6:1 5:1','4:1 7:1 8:.5 6:.5 5:1','4:1 1:1 6:1 .:1'),
        (52,48,43,53,61,14), (0,1.5,2.5,3.25), .90,-20),
}


def varlen(value):
    groups = [value & 127]
    while value > 127:
        value >>= 7
        groups.insert(0,128 | (value & 127))
    return bytes(groups)


def render_score(score, name, path):
    """Render two score iterations so the exported loop has a real reverb pre-roll."""
    rng = Random('checkmate-a4:'+name)
    stride = score.beats*32
    events = []
    boss = name.startswith('boss_')
    chapter = name.removeprefix('boss_')
    def event(beat, *message):
        events.append((round(beat*PPQ),bytes(message)))
    def note(ch, beat, n, length, velocity):
        if 0 <= n <= 127:
            start = round(beat*PPQ)+rng.randint(0,5)
            events.extend(((start,bytes((0x90|ch,n,max(1,min(127,velocity+rng.randint(-3,3)))))),
                           (start+max(1,round(length*PPQ)),bytes((0x80|ch,n,0)))))
    def pitch(degree):
        octave, scale_degree = divmod(degree,7)
        return score.tonic + octave*12 + score.scale[scale_degree]
    def chord(degree, below=0):
        return [pitch(degree+step)-below for step in (0,2,4)]
    event(0,255,81,3,*round(60_000_000/score.tempo).to_bytes(3,'big'))
    for channel, program in enumerate(score.ensemble):
        if program is not None:
            event(0,0xc0|channel,program)
            for setting,value in ((7,(96,72,92,72,74,72)[channel]),(10,(62,41,63,83,96,35)[channel]),
                                  (91,round(score.hall*(58,70,32,84,47,71)[channel])),(93,12 if channel in (1,3) else 0)):
                event(0,0xb0|channel,setting,value)
    event(0,0xc9,48)  # orchestral percussion kit
    event(0,0xb9,7,84)
    event(0,0xb9,91,round(score.hall*34))
    for bar in range(32):
        t = bar*score.beats
        section, index = divmod(bar,8)
        harmony = score.harmony[section==2]
        degree = harmony[index]
        root, third, fifth = chord(degree)
        energy = (67,74,82,71)[section]+(8 if boss else 0)
        if index in (0,4):
            energy += 4
        melody_time=0.
        for token in score.phrase[index].split():
            symbol,length = token.split(':')
            length = float(length)
            if symbol!='.':
                d=int(symbol)
                n=pitch(d)
                if chapter=='caldera':
                    n-=12
                sustain=length*(.92 if chapter in ('royal','forest','gothic') else .82)
                note(0,t+melody_time,n,sustain,energy+5)
                if chapter=='forest':
                    if index in (1,3,5,7) and melody_time+length==score.beats:
                        answer=third if index in (1,5) else fifth
                        note(5,t+melody_time+.14,answer-(12 if boss else 0),
                             score.beats-melody_time-.25,energy-(16 if boss else 19))
                elif section in (1,2) and melody_time in (0,2):
                    note(5,t+melody_time+.045,n-12 if n>=64 else n+12,min(1.85,sustain),energy-19)
            melody_time+=length
        if melody_time!=score.beats:
            raise ValueError((name,bar,melody_time))
        upper=pitch(degree+(6 if boss else 8)) if chapter=='forest' else root
        for i,n in enumerate((root-12,third-12,fifth-12,upper)):
            note(1,t+i*.045,n,score.beats-.19-i*.045,energy-(12 if i==3 else 16))
        bass_step=.5 if boss and chapter in ('caldera','frozen') else 1.
        if not boss and chapter in ('forest','frozen'):
            note(2,t,root-12,score.beats-.3,energy-27)
        else:
            for i in range(round(score.beats/bass_step)):
                b = i*bass_step
                bass=fifth if i in (3,6) or (chapter=='forest' and i==2) else root
                note(2,t+b,bass-24,bass_step*.79,energy+(3 if i==0 else -12))
        if score.ensemble[3] is not None and (section!=0 or chapter in ('gothic','royal') or boss):
            for i,n in enumerate((fifth-12,root,third)):
                note(3,t+.23+i*.035,n,score.beats-.42-i*.035,energy-(21 if section==2 else 27))
        if chapter in ('forest','frozen','royal') and not boss:
            notes=(root-12,fifth-12,root,third,fifth,third,root,fifth-12)
            for i in range(score.beats*2):
                if section!=0 or i%2==0:
                    note(4,t+i*.5,notes[i]+(12 if chapter=='frozen' else 0),.62,energy-21-i%3*3)
        elif chapter=='forest':
            for i,b in enumerate(score.pulse):
                harp_pitch=(root-12,fifth-12,upper)[i]
                note(4,t+b,harp_pitch,.54,energy-(17+i*4))
            if section in (1,2) or index%2==0:
                note(9,t,41,.22,energy-17)
        elif chapter!='gothic' or boss:
            for i,b in enumerate(score.pulse):
                percussion=(36,41,38,45,41,47)[i%6]
                note(9,t+b,percussion,.25,energy+(8 if i==0 else -6))
                if (i==0 and index%2==0) or (boss and chapter=='caldera' and i%2==0):
                    if score.ensemble[4]==47:
                        note(4,t+b,max(40,root-17),.6,energy+4)
        else:
            for n in (root-12,fifth-12,root):
                note(4,t+.1,n,score.beats-.28,energy-29)
        if index in (0,4) and chapter in ('royal','gothic','frozen'):
            note(5,t,root+(12 if chapter=='frozen' else 0),2.2,energy-20)
        if boss and index==0 and chapter!='forest':
            note(9,t,49,.24,energy-2)
    musical = [(tick,message) for tick,message in events if message[0] & 0xf0 in (0x80,0x90)]
    events.extend((tick+stride*PPQ,message) for tick,message in musical)
    events.extend((tick+2*stride*PPQ,message) for tick,message in musical if tick<score.beats*PPQ)
    events.append(((2*stride+score.beats)*PPQ,bytes((255,47,0))))
    stream = bytearray()
    previous = 0
    for tick,message in sorted(events,key=lambda x:(x[0],x[1][0]&0xf0==0x90)):
        stream.extend(varlen(tick-previous)+message)
        previous=tick
    path.write_bytes(b'MThd'+pack('>IHHH',6,0,1,PPQ)+b'MTrk'+pack('>I',len(stream))+stream)
    return round(stride*60/score.tempo*RATE)
