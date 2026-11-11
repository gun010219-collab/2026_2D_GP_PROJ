"""Bishop PDF geometry, stationary combat and approved opposite-color turns."""
from dataclasses import replace
import unittest
from unittest.mock import Mock

from bishop_behavior import color_targets
from board import tile_bounds
from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from enemy_factory import create_enemy, create_stage_enemies, UnsupportedEnemyError
from enemy_renderer import EnemyRenderer
from enemy_attack_renderer import EnemyAttackRenderer
from health_renderer import HealthRenderer
from parry import Parry
from player import Player
from stage_manager import StageCatalog


def bishop(name='b', col=2, row=8, delay=0):
    return Enemy(name,col,row,None,delay,kind='bishop')


def battle(enemies=None, player=None):
    p = player if player is not None else Player(5,1)
    c,q = Combat(),Parry()
    e = EnemyEncounter((bishop(),) if enemies is None else enemies,
                       combat_session_id=c.combat_session_id,stage_instance_id=c.stage_instance_id)
    r = CombatResolver(p,c,e,parry=q)
    r.resolve_current_tick()
    return p,c,q,e,r


class BishopDefinitionTests(unittest.TestCase):
    def test_actual_model_hp_id_and_no_invented_pawn_direction(self):
        a,b = bishop(),bishop()
        self.assertEqual((a.kind,a.position,a.forward,a.health.current_hp,a.health.max_hp),
                         ('bishop',(2,8),None,3,3))
        self.assertNotEqual(a.data_id,a.entity_instance_id)
        self.assertNotEqual(a.entity_instance_id,b.entity_instance_id)
        self.assertIsNot(a.health,b.health)
        self.assertEqual(bishop(delay=.8).initial_delay_ticks,48)

    def test_original_stage_four_factory_order_hp_delay_and_definition_immutability(self):
        stage = StageCatalog.load().get_stage(4)
        enemies = create_stage_enemies(stage)
        self.assertEqual(stage.player_spawn,(5,1))
        self.assertEqual([(e.kind,e.position,e.health.current_hp,e.initial_delay_ticks) for e in enemies],
            [('bishop',(2,8),3,48),('rook',(2,4),4,62),('pawn',(1,6),2,75),('pawn',(8,6),2,88)])
        enemies[0].health.apply_damage(1,tick=0)
        fresh = create_stage_enemies(stage)
        self.assertEqual(fresh[0].health.current_hp,3)
        self.assertEqual(stage.enemies[0].position,(2,8))
        self.assertFalse(hasattr(stage.enemies[0],'health'))
        self.assertTrue({e.entity_instance_id for e in enemies}.isdisjoint(e.entity_instance_id for e in fresh))

    def test_bad_bishop_fields_options_and_unimplemented_queen_king_are_rejected(self):
        for change in ({'col':True},{'row':10},{'forward':(0,-1)},{'initial_delay':-1},
                       {'initial_delay':float('nan')},{'kind':'queen'}):
            values=dict(data_id='b',col=2,row=8,forward=None,initial_delay=0,kind='bishop')
            values.update(change)
            with self.assertRaises(ValueError):
                Enemy(**values)
        catalog=StageCatalog.load()
        with self.assertRaises(UnsupportedEnemyError):
            create_enemy(replace(catalog.get_stage(4).enemies[0],options={'forward':(0,-1)}))
        for kind in ('queen','king'):
            definition=next(e for s in catalog.stages for e in s.enemies if e.kind==kind)
            with self.assertRaises(UnsupportedEnemyError):
                create_enemy(definition)


class BishopGeometryTests(unittest.TestCase):
    def test_every_origin_targets_exactly_fifty_same_color_squares_including_origin(self):
        for col in range(10):
            for row in range(10):
                cells=color_targets((col,row))
                self.assertIsInstance(cells,tuple)
                self.assertEqual(len(cells),50)
                self.assertEqual(len(set(cells)),50)
                self.assertIn((col,row),cells)
                self.assertTrue(all(0<=x<10 and 0<=y<10 and (x+y)%2==(col+row)%2 for x,y in cells))
        self.assertTrue(set(color_targets((0,0))).isdisjoint(color_targets((0,1))))
        self.assertEqual(len(set(color_targets((0,0)))|set(color_targets((0,1)))),100)

    def test_targets_are_not_diagonal_rays_and_bad_origins_fail(self):
        self.assertIn((8,0),color_targets((2,8)))
        for origin in (None,(True,1),(10,1),(-1,1),(1,),('2',8)):
            with self.assertRaises(ValueError):
                color_targets(origin)


class BishopCombatTests(unittest.TestCase):
    def test_exact_108_hit_once_stationary_and_240_recovery_boundary(self):
        p,c,q,e,r=battle()
        source=e.enemies[0]
        event=source.current_attack
        self.assertEqual((event.start_tick,event.hit_tick,len(event.target_cells)),(0,108,50))
        r.advance(107)
        self.assertEqual(p.health.current_hp,3)
        r.advance(1)
        self.assertEqual((p.health.current_hp,source.position,source.next_action_tick),(2,(2,8),348))
        for _ in range(5):
            self.assertIsNone(r.resolve_enemy_attack(event))
        r.advance(239)
        self.assertEqual(source.state,'recovering')
        r.advance(1)
        self.assertEqual(source.current_attack.start_tick,348)
        self.assertNotEqual(source.current_attack.key,event.key)

    def test_warns_on_schedule_even_when_player_starts_safe_and_entry_can_hit(self):
        p,c,q,e,r=battle(player=Player(5,2))
        event=e.enemies[0].current_attack
        self.assertIsNotNone(event)
        p.move('down',e.occupied_cells)
        r.advance(108)
        self.assertEqual(p.health.current_hp,2)
        self.assertEqual(e.ledger.outcome(event),'hit')

    def test_one_cardinal_step_evades_frozen_color_without_moving_bishop(self):
        p,c,q,e,r=battle()
        event=e.enemies[0].current_attack
        p.move('up',e.occupied_cells)
        r.advance(108)
        self.assertEqual((p.health.current_hp,e.enemies[0].position),(3,(2,8)))
        self.assertEqual(e.ledger.outcome(event),'miss')
        p.move('down',e.occupied_cells)
        self.assertIsNone(r.resolve_enemy_attack(event))
        self.assertEqual(p.health.current_hp,3)

    def test_other_active_pieces_do_not_occlude_any_of_fifty_squares(self):
        p,c,q,e,r=battle((bishop(),Enemy('r',2,4,None,10,kind='rook'),Enemy('p',1,7,(0,-1),10)))
        event=e.enemies[0].current_attack
        self.assertIn((2,4),event.target_cells)
        self.assertIn((1,7),event.target_cells)
        r.advance(108)
        self.assertEqual(p.health.current_hp,2)
        self.assertEqual(e.ledger.outcome(event),'hit')
        self.assertEqual([x.health.current_hp for x in e.enemies],[3,4,2])

    def test_actual_parry_boundaries_and_stationary_position(self):
        for delta,grade in ((0,'unbound'),(1,'perfect'),(7,'perfect'),(8,'normal'),(18,'normal'),(19,'unbound')):
            p,c,q,e,r=battle()
            r.advance(108-delta)
            attempt=q.request(c.tick)
            r.register_parry(attempt)
            r.advance(delta)
            self.assertEqual(r.parry_result(attempt).status,grade)
            self.assertEqual(e.enemies[0].position,(2,8))
            self.assertEqual(p.health.current_hp,2 if grade=='unbound' else 3)
            self.assertEqual(c.pending_attack_bonus,2 if grade=='perfect' else 0)

    def test_perfect_stuns_source_only_until_168_and_bonus_consumed_by_next_attack(self):
        p,c,q,e,r=battle((bishop(),Enemy('p',9,9,(0,-1),10)))
        r.advance(101)
        r.resolve_player_attack(c.request_attack(p))
        self.assertEqual(c.next_attack_tick,137)
        attempt=q.request(c.tick)
        r.register_parry(attempt)
        event=e.enemies[0].current_attack
        r.advance(7)
        self.assertEqual((e.enemies[0].state,e.enemies[0].stun_until_tick,c.next_attack_tick),('stunned',168,108))
        self.assertNotEqual(e.enemies[1].state,'stunned')
        counter=c.request_attack(p)
        self.assertEqual(counter.damage_bonus,2)
        r.resolve_player_attack(counter)  # A miss still spends the bonus.
        self.assertEqual(c.pending_attack_bonus,0)
        self.assertIsNone(r.resolve_enemy_attack(event))
        r.advance(59)
        self.assertEqual(e.enemies[0].state,'stunned')
        r.advance(1)
        self.assertEqual(e.enemies[0].current_attack.start_tick,168)

    def test_existing_invulnerability_suppresses_parry_reward_and_delayed_hit(self):
        p,c,q,e,r=battle()
        r.advance(101)
        attempt=q.request(c.tick)
        r.register_parry(attempt)
        event=e.enemies[0].current_attack
        r.player_invulnerable_until_tick=109
        r.advance(7)
        self.assertEqual((p.health.current_hp,c.pending_attack_bonus),(3,0))
        self.assertEqual(e.ledger.outcome(event),'invulnerable')
        self.assertEqual(r.parry_result(attempt).reason,'invulnerable')
        r.advance(1)
        self.assertIsNone(r.resolve_enemy_attack(event))

    def test_perfect_bonus_kills_bishop_with_one_three_damage_attack(self):
        p,c,q,e,r=battle((bishop(col=5,row=3),))
        r.advance(101)
        r.register_parry(q.request(c.tick))
        event=e.enemies[0].current_attack
        r.advance(7)
        p.move('up',e.occupied_cells)
        attack=c.request_attack(p)
        hit=r.resolve_player_attack(attack)
        self.assertEqual((attack.damage_bonus,hit.amount,e.enemies[0].health.current_hp),(2,3,0))
        self.assertEqual(c.pending_attack_bonus,0)
        self.assertIsNone(r.resolve_player_attack(attack))
        self.assertEqual(e.ledger.outcome(event),'parried_perfect')

    def test_normal_parry_does_not_reset_attack_cooldown_or_add_invulnerability(self):
        p,c,q,e,r=battle()
        r.advance(90)
        r.resolve_player_attack(c.request_attack(p))
        r.register_parry(q.request(c.tick))
        r.advance(18)
        self.assertEqual((r.last_parry_result.status,c.next_attack_tick,c.pending_attack_bonus,
                          r.player_invulnerable_until_tick),('normal',126,0,0))

    def test_death_stun_and_stop_cancel_pending_attack_without_rewards(self):
        for cause in ('death','stun','stop'):
            p,c,q,e,r=battle()
            event=e.enemies[0].current_attack
            r.advance(101)
            attempt=q.request(c.tick)
            r.register_parry(attempt)
            if cause=='death':
                e.enemies[0].health.apply_damage(3,tick=c.tick)
                e.deactivate(e.enemies[0].entity_instance_id)
            elif cause=='stun':
                e.stun(e.enemies[0].entity_instance_id,c.tick)
            else:
                r.stop()
            r.advance(7)
            self.assertEqual(e.ledger.state(event),'cancelled')
            self.assertEqual((p.health.current_hp,c.pending_attack_bonus),(3,0))
            self.assertIsNone(r.resolve_enemy_attack(event))

    def test_fatal_space_before_same_tick_ai_cancels_bishop(self):
        p,c,q,e,r=battle((bishop(col=5,row=2),),Player(5,3))
        source=e.enemies[0]
        source.health.apply_damage(2,tick=0)
        event=source.current_attack
        r.advance(107)
        p.move('down',e.occupied_cells)  # Blocked move faces the Bishop.
        c.advance()
        r.resolve_player_attack(c.request_attack(p))
        r.resolve_current_tick()
        self.assertFalse(source.active)
        self.assertEqual(e.ledger.state(event),'cancelled')
        self.assertEqual(p.health.current_hp,3)

    def test_past_foreign_modified_and_ledger_only_events_are_rejected(self):
        p,c,q,e,r=battle()
        event=e.enemies[0].current_attack
        fresh=battle()
        for bad in (event,replace(event,target_cells=((0,0),))):
            with self.assertRaises(ValueError):
                fresh[-1].resolve_enemy_attack(bad)
        with self.assertRaises(ValueError):
            r.resolve_enemy_attack(replace(event,hit_tick=109))
        fake=e.ledger.create(e.enemies[0].entity_instance_id,0,1,((5,1),))
        c.advance()
        e.advance_to(1,p.position)
        e.ledger.mark_due(fake,1)
        with self.assertRaisesRegex(ValueError,'color attack plan'):
            r.resolve_enemy_attack(fake)


class BishopTurnTests(unittest.TestCase):
    def test_opposite_colors_wait_through_due_then_start_on_109(self):
        p,c,q,e,r=battle((bishop('a'),bishop('b',7,8)))
        self.assertIsNone(e.enemies[1].current_attack)
        r.advance(107)
        c.advance()
        due=e.advance_to(108,p.position)
        self.assertIsNone(e.enemies[1].current_attack)
        # Unresolved due must block the opposite attack even with AI-only advance.
        e.advance_to(109,p.position)
        self.assertIsNone(e.enemies[1].current_attack)
        # Late adjudication expires rather than applying historical damage.
        c.advance()
        r.resolve_enemy_attack(due[0])
        r.advance(1)
        self.assertEqual(e.enemies[1].current_attack.start_tick,110)
        normal=battle((bishop('a'),bishop('b',7,8)))
        normal[-1].advance(108)
        self.assertIsNone(normal[-2].enemies[1].current_attack)
        normal[-1].advance(1)
        self.assertEqual(normal[-2].enemies[1].current_attack.start_tick,109)

    def test_json_order_controls_winner_same_color_can_overlap(self):
        for enemies in ((bishop('a'),bishop('b',7,8)),(bishop('b',7,8),bishop('a'))):
            p,c,q,e,r=battle(enemies)
            self.assertIsNotNone(e.enemies[0].current_attack)
            self.assertIsNone(e.enemies[1].current_attack)
        p,c,q,e,r=battle((bishop('a'),bishop('b',4,8)))
        events=[x.current_attack for x in e.enemies]
        self.assertTrue(all(events))
        r.advance(108)
        self.assertEqual([e.ledger.outcome(x) for x in events],['hit','invulnerable'])
        self.assertEqual(p.health.current_hp,2)

    def test_cancel_and_perfect_release_only_from_following_tick(self):
        for cause in ('cancel','perfect'):
            p,c,q,e,r=battle((bishop('a'),bishop('b',7,8)))
            if cause=='cancel':
                r.advance(50)
                e.cancel_attacks(e.enemies[0].entity_instance_id,tick=50)
                release=51
            else:
                r.advance(101)
                r.register_parry(q.request(c.tick))
                r.advance(7)
                release=109
            self.assertIsNone(e.enemies[1].current_attack)
            r.advance(1)
            self.assertEqual(e.enemies[1].current_attack.start_tick,release)

    def test_input_death_before_ai_defers_opposite_until_next_tick(self):
        p,c,q,e,r=battle((bishop('a',5,2),bishop('b',6,8)))
        e.enemies[0].health.apply_damage(2,tick=0)
        r.advance(49)
        c.advance()
        r.resolve_player_attack(c.request_attack(p))
        r.resolve_current_tick()
        self.assertIsNone(e.enemies[1].current_attack)
        r.advance(1)
        self.assertEqual(e.enemies[1].current_attack.start_tick,51)

    def test_original_two_bishop_data_runs_without_covering_both_colors(self):
        p,c,q,e,r=battle(create_stage_enemies(StageCatalog.load().get_stage(12)))
        for _ in range(400):
            colors={sum(source.position)%2 for source in e.enemies if source.kind=='bishop'
                    and source.current_attack is not None and e.ledger.state(source.current_attack)=='telegraph'}
            self.assertLessEqual(len(colors),1)
            r.advance(1)
            if not p.alive:
                break

    def test_invalid_cancel_tick_does_not_cancel_a_live_attack(self):
        p,c,q,e,r=battle()
        event=e.enemies[0].current_attack
        for bad in (-1,True,1.5):
            with self.assertRaises(ValueError):
                e.cancel_attacks(e.enemies[0].entity_instance_id,tick=bad)
        self.assertEqual(e.ledger.state(event),'telegraph')

    def test_repeated_opposite_color_turns_never_overlap_or_starve(self):
        p,c,q,e,r=battle((bishop('a'),bishop('b',7,8)))
        starts={'a':set(),'b':set()}
        for _ in range(900):
            active=[x.current_attack for x in e.enemies if x.current_attack is not None]
            self.assertLessEqual(len(active),1)
            for source in e.enemies:
                event=source.current_attack
                if event is not None:
                    starts[source.data_id].add(event.start_tick)
                    if event.hit_tick==c.tick+1 and p.position in event.target_cells:
                        p.move('up' if p.row==1 else 'down',e.occupied_cells)
            r.advance(1)
        self.assertEqual(p.health.current_hp,3)
        self.assertGreaterEqual(len(starts['a']),3)
        self.assertGreaterEqual(len(starts['b']),3)


class BishopRendererTests(unittest.TestCase):
    def test_warning_is_exact_fifty_cells_and_rendering_never_consumes_or_moves(self):
        p,c,q,e,r=battle()
        event=e.enemies[0].current_attack
        before=(p.health.current_hp,c.tick,e.enemies[0].position,c.pending_attack_bonus)
        for _ in range(3):
            canvas=Mock()
            EnemyAttackRenderer().draw(canvas,e.ledger)
            self.assertEqual(canvas.draw_rectangle.call_count,100)
            bounds=[call.args[:4] for call in canvas.draw_rectangle.call_args_list[::2]]
            self.assertEqual(bounds,[(l,b,rr-1,t-1) for l,b,rr,t in map(lambda cell:tile_bounds(*cell),event.target_cells)])
            EnemyRenderer().draw(canvas,e.enemies)
            HealthRenderer().draw(canvas,p,e.enemies,c.tick)
        self.assertEqual(before,(p.health.current_hp,c.tick,e.enemies[0].position,c.pending_attack_bonus))
        self.assertEqual(e.ledger.state(event),'telegraph')

    def test_split_crown_silhouette_fits_board_and_dead_bishop_is_hidden(self):
        for col in range(10):
            for row in range(10):
                source=bishop(col=col,row=row)
                canvas=Mock()
                EnemyRenderer().draw(canvas,(source,))
                canvas.draw_circle.assert_not_called()
                left,bottom,right,top=tile_bounds(col,row)
                self.assertTrue(all(left<x1<=x2<right-1 and bottom<y1<=y2<top-1
                                    for x1,y1,x2,y2,*_ in (call.args for call in canvas.draw_rectangle.call_args_list)))
        source.health.apply_damage(3,tick=0)
        canvas=Mock()
        EnemyRenderer().draw(canvas,(source,))
        self.assertEqual(canvas.mock_calls,[])


if __name__=='__main__':
    unittest.main()
