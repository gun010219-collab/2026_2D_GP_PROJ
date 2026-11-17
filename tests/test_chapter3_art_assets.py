"""D1 art preparation/inspection contracts; does not activate a live renderer."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tools import prepare_chapter3_units as prep
from tools.chapter3_art_review import ASSETS, ROOT, actors, candidate_layout, Review, TARGET_HEIGHT


class Chapter3ArtAssetTests(unittest.TestCase):
    def setUp(self):
        self.record=json.loads((ASSETS/'asset_manifest.json').read_text())
        self.rows={r['name']:r for r in self.record['assets']}

    def copy_sources(self, target):
        (target/'source').mkdir()
        for kind in prep.KINDS:shutil.copy2(ASSETS/'source'/(kind+'.png'),target/'source'/(kind+'.png'))

    def test_source_prepared_hash_alpha_dimensions_and_soft_edge_pixels(self):
        import sdl2 as s
        from sdl2.sdlimage import IMG_Load,IMG_Init,IMG_Quit,IMG_INIT_PNG
        s.SDL_Init(0);IMG_Init(IMG_INIT_PNG)
        try:
            for kind,row in self.rows.items():
                for name,digest in ((row['source'],row['source_sha256']),(row['file'],row['sha256'])):
                    path=ASSETS/name
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
                    self.assertEqual(path.read_bytes()[24:26],bytes((8,6)))
                self.assertGreaterEqual(max(row['source_size']),1024)
                self.assertGreaterEqual(row['source_safety_margin_fraction'],.05)
                self.assertEqual(row['size'],[256,256])
                self.assertEqual(max(row['normalized_dimensions']),220)
                surface=IMG_Load(str(ASSETS/row['file']).encode())
                self.assertTrue(surface)
                rgba=s.SDL_ConvertSurfaceFormat(surface,s.SDL_PIXELFORMAT_RGBA32,0)
                try:
                    m=prep.metrics(rgba);raw=prep.pixels(rgba)
                    self.assertEqual(m['alpha_bbox'],row['alpha_bbox'])
                    self.assertGreater(m['transparent_pixels'],0)
                    self.assertTrue(all(0<v<256 for v in row['alpha_bbox']))
                    # Very low alpha can quantize to black; near-opaque dark
                    # joints are intentional. Inspect the visible soft edge.
                    dirty=sum(8<=raw[i+3]<=240 and max(raw[i:i+3])<8 for i in range(0,len(raw),4))
                    self.assertEqual(dirty,0)
                    self.assertEqual(row['foot_anchor'][1],row['alpha_bbox'][3])
                finally:
                    s.SDL_FreeSurface(rgba);s.SDL_FreeSurface(surface)
        finally:IMG_Quit();s.SDL_Quit()

    def test_preparation_reproduces_all_outputs_and_never_rewrites_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);self.copy_sources(folder)
            source={p:p.read_bytes() for p in (folder/'source').iterdir()}
            first=prep.prepare(folder);second=prep.prepare(folder)
            self.assertEqual(first,second)
            self.assertEqual(first,self.record)
            for kind in prep.KINDS:
                self.assertEqual((folder/(kind+'.png')).read_bytes(),(ASSETS/(kind+'.png')).read_bytes())
            for path,data in source.items():self.assertEqual(path.read_bytes(),data)

    def test_invalid_source_failure_preserves_existing_files_without_outputs(self):
        for mode in ('missing','corrupt'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                folder=Path(directory);self.copy_sources(folder)
                source=folder/'source/knight.png'
                if mode=='missing':source.unlink()
                else:source.write_bytes(b'not a PNG')
                sentinel=folder/'retained.txt';sentinel.write_bytes(b'keep')
                with self.assertRaises((OSError,ValueError)):prep.prepare(folder)
                self.assertEqual(sentinel.read_bytes(),b'keep')
                self.assertEqual(sorted(p.name for p in folder.iterdir()),['retained.txt','source'])

    def test_publish_failure_removes_only_new_partial_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);self.copy_sources(folder)
            sentinel=folder/'retained.txt';sentinel.write_bytes(b'keep')
            real_open=Path.open
            def opening(path,*args,**kwargs):
                if path==folder/'knight.png' and args and args[0]=='xb':
                    raise OSError('injected final publication failure')
                return real_open(path,*args,**kwargs)
            with patch.object(Path,'open',opening),self.assertRaises(OSError):
                prep.prepare(folder)
            self.assertEqual(sorted(p.name for p in folder.iterdir()),['retained.txt','source'])
            self.assertEqual(sentinel.read_bytes(),b'keep')

    def test_existing_conflicting_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);self.copy_sources(folder)
            sentinel=folder/'pawn.png';sentinel.write_bytes(b'preserved conflicting image')
            with self.assertRaises(ValueError):prep.prepare(folder)
            self.assertEqual(sentinel.read_bytes(),b'preserved conflicting image')
            self.assertFalse((folder/'rook.png').exists())
            self.assertFalse((folder/'asset_manifest.json').exists())

    def test_static_roster_camera_anchor_hp_and_natural_ratios(self):
        roster=actors();enemies=roster[1:]
        self.assertEqual([(a.kind,a.col,a.row,a.hp) for a in enemies],
                         [('rook',2,4,16),('rook',7,4,16),('knight',3,6,13),('knight',6,6,13),('pawn',1,6,9)])
        self.assertEqual(sum(a.hp for a in enemies),67)
        self.assertEqual((roster[0].col,roster[0].row),(5,1))
        for kind,row in self.rows.items():
            front=candidate_layout(kind,0,0,self.rows)
            self.assertAlmostEqual(front['top']-front['foot'][1],TARGET_HEIGHT[kind])
            for col in range(10):
                for grid_row in range(10):
                    layout=candidate_layout(kind,col,grid_row,self.rows)
                    from arena_art_common import CAMERA
                    self.assertEqual(layout['foot'],CAMERA.project(col+.5,grid_row+.25))
                    self.assertGreaterEqual(layout['hp_y']-layout['top'],8)
                    self.assertGreater(layout['height'],0)
            self.assertLess(candidate_layout(kind,0,9,self.rows)['height'],front['height'])
            bw,bh=row['source_alpha_bbox'][2]-row['source_alpha_bbox'][0],row['source_alpha_bbox'][3]-row['source_alpha_bbox'][1]
            dw,dh=row['normalized_dimensions']
            self.assertLess(abs(dw/dh-bw/bh),.006)

    def test_partial_review_loading_failure_releases_prior_textures(self):
        canvas=Mock()
        images=[SimpleNamespace(texture=101),SimpleNamespace(texture=102)]
        canvas.load_image.side_effect=[*images,OSError('expected load failure')]
        with self.assertRaises(OSError):Review(canvas)
        self.assertEqual([c.args[0] for c in canvas.SDL_DestroyTexture.call_args_list],[101,102])
        self.assertTrue(all(i.texture is None for i in images))

    def test_native_six_page_captures_repeat_without_roster_or_texture_changes(self):
        script=r"""
import ctypes,hashlib,json,tempfile
from pathlib import Path
from unittest.mock import patch
from pico2d import pico2d as c
from tools.stage5_art_preview import open_preview
from tools.chapter3_art_review import Review,capture,ASSETS,PAGES
open_preview(c,capture=True);review=None
try:
    load,destroy=c.load_image,c.SDL_DestroyTexture
    live=set();counts=[0,0]
    def loading(path):
        image=load(path);key=ctypes.cast(image.texture,ctypes.c_void_p).value
        assert key not in live;live.add(key);counts[0]+=1;return image
    def destroying(texture):
        key=ctypes.cast(texture,ctypes.c_void_p).value
        if key is not None:assert key in live;live.remove(key);counts[1]+=1
        return destroy(texture)
    with patch.object(c,'load_image',loading),patch.object(c,'SDL_DestroyTexture',destroying):
        review=Review(c);assert counts[0]==11
        before=review.roster
        with tempfile.TemporaryDirectory() as directory:
            a=capture(c,review,Path(directory)/'a');b=capture(c,review,Path(directory)/'b')
            baseline=json.loads((ASSETS/'review/review_manifest.json').read_text())
            assert a==b and json.loads(json.dumps(a))==baseline
            assert len(a['captures'])==len(PAGES)==6
        assert review.roster==before and counts[0]==11
        review.close();assert counts==[11,11] and not live
finally:
    if review:review.close()
    c.close_canvas();c.window=c.renderer=None
"""
        env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','PYTHONUTF8':'1'}
        result=subprocess.run([sys.executable,'-X','utf8','-c',script],cwd=ROOT,env=env,
                              capture_output=True,text=True,encoding='utf-8',timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
