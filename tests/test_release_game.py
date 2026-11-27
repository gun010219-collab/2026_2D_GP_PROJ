from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from campaign_save import record_clear,start_chapter
from display_settings import logical_mouse_to_canvas
from front_menu import FrontInput,buttons
from game import GameState
from game_audio import AudioSettings
from main import _new_stage_game
from save_manager import SaveData,SaveStore,decode,encode
from tests.test_hp_carryover import fight
from tools.campaign_qa import release_campaign_rows
from tools.chapter_art_play import advance_campaign,session
from upgrades import ChapterBuild


def reach_boss(flow):
    while not flow.game.boss:
        result = fight(flow)
        assert result[1]=='UPGRADE',result
        advance_campaign(flow,result)
    return flow


class ReleaseSaveTests(unittest.TestCase):
    def setUp(self):
        tmp = self.enterContext(TemporaryDirectory())
        self.path = Path(tmp)/'save.json'
        self.store = SaveStore(self.path)

    def test_first_run_and_chapter_locks_do_not_write(self):
        self.assertEqual(self.store.data,SaveData())
        self.assertFalse(buttons('main',self.store.data)[1].enabled)
        self.assertEqual([b.enabled for b in buttons('chapters',self.store.data)[:5]],
                         [True,False,False,False,False])
        with self.assertRaises(ValueError):
            start_chapter(self.store,2,_new_stage_game)
        self.assertFalse(self.path.exists())

    def test_checkpoint_entry_replay_and_new_game_preserve_progress(self):
        flow = reach_boss(start_chapter(self.store,1,_new_stage_game))
        self.assertEqual(fight(flow)[1],'BOSS_CLEAR')
        record_clear(self.store,flow)
        raw = self.path.read_bytes()
        record_clear(self.store,flow)
        self.assertEqual(raw,self.path.read_bytes())
        self.assertEqual(self.store.data.entry_builds,(ChapterBuild(),flow.run.build))
        actual,_ = flow.enter_next_chapter(_new_stage_game)
        reopened = SaveStore(self.path)
        continued = start_chapter(reopened,reopened.data.continue_chapter,_new_stage_game)
        self.assertEqual(continued.game.stage_number,6)
        self.assertEqual(continued.run.stats,flow.run.stats)
        self.assertEqual(continued.game.player.health.current_hp,actual.player.health.current_hp)
        self.assertEqual(continued.run.receipts,())
        self.assertIsNot(continued.game.combat,actual.combat)
        new = start_chapter(reopened,1,_new_stage_game,new_game=True)
        self.assertEqual(new.run.entry_build,ChapterBuild())
        self.assertEqual(reopened.data.continue_chapter,1)
        self.assertEqual(reopened.data.unlocked,(1,2))
        self.assertEqual(reopened.data.entry_builds,(ChapterBuild(),None))

    def test_only_owned_all_enemy_boss_clear_progresses(self):
        flow = reach_boss(start_chapter(self.store,1,_new_stage_game))
        game = flow.game
        king = game.encounter.pulse.king
        king.health.apply_damage(king.health.current_hp,tick=game.combat.tick)
        self.assertFalse(game.update_state())
        with self.assertRaises(ValueError):
            record_clear(self.store,flow)
        # Same-tick defeat takes priority even if no enemy remains.
        for enemy in game.encounter.enemies:
            if enemy.alive:
                enemy.health.apply_damage(enemy.health.current_hp,tick=game.combat.tick)
        game.player.health.apply_damage(game.player.health.current_hp,tick=game.combat.tick)
        self.assertTrue(game.update_state())
        self.assertIs(game.state,GameState.GAME_OVER)
        with self.assertRaises(ValueError):
            record_clear(self.store,flow)
        restarted,_ = flow.restart(_new_stage_game)
        self.assertEqual(restarted.stage_number,1)
        self.assertEqual(flow.run.receipts,())
        self.assertEqual(self.store.data.unlocked,(1,))

    def test_complete_real_campaign_and_final_replay_are_idempotent(self):
        flow = start_chapter(self.store,1,_new_stage_game)
        results = []
        for stage in range(1,26):
            result = fight(flow)
            results.append(list(result))
            if stage%5==0:
                old = self.store.data.entry_builds
                ending = record_clear(self.store,flow)
                self.assertEqual(self.store.data.entry_builds[:len(old)],old)
            if stage<25:
                advance_campaign(flow,result)
        self.assertEqual(results,release_campaign_rows())
        fresh = SaveStore(self.path)
        self.assertEqual(fresh.data.final_clear,ending)
        self.assertEqual(fresh.data.cleared,(1,2,3,4,5))
        self.assertEqual(fresh.data.unlocked,(1,2,3,4,5))
        with self.assertRaises(ValueError):
            flow.enter_next_chapter(_new_stage_game)
        history = flow.run.receipts
        flow.restart(_new_stage_game)
        self.assertEqual(flow.game.stage_number,25)
        self.assertEqual(flow.run.receipts,history)
        self.assertEqual(fight(flow)[1],'BOSS_CLEAR')
        record_clear(self.store,flow)
        self.assertEqual(SaveStore(self.path).data.final_clear,ending)

    def test_invalid_version_and_ranges_are_rejected(self):
        payload = json.loads(encode(SaveData()))
        for key,value in (('version',3),('version',True),('entry_builds',[{'attack_level': 1, 'hp_level': 0, 'move_level': 0}]),('bgm',101),
                          ('fullscreen',0),('cleared',[1]),('continue_chapter',5)):
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                decode(json.dumps({**payload,key:value}))

    def test_interrupted_replace_keeps_last_valid_save_and_can_retry(self):
        self.assertTrue(self.store.remember(replace(self.store.data,continue_chapter=1)))
        raw = self.path.read_bytes()
        import os
        actual = os.replace
        def fail_primary(src,dst):
            if dst==self.path:
                raise PermissionError('injected primary write failure')
            return actual(src,dst)
        with patch('save_manager.os.replace',side_effect=fail_primary):
            self.assertFalse(self.store.settings(AudioSettings(23,67,True,False),True))
        self.assertEqual(self.path.read_bytes(),raw)
        self.assertEqual(self.path.with_suffix('.bak').read_bytes(),raw)
        self.assertFalse(list(self.path.parent.glob('*.tmp')))
        self.assertIn('SAVE FAILED',self.store.notice)
        self.assertTrue(self.store.flush())
        self.assertEqual(SaveStore(self.path).data.audio(),AudioSettings(23,67,True,False))
        self.assertTrue(SaveStore(self.path).data.fullscreen)

    def test_corrupt_primary_preserved_and_valid_backup_restored(self):
        self.store.settings(AudioSettings(25,70),False)
        self.store.settings(AudioSettings(30,70),False)
        broken = b'{not-json'
        self.path.write_bytes(broken)
        fresh = SaveStore(self.path)
        self.assertEqual(fresh.data.bgm,25)
        self.assertIn('BACKUP LOADED',fresh.notice)
        self.assertEqual(self.path.read_bytes(),broken)
        self.assertTrue(fresh.flush())
        self.assertEqual(next(self.path.parent.glob('save-recovery-*')).read_bytes(),broken)
        self.assertEqual(SaveStore(self.path).data.bgm,25)

    def test_newer_schema_is_read_only_and_unreadable_save_is_reported(self):
        raw = b'{"version": 3}'
        self.path.write_bytes(raw)
        fresh = SaveStore(self.path)
        self.assertFalse(fresh.settings(AudioSettings(20),False))
        self.assertEqual(self.path.read_bytes(),raw)
        self.assertIn('UNSUPPORTED',fresh.notice)
        with patch('save_manager._read',side_effect=PermissionError):
            fresh = SaveStore(self.path)
        self.assertTrue(fresh.blocked)
        self.assertIn('UNREADABLE',fresh.notice)

    def test_two_instances_do_not_overwrite_current_checkpoint(self):
        other = SaveStore(self.path)
        self.assertTrue(self.store.settings(AudioSettings(20),False))
        self.assertFalse(other.settings(AudioSettings(60),False))
        self.assertIn('ELSEWHERE',other.notice)
        self.assertEqual(SaveStore(self.path).data.bgm,20)

    def test_development_factory_and_fight_do_not_read_or_write_save(self):
        with patch('save_manager.SaveStore',side_effect=AssertionError('unexpected save')):
            _,flow = session(3)
            self.assertEqual(fight(flow)[1],'UPGRADE')
        self.assertFalse(self.path.exists())

    def test_menu_keyboard_skips_disabled_and_logical_hit_test_matches(self):
        c = NS(SDL_MOUSEBUTTONDOWN=1,SDL_BUTTON_LEFT=1,SDL_KEYDOWN=2,SDLK_UP=3,SDLK_DOWN=4,
               SDLK_LEFT=5,SDLK_RIGHT=6,SDLK_RETURN=7)
        menu = FrontInput()
        items = buttons('main',self.store.data)
        menu.action(c,NS(type=2,key=4),items,None)
        self.assertEqual(menu.action(c,NS(type=2,key=7),items,None),'chapters')
        cards = buttons('chapters',self.store.data)
        mouse = NS(type=1,button=1)
        for card in cards[:5]:
            p = logical_mouse_to_canvas(card.rect.left,899-card.rect.bottom)
            self.assertEqual(menu.action(c,mouse,cards,p),card.action if card.enabled else None)
        self.assertIsNone(menu.action(c,mouse,cards,logical_mouse_to_canvas(-1,20)))

    def test_native_release_qa(self):
        result = subprocess.run([sys.executable,'tools/release_game_qa.py','--renderer','software'],
                                capture_output=True,cwd=Path(__file__).resolve().parents[1],timeout=65)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
