"""Integer-tick boss lifecycle tests; no sleep, desktop, or alternate engine."""
from dataclasses import replace
import unittest

from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from parry import Parry
from player import Player
from tests.test_king import king


def battle(*, enemies=None, start=0, first=None, deadlines=None):
    p, c, q = Player(5, 1), Combat(), Parry()
    c.advance(start)
    enemies = (king(col=9, row=9),) if enemies is None else enemies
    e = EnemyEncounter(enemies, start_tick=start, combat_session_id=c.combat_session_id,
                       stage_instance_id=c.stage_instance_id, boss=True)
    if first is not None:
        e.pulse.next_use_tick = first
    for enemy, fields in deadlines or ():
        for field, value in fields.items():
            setattr(enemy, field, value)
    r = CombatResolver(p, c, e, parry=q)
    r.resolve_current_tick()
    return p, c, q, e, r


def pulse_battle(*, hp=8, general=None):
    return battle(enemies=(king(col=9, row=9, hp=hp), *(general or ())), first=0)


def parry(parts, delta):
    p, c, q, e, r = parts
    h = e.pulse.event.hit_tick
    r.advance(h - delta - c.tick)
    attempt = q.request(c.tick)
    r.register_parry(attempt)
    r.advance(delta)
    return attempt


class PulseScheduleTests(unittest.TestCase):
    def test_first_240_ready_request_then_next_tick_start(self):
        p, c, q, e, r = battle(start=239, deadlines=[])
        # Real initial wait ends at 239; next move deadline is 311.
        r.advance(1)
        self.assertIsNone(e.pulse.event)
        self.assertEqual(e.pulse.next_use_tick, 479)  # relative to session start
        p, c, q, e, r = battle()
        r.advance(239)
        self.assertIsNone(e.pulse.event)
        # King has moved on 0,72,144,216; waits until 288 before requesting.
        r.advance(49)
        self.assertEqual(e.pulse.state, 'DRAINING')
        self.assertIsNone(e.pulse.event)
        r.advance(1)
        self.assertEqual(e.pulse.event.start_tick, 289)

    def test_exact_240_boundary_when_king_is_ready(self):
        p, c, q, e, r = battle()
        e.pulse.king.next_action_tick = 240
        r.advance(239)
        self.assertEqual(e.pulse.state, 'NORMAL')
        r.advance(1)
        self.assertEqual(e.pulse.state, 'DRAINING')
        r.advance(1)
        self.assertEqual(e.pulse.event.start_tick, 241)

    def test_initial_wait_recovery_and_stun_postpone_request(self):
        for state in ('initial_wait', 'recovering', 'stunned'):
            k = king(col=9, row=9)
            fields = {'state': state, 'next_action_tick': 300, 'stun_until_tick': 300}
            p, c, q, e, r = battle(enemies=(k,), first=240, deadlines=[(k, fields)])
            r.advance(299)
            self.assertEqual(e.pulse.state, 'NORMAL')
            r.advance(1)
            self.assertEqual(e.pulse.state, 'DRAINING')
            r.advance(1)
            self.assertEqual(e.pulse.event.start_tick, 301)

    def test_100_unique_immutable_cells_120_warning_one_damage(self):
        p, c, q, e, r = pulse_battle()
        r.advance(1)
        event = e.pulse.event
        self.assertEqual((event.start_tick, event.hit_tick, event.attack_kind), (1, 121, 'king_pulse'))
        self.assertEqual(set(event.target_cells), {(x, y) for x in range(10) for y in range(10)})
        self.assertEqual(len(event.target_cells), 100)
        with self.assertRaises(AttributeError):
            event.hit_tick = 999
        p.move('left', e.occupied_cells)
        r.advance(119)
        self.assertEqual(p.health.current_hp, 3)
        r.advance(1)
        self.assertEqual((p.health.current_hp, e.ledger.outcome(event)), (2, 'hit'))
        self.assertEqual(e.pulse.state, 'CLEANUP')
        self.assertEqual(e.pulse.next_use_tick, 601)
        self.assertIsNone(r.resolve_enemy_attack(event))
        self.assertEqual(p.health.current_hp, 2)

    def test_cleanup_30_and_cooldown_480_do_not_freeze_regular_king_ai(self):
        p, c, q, e, r = pulse_battle()
        r.advance(121)
        k = e.pulse.king
        origin = k.position
        r.advance(29)
        self.assertEqual(e.pulse.state, 'CLEANUP')
        self.assertEqual(k.position, origin)
        r.advance(1)
        self.assertEqual(e.pulse.state, 'NORMAL')
        self.assertNotEqual(k.position, origin)
        # Isolate the cooldown from pursuit/melee and make King ready exactly at expiry.
        k.next_action_tick = 601
        r.advance(449)
        self.assertEqual((c.tick, e.pulse.state, len(e.pulse._issued)), (600, 'NORMAL', 1))
        r.advance(1)
        self.assertEqual(e.pulse.state, 'DRAINING')
        r.advance(1)
        self.assertEqual((e.pulse.event.start_tick, len(e.pulse._issued)), (602, 2))

    def test_basic_king_encounter_keeps_task_1p_contract(self):
        e = EnemyEncounter((king(),))
        self.assertIsNone(e.pulse)
        with self.assertRaises(ValueError):
            EnemyEncounter((Enemy('p', 1, 1, (0, -1), 0),), boss=True)


class PulseDrainingTests(unittest.TestCase):
    def test_each_existing_piece_finishes_original_event_and_move_before_start(self):
        for kind, position, forward, hit in (
                ('pawn', (4, 2), (0, -1), 39), ('rook', (2, 1), None, 48),
                ('knight', (4, 3), None, 36), ('bishop', (2, 8), None, 108)):
            with self.subTest(kind=kind):
                other = Enemy('other', *position, forward, 0, kind=kind)
                p, c, q, e, r = battle(enemies=(king(col=9, row=9), other), first=1)
                event = other.current_attack
                self.assertEqual(event.hit_tick, hit)
                e.pulse.king.next_action_tick = 1
                r.advance(hit)
                self.assertEqual(e.pulse.state, 'DRAINING')
                self.assertIsNone(e.pulse.event)
                self.assertEqual(e.ledger.state(event), 'resolved')
                self.assertEqual(event.hit_tick, hit)
                self.assertEqual(e._attack_moves, {})
                self.assertEqual(len(e.ledger._records), 1)
                r.advance(1)
                self.assertEqual(e.pulse.event.start_tick, hit + 1)

    def test_king_melee_is_drained_and_normal_recovery_finishes(self):
        p, c, q, e, r = battle(enemies=(king(col=5, row=2),), first=1)
        event = e.pulse.king.current_attack
        r.advance(1)
        self.assertEqual(e.pulse.state, 'DRAINING')
        r.advance(47)
        self.assertEqual(e.ledger.outcome(event), 'hit')
        r.advance(89)
        self.assertIsNone(e.pulse.event)
        r.advance(1)
        self.assertEqual(e.pulse.event.start_tick, 138)

    def test_all_four_pending_attacks_finish_without_new_reservations(self):
        others = (Enemy('p',4,2,(0,-1),0), Enemy('r',2,1,None,0,kind='rook'),
                  Enemy('n',4,3,None,0,kind='knight'), Enemy('b',2,8,None,0,kind='bishop'))
        p, c, q, e, r = battle(enemies=(king(col=9,row=9),*others),first=1)
        events = tuple(x.current_attack for x in others)
        e.pulse.king.next_action_tick = 1
        r.advance(108)
        self.assertTrue(all(e.ledger.state(x) == 'resolved' for x in events))
        self.assertEqual(len(e.ledger._records), 4)
        self.assertIsNone(e.pulse.event)
        r.advance(1)
        self.assertEqual(e.pulse.event.start_tick, 109)

    def test_due_ledger_without_current_pointer_prevents_early_entry(self):
        p, c, q, e, r = pulse_battle()
        stray = e.ledger.create(e.pulse.king.entity_instance_id, 0, 5, ((5, 1),))
        e.ledger.mark_due(stray, 5)
        r.advance(10)
        self.assertEqual(e.pulse.state, 'DRAINING')
        self.assertIsNone(e.pulse.event)
        e.ledger.cancel(stray)
        r.advance(1)
        self.assertIsNone(e.pulse.event)
        r.advance(1)
        self.assertEqual(e.pulse.event.start_tick, 12)

    def test_cancelled_or_dead_attack_does_not_leave_draining_stuck(self):
        for dead in (False, True):
            other = Enemy('r',2,1,None,0,kind='rook')
            p,c,q,e,r = battle(enemies=(king(col=9,row=9),other),first=1)
            e.pulse.king.next_action_tick=1
            event=other.current_attack
            if dead:
                other.health.apply_damage(4,tick=0)
                e.deactivate(other.entity_instance_id,tick=0)
            else:
                e.ledger.cancel(event)
            r.advance(1)
            r.advance(1)
            self.assertEqual(e.pulse.event.start_tick,2)
            self.assertEqual(e.ledger.state(event),'cancelled')


class PulseFreezeTests(unittest.TestCase):
    def test_s200_h320_r350_deadlines_and_historical_damage_are_preserved(self):
        for state, deadline, stun, expected in (
                ('initial_wait',260,0,410), ('waiting',260,0,410),
                ('recovering',260,0,410), ('waiting',201,0,351),
                ('stunned',230,230,380)):
            with self.subTest(state=state):
                other=Enemy('p',1,6,(0,-1),0)
                other.health.apply_damage(1,tick=190)
                fields={'state':state,'next_action_tick':deadline,'stun_until_tick':stun}
                p,c,q,e,r=battle(enemies=(king(col=9,row=9),other),start=199,first=199,
                                 deadlines=[(other,fields)])
                r.advance(1)
                self.assertEqual(e.pulse.freeze_tick,200)
                origin=other.position
                r.advance(149)
                self.assertEqual((other.position,other.state,other.next_action_tick),(origin,state,deadline))
                self.assertEqual(other.health.last_damage_tick,190)
                r.advance(1)
                self.assertEqual((c.tick,e.pulse.state,other.next_action_tick),(350,'NORMAL',expected))
                if state=='stunned':
                    self.assertEqual(other.stun_until_tick,380)
                self.assertEqual(other.health.last_damage_tick,190)
                r.advance(expected-1-c.tick)
                self.assertEqual(other.position,origin)
                r.advance(1)
                self.assertNotEqual(other.position,origin)

    def test_drained_event_receipts_hit_tick_and_health_history_never_shift(self):
        other=Enemy('r',2,1,None,0,kind='rook')
        p,c,q,e,r=battle(enemies=(king(col=9,row=9),other),first=1)
        event=other.current_attack
        e.pulse.king.next_action_tick=1
        r.advance(49)
        self.assertEqual(e.pulse.freeze_tick,49)
        history=(event.hit_tick,e.ledger.state(event),e.ledger.outcome(event),p.health.last_damage_tick)
        self.assertEqual(history,(48,'resolved','hit',48))
        r.player_invulnerable_until_tick=10000
        r.advance(150)
        self.assertEqual(history,(event.hit_tick,e.ledger.state(event),e.ledger.outcome(event),p.health.last_damage_tick))
        self.assertEqual(other.next_action_tick,288)  # 138 - S49 + R199

    def test_ready_enemy_moves_once_on_resume_not_catchup(self):
        other=Enemy('p',1,6,(0,-1),0)
        p,c,q,e,r=battle(enemies=(king(col=9,row=9),other),start=199,first=199)
        r.advance(150)
        self.assertEqual(other.position,(1,6))
        r.advance(1)
        self.assertEqual(other.position,(1,5))
        self.assertEqual(other.next_action_tick,482)
        before=(other.position,other.next_action_tick)
        e.finish_tick()
        r.resolve_current_tick()
        self.assertEqual((other.position,other.next_action_tick),before)

    def test_bishop_retry_wait_and_past_closed_tick_do_not_shift(self):
        b=Enemy('b',2,8,None,0,kind='bishop')
        fields={'state':'waiting','next_action_tick':201}
        p,c,q,e,r=battle(enemies=(king(col=9,row=9),b),start=199,first=199,deadlines=[(b,fields)])
        e._bishop_closed_tick[1]=198
        r.advance(151)
        self.assertEqual(b.next_action_tick,351)
        self.assertEqual(e._bishop_closed_tick[1],198)
        r.advance(1)
        self.assertEqual(b.current_attack.start_tick,351)

    def test_frozen_general_can_be_killed_by_real_space_and_never_revives(self):
        other=Enemy('p',5,2,(0,-1),0)
        parts=pulse_battle(general=(other,))
        p,c,q,e,r=parts
        # DRAINING suppresses the ready Pawn before it starts an attack.
        r.advance(1)
        origin=other.position
        for tick in (1,37):
            r.advance(tick-c.tick)
            r.resolve_player_attack(c.request_attack(p))
        self.assertFalse(other.alive)
        self.assertNotIn(origin,e.occupied_cells)
        r.advance(114)
        self.assertEqual((other.state,other.health.current_hp),('inactive',0))
        self.assertFalse(any(ev.source_entity_instance_id==other.entity_instance_id for ev in e.ledger.pending))

    def test_repeated_freezes_add_exact_durations_without_drift(self):
        other=Enemy('p',1,6,(0,-1),10)
        p,c,q,e,r=pulse_battle(general=(other,))
        for expected_s in (1,153,305):
            if c.tick<expected_s:
                r.advance(expected_s-c.tick)
            self.assertEqual(e.pulse.freeze_tick,expected_s)
            old=other.next_action_tick
            r.player_invulnerable_until_tick=10000
            r.advance(150)
            self.assertEqual(other.next_action_tick,old+150)
            e.pulse.next_use_tick=c.tick+1
            e.pulse.king.next_action_tick=c.tick+1
        self.assertEqual(other.next_action_tick,1050)

    def test_bulk_8_and_single_tick_paths_have_identical_results(self):
        traces=[]
        for chunk in (1,8):
            other=Enemy('p',1,6,(0,-1),10)
            p,c,q,e,r=pulse_battle(general=(other,))
            r.player_invulnerable_until_tick=10000
            for _ in range(1200//chunk):
                r.advance(chunk)
            traces.append((c.tick,p.health.current_hp,e.pulse.state,e.pulse.next_use_tick,
                           [(x.position,x.state,x.next_action_tick,x.stun_until_tick) for x in e.enemies],
                           [(x.event.start_tick,x.event.hit_tick,x.state,x.outcome) for x in e.ledger._records.values()]))
        self.assertEqual(*traces)


class PulseParryTests(unittest.TestCase):
    def test_resolution_state_exists_at_exact_hit_before_single_adjudication(self):
        p,c,q,e,r=pulse_battle()
        r.advance(120)
        c.advance()
        due=e.advance_to(c.tick,p.position)
        self.assertEqual(e.pulse.state,'PULSE_RESOLUTION')
        self.assertEqual(due,(e.pulse.event,))
        r.resolve_enemy_attack(due[0])
        e.finish_tick()
        self.assertEqual(e.pulse.state,'CLEANUP')
        self.assertEqual(p.health.current_hp,2)

    def test_normal_perfect_and_failure_boundaries(self):
        for delta,status in ((0,'unbound'),(1,'perfect'),(7,'perfect'),(8,'normal'),(18,'normal'),(19,'unbound')):
            parts=pulse_battle()
            p,c,q,e,r=parts
            r.advance(1)
            event=e.pulse.event
            attempt=parry(parts,delta)
            self.assertEqual(r.parry_result(attempt).status,status)
            self.assertEqual(p.health.current_hp,2 if status=='unbound' else 3)
            self.assertEqual(e.pulse.king.health.current_hp,6 if status=='perfect' else 8)
            self.assertEqual(c.pending_attack_bonus,2 if status=='perfect' else 0)
            if status=='perfect':
                self.assertEqual(e.pulse.king.stun_until_tick,event.hit_tick+60)
            else:
                self.assertNotEqual(e.pulse.king.state,'stunned')

    def test_hp_1_2_3_reflection_records_rewards_before_death(self):
        for hp,after in ((1,0),(2,0),(3,1)):
            parts=pulse_battle(hp=hp)
            p,c,q,e,r=parts
            r.advance(1)
            event=e.pulse.event
            attempt=parry(parts,7)
            outcome=r.parry_result(attempt)
            self.assertEqual((e.pulse.king.health.current_hp,c.pending_attack_bonus),(after,2))
            self.assertEqual((outcome.status,e.ledger.outcome(event)),('perfect','parried_perfect'))
            self.assertEqual(c.next_attack_tick,121)
            for _ in range(4):
                self.assertIsNone(r.resolve_enemy_attack(event))
                r.register_parry(attempt)
            self.assertEqual(e.pulse.king.health.current_hp,after)
            self.assertIs(r.parry_result(attempt),outcome)
            self.assertEqual(c.pending_attack_bonus,2)

    def test_perfect_60_stun_cleanup_30_and_separate_next_attack_bonus(self):
        parts=pulse_battle()
        p,c,q,e,r=parts
        r.advance(1)
        parry(parts,7)
        origin=e.pulse.king.position
        self.assertEqual(e.pulse.king.health.last_damage_amount,2)
        self.assertEqual(e.pulse.king.health.last_damage_tick,121)
        r.advance(30)
        self.assertEqual(e.pulse.state,'NORMAL')
        r.advance(29)
        self.assertEqual(e.pulse.king.position,origin)
        r.advance(1)
        self.assertNotEqual(e.pulse.king.position,origin)
        attack=c.request_attack(p)
        self.assertEqual(attack.damage_bonus,2)
        r.resolve_player_attack(attack)
        self.assertEqual(c.pending_attack_bonus,0)

    def test_invulnerability_precedes_perfect_and_no_late_replay(self):
        parts=pulse_battle()
        p,c,q,e,r=parts
        r.advance(1)
        r.player_invulnerable_until_tick=122
        attempt=parry(parts,7)
        event=e.pulse.event
        self.assertEqual(r.parry_result(attempt).status,'failed')
        self.assertEqual(e.ledger.outcome(event),'invulnerable')
        self.assertEqual((e.pulse.king.health.current_hp,p.health.current_hp,c.pending_attack_bonus),(8,3,0))
        r.advance(1)
        self.assertIsNone(r.resolve_enemy_attack(event))

    def test_forged_pulse_kind_and_hundred_cells_do_not_authorize_reflection(self):
        parts=pulse_battle()
        p,c,q,e,r=parts
        r.advance(1)
        event=e.pulse.event
        for fake in (replace(event,attack_kind='basic'), replace(event,source_entity_instance_id='foreign')):
            with self.assertRaises(ValueError):
                r.resolve_enemy_attack(fake)
        # Even a ledger-issued payload needs the boss controller's live plan.
        fake=e.ledger.create(e.pulse.king.entity_instance_id,1,2,event.target_cells,attack_kind='king_pulse')
        e.ledger.mark_due(fake,2)
        c.advance(1)
        e.advance_to(2,p.position)
        with self.assertRaises(ValueError):
            r.resolve_enemy_attack(fake)
        self.assertEqual(e.pulse.king.health.current_hp,8)


class PulseDeathTests(unittest.TestCase):
    def test_duplicate_death_notifications_cannot_postpone_resume(self):
        other=Enemy('p',1,6,(0,-1),0)
        p,c,q,e,r=pulse_battle(general=(other,))
        r.advance(40)
        e.pulse.king.health.apply_damage(8,tick=40)
        e.deactivate(e.pulse.king.entity_instance_id,tick=40)
        e.deactivate(e.pulse.king.entity_instance_id,tick=41)
        self.assertEqual(e.pulse.resume_tick,41)
        r.advance(1)
        self.assertEqual(other.position,(1,5))

    def test_draining_telegraph_and_cleanup_king_death_resumes_next_tick(self):
        for death_tick in (0,40,121,135):
            other=Enemy('p',1,6,(0,-1),10)
            p,c,q,e,r=pulse_battle(general=(other,))
            r.advance(death_tick)
            event=e.pulse.event
            frozen=e.pulse.freeze_tick
            deadline=other.next_action_tick
            e.pulse.king.health.apply_damage(8,tick=c.tick)
            e.deactivate(e.pulse.king.entity_instance_id,tick=c.tick)
            if event is not None:
                self.assertEqual(e.ledger.state(event),'resolved' if death_tick>=121 else 'cancelled')
            self.assertEqual(e.pulse.resume_tick,death_tick+1)
            r.advance(1)
            self.assertEqual(e.pulse.state,'NORMAL')
            self.assertIsNone(e.pulse.freeze_tick)
            self.assertEqual(other.next_action_tick,deadline+(death_tick+1-frozen if frozen is not None else 0))
            previous=other.next_action_tick
            e.finish_tick()
            self.assertEqual(other.next_action_tick,previous)

    def test_real_space_on_hit_tick_kills_before_pulse_damage(self):
        other=Enemy('p',1,6,(0,-1),10)
        p,c,q,e,r=pulse_battle(hp=1,general=(other,))
        r.advance(120)
        event=e.pulse.event
        # Move only the player to a legal adjacent square; King is stationary in Pulse.
        for _ in range(4):
            p.move('right',e.occupied_cells)
        for _ in range(7):
            p.move('up',e.occupied_cells)
        c.advance()
        r.resolve_player_attack(c.request_attack(p))
        r.resolve_current_tick()
        self.assertEqual((p.health.current_hp,e.ledger.state(event)),(3,'cancelled'))
        self.assertEqual(e.pulse.resume_tick,122)
        r.advance(1)
        self.assertEqual(e.pulse.state,'NORMAL')

    def test_perfect_death_resumes_living_generals_and_keeps_success(self):
        other=Enemy('p',1,6,(0,-1),0)
        parts=pulse_battle(hp=2,general=(other,))
        p,c,q,e,r=parts
        r.advance(1)
        attempt=parry(parts,7)
        self.assertEqual(other.position,(1,6))
        r.advance(1)
        self.assertEqual(other.position,(1,5))
        self.assertEqual((r.parry_result(attempt).status,c.pending_attack_bonus),('perfect',2))

    def test_cancelled_pulse_stun_does_not_replay_and_releases_after_cleanup(self):
        p,c,q,e,r=pulse_battle()
        r.advance(20)
        event=e.pulse.event
        e.stun(e.pulse.king.entity_instance_id,c.tick)
        r.advance(1)
        self.assertEqual((e.pulse.state,e.ledger.state(event)),('CLEANUP','cancelled'))
        r.advance(30)
        self.assertEqual(e.pulse.state,'NORMAL')
        r.advance(100)
        self.assertEqual(p.health.current_hp,3)
        self.assertEqual(e.ledger.state(event),'cancelled')

    def test_stopped_resolver_discards_freeze_without_rewards_or_future_work(self):
        parts=pulse_battle()
        p,c,q,e,r=parts
        r.advance(40)
        event=e.pulse.event
        attempt=q.request(c.tick)
        r.register_parry(attempt)
        r.stop()
        before=(c.tick,p.health.current_hp,e.pulse.king.health.current_hp,c.pending_attack_bonus,len(e.ledger._records))
        for _ in range(3):
            r.advance(1000)
            r.resolve_enemy_attack(event)
            r.register_parry(attempt)
        self.assertEqual(before,(c.tick,p.health.current_hp,e.pulse.king.health.current_hp,c.pending_attack_bonus,len(e.ledger._records)))
        self.assertEqual(e.pulse._remaining,{})
        self.assertEqual(e.ledger.state(event),'cancelled')


if __name__ == '__main__':
    unittest.main()
