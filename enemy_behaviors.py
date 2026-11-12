"""Shared tick/ledger lifecycle for supported enemies, including King melee."""
from board import in_bounds
from combat import _duration_ticks
from config import (
    PAWN_MOVE_INTERVAL_SECONDS, PAWN_RECOVERY_SECONDS, PAWN_TELEGRAPH_SECONDS,
    PERFECT_PARRY_STUN_SECONDS, ROOK_MOVE_INTERVAL_SECONDS,
    ROOK_RECOVERY_SECONDS, ROOK_TELEGRAPH_SECONDS,
    KNIGHT_RECOVERY_SECONDS, KNIGHT_TELEGRAPH_SECONDS,
    BISHOP_RECOVERY_SECONDS, BISHOP_TELEGRAPH_SECONDS,
    KING_MOVE_INTERVAL_SECONDS, KING_RECOVERY_SECONDS, KING_TELEGRAPH_SECONDS,
)
from enemy import Enemy
from enemy_attack import EnemyAttackLedger
from rook_behavior import attack_path, choose_move
from knight_behavior import choose_landing
from bishop_behavior import color_targets
from king_behavior import choose_move as choose_king_move, melee_target


# Stable tie order; movement does not change the JSON attack-facing vector.
PAWN_MOVE_STEPS = ((0, 1), (0, -1), (-1, 0), (1, 0))


class EnemyEncounter:
    def __init__(self, enemies, start_tick=0, combat_session_id=None, stage_instance_id=None):
        self._validate_tick(start_tick)
        self.enemies = tuple(enemies)
        if any(not isinstance(e, Enemy) or e.kind not in ('pawn', 'rook', 'knight', 'bishop', 'king') for e in self.enemies):
            raise ValueError('Encounter supports live Pawn/Rook/Knight/Bishop/King instances only')
        self.ledger = EnemyAttackLedger(combat_session_id, stage_instance_id)
        self.move_ticks = _duration_ticks(PAWN_MOVE_INTERVAL_SECONDS)
        self.telegraph_ticks = _duration_ticks(PAWN_TELEGRAPH_SECONDS)
        self.recovery_ticks = _duration_ticks(PAWN_RECOVERY_SECONDS)
        self.rook_move_ticks = _duration_ticks(ROOK_MOVE_INTERVAL_SECONDS)
        self.rook_telegraph_ticks = _duration_ticks(ROOK_TELEGRAPH_SECONDS)
        self.rook_recovery_ticks = _duration_ticks(ROOK_RECOVERY_SECONDS)
        self.knight_telegraph_ticks = _duration_ticks(KNIGHT_TELEGRAPH_SECONDS)
        self.knight_recovery_ticks = _duration_ticks(KNIGHT_RECOVERY_SECONDS)
        self.bishop_telegraph_ticks = _duration_ticks(BISHOP_TELEGRAPH_SECONDS)
        self.bishop_recovery_ticks = _duration_ticks(BISHOP_RECOVERY_SECONDS)
        self.king_move_ticks = _duration_ticks(KING_MOVE_INTERVAL_SECONDS)
        self.king_telegraph_ticks = _duration_ticks(KING_TELEGRAPH_SECONDS)
        self.king_recovery_ticks = _duration_ticks(KING_RECOVERY_SECONDS)
        self.tick = start_tick - 1
        self._movement_history = {}
        self._attack_moves = {}
        # Live non-Pawn plans share one store, including stationary attacks.
        # Only the last release per color is needed, not another event ledger.
        self._bishop_closed_tick = {}
        if len({e.entity_instance_id for e in self.enemies}) != len(self.enemies):
            raise ValueError('Duplicate enemy instance IDs')
        if len({e.data_id for e in self.enemies}) != len(self.enemies):
            raise ValueError('Duplicate enemy data IDs')
        for enemy in self.enemies:
            enemy.state = 'initial_wait' if enemy.alive else 'inactive'
            enemy.current_attack = None
            enemy.stun_until_tick = 0
            enemy.next_action_tick = start_tick + enemy.initial_delay_ticks
        self._check_occupancy()

    @staticmethod
    def _validate_tick(tick):
        if type(tick) is not int or tick < 0:
            raise ValueError('Encounter tick must be a nonnegative integer')

    @property
    def occupied_cells(self):
        return frozenset(e.position for e in self.enemies if e.active)

    def _check_occupancy(self, player_cell=None):
        positions = [e.position for e in self.enemies if e.active]
        if (len(positions) != len(set(positions)) or not all(in_bounds(*p) for p in positions)
                or player_cell in positions):
            raise ValueError('Encounter contains overlapping or out-of-bounds occupied cells')

    def _recovery_ticks(self, enemy):
        return {'pawn': self.recovery_ticks, 'rook': self.rook_recovery_ticks,
                'knight': self.knight_recovery_ticks, 'bishop': self.bishop_recovery_ticks,
                'king': self.king_recovery_ticks}[enemy.kind]

    def _choose_move(self, enemy, player_cell):
        """Greedy one-cell pursuit with bounded memory, not a pathfinder.

        A fixed player/obstacle arrangement never revisits a cell. This permits
        a short detour without repeatedly bouncing back into the same dead end.
        Changed player/other-Pawn positions reopen previously visited cells.
        """
        occupied = self.occupied_cells - {enemy.position}
        context = player_cell, occupied
        previous_context, visited = self._movement_history.get(
            enemy.entity_instance_id, (None, set()))
        if previous_context != context:
            visited = {enemy.position}
            self._movement_history[enemy.entity_instance_id] = context, visited
        col, row = enemy.position
        candidates = [(col + dx, row + dy) for dx, dy in PAWN_MOVE_STEPS]
        candidates = [cell for cell in candidates if in_bounds(*cell)
                      and cell != player_cell and cell not in occupied and cell not in visited]
        if not candidates:
            return enemy.position
        # min keeps the first tied candidate: up, down, left, right.
        target = min(candidates, key=lambda cell: abs(cell[0] - player_cell[0])
                     + abs(cell[1] - player_cell[1]))
        visited.add(target)
        return target

    def advance_to(self, tick, player_cell):
        """Process each elapsed integer tick once, in stable JSON enemy order.

        Returns only newly due events. They remain unconsumed; callers must not
        interpret a due event as damage or a parry result.
        """
        self._validate_tick(tick)
        if tick < self.tick:
            raise ValueError('Encounter time cannot move backwards')
        if not isinstance(player_cell, (tuple, list)) or len(player_cell) != 2 or not in_bounds(*player_cell):
            raise ValueError('Player cell must be in bounds')
        player_cell = tuple(player_cell)
        self._check_occupancy(player_cell)
        due = []
        for now in range(self.tick + 1, tick + 1):
            for enemy in self.enemies:
                if not enemy.alive and enemy.state != 'inactive':
                    self.deactivate(enemy.entity_instance_id, tick=now)
                if not enemy.active:
                    continue
                recovery_ticks = self._recovery_ticks(enemy)
                if enemy.state == 'stunned':
                    if now < enemy.stun_until_tick:
                        continue
                    # Expiration creates a fresh ready action; cancelled attack
                    # snapshots are never reused or moved to a later hit tick.
                    enemy.state = 'waiting'
                    enemy.next_action_tick = enemy.stun_until_tick
                if enemy.current_attack is not None:
                    event = enemy.current_attack
                    if self.ledger.state(event) == 'cancelled':
                        self._discard_attack_moves(enemy.entity_instance_id, tick=now)
                        enemy.current_attack = None
                        enemy.state = 'waiting'
                        enemy.next_action_tick = now + recovery_ticks
                    elif now >= event.hit_tick:
                        if self.ledger.mark_due(event, now):
                            due.append(event)
                        enemy.current_attack = None
                        enemy.state = 'recovering'
                        enemy.next_action_tick = event.hit_tick + recovery_ticks
                    continue
                if any(source is enemy for _, source, _ in self._attack_moves.values()):
                    # AI-only callers must adjudicate a due move before advancing it.
                    continue
                if now < enemy.next_action_tick:
                    continue
                if enemy.kind == 'rook':
                    self._begin_rook_action(enemy, player_cell, now)
                    continue
                if enemy.kind == 'knight':
                    self._begin_knight_action(enemy, player_cell, now)
                    continue
                if enemy.kind == 'bishop':
                    self._begin_bishop_action(enemy, now)
                    continue
                if enemy.kind == 'king':
                    self._begin_king_action(enemy, player_cell, now)
                    continue
                # A single ready-action reservation: attack takes priority over moving.
                col, row = enemy.position
                forward_col, forward_row = col + enemy.forward[0], row + enemy.forward[1]
                diagonal_cells = ((forward_col - 1, forward_row), (forward_col + 1, forward_row))
                if player_cell in diagonal_cells and in_bounds(*player_cell):
                    enemy.current_attack = self.ledger.create(
                        enemy.entity_instance_id, now, now + self.telegraph_ticks, (player_cell,))
                    enemy.state = 'telegraph'
                    enemy.next_action_tick = enemy.current_attack.hit_tick
                else:
                    enemy.col, enemy.row = self._choose_move(enemy, player_cell)
                    enemy.state = 'waiting'
                    enemy.next_action_tick = now + self.move_ticks
            # All AI moves for this tick precede damage. A later JSON entry can
            # obstruct a dash already marked due by an earlier entry.
            self._cancel_obstructed_moves(now)
        self.tick = tick
        return tuple(event for event in due if self.ledger.state(event) == 'due')

    def _begin_king_action(self, enemy, player_cell, tick):
        target = melee_target(enemy.position, player_cell)
        if target is not None:
            enemy.current_attack = self.ledger.create(
                enemy.entity_instance_id, tick, tick + self.king_telegraph_ticks, (target,))
            self._attack_moves[enemy.current_attack.key] = (enemy.current_attack, enemy, enemy.position)
            enemy.state = 'telegraph'
            enemy.next_action_tick = enemy.current_attack.hit_tick
        else:
            enemy.col, enemy.row = choose_king_move(
                enemy.position, player_cell, self.occupied_cells - {enemy.position})
            enemy.state = 'waiting'
            enemy.next_action_tick = tick + self.king_move_ticks

    def _begin_rook_action(self, enemy, player_cell, tick):
        occupied = self.occupied_cells - {enemy.position}
        path = attack_path(enemy.position, player_cell, occupied)
        if path:
            enemy.current_attack = self.ledger.create(
                enemy.entity_instance_id, tick, tick + self.rook_telegraph_ticks, path)
            self._attack_moves[enemy.current_attack.key] = (enemy.current_attack, enemy, enemy.position)
            enemy.state = 'telegraph'
            enemy.next_action_tick = enemy.current_attack.hit_tick
        else:
            enemy.col, enemy.row = choose_move(enemy.position, player_cell, occupied)
            enemy.state = 'waiting'
            enemy.next_action_tick = tick + self.rook_move_ticks

    def _begin_knight_action(self, enemy, player_cell, tick):
        target = choose_landing(enemy.position, player_cell, self.occupied_cells - {enemy.position})
        if target is None:
            # No legal landing: bounded idle retry, not an invented move timer.
            enemy.state = 'waiting'
            enemy.next_action_tick = tick + self.knight_recovery_ticks
            return
        enemy.current_attack = self.ledger.create(
            enemy.entity_instance_id, tick, tick + self.knight_telegraph_ticks, (target,))
        self._attack_moves[enemy.current_attack.key] = (enemy.current_attack, enemy, enemy.position)
        enemy.state = 'telegraph'
        enemy.next_action_tick = enemy.current_attack.hit_tick

    def _begin_bishop_action(self, enemy, tick):
        opposite = 1 - sum(enemy.position) % 2
        pending_opposite = any(source.kind == 'bishop' and sum(origin) % 2 == opposite
                              and self.ledger.state(event) in ('telegraph', 'due')
                              for event, source, origin in self._attack_moves.values())
        if pending_opposite or self._bishop_closed_tick.get(opposite) == tick:
            # Approved: no event/cooldown is spent while waiting; try next tick.
            enemy.state = 'waiting'
            enemy.next_action_tick = tick + 1
            return
        enemy.current_attack = self.ledger.create(
            enemy.entity_instance_id, tick, tick + self.bishop_telegraph_ticks,
            color_targets(enemy.position))
        self._attack_moves[enemy.current_attack.key] = (enemy.current_attack, enemy, enemy.position)
        enemy.state = 'telegraph'
        enemy.next_action_tick = enemy.current_attack.hit_tick

    def _cancel_obstructed_moves(self, tick):
        """Approved policy: cancel the WHOLE snapshot, recover from cancel tick.

        Never shrink target_cells, reserve cells or alter Pawn movement. Check
        after AI and each completed move, before subsequent adjudication.
        Rook checks its whole path; Knight checks its single landing only.
        """
        for event, source, origin in tuple(self._attack_moves.values()):
            if source.kind in ('bishop', 'king'):
                continue  # Stationary attacks have no movement path to obstruct.
            if self.ledger.state(event) not in ('telegraph', 'due'):
                continue
            occupied = self.occupied_cells - {source.position}
            if source.position != origin or any(cell in occupied for cell in event.target_cells):
                self.ledger.cancel(event)
                self._discard_attack_moves(source.entity_instance_id)
                source.current_attack = None
                if source.active and source.state != 'stunned':
                    source.state = 'recovering'
                    source.next_action_tick = tick + self._recovery_ticks(source)

    def prepare_attack(self, event):
        """Verify a non-Pawn attack has an actual AI-issued plan, not just an ID."""
        source = next((e for e in self.enemies
                       if e.entity_instance_id == event.source_entity_instance_id), None)
        if source is not None and source.kind in ('rook', 'knight', 'bishop', 'king'):
            plan = self._attack_moves.get(event.key)
            if plan is None or plan[0] != event or plan[1] is not source:
                action = {'rook': 'dash', 'knight': 'jump', 'bishop': 'color attack', 'king': 'melee'}[source.kind]
                raise ValueError(f'{source.kind.title()} attack has no matching live {action} plan')
            self._cancel_obstructed_moves(self.tick)
        return self.ledger.state(event) == 'due'

    def complete_attack(self, event, player_cell):
        """Complete attack movement once, after damage/parry; never in rendering.

        The player may occupy ANY warned path cell. Stop immediately before
        that cell even on an invulnerable or normal-parried attack. Perfect
        parry stuns/cancels movement before this method and leaves its origin.
        A Knight stays at its origin if the player occupies its landing cell.
        A Bishop never moves; closing its plan releases the opposite color.
        """
        plan = self._attack_moves.get(event.key)
        if plan is None or plan[0] != event:
            return False
        state = self.ledger.state(event)
        if state not in ('resolved', 'cancelled'):
            return False
        del self._attack_moves[event.key]
        _, source, origin = plan
        if source.kind == 'bishop':
            self._bishop_closed_tick[sum(origin) % 2] = self.tick
            return False  # Stationary even on hit, miss, invulnerability or parry.
        if source.kind == 'king':
            return False  # Melee never moves and grants no Pulse-specific effect.
        if (state != 'resolved' or event.hit_tick != self.tick
                or self.ledger.outcome(event) not in ('hit', 'miss', 'invulnerable', 'parried_normal')
                or not source.active or source.state == 'stunned' or source.position != origin):
            return False
        destination = origin
        occupied = self.occupied_cells - {origin}
        if source.kind == 'knight':
            target = event.target_cells[0]
            if target != player_cell and target not in occupied:
                destination = target
        else:
            for cell in event.target_cells:
                if cell == player_cell or cell in occupied:
                    break
                destination = cell
        source.col, source.row = destination
        self._check_occupancy(player_cell)
        self._cancel_obstructed_moves(self.tick)
        return True

    def cancel_attacks(self, entity_instance_id, *, tick=None):
        """Release live plans while retaining ledger receipts and tombstones."""
        if tick is not None:
            self._validate_tick(tick)
        count = self.ledger.cancel_source(entity_instance_id)
        self._discard_attack_moves(entity_instance_id, tick=tick)
        for enemy in self.enemies:
            if enemy.entity_instance_id == entity_instance_id:
                enemy.current_attack = None
        return count

    def stun(self, entity_instance_id, tick, duration_ticks=None):
        """Suspend one live source and cancel pending attacks at this tick.

        The successful parry event must be finished before this call. Resolved
        outcomes remain intact; only still-pending attacks are cancelled.
        Reapplying a stun refreshes its end, without adding durations together.
        """
        self._validate_tick(tick)
        if duration_ticks is None:
            duration_ticks = _duration_ticks(PERFECT_PARRY_STUN_SECONDS)
        if type(duration_ticks) is not int:
            raise TypeError('Stun duration must be integer ticks')
        if duration_ticks <= 0:
            raise ValueError('Stun duration must be positive')
        if not isinstance(entity_instance_id, str) or not entity_instance_id.strip():
            raise ValueError('Stun source ID must be a nonempty string')
        if tick != self.tick:
            raise ValueError('Stun tick must match the current encounter tick')
        for enemy in self.enemies:
            if enemy.entity_instance_id == entity_instance_id:
                if not enemy.active:
                    return False
                self.cancel_attacks(entity_instance_id, tick=tick)
                enemy.stun_until_tick = max(enemy.stun_until_tick, tick + duration_ticks)
                enemy.next_action_tick = enemy.stun_until_tick
                enemy.state = 'stunned'
                return True
        raise ValueError('Unknown enemy instance ID')

    def deactivate(self, entity_instance_id, *, tick=None):
        """Cancel source attacks and release occupancy without removing history."""
        for enemy in self.enemies:
            if enemy.entity_instance_id == entity_instance_id:
                self.cancel_attacks(entity_instance_id, tick=tick)
                enemy.stun_until_tick = 0
                enemy.state = 'inactive'
                return
        raise ValueError('Unknown enemy instance ID')

    def _discard_attack_moves(self, entity_instance_id, *, tick=None):
        closed_tick = max(0, self.tick) if tick is None else tick
        for _, source, origin in self._attack_moves.values():
            if source.entity_instance_id == entity_instance_id and source.kind == 'bishop':
                self._bishop_closed_tick[sum(origin) % 2] = closed_tick
        self._attack_moves = {key: record for key, record in self._attack_moves.items()
                              if record[1].entity_instance_id != entity_instance_id}


class PawnEncounter(EnemyEncounter):
    """Compatibility entry point: original Pawn-only API and behavior."""
    def __init__(self, enemies, start_tick=0, combat_session_id=None, stage_instance_id=None):
        enemies = tuple(enemies)
        if any(not isinstance(e, Enemy) or e.kind != 'pawn' for e in enemies):
            raise ValueError('PawnEncounter accepts Pawn instances only')
        super().__init__(enemies, start_tick, combat_session_id, stage_instance_id)
