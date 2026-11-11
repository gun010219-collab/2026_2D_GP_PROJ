"""Tick-driven Stage 1 Pawn encounter. No damage, HP or parry results."""
from board import in_bounds
from combat import _duration_ticks
from config import PAWN_MOVE_INTERVAL_SECONDS, PAWN_RECOVERY_SECONDS, PAWN_TELEGRAPH_SECONDS
from enemy_attack import EnemyAttackLedger


# Stable tie order; movement does not change the JSON attack-facing vector.
PAWN_MOVE_STEPS = ((0, 1), (0, -1), (-1, 0), (1, 0))


class PawnEncounter:
    def __init__(self, enemies, start_tick=0, combat_session_id=None, stage_instance_id=None):
        self._validate_tick(start_tick)
        self.enemies = tuple(enemies)
        self.ledger = EnemyAttackLedger(combat_session_id, stage_instance_id)
        self.move_ticks = _duration_ticks(PAWN_MOVE_INTERVAL_SECONDS)
        self.telegraph_ticks = _duration_ticks(PAWN_TELEGRAPH_SECONDS)
        self.recovery_ticks = _duration_ticks(PAWN_RECOVERY_SECONDS)
        self.tick = start_tick - 1
        self._movement_history = {}
        if len({e.entity_instance_id for e in self.enemies}) != len(self.enemies):
            raise ValueError('Duplicate enemy instance IDs')
        if len({e.data_id for e in self.enemies}) != len(self.enemies):
            raise ValueError('Duplicate enemy data IDs')
        for enemy in self.enemies:
            enemy.state = 'initial_wait'
            enemy.current_attack = None
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
                if not enemy.active:
                    continue
                if enemy.current_attack is not None:
                    event = enemy.current_attack
                    if self.ledger.state(event) == 'cancelled':
                        enemy.current_attack = None
                        enemy.state = 'waiting'
                        enemy.next_action_tick = now + self.recovery_ticks
                    elif now >= event.hit_tick:
                        if self.ledger.mark_due(event, now):
                            due.append(event)
                        enemy.current_attack = None
                        enemy.state = 'recovering'
                        enemy.next_action_tick = event.hit_tick + self.recovery_ticks
                    continue
                if now < enemy.next_action_tick:
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
        self.tick = tick
        return tuple(due)

    def deactivate(self, entity_instance_id):
        """Cancel pending/previous events and disable AI; this is not a death system."""
        for enemy in self.enemies:
            if enemy.entity_instance_id == entity_instance_id:
                self.ledger.cancel_source(entity_instance_id)
                enemy.current_attack = None
                enemy.state = 'inactive'
                return
        raise ValueError('Unknown enemy instance ID')
