"""Stage definitions -> fresh supported enemy instances, never progression."""
from enemy import Enemy
from combat_balance import profile_for
from stage_manager import EnemyDefinition, StageDefinition


class UnsupportedEnemyError(ValueError):
    """A definition has no implemented live behavior or optional setting."""


def _check_supported(definition):
    if not isinstance(definition, EnemyDefinition):
        raise TypeError('Expected an EnemyDefinition')
    if definition.kind not in ('pawn', 'rook', 'knight', 'bishop', 'king'):
        raise UnsupportedEnemyError(f'Unsupported combat piece: {definition.kind}')
    allowed = {'forward'} if definition.kind == 'pawn' else set()
    if set(definition.options) != allowed:
        raise UnsupportedEnemyError(f'Unsupported {definition.kind} options: {dict(definition.options)}')


def create_enemy(definition, *, boss_hp=None, max_hp=None):
    """Spawn HP/AI/IDs anew; definitions remain immutable and state-free."""
    _check_supported(definition)
    forward = definition.options['forward'] if definition.kind == 'pawn' else None
    return Enemy(definition.data_id, definition.col, definition.row, forward,
                 definition.initial_delay, kind=definition.kind, boss_hp=boss_hp, max_hp=max_hp)


def create_stage_enemies(stage, *, profile=None):
    """Preserve JSON order; reject unsupported entries instead of skipping them."""
    if not isinstance(stage, StageDefinition):
        raise TypeError('Expected a StageDefinition')
    for definition in stage.enemies:
        _check_supported(definition)
    kings = [e for e in stage.enemies if e.kind == 'king']
    if type(stage.boss) is not bool:
        raise ValueError('Stage boss flag must be boolean')
    if stage.boss:
        if len(kings) != 1 or type(stage.boss_hp) is not int or stage.boss_hp <= 0:
            raise ValueError('Boss stage requires exactly one King and positive integer boss_hp')
    elif kings or stage.boss_hp is not None:
        raise ValueError('Non-boss stage cannot contain a King or boss_hp')
    if profile is not None and profile != profile_for(stage.chapter):
        raise ValueError('Unapproved or wrong chapter HP profile')
    enemies = tuple(create_enemy(definition,
                    boss_hp=(profile.king if profile else stage.boss_hp) if definition.kind == 'king' else None,
                    max_hp=profile.hp(definition.kind) if profile and definition.kind != 'king' else None)
                    for definition in stage.enemies)
    ids = [e.data_id for e in enemies]
    positions = [stage.player_spawn, *(e.position for e in enemies)]
    if len(set(ids)) != len(ids) or len(set(positions)) != len(positions):
        raise ValueError('Stage definition contains duplicate IDs or overlapping spawns')
    return enemies
