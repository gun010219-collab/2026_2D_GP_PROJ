"""Deterministic Stage 1 HP resolution; no SDL, rendering or private clock.

Current-tick input is processed before resolve_current_tick(), following the
PDF p.7 order. Historical catch-up is settled one integer tick at a time.
Actual parry adjudication is deliberately deferred to Task 1-G.
"""
from dataclasses import dataclass

from board import in_bounds
from combat import AttackEvent, Combat, _duration_ticks
from config import (
    PAWN_ATTACK_DAMAGE, PLAYER_ATTACK_DAMAGE,
    PLAYER_HIT_INVULNERABILITY_SECONDS,
)
from enemy import Enemy
from enemy_attack import EnemyAttackEvent
from enemy_behaviors import PawnEncounter
from health import Health
from player import Player


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
                 pawn_damage=PAWN_ATTACK_DAMAGE):
        if not isinstance(player, Player):
            raise TypeError('Damage target/source must be a Player')
        if not isinstance(combat, Combat) or not isinstance(encounter, PawnEncounter):
            raise TypeError('Resolution requires a Combat and PawnEncounter')
        self._validate_damage(player_damage)
        self._validate_damage(pawn_damage)
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
        self.player_invulnerability_ticks = _duration_ticks(PLAYER_HIT_INVULNERABILITY_SECONDS)
        self.player_invulnerable_until_tick = 0
        self._validate_entities()
        # A restarted stage can share a Combat clock, but never player events.
        self.combat.bind_stage(encounter.ledger.stage_instance_id)

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

    def _apply(self, event, source_id, target):
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
        result = None
        if targets:
            target = targets[0]
            if self.combat.consume_attack(event, target.entity_instance_id):
                result = self._apply(event, self._player_id, target)
                if not target.alive:
                    self.encounter.deactivate(target.entity_instance_id)
        self.combat.finish_attack(event)
        return result

    def resolve_enemy_attack(self, event):
        """Adjudicate only an authentic due event at its exact hit_tick.

        Misses and invulnerability close the event without a damage receipt.
        This is the Task 1-G connection point for EnemyAttackEvent together
        with the input-tick ParryAttempt, before the consume/apply boundary.
        """
        self._validate_entities()
        self._validate_damage(self.pawn_damage)
        ledger = self.encounter.ledger
        if not isinstance(event, EnemyAttackEvent) or ledger.state(event) == 'unknown':
            raise ValueError('Enemy attack was not scheduled for this combat/stage')
        source = self._enemies.get(event.source_entity_instance_id)
        if source is None:
            raise ValueError('Enemy attack source does not match this encounter')
        state = ledger.state(event)
        if state in ('cancelled', 'resolved'):
            return None
        if not source.active:
            self.encounter.deactivate(source.entity_instance_id)
            return None
        if self.combat.tick < event.hit_tick or state != 'due':
            return None
        if self.combat.tick > event.hit_tick:
            ledger.finish(event, 'expired')
            return None
        if not self.player.alive:
            ledger.finish(event, 'target_dead')
            return None
        if self.player.position not in event.target_cells:
            ledger.finish(event, 'miss')
            return None
        if self.combat.tick < self.player_invulnerable_until_tick:
            ledger.finish(event, 'invulnerable')
            return None
        if not ledger.consume(event, self._player_id):
            ledger.finish(event, 'expired')
            return None
        result = self._apply(event, source.entity_instance_id, self.player)
        self.player_invulnerable_until_tick = self.combat.tick + self.player_invulnerability_ticks
        ledger.finish(event, 'hit')
        return result

    def resolve_current_tick(self):
        """Run current-tick AI/due events after current-tick player inputs.

        At most one tick may be pending. Repeated calls at an already settled
        tick are harmless; stale bulk advancement is rejected instead of
        applying a historical hit against a later player position.
        """
        self._validate_entities()
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
        return tuple(results)

    def advance(self, ticks=1):
        """Settle historical ticks sequentially, stopping safely on death."""
        if type(ticks) is not int:
            raise TypeError('Resolution ticks must be an integer')
        if ticks < 0:
            raise ValueError('Resolution ticks cannot move backwards')
        if not self.player.alive:
            return ()
        results = list(self.resolve_current_tick())
        for _ in range(ticks):
            if not self.player.alive:
                break
            self.combat.advance()
            results.extend(self.resolve_current_tick())
        return tuple(results)
