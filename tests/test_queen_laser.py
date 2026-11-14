"""Task2-G piercing rays, escape routes and read-only laser presentation."""
from collections import deque
from dataclasses import replace
from unittest.mock import Mock
import unittest
import main
from queen_behavior import queen_ray_targets, RAY_STEPS, choose_reposition
from enemy_attack_renderer import EnemyAttackRenderer
from tests.test_queen import fixture
from input_controller import InputController
from player import DIRECTIONS


class QueenLaserTests(unittest.TestCase):
    def test_center_directions_order_and35_unique_cells(self):
        cells=queen_ray_targets((4,4))
        self.assertEqual(RAY_STEPS,((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)))
        self.assertEqual((len(cells),len(set(cells))),(35,35))
        self.assertNotIn((4,4),cells)
        for cell in ((4,9),(9,9),(9,4),(8,0),(4,0),(0,0),(0,4),(0,8)):self.assertIn(cell,cells)

    def test_every_board_origin_matches_independent_alignment_oracle(self):
        for x in range(10):
            for y in range(10):
                expected={(a,b) for a in range(10) for b in range(10) if (a,b)!=(x,y) and (a==x or b==y or abs(a-x)==abs(b-y))}
                cells=queen_ray_targets((x,y));self.assertEqual(set(cells),expected)
                self.assertEqual(len(cells),len(expected));self.assertEqual(cells,queen_ray_targets((x,y)))
        self.assertEqual(len(queen_ray_targets((0,0))),27)

    def test_occupancy_cannot_shorten_legacy_alias_or_ai_evaluation(self):
        from queen_behavior import diagonal_targets,reposition_candidates
        full={(x,y) for x in range(10) for y in range(10)}
        self.assertEqual(diagonal_targets((4,4),(4,5),full),queen_ray_targets((4,4)))
        options=reposition_candidates((4,7),(5,1),{(3,6),(1,6),(8,6),(3,8)})
        selected=choose_reposition((4,7),(5,1),{(3,6),(1,6),(8,6),(3,8)})
        expected=min(options,key=lambda c:((5,1) not in queen_ray_targets(c),abs(c[0]-5)+abs(c[1]-1)))
        self.assertEqual(selected,expected)

    def test_low_hp_escape_routes_all_move_levels_solo_and_double(self):
        for two in (False,True):
            for interval in (18,15,12):
                g,q,event=fixture(two=two);g.player.health.apply_damage(2,tick=0)
                events=g.encounter.ledger.pending;danger=set().union(*(set(e.target_cells) for e in events))
                queue=deque([(g.player.position,())]);seen={g.player.position};path=None
                occupied=set(g.encounter.occupied_cells)
                while queue:
                    cell,moves=queue.popleft()
                    if cell not in danger:path=moves;break
                    if len(moves)>=72//interval:continue
                    for name,(dx,dy) in DIRECTIONS.items():
                        nextcell=cell[0]+dx,cell[1]+dy
                        if 0<=nextcell[0]<10 and 0<=nextcell[1]<10 and nextcell not in seen|occupied:
                            seen.add(nextcell);queue.append((nextcell,moves+(name,)))
                self.assertIsNotNone(path)
                controls=InputController(move_interval_ticks=interval)
                for name in path:
                    g.advance(interval);controls.key_down(name,g.player,tick=g.combat.tick,occupied=g.encounter.occupied_cells);controls.key_up(name)
                g.advance(72-g.combat.tick)
                self.assertEqual(g.player.health.current_hp,1)
                self.assertTrue(all(g.encounter.ledger.outcome(e)=='miss' for e in events))

    def test_snapshot_and_authentication_remain_single_consumer(self):
        g,q,event=fixture();cells=event.target_cells
        g.advance(71);g.combat.advance();g.encounter.advance_to(72,g.player.position)
        with self.assertRaises(ValueError):g.resolver.resolve_enemy_attack(replace(event,target_cells=((0,1),)))
        g.resolver.resolve_enemy_attack(event);hp=g.player.health.current_hp
        self.assertIsNone(g.resolver.resolve_enemy_attack(event));self.assertEqual(g.player.health.current_hp,hp)
        self.assertEqual(event.target_cells,cells)

    def renderer(self,g,q):
        r=EnemyAttackRenderer();r.source_cells={q.entity_instance_id:q.position};return r

    def test_charge_ramps_and_exact_snapshot_cells_are_drawn(self):
        from board import tile_bounds
        g,q,e=fixture();r=self.renderer(g,q);c=Mock()
        r.tick=0;r.draw(c,g.encounter.ledger);early=c.draw_rectangle.call_args_list
        for cell in e.target_cells:
            l,b,rr,t=tile_bounds(*cell)
            self.assertTrue(any(call.args[:4]==(l+5,b+5,rr-6,t-6) for call in early))
        c.reset_mock();r.tick=71;r.draw(c,g.encounter.ledger)
        self.assertNotEqual(early[-1].args[4:],c.draw_rectangle.call_args_list[-1].args[4:])
        self.assertEqual(len(r._beams[e.key][1]),8)

    def test_fire_fade_end_without_repeat_damage(self):
        g,q,e=fixture();r=self.renderer(g,q);r.draw(Mock(),g.encounter.ledger)
        g.advance(72);hp=g.player.health.current_hp
        c=Mock();r.tick=72;r.draw(c,g.encounter.ledger)
        self.assertTrue(any(call.args[-3:]==(255,244,210) for call in c.draw_line.call_args_list))
        c.reset_mock();r.tick=76;r.draw(c,g.encounter.ledger)
        self.assertTrue(any(call.args[-3:]==(158,112,205) for call in c.draw_line.call_args_list))
        for _ in range(5):r.draw(Mock(),g.encounter.ledger)
        self.assertEqual(g.player.health.current_hp,hp);self.assertEqual(g.combat.tick,72)
        r.tick=84;r.draw(Mock(),g.encounter.ledger);self.assertFalse(r._beams)

    def test_cancel_death_terminal_and_session_clear_visual_state(self):
        for reason in ('cancel','death','terminal','session'):
            g,q,e=fixture();r=self.renderer(g,q);r.draw(Mock(),g.encounter.ledger)
            if reason=='cancel':g.encounter.ledger.cancel(e)
            elif reason=='death':r.source_cells={}
            elif reason=='terminal':r.active=False
            else:
                other=main._new_stage_game(13);g.encounter.ledger=other.encounter.ledger
            c=Mock();r.draw(c,g.encounter.ledger)
            self.assertFalse(r._beams);self.assertFalse(c.draw_line.called)

    def test_renderer_repetition_does_not_change_any_attack_receipt(self):
        g,q,e=fixture(two=True);r=self.renderer(g,q)
        before=[(x.event,x.state,x.outcome) for x in g.encounter.ledger._records.values()]
        for _ in range(20):r.draw(Mock(),g.encounter.ledger)
        self.assertEqual(before,[(x.event,x.state,x.outcome) for x in g.encounter.ledger._records.values()])
        self.assertEqual(g.player.health.current_hp,3)

    def test_all_mixed_stages_keep_unsupported_boundary(self):
        for stage in (13,14,15):
            g=main._new_stage_game(stage)
            for _ in range(160):
                g.advance()
                r=EnemyAttackRenderer();r.tick=g.combat.tick;r.source_cells={e.entity_instance_id:e.position for e in g.encounter.enemies if e.active};r.draw(Mock(),g.encounter.ledger)
        for n in range(18,26):
            with self.assertRaises(ValueError):main._new_stage_game(n)
