"""Stage-owned Pulse scheduling on EnemyEncounter's existing clock and ledger.

No damage, parry, movement, or independent simulation clock lives here.
Only boss-enabled encounters use this controller; generic King AI stays melee-only.
"""
from config import (KING_PULSE_FIRST_TICKS, KING_PULSE_TELEGRAPH_TICKS,
                    KING_PULSE_COOLDOWN_TICKS, KING_PULSE_CLEANUP_TICKS)


PULSE_CELLS = tuple((col, row) for row in range(10) for col in range(10))


class KingPulse:
    def __init__(self, encounter, king, start_tick):
        self.encounter = encounter
        self.king = king
        self.state = 'NORMAL'
        self.next_use_tick = start_tick + KING_PULSE_FIRST_TICKS
        self.event = None
        self._issued = {}
        self._drained_tick = None
        self.freeze_tick = None
        self.resume_tick = None
        self._remaining = {}
        self.stopped = False
        self._death_notified = False

    def owns(self, event):
        return (self._issued.get(event.key) == event and event.attack_kind == 'king_pulse'
                and event.source_entity_instance_id == self.king.entity_instance_id
                and self.encounter.ledger.state(event) != 'unknown')

    def _pending(self):
        # Movement plans may still require completion after ledger resolution.
        return bool(self.encounter.ledger.pending or self.encounter._attack_moves)

    def _king_ready(self, now):
        k = self.king
        return (k.active and k.current_attack is None and now >= k.next_action_tick
                and (k.state != 'stunned' or now >= k.stun_until_tick))

    def before_tick(self, now):
        if self.stopped:
            return
        if self.resume_tick is not None and now >= self.resume_tick:
            self._resume(now)
        if not self.king.active:
            return
        if self.state == 'NORMAL' and now >= self.next_use_tick:
            # Latch during a melee telegraph, then wait for its normal recovery.
            # Existing movement waits/recovery/stuns finish before requesting.
            if self._king_ready(now) or self.king.current_attack is not None:
                self.state = 'DRAINING'
                self._drained_tick = None
        if (self.state == 'DRAINING' and self._drained_tick is not None
                and now > self._drained_tick and not self._pending() and self._king_ready(now)):
            self._freeze(now)
            event = self.encounter.ledger.create(
                self.king.entity_instance_id, now, now + KING_PULSE_TELEGRAPH_TICKS,
                PULSE_CELLS, attack_kind='king_pulse')
            self.event = event
            self._issued[event.key] = event
            self.king.current_attack = event
            self.king.state = 'telegraph'
            self.king.next_action_tick = event.hit_tick
            self.encounter._attack_moves[event.key] = (event, self.king, self.king.position)
            self.state = 'PULSE_TELEGRAPH'
        if self.state == 'PULSE_TELEGRAPH' and now >= self.event.hit_tick:
            self.state = 'PULSE_RESOLUTION'

    def after_tick(self, now):
        if self.stopped:
            return
        if self.state == 'DRAINING':
            if self._pending():
                self._drained_tick = None
            elif self._drained_tick is None:
                self._drained_tick = now
        elif self.state in ('PULSE_TELEGRAPH', 'PULSE_RESOLUTION'):
            status = self.encounter.ledger.state(self.event)
            if status in ('resolved', 'cancelled'):
                self.state = 'CLEANUP'
                self.resume_tick = now + KING_PULSE_CLEANUP_TICKS
                self.next_use_tick = (self.event.hit_tick if status == 'resolved' else now) + KING_PULSE_COOLDOWN_TICKS
                if self.king.state != 'stunned':
                    self.king.state = 'recovering'
                    self.king.next_action_tick = self.resume_tick

    def blocks(self, enemy):
        if self.stopped:
            return True
        if self.freeze_tick is not None and enemy is not self.king:
            return True
        return self.state != 'NORMAL'

    def frozen(self, enemy):
        return self.freeze_tick is not None and enemy is not self.king

    def _freeze(self, now):
        self.freeze_tick = now
        self._remaining = {
            e.entity_instance_id: (e.state, max(0, e.next_action_tick - now),
                                   max(0, e.stun_until_tick - now))
            for e in self.encounter.enemies if e is not self.king and e.active}

    def _resume(self, now):
        for e in self.encounter.enemies:
            saved = self._remaining.get(e.entity_instance_id)
            if saved is not None and e.active:
                state, action, stun = saved
                e.state = state
                e.next_action_tick = now + action
                if state == 'stunned':
                    e.stun_until_tick = now + stun
        self._remaining.clear()
        self.freeze_tick = self.resume_tick = None
        self._drained_tick = None
        self.state = 'NORMAL'

    def king_died(self, tick):
        if self.stopped or self._death_notified:
            return
        self._death_notified = True
        # Even in DRAINING, suppress fresh reservations until the next tick.
        # Resolved receipts survive cancel_source() and the early release.
        if self.state != 'NORMAL' or self.freeze_tick is not None:
            self.state = 'CLEANUP'
            if self.resume_tick is None or self.resume_tick != tick + 1:
                self.resume_tick = tick + 1

    def stop(self):
        self.stopped = True
        self._remaining.clear()
        self.freeze_tick = self.resume_tick = None
        self.state = 'NORMAL'
