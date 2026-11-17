"""D3A image/static review checks; never activate live Stage12 rendering."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

import main
from arena_art_common import CAMERA
from stage11_art_renderer import LiveArenaArtPath,actor_layout as approved_layout
from tools import prepare_ice_bishop as prep
from tools.prepare_chapter3_units import metrics,pixels
from tools import ice_bishop_review as review


class IceBishopArtTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((review.ASSETS/'bishop_manifest.json').read_text())
        self.row=self.manifest['assets'][0]

    def source_folder(self,folder):
        (folder/'source').mkdir()
        shutil.copy2(review.ASSETS/'source/bishop.png',folder/'source/bishop.png')

    def test_actual_source_prepared_metrics_alpha_edges_and_generation_history(self):
        import sdl2 as s
        from sdl2.sdlimage import IMG_Load
        r=self.row
        for name,digest in ((r['source'],r['source_sha256']),(r['file'],r['sha256'])):
            p=review.ASSETS/name;self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),digest)
            self.assertEqual(p.read_bytes()[24:26],bytes((8,6)))
            surface=IMG_Load(str(p).encode());self.assertTrue(surface)
            rgba=s.SDL_ConvertSurfaceFormat(surface,s.SDL_PIXELFORMAT_RGBA32,0)
            try:
                actual=metrics(rgba)
                self.assertGreater(actual['transparent_pixels'],0)
                if name==r['source']:
                    self.assertEqual(actual['size'],[1024,1536])
                    self.assertEqual(actual['alpha_bbox'],r['source_alpha_bbox'])
                    self.assertGreaterEqual(actual['safety_margin_fraction'],.05)
                else:
                    self.assertEqual(actual['size'],[256,256])
                    self.assertEqual(actual['alpha_bbox'],[91,18,165,238])
                    self.assertEqual(actual['alpha_nonzero_bbox'],actual['alpha_bbox'])
                    data=pixels(rgba)
                    self.assertEqual(sum(8<=data[i+3]<=240 and max(data[i:i+3])<8 for i in range(0,len(data),4)),0)
            finally:s.SDL_FreeSurface(rgba);s.SDL_FreeSurface(surface)
        prompt=json.loads((review.ASSETS/'bishop_prompt.json').read_text())
        self.assertIn('OpenAI built-in image_gen',prompt['tool'])
        self.assertEqual(prompt['selected_output'],r['source'])
        self.assertIn('unverified',prompt['license_status'])
        self.assertIn('not exposed',prompt['exact_model'])
        for source in prompt['source_records']:
            p=review.ASSETS/source['file']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),source['sha256'])

    def test_preparation_reproduces_both_outputs_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.source_folder(folder);source=(folder/'source/bishop.png').read_bytes()
            self.assertEqual(prep.prepare(folder),self.manifest)
            self.assertEqual(prep.prepare(folder),self.manifest)
            self.assertEqual((folder/'bishop.png').read_bytes(),(review.ASSETS/'bishop.png').read_bytes())
            self.assertEqual((folder/'source/bishop.png').read_bytes(),source)
            self.assertEqual(self.row['normalized_dimensions'],[74,220])
            sw,sh=self.row['source_alpha_bbox'][2]-self.row['source_alpha_bbox'][0],self.row['source_alpha_bbox'][3]-self.row['source_alpha_bbox'][1]
            self.assertLess(abs(74/220-sw/sh),.006)

    def test_invalid_missing_or_conflicting_files_are_never_overwritten(self):
        for mode in ('missing','corrupt','conflicting'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                folder=Path(d);self.source_folder(folder)
                if mode=='missing':(folder/'source/bishop.png').unlink()
                elif mode=='corrupt':(folder/'source/bishop.png').write_bytes(b'not PNG')
                else:(folder/'bishop.png').write_bytes(b'preserve conflicting candidate')
                with self.assertRaises((OSError,ValueError)):prep.prepare(folder)
                self.assertFalse((folder/'bishop_manifest.json').exists())
                if mode=='conflicting':self.assertEqual((folder/'bishop.png').read_bytes(),b'preserve conflicting candidate')
                else:self.assertFalse((folder/'bishop.png').exists())

    def test_failed_publication_cleans_only_its_own_new_partial_files(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.source_folder(folder);sentinel=folder/'keep.txt';sentinel.write_bytes(b'keep')
            original=Path.open
            def opening(p,*args,**kwargs):
                if p==folder/'bishop_manifest.json' and args and args[0]=='xb':raise OSError('publication fixture')
                return original(p,*args,**kwargs)
            with patch.object(Path,'open',opening),self.assertRaises(OSError):prep.prepare(folder)
            self.assertEqual(sorted(p.name for p in folder.iterdir()),['keep.txt','source'])
            self.assertEqual(sentinel.read_bytes(),b'keep')

    def test_actual_stage12_roster_hp60_and_live_art_remains_disabled(self):
        g=main._new_stage_game(12);before=pickle.dumps(g)
        self.assertEqual([(e.kind,*e.position,e.health.current_hp) for e in g.encounter.enemies],
                         [('bishop',2,8,13),('bishop',7,8,13),('rook',2,4,16),('pawn',1,6,9),('pawn',8,6,9)])
        a=review.actors()
        self.assertEqual([(x.kind,x.col,x.row,x.hp) for x in a[1:]],[(e.kind,*e.position,e.health.current_hp) for e in g.encounter.enemies])
        self.assertEqual(sum(x.hp for x in a[1:]),60)
        self.assertEqual((a[0].col,a[0].row),(5,1))
        self.assertIsNone(g.encounter.pulse)
        canvas=Mock()
        with patch.dict(os.environ,{f'CHECKMATE_STAGE{n}_ART':'1' for n in range(5,13)}):
            path=LiveArenaArtPath(canvas)
            self.assertFalse(path.draw(g,{}));path.close()
        canvas.load_image.assert_not_called();self.assertEqual(pickle.dumps(g),before)

    def test_shared_camera_hundred_cells_foot_hp_and_old_profiles_unchanged(self):
        rows={r['name']:r for r in json.loads((review.ASSETS/'asset_manifest.json').read_text())['assets']}
        rows['bishop']=self.row
        for col in range(10):
            for row in range(10):
                for kind in ('pawn','rook','knight','player'):
                    self.assertEqual(review.candidate_layout(kind,col,row,rows),approved_layout(kind,col,row))
                layout=review.candidate_layout('bishop',col,row,rows)
                self.assertEqual(layout['foot'],CAMERA.project(col+.5,row+.25))
                self.assertAlmostEqual(layout['hp_y']-layout['top'],10)
                self.assertAlmostEqual(layout['top']-layout['foot'][1],84*(1.10-.023*row)/1.10)
                self.assertEqual(CAMERA.pick(*CAMERA.center(col,row)),(col,row))
        front=review.candidate_layout('bishop',0,0,rows)
        self.assertAlmostEqual(front['height']*74/256,84*74/220)
        self.assertAlmostEqual(front['center'][1]-front['height']/2+front['height']*18/256,front['foot'][1])

    def test_warning_geometry_is_explicitly_static_and_source_scoped_no_game_imports(self):
        self.assertEqual(len(review.COLOR_CELLS),50)
        self.assertTrue(set(review.COLOR_CELLS)&set(review.ROOK_CELLS))
        self.assertTrue(all(0<=c<10 and 0<=r<10 for c,r in (*review.COLOR_CELLS,*review.ROOK_CELLS,*review.DIAGONAL_GUIDE)))
        self.assertNotEqual(set(review.DIAGONAL_GUIDE),set(review.COLOR_CELLS))
        import ast
        tree=ast.parse(Path(review.__file__).read_text())
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertFalse(imports&{'game','enemy_behaviors','combat_resolution'})

    def test_partial_static_loading_failure_releases_only_owned_textures(self):
        c=Mock();images=[SimpleNamespace(texture=100),SimpleNamespace(texture=101)]
        c.load_image.side_effect=[*images,OSError('injected load failure')]
        with self.assertRaises(OSError):review.Review(c)
        self.assertEqual(c.SDL_DestroyTexture.call_count,2)
        self.assertTrue(all(x.texture is None for x in images))

    def test_native_six_static_pages_deterministic_and_thirteen_textures_released(self):
        script=r'''
import ctypes,json,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
from pico2d import pico2d as c
from tools.stage5_art_preview import open_preview
from tools.ice_bishop_review import Review,capture,ASSETS
open_preview(c,capture=True);r=None
try:
    load,destroy=c.load_image,c.SDL_DestroyTexture;live=set();counts=[0,0];names=[]
    def loading(p):
        image=load(p);key=ctypes.cast(image.texture,ctypes.c_void_p).value
        assert key and key not in live;live.add(key);counts[0]+=1;names.append(p);return image
    def destroying(texture):
        key=ctypes.cast(texture,ctypes.c_void_p).value
        if key is not None:assert key in live;live.remove(key);counts[1]+=1
        return destroy(texture)
    with patch.object(c,'load_image',loading),patch.object(c,'SDL_DestroyTexture',destroying):
        r=Review(c);before=r.roster
        assert counts[0]==13 and sum(Path(p).name=='bishop.png' for p in names)==2  # Source+prepared, not per actor.
        with tempfile.TemporaryDirectory() as d:
            a=capture(c,r,Path(d)/'a');b=capture(c,r,Path(d)/'b')
            baseline=json.loads((ASSETS/'bishop_review/review_manifest.json').read_text())
            assert a==b and json.loads(json.dumps(a))==baseline
            for row in a['captures']:
                assert hashlib.sha256((Path(d)/'a'/row['file']).read_bytes()).hexdigest()==row['sha256']
            assert len(a['captures'])==6 and 'NOT an attack' in a['warning_note']
        assert r.roster==before and counts[0]==13
        r.close();assert counts==[13,13] and not live
finally:
    if r:r.close()
    c.close_canvas();c.window=c.renderer=None
'''
        p=subprocess.run([sys.executable,'-X','utf8','-c',script],cwd=review.ROOT,
                         env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,encoding='utf-8',timeout=90)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
