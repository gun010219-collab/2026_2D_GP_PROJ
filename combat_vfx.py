"""Read-only, session-scoped combat effects. Times are presentation seconds."""
from dataclasses import dataclass
from math import cos, sin, tau
from zlib import crc32

from config import BOARD_BOTTOM, BOARD_LEFT, TILE_SIZE, cell_center



@dataclass(frozen=True, slots=True)
class Material:
    color: tuple
    edge: tuple
    fragment: str
    gravity: float
    drag: float


MATERIALS = {
    1: Material((232, 173, 69), (255, 241, 184), 'splinter', 195, .24),
    2: Material((88, 177, 96), (198, 244, 153), 'leaf', 55, .64),
    3: Material((90, 181, 245), (219, 252, 255), 'crystal', 120, .18),
    4: Material((246, 105, 46), (255, 207, 104), 'ember', -55, .49),
    5: Material((186, 46, 85), (245, 175, 193), 'iron', 250, .14),
}

# Duration, optional debris allocation per occurrence. Real damage / parry labels
# have independent geometry even when every debris slot is in use.
SPECS = {
    'player_swing': (.19, 0), 'player_hit': (.38, 9), 'player_hurt': (.41, 10),
    'parry_normal': (.27, 11), 'parry_perfect': (.49, 24),
    'pawn_thrust': (.14, 0), 'rook_strike': (.20, 0), 'rook_impact': (.27, 12),
    'knight_strike': (.16, 0), 'knight_land': (.30, 11),
    'bishop_cast': (.37, 7), 'queen_fire': (.38, 6), 'king_strike': (.28, 12),
    'king_pulse': (.54, 18), 'enemy_death': (.36, 12), 'boss_death': (.84, 24),
    'player_death': (.48, 12),
}
CASTS = dict(player='player_swing', pawn='pawn_thrust', rook='rook_strike', knight='knight_strike',
             bishop='bishop_cast', queen='queen_fire', king='king_strike')

# Reused polar samples. Index by a stable stage-local actor and receipt, never UUID.
SAMPLES = tuple((cos(i * 2.399963), sin(i * 2.399963), 47 + i * 37 % 117,
                 1.4 + (i * 7 % 13) / 5) for i in range(64))
MAX_EFFECTS = 64
MAX_PARTICLES = 128
IMPORTANT = {'player_hit', 'player_hurt', 'parry_normal', 'parry_perfect'}


@dataclass(slots=True)
class Effect:
    name: str
    key: tuple
    origin: tuple
    cell: tuple
    cells: tuple
    start: float
    duration: float
    amount: int
    seed: int
    particles: int
    travel_pose: tuple | None = None
    landed: float | None = None
    source_kind: str | None = None


def cue_name(event, kind):
    """R5 can map the same immutable batch; key each cue by (event.key, name)."""
    if event.kind == 'telegraph':
        return 'king_charge' if event.payload.attack_kind == 'king_pulse' else kind + '_charge'
    if event.kind == 'attack_start':
        return 'king_pulse' if getattr(event.payload, 'attack_kind', '') == 'king_pulse' else CASTS[kind]
    if event.kind == 'rook_blocked':
        return 'rook_impact'
    if event.kind == 'attack_move':
        return {'rook': 'rook_impact', 'knight': 'knight_land'}.get(kind)
    if event.kind == 'hurt' and event.payload.hp_before > event.payload.hp_after:
        return 'player_hurt' if kind == 'player' else 'player_hit'
    if event.kind in ('parry_perfect', 'parry_normal'):
        return event.kind
    if event.kind == 'death':
        return 'boss_death' if kind == 'king' else ('player_death' if kind == 'player' else 'enemy_death')
    return None



class CombatVFX:
    def __init__(self, *, renewed=False, layered=False):
        self.renewed = renewed or layered
        self.layered = layered
        self.scope = None
        self.effects = []
        self.charges = {}
        self.seen = set()
        self.last_tick = -1
        self.time = 0.
        self.failed = False

    def close(self):
        self.effects.clear()
        self.charges.clear()
        self.seen.clear()
        self.scope = None
        self.last_tick = -1
        self.time = 0.
        self.failed = False

    def update(self, game, elapsed, batch, *, paused=False, motion=None):
        scope = game.combat.combat_session_id, game.combat.stage_instance_id
        if self.scope != scope:
            self.close()
            self.scope = scope
        elif not paused and 0 <= elapsed <= .15:
            self.time += elapsed
        if self.failed:
            return
        self.effects[:] = [fx for fx in self.effects if self.time < fx.start + fx.duration]
        if batch:
            actors = {e.entity_instance_id: e for e in (game.player, *game.encounter.enemies)}
            for event in batch:
                if event.cause_key[:2] != scope or event.tick < self.last_tick:
                    continue
                if event.tick > self.last_tick:
                    self.seen.clear()
                    self.last_tick = event.tick
                if event.key in self.seen:
                    continue
                self.seen.add(event.key)
                actor = actors.get(event.subject)
                if actor is None:
                    continue
                kind = getattr(actor, 'kind', 'player')
                if event.kind == 'telegraph':
                    if event.origin is not None:
                        self.charges[event.cause_key] = (event.payload, event.origin, kind)
                    continue
                name = cue_name(event, kind)
                if name in SPECS:
                    source = actors.get(event.payload.source_entity_instance_id) if event.kind=='hurt' else None
                    self._start(game,event,name,getattr(actor,'data_id','player'),
                                source_kind=getattr(source,'kind',None))
        if motion is not None:
            for fx in self.effects:
                if fx.name in ('knight_land','rook_impact') and fx.landed is None:
                    self._follow_move(game,motion,fx)
        ledger = game.encounter.ledger
        for key, (attack, _, _) in tuple(self.charges.items()):
            if ledger.state(attack) != 'telegraph':
                del self.charges[key]

    def _follow_move(self, game, motion, fx):
        # Follow the same ground interpolation and 18px lift as the actor.
        subject = fx.key[2]
        actor = next((e for e in game.encounter.enemies if e.entity_instance_id == subject), None)
        if actor is None or actor.position != fx.cell or not actor.active:
            fx.travel_pose = None
            return
        ground, lift = motion.ground_pose(actor)
        if ground == cell_center(*fx.cell) or fx.origin == fx.cell:
            fx.travel_pose = None
            fx.landed = self.time
        else:
            fx.travel_pose = ((ground[0]-BOARD_LEFT)/TILE_SIZE, (ground[1]-BOARD_BOTTOM)/TILE_SIZE, lift)

    def _start(self, game, event, name, stable_id, *, source_kind=None):
        cells = getattr(event.payload, 'target_cells', ())
        origin = event.origin
        cell = event.destination or (cells[-1] if cells else origin)
        if origin is None or cell is None:
            return
        start = self.time - max(0, game.combat.tick - event.tick) / 60
        duration, wanted = SPECS[name]
        if self.time >= start + duration:
            return
        if len(self.effects) >= MAX_EFFECTS:
            optional = next((fx for fx in self.effects if fx.name not in IMPORTANT), None)
            if optional is None:
                # At most one player attack per cooldown, one hurt per immunity
                # interval and one parry per attempt in the actual game.
                return
            self.effects.remove(optional)
        free = MAX_PARTICLES - sum(fx.particles for fx in self.effects)
        amount = event.payload.hp_before - event.payload.hp_after if event.kind == 'hurt' else 0
        seed = crc32(f'{stable_id}/{event.tick}/{name}'.encode()) % len(SAMPLES)
        self.effects.append(Effect(name, event.key, origin, cell, cells, start, duration,
                                   amount, seed, min(free,wanted),source_kind=source_kind))

    def shake(self):
        for fx in reversed(self.effects):
            age = self.time - fx.start
            if fx.name == 'parry_perfect' and 0 <= age < .115:
                strength = 2 * (1 - age / .115)
                return round(strength * cos(tau * age * 25)), round(strength * sin(tau * age * 19))
        return 0, 0
