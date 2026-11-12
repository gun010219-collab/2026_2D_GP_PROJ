"""Deterministic supported-enemy HP resolution; no SDL/render/private clock.

Current-tick input is processed before resolve_current_tick(), following the
PDF p.7 order. Historical catch-up is settled one integer tick at a time.
Parry links are selected at input, adjudicated at hit_tick, and never inferred
from the input-relative preview ring.
"""
from dataclasses import dataclass

from board import in_bounds
from combat import AttackEvent, Combat, _duration_ticks
from config import (
    PAWN_ATTACK_DAMAGE, PLAYER_ATTACK_DAMAGE, ROOK_ATTACK_DAMAGE,
    KNIGHT_ATTACK_DAMAGE, BISHOP_ATTACK_DAMAGE, KING_ATTACK_DAMAGE,
    PLAYER_HIT_INVULNERABILITY_SECONDS,
    KING_PULSE_REFLECT_DAMAGE,
)
from enemy import Enemy
from enemy_attack import EnemyAttackEvent
from enemy_behaviors import EnemyEncounter
from health import Health
from player import Player
from parry import Parry, ParryAttempt
from parry_resolution import ParryBinding, ParryResult, grade_for_delta


@dataclass(frozen=True)
class DamageResult:
    attack_key: tuple
    source_entity_instance_id: str
    target_entity_instance_id: str
    tick: int
    amount: int
    hp_before: int
    hp_after: int


class CombatResolver:
    def __init__(self, player, combat, encounter, *,
                 player_damage=PLAYER_ATTACK_DAMAGE,
                 pawn_damage=PAWN_ATTACK_DAMAGE, parry=None, rook_damage=ROOK_ATTACK_DAMAGE,
                 knight_damage=KNIGHT_ATTACK_DAMAGE, bishop_damage=BISHOP_ATTACK_DAMAGE,
                 king_damage=KING_ATTACK_DAMAGE):
        if not isinstance(player, Player):
            raise TypeError('Damage target/source must be a Player')
        if not isinstance(combat, Combat) or not isinstance(encounter, EnemyEncounter):
            raise TypeError('Resolution requires a Combat and EnemyEncounter')
        self._validate_damage(player_damage)
        self._validate_damage(pawn_damage)
        self._validate_damage(rook_damage)
        self._validate_damage(knight_damage)
        self._validate_damage(bishop_damage)
        self._validate_damage(king_damage)
        if parry is not None and not isinstance(parry, Parry):
            raise TypeError('Parry input model must be a Parry')
        self.player = player
        self.combat = combat
        self.encounter = encounter
        self._player_ref = player
        self._combat_ref = combat
        self._encounter_ref = encounter
        self._player_id = player.entity_instance_id
        self._enemies = {e.entity_instance_id: e for e in encounter.enemies}
        if self._player_id in self._enemies:
            raise ValueError('Player and enemy instance IDs must be distinct')
        self.player_damage = player_damage
        self.pawn_damage = pawn_damage
        self.rook_damage = rook_damage
        self.knight_damage = knight_damage
        self.bishop_damage = bishop_damage
        self.king_damage = king_damage
        self.player_invulnerability_ticks = _duration_ticks(PLAYER_HIT_INVULNERABILITY_SECONDS)
        self.player_invulnerable_until_tick = 0
        self.parry = parry
        self._parry_ref = parry
        self._parry_bindings = {}
        self._parry_attempts = {}
        self._linked_events = {}
        self._event_parries = {}
        self._parry_results = {}
        self._last_parry_result = None
        self._stopped = False
        self._validate_entities()
        # A restarted stage can share a Combat clock, but never player events.
        self.combat.bind_stage(encounter.ledger.stage_instance_id)
        if self.parry is not None:
            self.parry.bind_stage(encounter.ledger.stage_instance_id)

    @property
    def last_parry_result(self):
        return self._last_parry_result

    @property
    def stopped(self):
        return self._stopped

    def stop(self):
        """Retire a terminal session without deleting receipts or old results."""
        if self.stopped:
            return False
        for enemy in self.encounter.enemies:
            self.encounter.cancel_attacks(enemy.entity_instance_id, tick=self.combat.tick)
        self._close_invalid_parries()
        self._stopped = True
        if self.encounter.pulse is not None:
            self.encounter.pulse.stop()
        return True

    def parry_binding(self, attempt):
        return self._parry_bindings.get(attempt.key) if isinstance(attempt, ParryAttempt) else None

    def parry_result(self, attempt):
        return self._parry_results.get(attempt.key) if isinstance(attempt, ParryAttempt) else None

    def _record_parry_result(self, binding, status, reason):
        if binding.attempt_key in self._parry_results:
            return self._parry_results[binding.attempt_key]
        result = ParryResult(binding.parry_id, status, self.combat.tick,
                             tuple(self.player.position), binding.linked_enemy_event_key, reason)
        self._parry_results[binding.attempt_key] = result
        self._last_parry_result = result
        return result

    def register_parry(self, attempt):
        """Bind a genuine newly emitted attempt to one existing telegraph.

        The attempt/cooldown is spent even when unbound. Never scan again for
        a later event; a repeated delivery returns its original immutable link.
        """
        if self.stopped:
            return None
        self._validate_entities()
        if (self.parry is None or self.parry is not self._parry_ref
                or self.parry.stage_instance_id != self.encounter.ledger.stage_instance_id
                or not self.parry.owns(attempt)):
            raise ValueError('Parry attempt was not emitted for this input model/stage')
        if attempt.key in self._parry_bindings:
            return self._parry_bindings[attempt.key]
        if attempt.start_tick != self.combat.tick:
            raise ValueError('A parry attempt must be registered at its input tick')
        if not self.player.alive:
            raise ValueError('A dead player cannot register a parry attempt')
        ledger = self.encounter.ledger
        candidates = []
        for event in ledger.telegraphs:
            source = self._enemies.get(event.source_entity_instance_id)
            if (event.combat_session_id == ledger.combat_session_id
                    and event.stage_instance_id == ledger.stage_instance_id
                    and source is not None and source.active
                    and ledger.state(event) == 'telegraph'
                    and event.telegraph_start_tick <= self.combat.tick
                    and self.player.position in event.target_cells
                    and grade_for_delta(event.hit_tick - attempt.start_tick) is not None
                    and event.key not in self._event_parries):
                candidates.append(event)
        # Numeric IDs are stable JSON publication order within this ledger;
        # the complete scoped key is a final tie-break, never an unscoped ID.
        event = min(candidates, key=lambda e: (e.hit_tick, e.attack_id, e.key)) if candidates else None
        binding = ParryBinding(attempt.key, attempt.parry_id, attempt.start_tick,
                               event.key if event else None, event.hit_tick if event else None,
                               grade_for_delta(event.hit_tick - attempt.start_tick) if event else None)
        self._parry_bindings[attempt.key] = binding
        self._parry_attempts[attempt.key] = attempt
        if event is None:
            self._record_parry_result(binding, 'unbound', 'no_eligible_attack')
        else:
            self._linked_events[event.key] = event
            self._event_parries[event.key] = binding
        return binding

    def _fail_parry(self, event, reason):
        binding = self._event_parries.get(event.key)
        if binding is not None:
            self._record_parry_result(binding, 'failed', reason)

    def _close_invalid_parries(self):
        """Cancellation/death can finish a link without ever publishing due."""
        for event_key, binding in self._event_parries.items():
            if binding.attempt_key in self._parry_results:
                continue
            event = self._linked_events[event_key]
            state = self.encounter.ledger.state(event)
            source = self._enemies.get(event.source_entity_instance_id)
            attempt = self._parry_attempts[binding.attempt_key]
            if (self.parry is not self._parry_ref or self.parry is None
                    or self.parry.stage_instance_id != self.encounter.ledger.stage_instance_id
                    or not self.parry.owns(attempt)):
                self._record_parry_result(binding, 'failed', 'stale_attempt')
            elif state in ('cancelled', 'unknown', 'resolved'):
                self._record_parry_result(binding, 'failed', state)
            elif source is None or not source.active:
                self._record_parry_result(binding, 'failed', 'source_dead')
            elif not self.player.alive:
                self._record_parry_result(binding, 'failed', 'target_dead')
            elif self.combat.tick > event.hit_tick:
                self._record_parry_result(binding, 'failed', 'expired')

    @staticmethod
    def _validate_damage(amount):
        if type(amount) is not int:
            raise TypeError('Damage must be an integer')
        if amount <= 0:
            raise ValueError('Damage must be positive')

    def _validate_entities(self):
        if self.combat is not self._combat_ref or self.encounter is not self._encounter_ref:
            raise ValueError('Combat/encounter references do not match this resolver')
        if (self.player is not self._player_ref or not isinstance(self.player, Player)
                or self.player.entity_instance_id != self._player_id
                or not isinstance(self.player.health, Health)
                or not in_bounds(*self.player.position)):
            raise ValueError('Player reference does not match this encounter')
        if (len(self.encounter.enemies) != len(self._enemies)
                or any(not isinstance(e, Enemy) or self._enemies.get(e.entity_instance_id) is not e
                       or not isinstance(e.health, Health) or not in_bounds(*e.position)
                       for e in self.encounter.enemies)):
            raise ValueError('Enemy references do not match this encounter')

    def _apply(self, event, source_id, target, amount=None):
        if amount is None:
            amount = self.player_damage if target is not self.player else self.pawn_damage
        before = target.health.current_hp
        actual = target.health.apply_damage(amount, tick=self.combat.tick)
        return DamageResult(event.key, source_id, target.entity_instance_id,
                            self.combat.tick, actual, before, target.health.current_hp)

    def resolve_player_attack(self, event):
        """Resolve the newly emitted immutable target once, including misses.

        Duplicate deliveries return None. Unknown/modified events and foreign
        entity references are rejected before a receipt or HP can be changed.
        A visual effect is never a new attack, even at the same tick.
        """
        if self.stopped:
            return None
        self._validate_entities()
        self._validate_damage(self.player_damage)
        if not isinstance(event, AttackEvent) or self.combat.attack_state(event) == 'unknown':
            raise ValueError('Player attack was not emitted for this combat/stage')
        if event.source_entity_instance_id != self._player_id:
            raise ValueError('Player attack source does not match this encounter')
        if self.combat.attack_state(event) != 'pending':
            return None
        if event.start_tick > self.combat.tick:
            raise ValueError('Player attack cannot resolve before its start tick')
        if event.start_tick != self.combat.tick or not self.player.alive:
            self.combat.finish_attack(event)
            return None
        targets = [e for e in self.encounter.enemies if e.active and e.position == event.target_cell]
        if len(targets) > 1:
            raise ValueError('Multiple active enemies occupy the attack target')
        amount = self.player_damage + self.combat.attack_damage_bonus(event)
        result = None
        if targets:
            target = targets[0]
            if self.combat.consume_attack(event, target.entity_instance_id):
                result = self._apply(event, self._player_id, target, amount)
                if not target.alive:
                    self.encounter.deactivate(target.entity_instance_id, tick=self.combat.tick)
                    self._close_invalid_parries()
        self.combat.finish_attack(event)
        return result

    def resolve_enemy_attack(self, event):
        result = self._adjudicate_enemy_attack(event)
        if not self.stopped and isinstance(event, EnemyAttackEvent):
            self.encounter.complete_attack(event, self.player.position)
        return result

    def _adjudicate_enemy_attack(self, event):
        """Adjudicate only an authentic due event at its exact hit_tick.

        Misses and invulnerability close the event without a damage receipt.
        A bound ParryAttempt is evaluated before HP reduction, after exact
        time, position, death and existing hit-invulnerability checks.
        """
        if self.stopped:
            return None
        self._validate_entities()
        self._validate_damage(self.pawn_damage)
        self._validate_damage(self.rook_damage)
        self._validate_damage(self.knight_damage)
        self._validate_damage(self.bishop_damage)
        self._validate_damage(self.king_damage)
        self._close_invalid_parries()
        ledger = self.encounter.ledger
        if not isinstance(event, EnemyAttackEvent) or ledger.state(event) == 'unknown':
            raise ValueError('Enemy attack was not scheduled for this combat/stage')
        source = self._enemies.get(event.source_entity_instance_id)
        if source is None:
            raise ValueError('Enemy attack source does not match this encounter')
        state = ledger.state(event)
        if state == 'cancelled':
            self._fail_parry(event, 'cancelled')
            return None
        if state == 'resolved':
            return None
        if not source.active:
            self.encounter.deactivate(source.entity_instance_id, tick=self.combat.tick)
            self._fail_parry(event, 'source_dead')
            return None
        if self.combat.tick < event.hit_tick or state != 'due':
            return None
        if self.encounter.tick != self.combat.tick:
            raise ValueError('Enemy adjudication requires the encounter at the current combat tick')
        if self.combat.tick > event.hit_tick:
            ledger.finish(event, 'expired')
            self._fail_parry(event, 'expired')
            return None
        if not self.encounter.prepare_attack(event):
            self._fail_parry(event, 'cancelled')
            return None
        if not self.player.alive:
            ledger.finish(event, 'target_dead')
            self._fail_parry(event, 'target_dead')
            return None
        if self.player.position not in event.target_cells:
            ledger.finish(event, 'miss')
            self._fail_parry(event, 'evaded')
            return None
        if self.combat.tick < self.player_invulnerable_until_tick:
            ledger.finish(event, 'invulnerable')
            self._fail_parry(event, 'invulnerable')
            return None
        binding = self._event_parries.get(event.key)
        if (binding is not None and binding.attempt_key not in self._parry_results
                and binding.expected_hit_tick == self.combat.tick
                and binding.adjudication_grade == grade_for_delta(event.hit_tick - binding.parry_start_tick)
                and binding.adjudication_grade in ('normal', 'perfect')):
            if not ledger.consume(event, self._player_id):
                ledger.finish(event, 'expired')
                self._fail_parry(event, 'already_consumed')
                return None
            ledger.finish(event, 'parried_' + binding.adjudication_grade)
            result = self._record_parry_result(binding, binding.adjudication_grade, 'success')
            if binding.adjudication_grade == 'perfect':
                pulse = self.encounter.is_pulse(event)
                self.encounter.stun(source.entity_instance_id, self.combat.tick)
                self.combat.grant_perfect_counter()
                if pulse:
                    self._apply(event, self._player_id, source, KING_PULSE_REFLECT_DAMAGE)
                    if not source.alive:
                        self.encounter.deactivate(source.entity_instance_id, tick=self.combat.tick)
            return result
        if not ledger.consume(event, self._player_id):
            ledger.finish(event, 'expired')
            self._fail_parry(event, 'already_consumed')
            return None
        amount = {'pawn': self.pawn_damage, 'rook': self.rook_damage,
                  'knight': self.knight_damage, 'bishop': self.bishop_damage,
                  'king': self.king_damage}[source.kind]
        result = self._apply(event, source.entity_instance_id, self.player, amount)
        self.player_invulnerable_until_tick = self.combat.tick + self.player_invulnerability_ticks
        ledger.finish(event, 'hit')
        return result

    def resolve_current_tick(self):
        """Run current-tick AI/due events after current-tick player inputs.

        At most one tick may be pending. Repeated calls at an already settled
        tick are harmless; stale bulk advancement is rejected instead of
        applying a historical hit against a later player position.
        """
        if self.stopped:
            return ()
        self._validate_entities()
        self._close_invalid_parries()
        if self.encounter.tick == self.combat.tick:
            return ()
        if self.encounter.tick != self.combat.tick - 1:
            raise ValueError('Encounter must resolve every combat tick in order')
        if not self.player.alive:
            return ()
        due = self.encounter.advance_to(self.combat.tick, self.player.position)
        results = []
        for event in due:
            result = self.resolve_enemy_attack(event)
            if result is not None:
                results.append(result)
        self.encounter.finish_tick()
        self._close_invalid_parries()
        return tuple(results)

    def advance(self, ticks=1):
        """Settle historical ticks sequentially, stopping safely on death."""
        if type(ticks) is not int:
            raise TypeError('Resolution ticks must be an integer')
        if ticks < 0:
            raise ValueError('Resolution ticks cannot move backwards')
        if self.stopped or not self.player.alive:
            return ()
        results = list(self.resolve_current_tick())
        for _ in range(ticks):
            if not self.player.alive:
                break
            self.combat.advance()
            results.extend(self.resolve_current_tick())
        return tuple(results)
