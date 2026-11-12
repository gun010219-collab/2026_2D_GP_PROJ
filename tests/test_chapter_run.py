"""Explicit model commands, no fabricated StageGame outcomes or main hooks."""
from dataclasses import replace
from itertools import product
import unittest

from chapter_run import ChapterRun
from upgrades import ChapterBuild, UpgradeKind, UpgradeReceipt


def choose(run,kind):
    return run.select(run.offer_after_clear(run.current_stage,f'session-{run.current_stage}'),kind)


class ChapterRunTests(unittest.TestCase):
    def test_new_owner_has_fresh_run_id_baseline_and_no_fake_clear(self):
        a,b=ChapterRun(),ChapterRun()
        self.assertNotEqual(a.run_id,b.run_id)
        self.assertEqual((a.chapter,a.current_stage,a.build,a.receipts,a.active_offer),(1,1,ChapterBuild(),(),None))

    def test_public_state_is_read_only(self):
        run=ChapterRun()
        for field in ('chapter','run_id','current_stage','build','active_offer','receipts','stats'):
            with self.assertRaises(AttributeError):
                setattr(run,field,None)

    def test_duplicate_pending_clear_reuses_offer_not_another_opportunity(self):
        run=ChapterRun()
        o=run.offer_after_clear(1,'stage-a')
        self.assertIs(run.offer_after_clear(1,'stage-a'),o)
        with self.assertRaises(ValueError):
            run.offer_after_clear(1,'stage-b')
        self.assertEqual(run.build,ChapterBuild())

    def test_first_selection_updates_build_and_next_stage_once(self):
        run=ChapterRun()
        receipt=choose(run,'hp')
        self.assertEqual((run.build,run.current_stage,run.stats.max_hp),(ChapterBuild(0,1,0),2,4))
        self.assertIsNone(run.active_offer)
        self.assertEqual(run.receipts,(receipt,))
        self.assertIs(run.verify_receipt(receipt),receipt)

    def test_same_or_different_selection_on_consumed_offer_is_rejected(self):
        run=ChapterRun()
        receipt=choose(run,'attack')
        for _ in range(3):
            for kind in UpgradeKind:
                with self.assertRaises(ValueError):
                    run.select(receipt.offer,kind)
        self.assertEqual((run.build,run.current_stage,len(run.receipts)),(ChapterBuild(1),2,1))

    def test_failed_choice_leaves_build_offer_and_history_unchanged(self):
        run=ChapterRun()
        o=run.offer_after_clear(1,'a')
        for bad in ('critical',None,True,1,[],{}):
            with self.assertRaises(ValueError):
                run.select(o,bad)
            self.assertEqual((run.build,run.active_offer,run.receipts,run.current_stage),(ChapterBuild(),o,(),1))
        self.assertEqual(run.select(o,'move').after_build,ChapterBuild(0,0,1))

    def test_max_rejection_does_not_consume_the_opportunity(self):
        run=ChapterRun()
        choose(run,'attack'); choose(run,'attack')
        o=run.offer_after_clear(3,'s3')
        self.assertTrue(o.options[0].is_max)
        with self.assertRaises(ValueError):
            run.select(o,'attack')
        self.assertIs(run.active_offer,o)
        self.assertEqual(len(run.receipts),2)
        run.select(o,'hp')
        self.assertEqual(run.build,ChapterBuild(2,1,0))

    def test_external_equal_or_modified_offers_are_not_owner_issued(self):
        run=ChapterRun()
        o=run.offer_after_clear(1,'a')
        for fake in (replace(o),replace(o,offer_id='forged'),replace(o,before_build=ChapterBuild(1)),None):
            with self.assertRaises(ValueError):
                run.select(fake,'attack')
        self.assertEqual(run.build,ChapterBuild())

    def test_external_copied_and_foreign_receipts_cannot_be_authenticated(self):
        run,foreign=ChapterRun(),ChapterRun(2)
        receipt=choose(run,'hp')
        forged=UpgradeReceipt(receipt.offer,receipt.kind,receipt.after_build)
        for fake in (forged,replace(receipt),None):
            with self.assertRaises(ValueError):
                run.verify_receipt(fake)
        with self.assertRaises(ValueError):
            foreign.verify_receipt(receipt)
        with self.assertRaises(ValueError):
            run.select(receipt,'attack')
        self.assertEqual(run.build,ChapterBuild(0,1,0))

    def test_wrong_stage_chapter_and_invalid_instance_are_rejected(self):
        run=ChapterRun()
        for stage in (True,0,-1,2,4,5,6,1.0,'1',None):
            with self.assertRaises(ValueError):
                run.offer_after_clear(stage,'a')
        for instance in ('',' ',None,True):
            with self.assertRaises(ValueError):
                run.offer_after_clear(1,instance)
        other=ChapterRun(2).offer_after_clear(6,'other')
        with self.assertRaises(ValueError):
            run.select(other,'hp')
        self.assertEqual(run.build,ChapterBuild())

    def test_all_four_choice_sequences_obey_caps_and_never_exhaust_candidates(self):
        for sequence in product(UpgradeKind,repeat=4):
            run=ChapterRun()
            for i,kind in enumerate(sequence):
                o=run.offer_after_clear(i+1,f's{i}')
                self.assertEqual(len(o.options),3)
                self.assertTrue(any(x.enabled for x in o.options))
                if o.before_build.level(kind)==(3 if kind is UpgradeKind.HP else 2):
                    with self.assertRaises(ValueError):
                        run.select(o,kind)
                    break
                run.select(o,kind)
                self.assertEqual(sum((run.build.attack_level,run.build.hp_level,run.build.move_level)),i+1)
            else:
                self.assertEqual((run.current_stage,len(run.receipts)),(5,4))
                with self.assertRaises(ValueError):
                    run.offer_after_clear(5,'boss')

    def test_stale_stage_one_offer_cannot_change_later_stage_build(self):
        run=ChapterRun()
        old=choose(run,'attack').offer
        next_offer=run.offer_after_clear(2,'s2')
        with self.assertRaises(ValueError):
            run.select(old,'move')
        self.assertIs(run.active_offer,next_offer)
        self.assertEqual(run.build,ChapterBuild(1))

    def test_consumed_combat_instance_cannot_claim_the_next_stage_opportunity(self):
        run=ChapterRun()
        receipt=choose(run,'hp')
        with self.assertRaises(ValueError):
            run.offer_after_clear(2,receipt.offer.stage_instance_id)
        self.assertEqual((run.build,run.current_stage,run.active_offer),(ChapterBuild(0,1,0),2,None))

    def test_boss_replay_keeps_four_choices_and_never_offers_a_fifth(self):
        run=ChapterRun()
        for kind in ('attack','hp','hp','move'):
            choose(run,kind)
        before=(run.run_id,run.build,run.receipts)
        for _ in range(4):
            self.assertEqual(run.boss_replay_stats(),run.build.stats)
            with self.assertRaises(ValueError):
                run.offer_after_clear(5,'boss')
        self.assertEqual((run.run_id,run.build,run.receipts),before)
        with self.assertRaises(ValueError):
            ChapterRun().boss_replay_stats()

    def test_game_over_returns_new_baseline_stage_one_and_retires_old_offers(self):
        old=ChapterRun()
        receipt=choose(old,'hp')
        pending=old.offer_after_clear(2,'s2')
        fresh=old.restart_after_game_over()
        self.assertEqual((fresh.chapter,fresh.current_stage,fresh.build,fresh.receipts),(1,1,ChapterBuild(),()))
        self.assertNotEqual(old.run_id,fresh.run_id)
        self.assertTrue(old.retired)
        for owner in (old,fresh):
            with self.assertRaises(ValueError):
                owner.select(pending,'attack')
        with self.assertRaises(ValueError):
            fresh.verify_receipt(receipt)
        self.assertIs(old.verify_receipt(receipt),receipt)  # Historical read only.

    def test_new_chapter_reset_is_only_a_model_not_playable_stage_six(self):
        old=ChapterRun()
        choose(old,'attack')
        fresh=old.start_chapter(2)
        self.assertEqual((fresh.chapter,fresh.current_stage,fresh.build),(2,6,ChapterBuild()))
        self.assertTrue(old.retired)
        with self.assertRaises(ValueError):
            old.offer_after_clear(2,'late')
        import main
        with self.assertRaises(ValueError):
            main._new_stage_game(10)

    def test_invalid_chapter_reset_does_not_retire_or_modify_current_owner(self):
        run=ChapterRun()
        o=run.offer_after_clear(1,'a')
        for bad in (True,0,6,1.0,None):
            with self.assertRaises(ValueError):
                run.start_chapter(bad)
            self.assertFalse(run.retired)
            self.assertIs(run.active_offer,o)


if __name__=='__main__':
    unittest.main()
