import pickle
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from actor_animation import ActorAnimation, Pose, State
from actor_mesh import REST, deformation
from arena_art_common import CAMERA
from attack_telegraph import warning_frame
from combat_vfx import CombatVFX
from main import _new_stage_game
from player import DIRECTIONS
from player_combat_guide import arrow, draw_aim, player_aim
from presentation_events import PresentationEvents
from sdl_input import GameplayInput
from tests import test_main


class PlayerCombatVisualTests(unittest.TestCase):
    def start(self, stage=1):
        game = _new_stage_game(stage)
        game.encounter.ledger.presentation = PresentationEvents()
        return game, ActorAnimation(improved=True,enemy_attacks=True,player_actions=True)

    def present(self, game, animation, vfx=None, elapsed=1/60):
        batch = game.encounter.ledger.presentation.drain()
        before = pickle.dumps(game)
        animation.update(game,elapsed,batch)
        if vfx:
            vfx.update(game,elapsed,batch)
        self.assertEqual(pickle.dumps(game),before)
        return batch

    def test_direction_move_before_attack_and_locked_snapshot_after_turn(self):
        poses = set()
        for facing,(dx,dy) in DIRECTIONS.items():
            g,a = self.start()
            c = test_main.WindowLoopTests().make_canvas()
            controls = GameplayInput(c)
            def key(code):
                controls.handle_key(SimpleNamespace(type=c.SDL_KEYDOWN,key=code),g.player,g.combat,
                                    occupied=g.encounter.occupied_cells,parry=g.parry,
                                    on_attack=g.resolver.resolve_player_attack)
            if facing=='down':
                self.assertTrue(g.player.move('up'))
            key(getattr(c,'SDLK_'+facing.upper()))
            origin = g.player.position
            expect = (origin[0]+dx,origin[1]+dy)
            self.assertEqual((player_aim(g).facing,player_aim(g).target),(facing,expect))
            key(c.SDLK_LCTRL)
            event = g.combat.active_attack
            self.assertEqual((event.origin_cell,event.facing,event.target_cell),(origin,facing,expect))
            opposite = next(name for name,d in DIRECTIONS.items() if d==(-dx,-dy))
            g.player.move(opposite,occupied=g.encounter.occupied_cells)
            vfx = CombatVFX(layered=True)
            self.present(g,a,vfx)
            pose = a.pose(g,g.player,None)
            self.assertEqual((pose.state,pose.attack_motion,pose.direction,pose.depth_direction),
                             (State.ATTACK,'swing',dx,dy))
            aim = player_aim(g)
            self.assertEqual(aim.facing,opposite)
            self.assertIs(aim.strike,event)
            effect = next(f for f in vfx.effects if f.name=='player_swing')
            self.assertEqual((effect.origin,effect.cell),(origin,expect))
            a.update(g,.044,())
            poses.add(deformation('player',g.chapter,a.pose(g,g.player,None)))
        self.assertEqual(len(poses),4)

    def test_visual_swing_has_distinct_keys_and_recovers_while_feet_keep_game_position(self):
        states = [deformation('player',1,Pose(State.ATTACK,t,direction=1.,attack_motion='swing'))
                  for t in (0.,.19,.46,.73,1.)]
        self.assertEqual(len(set(states)),5)
        self.assertEqual(states[-1],REST)
        self.assertGreater(states[1].lean,states[0].lean)
        self.assertGreater(states[2].cloth,states[1].cloth)

    def test_edge_chevrons_stay_inside_the_player_cell_and_no_target_outside(self):
        for facing,edge in (('left',(0,1)),('right',(9,1)),('up',(5,9)),('down',(5,0))):
            g,_ = self.start()
            dx,dy = DIRECTIONS[facing]
            while g.player.position != edge:
                x,y = g.player.position
                next_direction = 'left' if x>edge[0] else 'right' if x<edge[0] else 'down' if y>edge[1] else 'up'
                self.assertTrue(g.player.move(next_direction))
            self.assertFalse(g.player.move(facing))
            self.assertIsNone(g.combat.request_attack(g.player))
            aim = player_aim(g)
            self.assertIsNone(aim.target)
            self.assertIsNone(aim.strike)
            for line in arrow(edge,facing):
                self.assertTrue(all(CAMERA.pick(*end)==edge for end in line))
            canvas = Mock()
            draw_aim(canvas,aim)
            self.assertEqual(canvas.draw_line.call_count,len(arrow(edge,facing)))

    def test_real_parry_grades_and_empty_link_make_distinct_body_poses(self):
        effects = {}
        for kind,tick in (('normal',369),('perfect',379),('unbound',1)):
            g,a = self.start(25 if kind!='unbound' else 1)
            while g.combat.tick < tick-1:
                g.advance()
                self.present(g,a)
            g.advance(0)
            g.combat.advance(1)
            attempt = g.parry.request(g.combat.tick)
            g.resolver.register_parry(attempt)
            g.resolve_current_tick()
            self.present(g,a)
            while kind!='unbound' and g.combat.tick<385:
                g.advance()
                self.present(g,a)
            self.assertEqual(g.resolver.last_parry_result.status,kind)
            pose = a.pose(g,g.player,None)
            self.assertEqual(pose.attack_motion,'guard')
            effects[kind] = deformation('player',g.chapter,pose)
        self.assertEqual(len(set(effects.values())),3)
        self.assertGreater(effects['perfect'].core,effects['normal'].core)
        self.assertGreater(effects['unbound'].squash,effects['normal'].squash)

    def test_same_input_tick_keeps_attack_and_parry_and_telegraph_readonly(self):
        g,a = self.start(24)
        while g.combat.tick < 63:
            g.advance()
            self.present(g,a)
        self.assertGreaterEqual(len(g.encounter.ledger.telegraphs),2)
        before = warning_frame(g)
        g.combat.advance(1)
        attack = g.combat.request_attack(g.player)
        g.resolver.resolve_player_attack(attack)
        attempt = g.parry.request(g.combat.tick)
        g.resolver.register_parry(attempt)
        g.resolve_current_tick()
        batch = self.present(g,a)
        self.assertTrue({'attack_start','parry_failed'} <= {e.kind for e in batch})
        self.assertIs(player_aim(g).strike,attack)
        self.assertEqual(a.pose(g,g.player,None).state,State.PARRY_FAILED)
        settled = warning_frame(g)
        snap = pickle.dumps(g)
        draw_aim(Mock(),player_aim(g))
        self.assertEqual(pickle.dumps(g),snap)
        self.assertEqual(warning_frame(g),settled)
        self.assertEqual(set(before[0]),set(settled[0]))
