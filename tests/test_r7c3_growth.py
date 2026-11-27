from dataclasses import asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from campaign_save import record_clear, start_chapter
from main import _new_stage_game
from release_game import ReleaseGame
from save_manager import FinalClear, SaveData, SaveStore, decode, encode
from tests.test_stage_transition import finish
from tests.test_upgrade_flow import clear
from upgrades import ChapterBuild


def clear_with(flow, choices):
    for kind in choices:
        flow.choose(clear(flow), kind, _new_stage_game)
    clear(flow)


class GrowthCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(self.enterContext(TemporaryDirectory()))/'save.json'
        self.store = SaveStore(self.path)

    def test_wounded_boss_entry_carries_hp_then_boss_replay_and_chapter_entry_heal(self):
        for kind in ('attack','hp','move'):
            with self.subTest(kind=kind):
                flow = start_chapter(self.store,1,_new_stage_game,new_game=True)
                for earlier in ('attack','move','hp'):
                    flow.choose(clear(flow),earlier,_new_stage_game)
                flow.game.player.health.apply_damage(2,tick=0)
                boss,_ = flow.choose(clear(flow),kind,_new_stage_game)
                expected = flow.run.build
                maximum = expected.stats.max_hp
                self.assertEqual((boss.stage_number,boss.player.health.current_hp,boss.player.health.max_hp),
                                 (5,2+(kind=='hp'),maximum))
                self.assertIsNone(boss.player.health.last_damage_tick)
                clear(flow)
                replay,_ = flow.restart(_new_stage_game)
                self.assertEqual((replay.stage_number,replay.player.health.current_hp,flow.run.build),
                                 (5,maximum,expected))
                replay.player.health.apply_damage(2,tick=0)
                clear(flow)
                record_clear(self.store,flow)
                chapter,_ = flow.enter_next_chapter(_new_stage_game)
                self.assertEqual((chapter.stage_number,chapter.player.health.current_hp,flow.run.entry_build),
                                 (6,maximum,expected))
                self.assertEqual(SaveStore(self.path).data.entry_builds[1],expected)

    def test_full_build_round_trip_for_continue_chapter_select_and_death_retry(self):
        flow = start_chapter(self.store,1,_new_stage_game)
        clear_with(flow,('attack','move','hp','move'))
        record_clear(self.store,flow)
        reopened = SaveStore(self.path)
        expected = ChapterBuild(1,1,2)
        self.assertEqual(reopened.data.continue_chapter,2)
        for chapter in (reopened.data.continue_chapter,2):
            resumed = start_chapter(reopened,chapter,_new_stage_game)
            self.assertEqual(resumed.run.entry_build,expected)
            self.assertEqual(resumed.game.player.health.current_hp,4)
            for kind in ('hp','attack'):
                resumed.choose(clear(resumed),kind,_new_stage_game)
            finish(resumed.game,'dead')
            game,_ = resumed.restart(_new_stage_game)
            self.assertEqual((game.stage_number,game.player.health.current_hp,
                              resumed.run.build,resumed.run.receipts),(6,4,expected,()))

    def test_reclear_keeps_existing_checkpoint_and_new_game_reseeds_once(self):
        flow = start_chapter(self.store,1,_new_stage_game)
        clear_with(flow,('attack',)*4)
        record_clear(self.store,flow)
        for _ in range(2):
            replay = start_chapter(self.store,1,_new_stage_game)
            clear_with(replay,('move','move','hp','hp'))
            record_clear(self.store,replay)
            checkpoint = self.store.data.entry_builds[1]
            replay.enter_next_chapter(_new_stage_game,entry_build=checkpoint)
            self.assertEqual(replay.run.build,ChapterBuild(4))
        fresh = start_chapter(self.store,1,_new_stage_game,new_game=True)
        self.assertEqual(self.store.data.unlocked,(1,2))
        self.assertEqual(self.store.data.cleared,(1,))
        self.assertEqual(self.store.data.entry_builds,(ChapterBuild(),None))
        clear_with(fresh,('move','move','hp','hp'))
        record_clear(self.store,fresh)
        self.assertEqual(SaveStore(self.path).data.entry_builds[1],ChapterBuild(0,2,2))
        before = self.path.read_bytes()
        record_clear(self.store,fresh)
        self.assertEqual(before,self.path.read_bytes())

    def test_release_actions_restore_full_checkpoint_then_reset_for_new_game(self):
        flow = start_chapter(self.store,1,_new_stage_game)
        clear_with(flow,('hp','move','hp','attack'))
        record_clear(self.store,flow)
        app = ReleaseGame.__new__(ReleaseGame)
        app.store = SaveStore(self.path)
        app.factory = _new_stage_game
        app.menu = SimpleNamespace(is_open=False)
        actions = iter(('continue',2,'new','exit'))
        app.front_loop = lambda screen,replay: next(actions)
        entries = []

        def play(game, flow, *, default_art, app):
            self.assertTrue(default_art)
            entries.append((game.stage_number,flow.run.entry_build,game.player.health.current_hp))
            return 'main'

        app.run(play)
        self.assertEqual(entries,[(6,ChapterBuild(1,2,1),5),(6,ChapterBuild(1,2,1),5),
                                  (1,ChapterBuild(),3)])
        self.assertEqual(SaveStore(self.path).data.entry_builds,(ChapterBuild(),None))

    def test_v1_migration_preserves_unlocks_final_record_settings_and_original_bytes(self):
        final = FinalClear(642,2,5,15)
        old = asdict(SaveData(unlocked=(1,2,3,4,5),cleared=(1,2,3,4,5),
                              final_clear=final,continue_chapter=4,bgm=19,fullscreen=True))
        del old['entry_builds']
        legacy = json.dumps(dict(old,version=1,entry_attack=[0,3,5,8,12])).encode()
        self.path.write_bytes(legacy)
        migrated = SaveStore(self.path)
        self.assertEqual(migrated.data.entry_builds,tuple(ChapterBuild(x) for x in (0,3,5,8,12)))
        self.assertEqual(migrated.data.final_clear,final)
        self.assertEqual(migrated.data.unlocked,(1,2,3,4,5))
        self.assertEqual((migrated.data.continue_chapter,migrated.data.bgm,migrated.data.fullscreen),
                         (4,19,True))
        with patch('save_manager.os.replace',side_effect=PermissionError):
            self.assertFalse(migrated.flush())
        self.assertEqual(self.path.read_bytes(),legacy)
        self.assertTrue(migrated.flush())
        self.assertEqual(self.path.with_suffix('.bak').read_bytes(),legacy)
        self.assertEqual(json.loads(self.path.read_bytes())['version'],2)
        self.assertEqual(SaveStore(self.path).data,migrated.data)
        self.path.write_bytes(b'corrupt')
        recovered = SaveStore(self.path)
        self.assertEqual(recovered.data,migrated.data)
        self.assertTrue(recovered.flush())

    def test_v2_checks_complete_fields_type_and_number_of_earned_choices(self):
        base = SaveData(unlocked=(1,2),cleared=(1,),entry_builds=(ChapterBuild(),ChapterBuild(2,1,1)))
        self.assertEqual(decode(encode(base)),base)
        for broken in ({'attack_level': 2, 'hp_level': 1},
                       {'attack_level': 3, 'hp_level': 1, 'move_level': 1},
                       {'attack_level': 2, 'hp_level': 1, 'move_level': True}):
            payload = json.loads(encode(base))
            payload['entry_builds'][1] = broken
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                decode(json.dumps(payload))

    def test_twenty_choices_reach_all_caps_only_after_stage24(self):
        flow = start_chapter(self.store,1,_new_stage_game)
        for stage in range(1,26):
            offer = clear(flow)
            if stage % 5:
                enabled = [option.kind for option in offer.options if option.enabled]
                self.assertTrue(enabled)
                if stage == 24:
                    self.assertEqual(len(enabled),1)
                flow.choose(offer,enabled[0],_new_stage_game)
            else:
                self.assertIsNone(offer)
                record_clear(self.store,flow)
                if stage < 25:
                    flow.enter_next_chapter(_new_stage_game)
        self.assertEqual(flow.run.build,ChapterBuild(15,3,2))
        before = self.path.read_bytes()
        flow.restart(_new_stage_game)
        clear(flow)
        record_clear(self.store,flow)
        self.assertEqual(self.path.read_bytes(),before)
