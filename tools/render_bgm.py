"""Offline music build with FluidSynth, GeneralUser GS, libsndfile and NumPy."""
import argparse
import ctypes as c
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

import numpy as np

from score_bgm import RATE, SCORES, render_score


class SoundInfo(c.Structure):
    _fields_ = [('frames',c.c_int64), ('rate',c.c_int), ('channels',c.c_int),
                ('format',c.c_int), ('sections',c.c_int), ('seekable',c.c_int)]


class AudioFiles:
    def __init__(self, dll):
        self.dll = c.CDLL(str(dll))
        self.open = self.dll.sf_wchar_open if hasattr(self.dll,'sf_wchar_open') else self.dll.sf_open
        self.wide = hasattr(self.dll,'sf_wchar_open')
        self.open.argtypes = [c.c_wchar_p if self.wide else c.c_char_p,c.c_int,c.POINTER(SoundInfo)]
        self.open.restype = c.c_void_p
        for fn in (self.dll.sf_readf_float,self.dll.sf_writef_float):
            fn.argtypes = [c.c_void_p,c.POINTER(c.c_float),c.c_int64]
            fn.restype = c.c_int64
        self.dll.sf_close.argtypes = [c.c_void_p]

    def transfer(self, path, samples=None):
        reading = samples is None
        info = SoundInfo() if reading else SoundInfo(len(samples),RATE,2,0x200060,0,0)
        filename = str(path) if self.wide else str(path).encode()
        handle = self.open(filename,0x10 if reading else 0x20,c.byref(info))
        if not handle:
            raise OSError(f'Cannot open {path}')
        try:
            if reading:
                samples = np.empty((info.frames,info.channels),dtype=np.float32)
            transfer = self.dll.sf_readf_float if reading else self.dll.sf_writef_float
            count=0
            for start in range(0,len(samples),8192):
                block=samples[start:start+8192]
                done=transfer(handle,block.ctypes.data_as(c.POINTER(c.c_float)),len(block))
                count+=done
                if done!=len(block):
                    if not reading:
                        raise OSError(f'Incomplete write: {path}')
                    break
            return samples[:count],info.rate
        finally:
            self.dll.sf_close(handle)


def hash_file(path):
    return sha256(path.read_bytes()).hexdigest()


def energy(data):
    return float(np.sqrt(np.mean(np.square(data),dtype=np.float64)))


def db(amplitude):
    return round(float(20*np.log10(max(amplitude,1e-10))),2)


def ambience(files, source, length, offset, amplitude, width):
    wet,rate = files.transfer(source)
    if rate!=RATE:
        times=np.arange(round(len(wet)*RATE/rate))*rate/RATE
        wet=np.column_stack([np.interp(times,np.arange(len(wet)),ch) for ch in wet.T]).astype(np.float32)
    if wet.shape[1]==1:
        wet=np.repeat(wet,2,axis=1)
    source_tail=wet[round(offset*RATE):]
    overlap=round(.22*RATE)
    if len(source_tail)<length+overlap:
        raise ValueError(f'Insufficient ambience: {source}')
    field=source_tail[:length].copy()
    factor=np.linspace(1,0,overlap,dtype=np.float32)[:,None]
    field[:overlap]=source_tail[length:length+overlap]*factor+field[:overlap]*(1-factor)
    field-=np.mean(field,axis=0)
    mono=field.mean(axis=1,keepdims=True)
    field=mono+(field-mono)*width
    # Keep close-mic bumps and isolated clicks from setting the music bus gain.
    field=np.tanh(field/max(4*energy(field),1e-6))
    return field * (amplitude/energy(field))


def bird_calls(field):
    # The creek is broadband. Keep narrow peaks in the bird-call band,
    # using the same mask for both channels to preserve their placement.
    size=2048
    hop=size//4
    window=np.hanning(size+1)[:-1].astype(np.float32)
    frequencies=np.fft.rfftfreq(size,1/RATE)
    bird_band=(frequencies>=2300)&(frequencies<=8000)
    padded=np.pad(field,((size-hop,size),(0,0)),mode='wrap')
    isolated=np.zeros_like(padded)
    norm=np.zeros(len(padded),dtype=np.float32)
    for start in range(0,len(padded)-size+1,hop):
        frame=slice(start,start+size)
        spectrum=np.fft.rfft(padded[frame]*window[:,None],axis=0)
        strength=np.max(np.abs(spectrum),axis=1)
        shoulders=sum(np.roll(strength,offset) for offset in (-6,-5,-4,4,5,6))/6
        mask=np.clip((strength/np.maximum(shoulders,1e-6)-4)/5,0,1)*bird_band
        isolated[frame]+=np.fft.irfft(spectrum*mask[:,None],n=size,axis=0)*window[:,None]
        norm[frame]+=window**2
    center=slice(size-hop,size-hop+len(field))
    return isolated[center]/norm[center,None]


def build(options):
    files=AudioFiles(options.sndfile.resolve())
    output=options.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    if options.track and any(output.iterdir()):
        raise ValueError('Use an empty output directory for a selected-track render')
    assets=[]
    with TemporaryDirectory(prefix='checkmate-bgm-') as directory:
        midi,wav=(Path(directory)/name for name in ('score.mid','render.wav'))
        for name,score in SCORES.items():
            if options.track and name not in options.track:
                continue
            length=render_score(score,name,midi)
            subprocess.run([str(options.fluid.resolve()),'-ni','-q','-F',str(wav),'-T','wav',
                            '-O','s16','-r',str(RATE),'-g','0.32',
                            '-o','synth.reverb.room-size=0.67','-o','synth.reverb.damp=0.48',
                            '-o','synth.reverb.width=0.83','-o','synth.reverb.level=0.42',
                            '-o','synth.chorus.level=0.38',
                            str(options.soundfont.resolve()),str(midi)],check=True)
            data,rate=files.transfer(wav)
            seam=round(.12*RATE)
            if rate!=RATE or data.shape[1]!=2 or len(data)<2*length+seam:
                raise ValueError(f'Unexpected renderer output: {name}')
            if np.max(np.abs(data))>=.9999:
                raise ValueError(f'FluidSynth master clipped: {name}')
            loop=data[length:2*length].copy()
            factor=np.linspace(1,0,seam,dtype=np.float32)[:,None]
            loop[:seam]=data[2*length:2*length+seam]*factor+loop[:seam]*(1-factor)
            loop-=np.mean(loop,axis=0)
            if name in ('forest','boss_forest'):
                normal=name=='forest'
                level=.014 if normal else .009
                mid=loop.mean(axis=1,keepdims=True)
                loop=mid+(loop-mid)*1.25
                creek=ambience(files,options.water,length,11 if normal else 48,level,.90)
                birds=bird_calls(creek)
                bird_level=level*(.20 if normal else .14)
                bird_peak=10*bird_level
                birds*=bird_level/max(energy(birds),1e-6)
                loop+=creek*.15
                loop+=bird_peak*np.tanh(birds/bird_peak)
                loop+=ambience(files,options.wind,length,7 if normal else 33,level*.65,1.1)
            loop*=10**(score.lufs_goal/20)/energy(loop)
            amplitude=np.abs(loop)
            peaks=amplitude>.34
            loop[peaks]=np.copysign(.34+.24*np.tanh((amplitude[peaks]-.34)/.24),loop[peaks])
            # Nudge the first few milliseconds to the previous sample before encoding.
            join=round(.006*RATE)
            edge=np.linspace(1,0,join,dtype=np.float32)[:,None]
            loop[:join]+=(loop[-1]-loop[0])*edge
            asset=output/(name+'.ogg')
            files.transfer(asset,loop)
            decoded,rate=files.transfer(asset)
            if rate!=RATE or decoded.shape!=loop.shape or not np.isfinite(decoded).all():
                raise ValueError(f'Unexpected Vorbis round trip: {name}')
            peak=np.max(np.abs(decoded))
            step=np.max(np.abs(decoded[0]-decoded[-1]))
            level=db(energy(decoded))
            if peak>=.8 or step>=.02 or abs(level-score.lufs_goal)>2:
                raise ValueError(f'Unsafe master: {name}, peak {peak}, seam {step}, RMS {level}')
            row=dict(file=asset.name,title=score.title,bars=32,bpm=score.tempo,duration_s=round(length/RATE,6),
                     sample_rate=RATE,channels=2,frames=length,bytes=asset.stat().st_size,
                     peak_dbfs=db(peak),rms_dbfs=db(energy(decoded)),seam_step_dbfs=db(step),
                     sha256=hash_file(asset))
            assets.append(row)
            print(f'{name}: {row["duration_s"]:.2f}s {row["peak_dbfs"]}dBFS peak, seam {row["seam_step_dbfs"]}dBFS',flush=True)
    manifest=dict(creator='CHECKMATE / Codex, original compositions',renderer='FluidSynth 2.5.5 + libsndfile',
        soundfont=dict(name='GeneralUser GS 2.0.3',sha256=hash_file(options.soundfont),
                       source='https://github.com/mrbumpy409/GeneralUser-GS',
                       license='https://github.com/mrbumpy409/GeneralUser-GS/blob/main/documentation/LICENSE.txt'),
        ambience=[
            dict(author='RabMusicLab',source='https://freesound.org/people/RabMusicLab/sounds/653906/',
                 edition='public HQ MP3 preview',license='CC0-1.0',sha256=hash_file(options.water)),
            dict(author='Cinetony',source='https://freesound.org/people/Cinetony/sounds/575380/',
                 edition='public HQ MP3 preview',license='CC0-1.0',sha256=hash_file(options.wind))],
        format='Ogg Vorbis stereo 44.1 kHz',files=assets)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for option in ('fluid','sndfile','soundfont','water','wind','output'):
        parser.add_argument('--'+option,type=Path,required=True)
    parser.add_argument('--track',action='append',choices=SCORES,
                        help='Render only this track into an empty staging directory (repeatable)')
    build(parser.parse_args())
