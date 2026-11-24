"""Read-only animation state driven by the real combat and presentation queue."""
from dataclasses import dataclass
from enum import Enum
from math import hypot
from zlib import crc32

from config import cell_center


class State(Enum):
    IDLE = 'idle'
    MOVE = 'move'
    WINDUP = 'windup'
    ATTACK = 'attack'
    HIT = 'hit'
    STUN = 'stun'
    DEATH = 'death'
    PARRY_READY = 'parry_ready'
    PARRY_NORMAL = 'parry_normal'
    PARRY_PERFECT = 'parry_perfect'
    PARRY_FAILED = 'parry_failed'


TIMED = {
    'attack_start': (State.ATTACK, .23),
    'hurt': (State.HIT, .19),
    'death': (State.DEATH, .52),
    'parry_normal': (State.PARRY_NORMAL, .26),
    'parry_perfect': (State.PARRY_PERFECT, .34),
    'parry_failed': (State.PARRY_FAILED, .25),
}
# Actual model state can outlast a pose trigger (stun, parry window, telegraph).
PRIORITY = (State.HIT, State.PARRY_PERFECT, State.PARRY_NORMAL, State.PARRY_FAILED, State.ATTACK)
FACING = {'left': -1., 'right': 1., 'up': -.24, 'down': .24}


@dataclass(frozen=True)
class Pose:
    state: State
    phase: float
    amount: float = 1.
    direction: float = 1.
    attack_kind: str = ''


@dataclass(frozen=True)
class DeathSprite:
    entity_instance_id: str
    kind: str
    position: tuple[int, int]


@dataclass(frozen=True)
class Cue:
    start: float
    duration: float
    amount: float
    direction: float
    attack_kind: str


class ActorAnimation:
    def __init__(self):
        self.scope = None
        self.time = 0.
        self._seen = set()
        self._cues = {}
        self._deaths = {}
        self._windups = {}
        self._phase = {}

    @property
    def deaths(self):
        return self._deaths.values()

    def update(self, game, elapsed, batch, *, paused=False):
        scope = game.combat.combat_session_id, game.combat.stage_instance_id
        if self.scope != scope:
            self.scope, self.time = scope, 0.
            self._seen.clear()
            self._cues.clear()
            self._deaths.clear()
            self._phase.clear()
        elif not paused and 0. <= elapsed <= .15:
            self.time += elapsed
        actors = {e.entity_instance_id: e for e in (game.player, *game.encounter.enemies)}
        self._windups = {e.source_entity_instance_id: e for e in game.encounter.ledger.telegraphs}
        tick = game.combat.tick
        for event in batch:
            if event.kind not in TIMED or event.cause_key[:2] != scope or event.key in self._seen:
                continue
            self._seen.add(event.key)
            actor = actors.get(event.subject)
            if actor is None:
                continue
            state, duration = TIMED[event.kind]
            kind = getattr(actor, 'kind', 'player')
            if state is State.DEATH:
                if actor.alive:
                    continue
                self._deaths[event.subject] = DeathSprite(event.subject, kind, actor.position)
                duration = .98 if kind == 'king' else duration
            elif state is State.ATTACK and kind == 'king':
                duration = .38 if event.payload.attack_kind == 'king_pulse' else .28
            start = self.time - max(0, tick-event.tick)/60
            target = getattr(event.payload, 'target_cell', None)
            facing = getattr(event.payload, 'facing', None)
            source = actors.get(getattr(event.payload, 'source_entity_instance_id', None))
            if state is State.HIT and source is not None:
                target = source.position
            if target is None:
                cells = getattr(event.payload, 'target_cells', ())
                target = cells[-1] if cells else actor.position
            side = target[0] - actor.position[0]
            direction = FACING.get(facing, (1. if side > 0 else -1.) if side else .24)
            cue = Cue(start, duration, getattr(event.payload, 'amount', 1), direction,
                      getattr(event.payload, 'attack_kind', ''))
            self._cues[event.subject, state] = cue
        for key, cue in tuple(self._cues.items()):
            if self.time - cue.start >= cue.duration:
                del self._cues[key]
                if key[1] is State.DEATH:
                    self._deaths.pop(key[0], None)

    def pose(self, game, actor, motion):
        key = actor.entity_instance_id
        if key in self._deaths:
            return self._timed(key, State.DEATH)
        tick = game.combat.tick
        if getattr(actor, 'stun_until_tick', 0) > tick:
            return Pose(State.STUN, self.time)
        for state in PRIORITY:
            if (key,state) in self._cues:
                return self._timed(key,state)
        if actor is game.player and game.parry.active_at(tick):
            return Pose(State.PARRY_READY, self.time, direction=FACING[actor.facing])
        event = self._windups.get(key)
        if event is not None and game.playing:
            charge = (tick-event.telegraph_start_tick) / max(1, event.hit_tick-event.telegraph_start_tick)
            delta = event.target_cells[-1][0] - actor.position[0]
            return Pose(State.WINDUP, charge, direction=1. if delta >= 0 else -1., attack_kind=event.attack_kind)
        offset = self._phase.get(key)
        if offset is None:
            offset = crc32(getattr(actor,'data_id','player').encode()) % 997 / 193
            self._phase[key] = offset
        kind = getattr(actor, 'kind', 'player')
        if kind != 'bishop' and motion is not None and game.playing:
            (x,y), lift = motion.ground_pose(actor)
            tx,ty = cell_center(*actor.position)
            if hypot(tx-x,ty-y) > .05 or lift > .05:
                return Pose(State.MOVE, self.time+offset, direction=1. if tx >= x else -1.)
        return Pose(State.IDLE, self.time+offset)

    def _timed(self, key, state):
        cue = self._cues[key,state]
        return Pose(state, min(1., max(0., (self.time-cue.start)/cue.duration)),
                    cue.amount, cue.direction, cue.attack_kind)
