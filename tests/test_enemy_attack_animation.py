import math
import pickle
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from actor_animation import ActorAnimation, Pose, State, attack_direction
from actor_mesh import ENEMY_ACTION, INDICES, REST, deformation, draw_actor
from chapter_art_renderer import CHAPTER_PROFILES
from combat_vfx import CombatVFX
from config import cell_center
from game_audio import AudioManager, AudioSettings
from main import _new_stage_game
from presentation_events import PresentationEvents
from render_motion import RenderMotion
from tests.test_game_audio import FakeMixer


class EnemyAttackAnimationTests(unittest.TestCase):
    def setup_stage(self, number):
        game = _new_stage_game(number)
        game.encounter.ledger.presentation = PresentationEvents()
        return game, ActorAnimation(improved=True,enemy_attacks=True), RenderMotion(improved=True)

    def step(self, game, animation, motion, *, parry=False):
        if parry:
            game.combat.advance(1)
            result = game.resolver.register_parry(game.parry.request(game.combat.tick))
            self.assertEqual(result.adjudication_grade,'perfect')
            game.resolve_current_tick()
        else:
            game.advance()
        motion.update((game.player,*game.encounter.enemies),1/60,session=game.combat.combat_session_id)
        batch = game.encounter.ledger.presentation.drain()
        before = pickle.dumps(game)
        animation.update(game,1/60,batch,motion=motion)
        self.assertEqual(pickle.dumps(game),before)
        return batch

    def test_distinct_piece_phases_and_king_pulse_spread(self):
        charges,releases = set(),set()
        for kind in ENEMY_ACTION:
            piece = 'king' if kind=='king_pulse' else kind
            attack = 'king_pulse' if kind=='king_pulse' else 'basic'
            args = dict(attack_kind=attack,direction=1. if piece not in ('queen','bishop') and attack=='basic' else 0.)
            make = lambda state,phase,action: deformation(piece,3,Pose(state,phase,attack_motion=action,**args))
            charges.add(make(State.WINDUP,1.,'anticipation'))
            release = make(State.ATTACK,0.,'release')
            releases.add(release)
            self.assertNotEqual(release,make(State.ATTACK,.36,'release'))
            self.assertEqual(make(State.ATTACK,1.,'release'),REST)
            if attack=='king_pulse':
                self.assertEqual(release.lean,0.)
                self.assertGreater(release.spread,0.)
        self.assertEqual(len(charges),7)
        self.assertEqual(len(releases),7)

    def test_direction_uses_receipt_origin_and_is_radial_for_spells(self):
        from enemy_attack import EnemyAttackLedger
        ledger = EnemyAttackLedger()
        strike = ledger.create('rook',0,10,((3,3),(5,3),(9,3)))
        self.assertEqual(attack_direction('rook',(2,3),strike),(1.,0.))
        self.assertEqual(attack_direction('rook',(4,3),strike),(-1.,0.))
        lunge = ledger.create('knight',0,10,((3,5),))
        sx,sy = attack_direction('knight',(2,3),lunge)
        self.assertAlmostEqual(math.hypot(sx,sy),1.)
        self.assertGreater(sy,sx)
        self.assertEqual(attack_direction('bishop',(0,0),strike),(0.,0.))
        self.assertEqual(attack_direction('queen',(0,0),strike),(0.,0.))
        for depth in (-1.,1.):
            pawn = deformation('pawn',1,Pose(State.ATTACK,0.,direction=0.,attack_motion='release',
                                            depth_direction=depth))
            self.assertEqual(pawn.lean,0.)
            self.assertGreater(pawn.gear_lift*depth,5.)

    def test_knight_and_rook_contact_share_vfx_and_audio_ground_pose(self):
        for number,kind,arrival_name in ((3,'knight','knight_land'),(6,'rook','rook_impact')):
            game,animation,motion = self.setup_stage(number)
            actor = next(e for e in game.encounter.enemies if e.kind==kind)
            vfx = CombatVFX(layered=True)
            mixer = FakeMixer()
            audio = AudioManager(mixer,AudioSettings())
            seen = set()
            lift = 0.
            for _ in range(270):
                batch = self.step(game,animation,motion)
                vfx.update(game,1/60,batch,motion=motion)
                mixer.live.clear()
                audio.update(game,1/60,batch,motion=motion)
                pose = animation.pose(game,actor,motion)
                if pose.attack_motion:
                    seen.add(pose.attack_motion)
                if pose.attack_motion=='travel':
                    lift = max(lift,motion.ground_pose(actor)[1])
                if pose.attack_motion=='arrival':
                    self.assertIn(arrival_name,mixer.cues)
                    self.assertTrue(any(fx.name==arrival_name and fx.landed is not None for fx in vfx.effects))
                    ground,landing_lift = motion.ground_pose(actor)
                    self.assertEqual(ground,cell_center(*actor.position))
                    self.assertAlmostEqual(landing_lift,0.)
                    self.assertLess(pose.phase,.10)
                    break
            self.assertTrue({'anticipation','travel','arrival'} <= seen)
            self.assertAlmostEqual(lift,18. if kind=='knight' else 0.)

    def test_spells_keep_real_target_counts_and_independent_release(self):
        for number,kind,targets in ((12,'bishop',50),(24,'queen',None)):
            g,a,m = self.setup_stage(number)
            actors = {e.entity_instance_id:e for e in g.encounter.enemies if e.kind==kind}
            positions = {key:e.position for key,e in actors.items()}
            events = []
            for _ in range(320):
                batch = self.step(g,a,m)
                for event in batch:
                    if event.kind != 'attack_start' or event.subject not in actors:
                        continue
                    actor = actors[event.subject]
                    pose = a.pose(g,actor,m)
                    self.assertEqual((pose.attack_motion,pose.phase,pose.direction),('release',0.,0.))
                    self.assertEqual(event.origin,actor.position)
                    self.assertEqual(len(event.payload.target_cells),targets or len(set(event.payload.target_cells)))
                    if kind=='bishop':
                        self.assertEqual(actor.position,positions[event.subject])
                    else:
                        self.assertNotIn(event.origin,event.payload.target_cells)
                    events.append((event.tick,event.subject))
                if len(events)==2:
                    break
            self.assertEqual(len({key for _,key in events}),2)
            self.assertLess(events[0][0],events[1][0])
            if kind=='queen':
                phases = [a.pose(g,e,m).phase for e in actors.values()]
                self.assertNotEqual(*phases)

    def test_cancelled_windup_and_perfect_pulse_stun_interrupt(self):
        g,a,m = self.setup_stage(24)
        while True:
            self.step(g,a,m)
            attack = next((e for e in g.encounter.ledger.telegraphs if e.attack_kind=='queen_diagonal'),None)
            if attack:
                break
        queen = next(e for e in g.encounter.enemies if e.entity_instance_id==attack.source_entity_instance_id)
        self.assertEqual(a.pose(g,queen,m).state,State.WINDUP)
        g.encounter.ledger.cancel(attack)
        a.update(g,0,(),motion=m)
        self.assertNotIn(a.pose(g,queen,m).state,(State.ATTACK,State.WINDUP))
        g,a,m = self.setup_stage(25)
        while g.combat.tick < 385:
            self.step(g,a,m,parry=g.combat.tick==378)
        king = next(e for e in g.encounter.enemies if e.kind=='king')
        self.assertEqual(g.resolver.last_parry_result.status,'perfect')
        self.assertEqual(a.pose(g,king,m).state,State.STUN)
        self.assertEqual(king.health.max_hp-king.health.current_hp,2)

    def test_release_and_followthrough_use_same_visual_time_at_60_144_180(self):
        outcomes = []
        for hz in (60,144,180):
            g,a,m = self.setup_stage(12)
            bishop = next(e for e in g.encounter.enemies if e.kind=='bishop')
            while g.combat.tick < 156:
                self.step(g,a,m)
            start = a.pose(g,bishop,m)
            a.update(g,1.,(),motion=m,paused=True)
            self.assertEqual(a.pose(g,bishop,m),start)
            for _ in range(hz//6):
                a.update(g,1/hz,(),motion=m)
            actual = a.pose(g,bishop,m)
            outcomes.append((actual.state,round(actual.phase,8),actual.attack_motion))
        self.assertEqual(outcomes,[outcomes[0]]*3)

    def test_mesh_keeps_foot_band_and_triangles_valid_in_all_chapters(self):
        def vertices(renderer,texture,verts,count,indices,n):
            collected[:] = [(verts[i].position.x,verts[i].position.y,verts[i].tex_coord.y) for i in range(count)]
            return 0
        collected = []
        with patch('sdl2.SDL_RenderGeometry',side_effect=vertices):
            for chapter,profile in CHAPTER_PROFILES.items():
                for kind in set(profile.pieces)-{'player'}:
                    layout = profile.layout(kind,4,4)
                    draw = lambda pose: draw_actor(SimpleNamespace(renderer=None),None,kind,chapter,layout,pose)
                    draw(Pose(State.IDLE,0))
                    old = [(x,y) for x,y,v in collected if 899-y<layout['foot'][1]]
                    for action,phase in (('release',0),('anticipation',1),('release',.35)):
                        draw(Pose(State.ATTACK,phase,attack_motion=action))
                        verts = collected[:]
                        for i,j,k in zip(INDICES[::3],INDICES[1::3],INDICES[2::3]):
                            a,b,c = verts[i],verts[j],verts[k]
                            self.assertGreater((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]),0)
                        feet = [(x,y) for x,y,v in verts if 899-y<layout['foot'][1]]
                        self.assertEqual(feet,old)
