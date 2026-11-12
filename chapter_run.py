"""Pure chapter upgrade ownership, independent of combat and SDL.

The progression adapter must verify StageGame outcomes before requesting
offers. This model never observes or fabricates combat clears or unlocks.
"""
from uuid import uuid4

from upgrades import (ChapterBuild, UpgradeOffer, UpgradeReceipt,
                      chapter_first_stage, upgrade_kind, _identifier)


class ChapterRun:
    def __init__(self, chapter=1, *, entry_attack_level=0):
        first = chapter_first_stage(chapter)
        self._chapter = chapter
        self._run_id = uuid4().hex
        self._current_stage = first
        self._build = ChapterBuild(attack_level=entry_attack_level)
        self._entry_attack_level = entry_attack_level
        self._active_offer = None
        self._receipts = {}
        self._retired = False

    @property
    def entry_attack_level(self):
        return self._entry_attack_level

    @property
    def chapter(self):
        return self._chapter

    @property
    def run_id(self):
        return self._run_id

    @property
    def current_stage(self):
        return self._current_stage

    @property
    def build(self):
        return self._build

    @property
    def stats(self):
        return self.build.stats

    @property
    def active_offer(self):
        return self._active_offer

    @property
    def receipts(self):
        return tuple(self._receipts.values())

    @property
    def retired(self):
        return self._retired

    def _require_active(self):
        if self.retired:
            raise ValueError('Chapter run has been retired')

    def offer_after_clear(self, stage, stage_instance_id):
        """Accept one explicit ordinary-stage opportunity in chapter order.

        Repeated notification for the same still-open opportunity reuses its
        offer. A different instance cannot replace a pending choice.
        """
        self._require_active()
        if (type(stage) is not int or stage != self.current_stage
                or stage == chapter_first_stage(self.chapter) + 4):
            raise ValueError('Upgrade opportunity must match the current ordinary stage')
        _identifier(stage_instance_id)
        if self.active_offer is not None:
            if self.active_offer.stage_instance_id != stage_instance_id:
                raise ValueError('Another stage instance already owns this opportunity')
            return self.active_offer
        if any(r.offer.stage_instance_id == stage_instance_id for r in self.receipts):
            raise ValueError('A previous combat instance cannot supply another opportunity')
        self._active_offer = UpgradeOffer(self.run_id, uuid4().hex, self.chapter, stage,
                                          stage_instance_id, self.build)
        return self.active_offer

    def select(self, offer, kind):
        """Commit one owner-issued offer once; failures leave all state intact."""
        self._require_active()
        if (not isinstance(offer, UpgradeOffer) or offer is not self.active_offer
                or offer.run_id != self.run_id or offer.chapter != self.chapter
                or offer.stage != self.current_stage or offer.before_build != self.build):
            raise ValueError('Offer is stale, foreign, consumed or not owner-issued')
        kind = upgrade_kind(kind)
        after = self.build.upgraded(kind)
        receipt = UpgradeReceipt(offer, kind, after)
        self._receipts[offer.offer_id] = receipt
        self._build = after
        self._current_stage += 1
        self._active_offer = None
        return receipt

    def verify_receipt(self, receipt):
        """Read-only authentication. Receipts can never be applied as commands.

        Equal-looking, copied or externally constructed receipts are not issued
        by this owner. This is in-process API ownership, not a security sandbox.
        """
        if (not isinstance(receipt, UpgradeReceipt) or receipt.run_id != self.run_id
                or self._receipts.get(receipt.offer.offer_id) is not receipt):
            raise ValueError('Receipt was not issued by this chapter run')
        return receipt

    def boss_replay_stats(self):
        """Return retained stats for a fresh boss session, without another offer.

        The caller must verify BOSS_CLEAR; no actual replay occurs here.
        """
        self._require_active()
        if self.current_stage != chapter_first_stage(self.chapter) + 4:
            raise ValueError('Boss replay requires all four ordinary choices')
        return self.stats

    def restart_after_game_over(self):
        """New unupgraded run at this chapter's start (Stage 1 for Chapter 1)."""
        self._require_active()
        fresh = ChapterRun(self.chapter, entry_attack_level=self.entry_attack_level)
        self.retire()
        return fresh

    def start_chapter(self, chapter):
        """Pure reset, not an unlock or a playable later-stage constructor."""
        self._require_active()
        fresh = ChapterRun(chapter, entry_attack_level=self.build.attack_level)
        self.retire()
        return fresh

    def retire(self):
        """Invalidate pending commands on application exit; retain read-only history."""
        if self.retired:
            return False
        self._active_offer = None
        self._retired = True
        return True
