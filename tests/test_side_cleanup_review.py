"""R6 replaces only the front-central relief; R5 combat/deck remain exact."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from tests.art_review_fixtures import reference_sha256
from unittest.mock import Mock,patch

from tools.side_cleanup_review import (ASSETS,ROOT,AFFECTED,THEMES,CAMERA,BAY,
    FRONT_REGION,DECK_Y,panel_layout,clip_parts,FacadeLayer,SideCleanupRenderer)
from tests.test_aligned_board_review import rgba,sample


class SideCleanupTests(unittest.TestCase):
    def records(self):return json.loads((ASSETS/'asset_manifest.json').read_text())['assets']

    def test_complete_front_panels_have_alpha_margin_and_recorded_source_hashes(self):
        records=self.records();self.assertEqual({r['theme'] for r in records},set(AFFECTED))
        for r in records:
            self.assertEqual(r['size'],[512,256]);self.assertGreater(r['transparent_pixels'],0)
            self.assertEqual(r['source'],r['theme']+('_facade.png' if r['theme'] in ('frozen','gothic') else '_panel.png'))
            for path,digest in ((ASSETS/(r['theme']+'_panel.png'),r['sha256']),
                                (ASSETS/'source'/r['source'],r['source_sha256'])):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)
            l,t,right,b=r['alpha_bounds'];self.assertTrue(0<l<right<512 and 0<t<b<256)

    def test_all_three_layouts_use_uniform_scale_and_stay_below_the_deck(self):
        l,b,r,t=FRONT_REGION
        for record in self.records():
            for choice in range(3):
                a=panel_layout(record,choice);x0,y0,x1,y1=a['opaque'];_,_,w,h=a['image']
                self.assertAlmostEqual(w/h,2)
                self.assertGreaterEqual(x0,l);self.assertGreaterEqual(y0,b)
                self.assertLessEqual(x1,r);self.assertLess(y1,DECK_Y)
                self.assertGreaterEqual(a['deck_clearance'],2)
                src=record['alpha_bounds']
                self.assertAlmostEqual((x1-x0)/(src[2]-src[0]),(y1-y0)/(src[3]-src[1]))
        for actual,expected in zip(CAMERA.corners,((292.6,133.5),(1177.4,133.5),(1093.4,721.5),(387.8,721.5))):
            for a,e in zip(actual,expected):self.assertAlmostEqual(a,e)

    def test_scissor_parts_cover_exactly_the_complement_of_the_front_bay(self):
        parts=clip_parts();l,b,r,t=BAY
        self.assertEqual(sum(w*h for _,_,w,h in parts),1440*900-(r-l)*(t-b))
        for y in range(900):
            for x in (0,l-1,l,r-1,r,1439):
                count=sum(px<=x<px+w and py<=y<py+h for px,py,w,h in parts)
                self.assertEqual(count,0 if l<=x<r and 899-t<=y<899-b else 1)

    def test_original_clip_is_restored_even_when_the_facade_render_fails(self):
        import sdl2 as s
        class Owner:pass
        owner=Owner();owner.show_original=False;owner.c=SimpleNamespace(renderer=object())
        owner.draw_front_bay=Mock();image=Mock();image.draw.side_effect=RuntimeError('draw failed')
        def old_rect(renderer,ptr):
            rect=ctypes.cast(ptr,ctypes.POINTER(s.SDL_Rect)).contents
            rect.x,rect.y,rect.w,rect.h=0,0,1440,900
        restored=[]
        def set_rect(renderer,ptr):
            rect=ctypes.cast(ptr,ctypes.POINTER(s.SDL_Rect)).contents
            restored.append((rect.x,rect.y,rect.w,rect.h));return 0
        with patch.object(s,'SDL_RenderIsClipEnabled',return_value=1), \
             patch.object(s,'SDL_RenderGetClipRect',side_effect=old_rect), \
             patch.object(s,'SDL_RenderSetClipRect',side_effect=set_rect):
            with self.assertRaisesRegex(RuntimeError,'draw failed'):FacadeLayer(owner,image).draw(720,450,1440,900)
        self.assertEqual(restored[-1],(0,0,1440,900));owner.draw_front_bay.assert_not_called()

    def test_missing_cleanup_assets_fail_without_substituting_old_art(self):
        with tempfile.TemporaryDirectory() as folder:
            canvas=Mock()
            with self.assertRaises(FileNotFoundError):SideCleanupRenderer(canvas,Path(folder))
            self.assertEqual(canvas.load_image.call_count,65)

    def test_old_central_crest_is_excluded_before_the_new_panel_is_drawn(self):
        import sdl2 as s
        class Owner:pass
        surface=s.SDL_CreateRGBSurfaceWithFormat(0,1440,900,32,s.SDL_PIXELFORMAT_RGBA32)
        self.assertTrue(surface);renderer=s.SDL_CreateSoftwareRenderer(surface)
        try:
            self.assertTrue(renderer)
            s.SDL_SetRenderDrawColor(renderer,0,0,255,255);s.SDL_RenderClear(renderer)
            owner=Owner();owner.c=SimpleNamespace(renderer=renderer);owner.show_original=False;owner.draw_front_bay=Mock()
            def paint_old(*args):
                s.SDL_SetRenderDrawColor(renderer,255,0,0,255)
                self.assertEqual(s.SDL_RenderFillRect(renderer,None),0)
            FacadeLayer(owner,SimpleNamespace(draw=paint_old)).draw()
            s.SDL_RenderPresent(renderer)
            pixels=ctypes.string_at(surface.contents.pixels,surface.contents.pitch*900);l,b,r,t=BAY
            for y in range(899-t,899-b):
                row=pixels[y*surface.contents.pitch+l*4:y*surface.contents.pitch+r*4]
                self.assertEqual(row,bytes((0,0,255,255))*(r-l))
            owner.draw_front_bay.assert_called_once_with()
            self.assertFalse(s.SDL_RenderIsClipEnabled(renderer))
        finally:
            if renderer:s.SDL_DestroyRenderer(renderer)
            s.SDL_FreeSurface(surface)

    def test_native_cleanup_replay_preserves_deck_rails_chapter_one_and_combat(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            result=subprocess.run([sys.executable,'tools/side_cleanup_review.py','--capture-dir',folder],cwd=ROOT,
                env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            data=json.loads((out/'review_manifest.json').read_text())
            self.assertEqual(data,json.loads((ASSETS/'review/review_manifest.json').read_text()))
            prior=json.loads((ROOT/'assets/aligned_board/review/review_manifest.json').read_text())
            self.assertEqual(data['scenes'],prior['scenes']);self.assertEqual(data['textures_loaded'],69)
            self.assertEqual(len(data['captures']),61);self.assertEqual(len(list(out.glob('*.png'))),82)
            for p in out.glob('*.png'):
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),reference_sha256(ASSETS/'review'/p.name))
                self.assertTrue(rgba(p)[1])
            for record in data['captures']:
                scene=next(s for s in data['scenes'] if s['scenario']==record['scenario'])
                self.assertEqual(record['warning_cells'],[cell for e in scene['events'] if e['state']=='telegraph' for cell in e['cells']])
                self.assertEqual(record['tile_quads'],[[list(p) for p in CAMERA.tile(c,row)] for c in range(10) for row in range(10)])
                if record['front_layout']:self.assertGreaterEqual(record['front_layout']['deck_clearance'],2)
            points=[CAMERA.project(c+u,r+v) for c in range(10) for r in range(10)
                    for u in (.12,.5,.88) for v in (.12,.5,.88)]
            l,b,r,t=FRONT_REGION
            for theme in THEMES:
                old=rgba(ROOT/'assets/aligned_board/review'/(theme+'_c_normal.png'))
                comparison=rgba(out/('prior_R5_'+theme+'_normal.png'))
                fixes=[rgba(out/(theme+'_'+v+'_normal.png')) for v in 'abc']
                for y in range(900):
                    start=y*old[0];end=(y+1)*old[0]
                    self.assertEqual(comparison[1][start+280*4:end],old[1][start+280*4:end])
                    spans=((280,l),(r,1440)) if 899-t<=y<899-b and theme!='royal' else ((280,1440),)
                    for x0,x1 in spans:
                        for fix in fixes:self.assertEqual(fix[1][start+x0*4:start+x1*4],old[1][start+x0*4:start+x1*4])
                for p in points:self.assertTrue(all(sample(fix,p)==sample(old,p) for fix in fixes))
            for name in ('normal','player_attack','enemy_warning','parry_normal','parry_perfect','pulse'):
                modes=[rgba(out/('forest_mode_'+str(m)+'_'+name+'.png')) for m in range(3)]
                for p in points:self.assertTrue(all(sample(m,p)==sample(modes[0],p) for m in modes))
            byfile={r['file']:r for r in data['captures']}
            self.assertEqual(byfile['forest_c_parry_perfect.png']['cue']['kind'],'perfect_success')
            self.assertNotEqual(byfile['forest_window_mode_1.png']['cue']['kind'],'perfect_success')
            resolved=byfile['pulse_resolved.png']
            self.assertEqual(resolved['cue']['kind'],'ready')
            self.assertEqual(resolved['warning_cells'],[])
            self.assertEqual(resolved['cue_segments'],next(r for r in prior['captures'] if r['file']=='pulse_resolved.png')['cue_segments'])

    def test_review_controls_ignore_repeat_and_keep_settings_comparison_and_phases(self):
        import tools.side_cleanup_review as preview
        from pico2d import pico2d as c
        def key(k,repeat=False):return SimpleNamespace(type=c.SDL_KEYDOWN,key=k,repeat=repeat)
        events=iter([[key(c.SDLK_2),key(c.SDLK_5,True),key(c.SDLK_6),key(c.SDLK_q),key(c.SDLK_r)],
            [key(c.SDLK_b),key(c.SDLK_l)],[key(c.SDLK_9),key(c.SDLK_t),key(c.SDLK_F11)],
            [SimpleNamespace(type=c.SDL_MOUSEBUTTONDOWN,button=c.SDL_BUTTON_LEFT,x=1295,y=41)],
            [key(c.SDLK_5),key(c.SDLK_ESCAPE)],[key(c.SDLK_ESCAPE)]])
        with patch.object(preview,'open_preview'),patch.object(preview,'DisplaySettings') as display, \
             patch.object(preview,'SettingsRenderer'),patch.object(preview,'SideCleanupRenderer') as renderer, \
             patch.object(c,'window',object(),create=True),patch.object(c,'renderer',object(),create=True), \
             patch.object(c,'hide_lattice'),patch.object(c,'get_events',side_effect=lambda:next(events)), \
             patch.object(c,'update_canvas'),patch.object(c,'close_canvas'),patch.object(preview,'sleep'):
            preview.run(SimpleNamespace(capture_dir=None,assets=ASSETS))
            calls=renderer.return_value.draw.call_args_list
            self.assertEqual(calls[0].args[0].name,'parry_window');self.assertEqual(calls[-1].args[0].name,'pulse_resolved')
            self.assertEqual(renderer.return_value.theme,1);self.assertEqual(renderer.return_value.variant,2)
            self.assertEqual(renderer.return_value.mode,1);self.assertFalse(renderer.return_value.compare)
            display.return_value.toggle.assert_called_once_with()
