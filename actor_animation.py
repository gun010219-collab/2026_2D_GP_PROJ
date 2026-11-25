"""Read-only animation state driven by the real combat and presentation queue."""
from dataclasses import dataclass, fields
from enum import Enum
from math import hypot
from zlib import crc32

from config import cell_center
from player import DIRECTIONS


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
PARRY_POSES = frozenset((State.PARRY_READY,State.PARRY_NORMAL,State.PARRY_PERFECT,State.PARRY_FAILED))
PARRY_RESULT_STATES = {'normal': State.PARRY_NORMAL, 'perfect': State.PARRY_PERFECT}
FACING = {'left': -1., 'right': 1., 'up': -.24, 'down': .24}


@dataclass(frozen=True)
class Pose:
    state: State
    phase: float
    amount: float = 1.
    direction: float = 1.
    attack_kind: str = ''
    attack_motion: str = ''
    depth_direction: float = 0.
    articulated: bool = False


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
    cause: tuple = ()
    depth_direction: float = 0.


@dataclass
class AttackTravel:
    destination: tuple
    arrived: float | None = None


ATTACK_SECONDS = {'pawn': .21, 'rook': .34, 'knight': .31, 'bishop': .42, 'queen': .44, 'king': .43}
RECOVERY_SECONDS = {'rook': .25, 'knight': .22}
ARTICULATED_SECONDS = {'pawn':.31,'rook':.40,'knight':.39,'bishop':.52,'queen':.54,'king':.53}
ARTICULATED_RECOVERY = {'rook':.32,'knight':.31}


def attack_direction(kind, origin, attack):
    if kind in ('bishop','queen') or attack.attack_kind == 'king_pulse':
        return 0.,0.
    target = attack.target_cells[0]
    dx,dy = target[0]-origin[0],target[1]-origin[1]
    length = hypot(dx,dy) or 1.
    return dx/length,dy/length


class ActorAnimation:
    def __init__(self, *, improved=False, enemy_attacks=False, player_actions=False, articulated=False,
                 sprites=False):
        self.improved = improved
        self.enemy_attacks = enemy_attacks
        self.player_actions = player_actions
        self.articulated = articulated
        self._sprite_cues = {} if sprites else None
        self.recovery_seconds = ARTICULATED_RECOVERY if articulated else RECOVERY_SECONDS
        self._travel = {}
        self._display = {}
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

    def update(self, game, elapsed, batch, *, paused=False, motion=None, reset=False):
        scope = game.combat.combat_session_id, game.combat.stage_instance_id
        if self.scope != scope:
            self.scope, self.time = scope, 0.
            self._seen.clear()
            self._cues.clear()
            self._deaths.clear()
            self._phase.clear()
            self._display.clear()
            self._travel.clear()
            if self._sprite_cues is not None:
                self._sprite_cues.clear()
        elif not paused and 0. <= elapsed <= .15:
            self.time += elapsed
        actors = {e.entity_instance_id: e for e in (game.player, *game.encounter.enemies)}
        warnings = (game.resolver.live_telegraphs(game.combat.tick) if self.enemy_attacks
                    else game.encounter.ledger.telegraphs)
        self._windups = {e.source_entity_instance_id: e for e in warnings}
        tick = game.combat.tick
        for event in batch:
            is_travel = self.enemy_attacks and event.kind in ('attack_move','rook_blocked')
            sprite_stun = self._sprite_cues is not None and event.kind == 'stun'
            if (event.kind not in TIMED and not is_travel and not sprite_stun) or event.cause_key[:2] != scope or event.key in self._seen:
                continue
            self._seen.add(event.key)
            actor = actors.get(event.subject)
            if actor is None:
                continue
            kind = getattr(actor, 'kind', 'player')
            if self._sprite_cues is not None and event.kind in ('hurt', 'death', 'stun'):
                self._sprite_cues.pop(event.subject, None)
            if sprite_stun:
                continue
            if is_travel:
                cue = self._cues.get((event.subject,State.ATTACK))
                if kind in RECOVERY_SECONDS and cue and event.cause_key == cue.cause:
                    arrived = cue.start if event.kind=='rook_blocked' else None
                    self._travel[event.subject] = AttackTravel(event.destination,arrived)
                continue
            state, duration = TIMED[event.kind]
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
            attack_kind = getattr(event.payload,'attack_kind','')
            depth = 0.
            if self.player_actions and actor is game.player:
                if state is State.ATTACK:
                    direction,depth = DIRECTIONS[event.payload.facing]
                    if self.articulated:
                        duration = .32
                elif state in PARRY_POSES:
                    direction,depth = DIRECTIONS[actor.facing]
                    if event.origin is not None and event.destination is not None:
                        dx,dy = (event.origin[i]-event.destination[i] for i in (0,1))
                        if distance := hypot(dx,dy):
                            direction,depth = dx/distance,dy/distance
            if self.enemy_attacks and kind != 'player' and state is State.ATTACK:
                if game.encounter.ledger.state(event.payload) == 'cancelled':
                    continue
                direction,depth = attack_direction(kind,event.origin or actor.position,event.payload)
                if self.articulated:
                    duration = .65 if attack_kind=='king_pulse' else ARTICULATED_SECONDS[kind]
                else:
                    duration = .56 if attack_kind=='king_pulse' else ATTACK_SECONDS[kind]
                self._travel.pop(event.subject,None)
            cue = Cue(start,duration,getattr(event.payload,'amount',1),direction,attack_kind,event.cause_key,depth)
            self._cues[event.subject, state] = cue
            if self._sprite_cues is not None and (state is State.ATTACK or state in PARRY_POSES):
                if state in PARRY_POSES:
                    vector = DIRECTIONS[actor.facing]
                    if event.origin is not None and event.destination is not None and event.origin != event.destination:
                        vector = tuple(a-b for a,b in zip(event.origin, event.destination))
                elif actor is game.player:
                    vector = DIRECTIONS[event.payload.facing]
                else:
                    vector = attack_direction(kind, event.origin or actor.position, event.payload)
                sources = self._sprite_cues.setdefault(event.subject, {})
                sources[state] = (event, cue.start, vector)
        if self.enemy_attacks:
            self._update_attack_travel(actors,motion,tick,paused)
        for key, cue in tuple(self._cues.items()):
            travel = self._travel.get(key[0]) if key[1] is State.ATTACK else None
            if travel and travel.arrived is not None:
                expired = self.time-travel.arrived >= self.recovery_seconds[actors[key[0]].kind]
            else:
                expired = self.time-cue.start >= cue.duration
            if expired:
                del self._cues[key]
                if travel:
                    self._travel.pop(key[0],None)
                if key[1] is State.DEATH:
                    self._deaths.pop(key[0], None)

        if self.improved:
            if reset:
                self._display.clear()
            if not paused or not self._display:
                self._blend(game,actors,motion)

    def _update_attack_travel(self, actors, motion, tick, paused):
        for key,actor in actors.items():
            if not hasattr(actor,'kind'):
                continue
            cue = self._cues.get((key,State.ATTACK))
            windup = self._windups.get(key)
            if cue is not None and (not actor.active or actor.stun_until_tick > tick
                                    or (key,State.HIT) in self._cues
                                    or (windup is not None and windup.key != cue.cause)):
                self._cues.pop((key,State.ATTACK))
                self._travel.pop(key,None)
                continue
            travel = self._travel.get(key)
            if travel is None or travel.arrived is not None:
                continue
            if actor.position != travel.destination:
                self._travel.pop(key)
            elif (not paused and motion is not None
                  and motion.ground_pose(actor)[0] == cell_center(*travel.destination)):
                segment = motion.segment(actor)
                overshoot = max(0.,motion.time-segment[1]) if segment else 0.
                travel.arrived = max(cue.start,self.time-overshoot)

    def _blend(self, game, actors, motion):
        from actor_mesh import deformation

        rendered = {}
        for key,actor in actors.items():
            if not actor.alive or not getattr(actor,'active',True):
                continue
            kind = getattr(actor,'kind','player')
            pose = self.pose(game,actor,motion)
            target = deformation(kind,game.chapter,pose,improved=True)
            old = self._display.get(key)
            source, started = None, self.time
            if old:
                old_pose, old_effect, previous, previous_start = old
                if old_pose.state is pose.state and old_pose.direction == pose.direction:
                    source, started = previous, previous_start
                elif (pose.state not in (State.PARRY_PERFECT,State.DEATH)
                      and not (kind=='player' and pose.attack_motion)
                      and not (self.enemy_attacks and kind != 'player'
                               and pose.state in (State.ATTACK,State.HIT,State.STUN))):
                    source = old_effect
                    cue = self._cues.get((key,pose.state))
                    if cue:
                        started = cue.start
                    if motion is not None and {old_pose.state,pose.state} == {State.IDLE,State.MOVE}:
                        segment = motion.segment(actor)
                        if segment is not None:
                            at = segment[0] if pose.state is State.MOVE else segment[1]
                            started = self.time-max(0.,motion.time-at)
                            boundary = Pose(old_pose.state,pose.phase-(self.time-started),
                                            direction=old_pose.direction)
                            source = deformation(kind,game.chapter,boundary,improved=True)
                if source is not None:
                    duration = .05 if pose.state in (State.ATTACK,State.HIT,State.PARRY_NORMAL) else .09
                    time = self.time-started
                    if time >= duration:
                        source = None
                    else:
                        floor = .78 if duration == .05 else 0.
                        weight = floor+(1-floor)*max(0.,time/duration)
                        target = type(target)(*(getattr(source,f.name)*(1-weight)+getattr(target,f.name)*weight
                                                for f in fields(target)))
            rendered[key] = pose,target,source,started
        self._display = rendered

    def sprite_source(self, game, actor, pose):
        if (self._sprite_cues is None or not actor.alive or not getattr(actor, 'active', True)
                or self.scope != (game.combat.combat_session_id, game.combat.stage_instance_id)
                or pose.state in (State.HIT, State.STUN, State.DEATH)):
            return None
        key = actor.entity_instance_id
        state, tick = pose.state, game.combat.tick
        if state is State.WINDUP:
            receipt = self._windups.get(key)
            if (receipt is not None and game.encounter.ledger.state(receipt) == 'telegraph'
                    and receipt.telegraph_start_tick <= tick < receipt.hit_tick):
                vector = attack_direction(actor.kind, actor.position, receipt)
                return state, receipt, 0., vector
            return None
        sources = self._sprite_cues.get(key, {})
        if state is State.PARRY_READY:
            attempt = game.parry.last_attempt
            if attempt is None or not game.parry.active_at(tick):
                return None
            result = game.resolver.parry_result(attempt)
            if result is None:
                return state, attempt, (tick-attempt.start_tick)/60, DIRECTIONS[actor.facing]
            # An adjudicated attempt must not show a second guard after its reaction.
            state = PARRY_RESULT_STATES.get(result.status, State.PARRY_FAILED)
            if state not in sources or sources[state][0].payload != result:
                return None
        if state in (State.IDLE, State.MOVE) and sources:
            # A frame clip may recover after the mesh transition has finished.
            state = max(sources, key=lambda s: (sources[s][0].tick, -PRIORITY.index(s)))
        if state not in sources:
            return None
        event, started, vector = sources[state]
        receipt = event.payload
        if actor.health.last_damage_tick is not None and actor.health.last_damage_tick >= event.tick:
            return None
        if state is State.ATTACK:
            if actor is game.player and game.combat.attack_state(receipt) != 'resolved':
                return None
            if actor is not game.player and game.encounter.ledger.state(receipt) != 'resolved':
                return None
        return state, receipt, self.time-started, vector

    def mesh_pose(self, game, actor, motion):
        frame = self._display.get(actor.entity_instance_id)
        return frame[:2] if frame else (self.pose(game,actor,motion),None)

    def pose(self, game, actor, motion):
        key = actor.entity_instance_id
        if key in self._deaths:
            return self._timed(key, State.DEATH)
        tick = game.combat.tick
        if getattr(actor, 'stun_until_tick', 0) > tick:
            return Pose(State.STUN, self.time)
        for state in PRIORITY:
            if (key,state) in self._cues:
                if self.enemy_attacks and actor is not game.player and state is State.ATTACK:
                    return self._attack_pose(actor,motion)
                if self.player_actions and actor is game.player:
                    if state is State.ATTACK:
                        return self._timed(key,state,'swing')
                    if state in PARRY_POSES:
                        return self._timed(key,state,'guard')
                return self._timed(key,state)
        if actor is game.player and game.parry.active_at(tick):
            if self.player_actions:
                side,depth = DIRECTIONS[actor.facing]
                return Pose(State.PARRY_READY,self.time,direction=side,attack_motion='guard',depth_direction=depth)
            return Pose(State.PARRY_READY, self.time, direction=FACING[actor.facing])
        event = self._windups.get(key)
        if event is not None and game.playing:
            charge = (tick-event.telegraph_start_tick) / max(1, event.hit_tick-event.telegraph_start_tick)
            if self.enemy_attacks and actor is not game.player:
                side,depth = attack_direction(actor.kind,actor.position,event)
                return Pose(State.WINDUP,charge,direction=side,attack_kind=event.attack_kind,
                            attack_motion='anticipation',depth_direction=depth,articulated=self.articulated)
            delta = event.target_cells[-1][0] - actor.position[0]
            return Pose(State.WINDUP, charge, direction=1. if delta >= 0 else -1., attack_kind=event.attack_kind)
        return self.locomotion_pose(game, actor, motion)

    def locomotion_pose(self, game, actor, motion):
        key = actor.entity_instance_id
        offset = self._phase.get(key)
        if offset is None:
            offset = crc32(getattr(actor,'data_id','player').encode()) % 997 / 193
            self._phase[key] = offset
        kind = getattr(actor, 'kind', 'player')
        if kind != 'bishop' and motion is not None and game.playing:
            (x,y), lift = motion.ground_pose(actor)
            tx,ty = cell_center(*actor.position)
            segment = motion.segment(actor) if self.improved else None
            moving = motion.time < segment[1] if segment is not None else (hypot(tx-x,ty-y) > .05 or lift > .05)
            if moving:
                if self.improved and kind == 'player':
                    return Pose(State.MOVE,self.time+offset,direction=FACING[actor.facing])
                return Pose(State.MOVE, self.time+offset, direction=1. if tx >= x else -1.)
        return Pose(State.IDLE, self.time+offset)

    def _attack_pose(self, actor, motion):
        key = actor.entity_instance_id
        cue = self._cues[key,State.ATTACK]
        travel = self._travel.get(key)
        if travel and travel.arrived is not None:
            phase = (self.time-travel.arrived)/self.recovery_seconds[actor.kind]
            action = 'arrival'
        elif travel and motion is not None and (segment := motion.segment(actor)):
            start,end = segment
            phase = (motion.time-start)/(end-start)
            action = 'travel'
        else:
            phase = (self.time-cue.start)/cue.duration
            action = 'release'
        return Pose(State.ATTACK,min(1.,max(0.,phase)),cue.amount,cue.direction,cue.attack_kind,
                    action,cue.depth_direction,self.articulated)

    def _timed(self, key, state, action=''):
        cue = self._cues[key,state]
        return Pose(state, min(1., max(0., (self.time-cue.start)/cue.duration)),
                    cue.amount,cue.direction,cue.attack_kind,action,cue.depth_direction,
                    self.articulated and action=='swing')
