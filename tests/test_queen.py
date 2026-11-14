"""Queen geometry, real combat, ownership and Pulse fixtures; no playable Stage13."""
from dataclasses import replace
import unittest
from unittest.mock import Mock
import main
from combat import Combat
from parry import Parry
from player import Player
from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from combat_resolution import CombatResolver
from combat_balance import profile_for
from stage_manager import StageCatalog
from enemy_factory import create_stage_enemies
from queen_behavior import *
from tools.queen_preview import PreviewCombat,PreviewFlow,PreviewRenderer


def fixture(two=False,king=False):
    g=PreviewCombat(3,'solo')
    # Timing fixture starts at attack phase to isolate adjudication boundaries.
    q=g.encounter.enemies[0]
    q.col,q.row=4,4
    g.player=Player(5,3)
    enemies=[q]
    if two:enemies.append(Enemy('q2',6,4,None,0,kind='queen',max_hp=14))
    if king:enemies.append(Enemy('king',9,9,None,0,kind='king',boss_hp=60))
    g.encounter=EnemyEncounter(enemies,combat_session_id=g.combat.combat_session_id,stage_instance_id=g.combat.stage_instance_id,boss=king)
    g.resolver=CombatResolver(g.player,g.combat,g.encounter,parry=g.parry)
    for e in enemies:
        if e.kind=='queen':g.encounter.queen_steps[e.entity_instance_id]='diagonal_attack'
    g.resolve_current_tick()
    return g,q,q.current_attack


class QueenTests(unittest.TestCase):
    def test_profiles_factory_and_no_implicit_default(self):
        for chapter,hp in ((3,14),(4,18),(5,22)):
            self.assertEqual(profile_for(chapter).hp('queen'),hp)
        for chapter in (1,2):
            with self.assertRaises(ValueError):profile_for(chapter).hp('queen')
        for hp in (None,0,-1,True,1.5):
            with self.assertRaises((ValueError,TypeError)):Enemy('q',4,4,None,0,kind='queen',max_hp=hp)
        for n in (13,14,15):
            d=StageCatalog.load().get_stage(n)
            es=create_stage_enemies(d,profile=profile_for(d.chapter))
            self.assertTrue(any(e.kind=='queen' and e.health.max_hp==14 for e in es))
            if n>=16:
                with self.assertRaises(ValueError):main._new_stage_game(n)
            else:self.assertEqual(main._new_stage_game(n).stage_number,n)
            with self.assertRaises(ValueError):create_stage_enemies(d)

    def test_candidate_order_blocking_and_three_cell_limit(self):
        cells=reposition_candidates((4,4),(9,9))
        self.assertEqual(cells[:6],((4,5),(4,6),(4,7),(5,5),(6,6),(7,7)))
        self.assertEqual(len(cells),24)
        for c in cells:self.assertLessEqual(max(abs(c[0]-4),abs(c[1]-4)),3)
        blocked=reposition_candidates((4,4),(4,6),{(5,5)})
        for c in ((4,6),(4,7),(5,5),(6,6),(7,7)):self.assertNotIn(c,blocked)
        self.assertNotIn((4,4),cells)

    def test_candidate_score_and_deterministic_ties(self):
        for x in range(10):
            for y in range(10):
                if (x,y)==(4,4):continue
                candidates=reposition_candidates((4,4),(x,y),{(5,5)})
                expected=min(candidates,key=lambda c:((x,y) not in diagonal_targets(c,(x,y),{(5,5)}),abs(c[0]-x)+abs(c[1]-y)))
                self.assertEqual(choose_reposition((4,4),(x,y),{(5,5)}),expected)

    def test_corner_and_no_candidates(self):
        occupied={(4+dx,4+dy) for dx,dy in MOVE_STEPS}
        self.assertEqual(choose_reposition((4,4),(9,9),occupied),(4,4))
        self.assertTrue(all(0<=v<=3 for c in reposition_candidates((0,0),(9,9)) for v in c))

    def test_ray_order_range_and_first_occupant_included(self):
        cells=diagonal_targets((4,4),(9,9),{(6,6),(2,2)})
        self.assertEqual(cells[:5],((4,5),(4,6),(4,7),(4,8),(4,9)))
        self.assertIn((7,7),cells);self.assertIn((1,1),cells);self.assertEqual(len(cells),35)
        self.assertIn((8,0),cells);self.assertIn((0,8),cells)
        self.assertNotIn((4,4),cells);self.assertEqual(len(cells),len(set(cells)))
        self.assertEqual(len(diagonal_targets((0,0),(2,2))),27)

    def test_initial_reposition_next_tick_attack_and_recovery(self):
        g=PreviewCombat();q=g.encounter.enemies[0];q.next_action_tick=48
        g.advance(47);self.assertIsNone(q.current_attack)
        origin=q.position;g.advance();self.assertNotEqual(q.position,origin)
        self.assertIsNone(q.current_attack);g.advance()
        event=q.current_attack;position=q.position
        self.assertEqual((event.start_tick,event.hit_tick),(49,121))
        g.advance(71);self.assertEqual(g.player.health.current_hp,3)
        g.advance();self.assertEqual(q.next_action_tick,301)
        g.advance(179);self.assertEqual(q.position,position)
        g.advance();self.assertIsNone(q.current_attack)
        self.assertEqual(g.encounter.queen_steps[q.entity_instance_id],'diagonal_attack')
        g.advance();self.assertEqual(q.current_attack.start_tick,302)

    def test_hit_exact72_and_no_duplicate(self):
        g,q,e=fixture();pos=q.position
        g.advance(71);self.assertEqual(g.player.health.current_hp,3)
        results=g.advance();self.assertEqual(results[0].amount,1)
        self.assertEqual(g.player.health.current_hp,2)
        self.assertEqual(g.resolver.player_invulnerable_until_tick,120)
        self.assertEqual(q.position,pos);self.assertFalse(g.encounter._attack_moves)
        self.assertIsNone(g.resolver.resolve_enemy_attack(e))

    def test_snapshot_does_not_recompute_after_occupancy_change(self):
        g,q,e=fixture();snapshot=e.target_cells
        g.player.move('right');g.advance(72)
        self.assertEqual(e.target_cells,snapshot)
        self.assertEqual(g.encounter.ledger.outcome(e),'miss')
        self.assertEqual(g.player.health.current_hp,3)

    def test_normal_and_perfect_no_reflect_and_stun_replaces_recovery(self):
        for delta,status in ((18,'normal'),(7,'perfect')):
            g,q,e=fixture();g.advance(72-delta)
            g.resolver.register_parry(g.parry.request(g.combat.tick));g.advance(delta)
            self.assertEqual(g.encounter.ledger.outcome(e),'parried_'+status)
            self.assertEqual((g.player.health.current_hp,q.health.current_hp),(3,14))
            self.assertEqual(g.combat.pending_attack_bonus,2 if status=='perfect' else 0)
            if status=='perfect':
                self.assertEqual(q.stun_until_tick,132)
                g.advance(59);self.assertEqual(q.position,(4,4))
                g.advance();self.assertEqual(g.encounter.queen_steps[q.entity_instance_id],'diagonal_attack')

    def test_bonus_miss_consumption(self):
        g,q,e=fixture();g.advance(65);g.resolver.register_parry(g.parry.request(65));g.advance(7)
        g.player.move('right');a=g.combat.request_attack(g.player)
        g.resolver.resolve_player_attack(a);self.assertEqual(a.damage_bonus,2)
        self.assertEqual(g.combat.pending_attack_bonus,0)

    def test_two_queens_ids_order_invulnerability_and_stationary(self):
        g,q,e=fixture(two=True);events=tuple(g.encounter.ledger.pending)
        self.assertEqual(len(events),2);self.assertNotEqual(events[0].key,events[1].key)
        positions=[e.position for e in g.encounter.enemies]
        g.advance(72)
        self.assertEqual([g.encounter.ledger.outcome(e) for e in events],['hit','invulnerable'])
        self.assertEqual([e.position for e in g.encounter.enemies],positions)
        self.assertFalse(g.encounter._attack_moves)

    def test_forged_modified_foreign_and_basic_queen_rejected(self):
        g,q,e=fixture();other,_,_=fixture()
        for changes in ({'attack_kind':'basic'},{'target_cells':((1,1),)},{'hit_tick':73},{'source_entity_instance_id':'foreign'}):
            with self.assertRaises(ValueError):g.resolver.resolve_enemy_attack(replace(e,**changes))
        with self.assertRaises(ValueError):other.resolver.resolve_enemy_attack(e)
        g.advance(71);g.combat.advance();g.encounter.advance_to(72,g.player.position)
        for kind in ('basic','queen_diagonal'):
            fake=g.encounter.ledger.create(q.entity_instance_id,0,72,(g.player.position,),attack_kind=kind)
            g.encounter.ledger.mark_due(fake,72)
            with self.assertRaises(ValueError):g.resolver.resolve_enemy_attack(fake)
        self.assertEqual(g.player.health.current_hp,3)

    def test_other_kind_queen_event_forgery_rejected(self):
        from tests.test_pawn_contact import start
        g,e=start();pawn=g.encounter.enemies[0]
        g.advance(38);g.combat.advance();g.encounter.advance_to(39,g.player.position)
        fake=g.encounter.ledger.create(pawn.entity_instance_id,0,39,(g.player.position,),attack_kind='queen_diagonal')
        g.encounter.ledger.mark_due(fake,39)
        with self.assertRaises(ValueError):g.resolver.resolve_enemy_attack(fake)

    def test_death_stun_and_stop_cancel_plans(self):
        for mode in ('death','stun','stop'):
            g,q,e=fixture();g.advance(20)
            if mode=='death':
                q.health.apply_damage(14,tick=20);g.encounter.deactivate(q.entity_instance_id,tick=20)
            elif mode=='stun':g.encounter.stun(q.entity_instance_id,20)
            else:g.resolver.stop()
            self.assertEqual(g.encounter.ledger.state(e),'cancelled')
            self.assertFalse(g.encounter._attack_moves)
            self.assertEqual(g.encounter.ledger.telegraphs,())
            self.assertIsNone(g.resolver.resolve_enemy_attack(e))

    def test_pulse_drains_all_outcomes_and_freezes_step(self):
        for outcome in ('hit','miss','normal','perfect','death'):
            g,q,e=fixture(king=True);p=g.encounter.pulse
            p.next_use_tick=1;p.king.next_action_tick=1
            g.advance();self.assertEqual(p.state,'DRAINING')
            if outcome=='miss':g.player.move('right')
            elif outcome=='death':
                q.health.apply_damage(14,tick=1);g.encounter.deactivate(q.entity_instance_id,tick=1)
            elif outcome in ('normal','perfect'):
                at=54 if outcome=='normal' else 65
                g.advance(at-g.combat.tick);g.resolver.register_parry(g.parry.request(at))
            while p.event is None and g.combat.tick<80:g.advance()
            self.assertIsNotNone(p.event);self.assertEqual(len(p.event.target_cells),100)
            self.assertNotIn(e.key,g.encounter._attack_moves)
            step=g.encounter.queen_steps[q.entity_instance_id];state=(q.position,q.next_action_tick)
            g.advance(30)
            self.assertEqual(g.encounter.queen_steps[q.entity_instance_id],step)
            self.assertEqual((q.position,q.next_action_tick),state)
            p.king.health.apply_damage(60,tick=g.combat.tick)
            g.encounter.deactivate(p.king.entity_instance_id,tick=g.combat.tick);g.advance()
            self.assertIsNone(p.freeze_tick)

    def test_two_queen_full_pulse_cleanup_restores_remaining_wait(self):
        g,q,e=fixture(two=True,king=True);p=g.encounter.pulse
        p.next_use_tick=1;p.king.next_action_tick=1
        g.advance(73)
        self.assertEqual(p.event.start_tick,73)
        saved=[(x.position,g.encounter.queen_steps[x.entity_instance_id]) for x in g.encounter.enemies[:2]]
        g.advance(113);g.resolver.register_parry(g.parry.request(186));g.advance(7)
        self.assertEqual(p.king.health.current_hp,58)
        g.advance(30)
        self.assertEqual(p.state,'NORMAL')
        for i,x in enumerate(g.encounter.enemies[:2]):
            self.assertEqual((x.position,g.encounter.queen_steps[x.entity_instance_id]),saved[i])
            self.assertEqual(x.next_action_tick,402)

    def test_mixed_and_double_queen_determinism(self):
        for scenario in ('mixed','double','pulse'):
            traces=[]
            for stride in (1,8):
                g=PreviewCombat(3,scenario)
                for _ in range(640//stride):g.advance(stride)
                traces.append((g.combat.tick,g.state,g.player.health.current_hp,
                  [(e.position,e.state,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies],
                  list(g.encounter.queen_steps.values()),[(r.event.start_tick,r.event.hit_tick,r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
            self.assertEqual(traces[0],traces[1])

    def test_render_is_read_only_and_stage_guard_remains(self):
        from enemy_renderer import EnemyRenderer
        from enemy_attack_renderer import EnemyAttackRenderer
        g,q,e=fixture();before=(q.position,e.target_cells,g.player.health.current_hp)
        for _ in range(3):
            EnemyRenderer().draw(Mock(),g.encounter.enemies)
            EnemyAttackRenderer().draw(Mock(),g.encounter.ledger)
        self.assertEqual(before,(q.position,e.target_cells,g.player.health.current_hp))
        for n in range(17,26):
            with self.assertRaises(ValueError):main._new_stage_game(n)
