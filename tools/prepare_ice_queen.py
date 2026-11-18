"""D4A mechanical Queen preparation; unchanged D1 normalizer, protected originals."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools.prepare_chapter3_units import normalized


def prepare(folder=ROOT/'assets/chapter3_units'):
    import sdl2 as s
    from sdl2.sdlimage import IMG_Init,IMG_Quit,IMG_INIT_PNG
    folder=Path(folder);source=folder/'source/queen.png';original=source.read_bytes()
    if s.SDL_Init(0):raise OSError('SDL initialization failed')
    hint=s.SDL_GetHint(s.SDL_HINT_RENDER_SCALE_QUALITY)
    try:
        if not IMG_Init(IMG_INIT_PNG)&IMG_INIT_PNG:raise OSError('PNG initialization failed')
        s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,b'1')
        encoded,before,after,dimensions=normalized(source)
        row=dict(name='queen',source='source/queen.png',file='queen.png',
                 source_size=before['size'],source_alpha_bbox=before['alpha_bbox'],
                 source_alpha_nonzero_bbox=before['alpha_nonzero_bbox'],source_transparent_pixels=before['transparent_pixels'],
                 source_safety_margin_fraction=before['safety_margin_fraction'],source_bytes=len(original),
                 source_sha256=hashlib.sha256(original).hexdigest(),**after,normalized_dimensions=dimensions,
                 rgba_bytes=256*256*4,file_bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest(),
                 foot_anchor=[128,after['alpha_bbox'][3]],anchor_note='alpha-bottom STATIC candidate; inspect actual boots; no live Stage13',
                 target_front_visible_height=90,hp_offset_candidate=12,
                 scale_reason='Measured source visible ratio861/1191; height86/88/90 gives width62.17/63.62/65.06px. Choose90px static candidate for commander height with width below84px cell; human approval pending.')
        manifest=dict(task='Task 5-D4A',status='Original Ice Queen static design candidate; user GUI pending; no live Stage13 renderer',
                      generator='OpenAI built-in image_gen; exact model not exposed',
                      normalization='Unchanged D1 normalized(): alpha>5 bbox, uniform max220 SDL premultiplied linear resize, straight RGBA256 padding',
                      alpha_bbox_threshold=5,assets=[row])
        outputs={'queen.png':encoded,'queen_manifest.json':(json.dumps(manifest,indent=2)+'\n').encode()}
        for name,data in outputs.items():
            p=folder/name
            if p.exists() and p.read_bytes()!=data:raise ValueError('Preserve conflicting output: '+name)
        if source.read_bytes()!=original:raise ValueError('Source changed during preparation')
        created=[]
        try:
            for name,data in outputs.items():
                p=folder/name
                if not p.exists():
                    stream=p.open('xb');created.append(p)
                    with stream:stream.write(data)
        except BaseException:
            for p in created:p.unlink(missing_ok=True)
            raise
        return manifest
    finally:
        if hint is None:s.SDL_ResetHint(s.SDL_HINT_RENDER_SCALE_QUALITY)
        else:s.SDL_SetHint(s.SDL_HINT_RENDER_SCALE_QUALITY,hint)
        IMG_Quit();s.SDL_Quit()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,default=ROOT/'assets/chapter3_units')
    print(json.dumps(prepare(p.parse_args().folder),indent=2))
