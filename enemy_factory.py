"""Stage definitions -> fresh Pawn/Rook/Knight instances, never progression."""
from enemy import Enemy
from stage_manager import EnemyDefinition, StageDefinition


class UnsupportedEnemyError(ValueError):
    """A definition has no implemented live behavior or optional setting."""


def _check_supported(definition):
    if not isinstance(definition, EnemyDefinition):
        raise TypeError('Expected an EnemyDefinition')
    if definition.kind not in ('pawn', 'rook', 'knight'):
        raise UnsupportedEnemyError(f'Unsupported combat piece: {definition.kind}')
    allowed = {'forward'} if definition.kind == 'pawn' else set()
    if set(definition.options) != allowed:
        raise UnsupportedEnemyError(f'Unsupported {definition.kind} options: {dict(definition.options)}')


def create_enemy(definition):
    """Spawn HP/AI/IDs anew; definitions remain immutable and state-free."""
    _check_supported(definition)
    forward = definition.options['forward'] if definition.kind == 'pawn' else None
    return Enemy(definition.data_id, definition.col, definition.row, forward,
                 definition.initial_delay, kind=definition.kind)


def create_stage_enemies(stage):
    """Preserve JSON order; reject unsupported entries instead of skipping them."""
    if not isinstance(stage, StageDefinition):
        raise TypeError('Expected a StageDefinition')
    for definition in stage.enemies:
        _check_supported(definition)
    enemies = tuple(create_enemy(definition) for definition in stage.enemies)
    ids = [e.data_id for e in enemies]
    positions = [stage.player_spawn, *(e.position for e in enemies)]
    if len(set(ids)) != len(ids) or len(set(positions)) != len(positions):
        raise ValueError('Stage definition contains duplicate IDs or overlapping spawns')
    return enemies
