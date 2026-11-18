"""D4A Queen asset/static review checks; no live Stage13 rendering or damage claims."""
import ast
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
from stage12_art_renderer import LiveArenaArtPath,actor_layout as approved_layout
from queen_behavior import queen_ray_targets
from tools import prepare_ice_queen as prep
from tools.prepare_chapter3_units import metrics,pixels
from tools import ice_queen_review as review


class IceQueenArtTests(unittest.TestCase):
    def setUp(self):self.manifest=json.loads((review.ASSETS/'queen_manifest.json').read_text());self.row=self.manifest['assets'][0]

    def source_folder(self,folder):
        (folder/'source').mkdir();shutil.copy2(review.ASSETS/'source/queen.png',folder/'source/queen.png')

    def test_actual_source_prepared_rgba_alpha_edges_hashes_and_history(self):
        import sdl2 as s
        from sdl2.sdlimage import IMG_Load
        r=self.row
        for fk,hk in (('source','source_sha256'),('file','sha256')):
            p=review.ASSETS/r[fk];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r[hk])
            self.assertEqual(p.read_bytes()[24:26],bytes((8,6)))
            a=IMG_Load(str(p).encode());self.assertTrue(a);b=s.SDL_ConvertSurfaceFormat(a,s.SDL_PIXELFORMAT_RGBA32,0)
            try:
                m=metrics(b);self.assertGreater(m['transparent_pixels'],0)
                if fk=='source':
                    self.assertEqual(m['size'],[1086,1448]);self.assertEqual(m['alpha_bbox'],r['source_alpha_bbox'])
                    self.assertGreaterEqual(m['safety_margin_fraction'],.05)
                else:
                    self.assertEqual(m['size'],[256,256]);self.assertEqual(m['alpha_bbox'],[48,18,207,238])
                    self.assertEqual(m['alpha_nonzero_bbox'],m['alpha_bbox'])
                    raw=pixels(b);self.assertEqual(sum(8<=raw[i+3]<=240 and max(raw[i:i+3])<8 for i in range(0,len(raw),4)),0)
            finally:s.SDL_FreeSurface(b);s.SDL_FreeSurface(a)
        prompt=json.loads((review.ASSETS/'queen_prompt.json').read_text())
        self.assertIn('OpenAI built-in image_gen',prompt['tool']);self.assertEqual(prompt['selected_output'],r['source'])
        self.assertIn('not exposed',prompt['exact_model']);self.assertIn('unverified',prompt['license_status'])
        for row in prompt['source_records']:
            p=review.ASSETS/row['file'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'])

    def test_preparation_reproduces_both_outputs_preserves_source_and_aspect(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.source_folder(folder);before=(folder/'source/queen.png').read_bytes()
            self.assertEqual(prep.prepare(folder),self.manifest);self.assertEqual(prep.prepare(folder),self.manifest)
            self.assertEqual((folder/'queen.png').read_bytes(),(review.ASSETS/'queen.png').read_bytes())
            self.assertEqual((folder/'source/queen.png').read_bytes(),before)
            self.assertEqual(self.row['normalized_dimensions'],[159,220]);self.assertLess(abs(159/220-861/1191),.006)

    def test_bad_or_missing_source_and_conflicting_output_are_preserved(self):
        for mode in ('missing','corrupt','conflict'):
            with tempfile.TemporaryDirectory() as d:
                folder=Path(d);self.source_folder(folder)
                if mode=='missing':(folder/'source/queen.png').unlink()
                elif mode=='corrupt':(folder/'source/queen.png').write_bytes(b'not PNG')
                else:(folder/'queen.png').write_bytes(b'preserve candidate')
                with self.assertRaises((ValueError,OSError)):prep.prepare(folder)
                self.assertFalse((folder/'queen_manifest.json').exists())
                if mode=='conflict':self.assertEqual((folder/'queen.png').read_bytes(),b'preserve candidate')
                else:self.assertFalse((folder/'queen.png').exists())

    def test_failed_publication_cleans_only_new_partial_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);self.source_folder(folder);sentinel=folder/'keep.txt';sentinel.write_bytes(b'keep')
            original=Path.open
            def opening(p,*a,**kw):
                if p==folder/'queen_manifest.json' and a and a[0]=='xb':raise OSError('publication fixture')
                return original(p,*a,**kw)
            with patch.object(Path,'open',opening),self.assertRaises(OSError):prep.prepare(folder)
            self.assertEqual(sorted(p.name for p in folder.iterdir()),['keep.txt','source']);self.assertEqual(sentinel.read_bytes(),b'keep')

    def test_original_stage13_roster_hp58_and_no_live_art_activation(self):
        g=main._new_stage_game(13);before=pickle.dumps(g);roster=review.actors()
        expected=[('queen',4,7,18),('knight',3,6,13),('pawn',1,6,9),('pawn',8,6,9),('pawn',3,8,9)]
        self.assertEqual([(a.kind,a.col,a.row,a.hp) for a in roster[1:]],expected)
        self.assertEqual([(e.kind,*e.position,e.health.current_hp) for e in g.encounter.enemies],expected)
        self.assertEqual(sum(a.hp for a in roster[1:]),58);self.assertEqual((roster[0].col,roster[0].row),(5,1))
        self.assertIsNone(g.encounter.pulse)
        c=Mock()
        with patch.dict(os.environ,{f'CHECKMATE_STAGE{n}_ART':'1' for n in range(5,14)}):
            path=LiveArenaArtPath(c);self.assertFalse(path.draw(g,{}));path.close()
        c.load_image.assert_not_called();self.assertEqual(pickle.dumps(g),before)

    def test_hundred_cells_preserve_old_layouts_and_measured_queen_foot_hp_depth(self):
        rows={r['name']:r for name in ('asset_manifest.json','bishop_manifest.json','queen_manifest.json') for r in json.loads((review.ASSETS/name).read_text())['assets']}
        for u in range(10):
            for v in range(10):
                for k in ('pawn','rook','knight','bishop','player'):self.assertEqual(review.candidate_layout(k,u,v,rows),approved_layout(k,u,v))
                l=review.candidate_layout('queen',u,v,rows);self.assertEqual(l['foot'],CAMERA.project(u+.5,v+.25))
                self.assertAlmostEqual(l['hp_y']-l['top'],12);self.assertAlmostEqual(l['height']*220/256,90*(1.10-.023*v)/1.10)
                self.assertEqual(CAMERA.pick(*CAMERA.center(u,v)),(u,v))
                self.assertAlmostEqual(l['center'][1]-l['height']/2+l['height']*18/256,l['foot'][1])
        front=review.candidate_layout('queen',0,0,rows);self.assertAlmostEqual(front['height']*159/256,65.04545454545455)

    def test_original_spawn_queen_visible_bounds_do_not_overlap_neighbor_hp_labels(self):
        rows={r['name']:r for name in ('asset_manifest.json','bishop_manifest.json','queen_manifest.json') for r in json.loads((review.ASSETS/name).read_text())['assets']}
        queen=next(a for a in review.actors() if a.kind=='queen')
        l=review.candidate_layout('queen',queen.col,queen.row,rows);box=review.visible_bounds(l,self.row)
        for a in review.actors():
            if a.kind=='queen':continue
            l=review.candidate_layout(a.kind,a.col,a.row,rows);w=len(str(a.hp)+'/'+str(a.hp))*8
            hp=(l['foot'][0]-w/2-3,l['hp_y']-3,l['foot'][0]+w/2+3,l['hp_y']+13)
            self.assertFalse(box[0]<hp[2] and hp[0]<box[2] and box[1]<hp[3] and hp[1]<box[3],a.data_id)

    def test_static_eight_rays_use_original_geometry_without_damage_or_ai_imports(self):
        rays=queen_ray_targets((4,7));self.assertEqual(len(rays),31);self.assertEqual(len(set(rays)),31)
        self.assertNotIn((4,7),rays);self.assertIn((3,8),rays);self.assertIn((3,6),rays)
        self.assertEqual({(int((x-4)>0)-int((x-4)<0),int((y-7)>0)-int((y-7)<0)) for x,y in rays},set(__import__('queen_behavior').RAY_STEPS))
        tree=ast.parse(Path(review.__file__).read_text())
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        self.assertFalse(imports&{'game','enemy_behaviors','combat_resolution'})

    def test_partial_review_load_failure_releases_owned_textures(self):
        c=Mock();images=[SimpleNamespace(texture=101),SimpleNamespace(texture=102)]
        c.load_image.side_effect=[*images,OSError('load fixture')]
        with self.assertRaises(OSError):review.Review(c)
        self.assertEqual(c.SDL_DestroyTexture.call_count,2);self.assertTrue(all(i.texture is None for i in images))

    def test_native_six_pages_repeat_and_fifteen_textures_load_once_and_release(self):
        script=r'''
import ctypes,json,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
from pico2d import pico2d as c
from tools.stage5_art_preview import open_preview
from tools.ice_queen_review import Review,capture,ASSETS
open_preview(c,capture=True);r=None
try:
    load,destroy=c.load_image,c.SDL_DestroyTexture;live=set();count=[0,0]
    def loading(p):
        image=load(p);key=ctypes.cast(image.texture,ctypes.c_void_p).value
        assert key and key not in live;live.add(key);count[0]+=1;return image
    def destroying(texture):
        key=ctypes.cast(texture,ctypes.c_void_p).value
        if key:assert key in live;live.remove(key);count[1]+=1
        return destroy(texture)
    with patch.object(c,'load_image',loading),patch.object(c,'SDL_DestroyTexture',destroying):
        r=Review(c);before=r.roster;assert count[0]==15
        with tempfile.TemporaryDirectory() as d:
            a=capture(c,r,Path(d)/'a');b=capture(c,r,Path(d)/'b')
            baseline=json.loads((ASSETS/'queen_review/review_manifest.json').read_text())
            assert a==b and json.loads(json.dumps(a))==baseline
            assert len(a['captures'])==6 and len(a['queen_rays'])==31
            for row in a['captures']:assert hashlib.sha256((Path(d)/'a'/row['file']).read_bytes()).hexdigest()==row['sha256']
        assert r.roster==before and count[0]==15
        r.close();assert count==[15,15] and not live
finally:
    if r:r.close()
    c.close_canvas();c.window=c.renderer=None
'''
        p=subprocess.run([sys.executable,'-X','utf8','-c',script],cwd=review.ROOT,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,encoding='utf-8',timeout=90)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
