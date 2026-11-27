"""Chapter-local HP transfer; terminal fixtures and real consecutive fights are separate."""
from dataclasses import replace
import unittest
from unittest.mock import Mock,patch,PropertyMock
import main
from health import Health
from player import Player,DIRECTIONS
from chapter_run import ChapterRun
from stage_progression import StageProgression
from game import GameState
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish,run_loop,key
from tests.test_chapter_three_entry import state
from tests.balance_driver import _guard_direction
from input_controller import InputController
from collections import deque


def owned(chapter=1,hp=2):
    r=ChapterRun(chapter);g=main._new_stage_game(r.current_stage,stats=r.stats,initial_hp=hp)
    return StageProgression(g,r)


def fight(f,limit=3600,*,guard=False):
    # Same deterministic walking/attack/parry policy as independent balance_driver.
    g=f.game;movement=InputController(move_interval_ticks=f.run.stats.move_interval_ticks)
    for _ in range(limit):
        if not g.playing:break
        tick=g.combat.tick;occupied=set(g.encounter.occupied_cells)
        queue=deque([(g.player.position,None)]);seen={g.player.position};direction=None
        while queue and direction is None:
            (x,y),first=queue.popleft()
            for name,(dx,dy) in DIRECTIONS.items():
                cell=x+dx,y+dy
                if cell in occupied:direction=first or name;break
                if 0<=cell[0]<10 and 0<=cell[1]<10 and cell not in seen:
                    seen.add(cell);queue.append((cell,first or name))
        if guard:
            direction=_guard_direction(g,direction,tick,f.run.stats.move_interval_ticks)
        if direction:
            movement.key_down(direction,g.player,occupied=occupied,tick=tick);movement.key_up(direction)
        if any(g.player.position in e.target_cells and 0<=e.hit_tick-tick<=7 for e in g.encounter.ledger.pending):
            a=g.parry.request(tick)
            if a:g.resolver.register_parry(a)
        attack=g.combat.request_attack(g.player)
        if attack:g.resolver.resolve_player_attack(attack)
        g.resolve_current_tick()
        if g.playing:g.combat.advance()
    return (g.stage_number,g.state.value,g.combat.tick,g.player.health.current_hp,g.player.health.max_hp)


class HPCarryoverTests(unittest.TestCase):
    def test_health_default_explicit_and_clean_damage_history(self):
        self.assertEqual(Health(3).current_hp,3)
        for hp in (1,2,3):
            h=Health(3,initial_hp=hp);self.assertEqual(h.current_hp,hp)
            self.assertIsNone(h.last_damage_tick);self.assertEqual(h.last_damage_amount,0)

    def test_invalid_initial_health_player_and_all_stage_factories(self):
        for hp in (0,-1,4,True,False,1.0,'2'):
            for factory in (lambda:Health(3,initial_hp=hp),lambda:Player(5,1,initial_hp=hp),lambda:main._new_stage_game(1,initial_hp=hp),lambda:main._new_stage_game(20,initial_hp=hp)):
                with self.assertRaises((ValueError,TypeError)):factory()
        for n in range(1,21):self.assertEqual(main._new_stage_game(n,initial_hp=1).player.health.current_hp,1)

    def test_all_approved_upgrade_examples(self):
        for hp,kind,expected in ((3,'attack',3),(2,'attack',2),(1,'move',1),(3,'hp',4),(2,'hp',3),(1,'hp',2)):
            f=owned(hp=hp);old=f.game;f.choose(clear(f),kind,main._new_stage_game)
            self.assertEqual((f.game.player.health.current_hp,f.game.player.health.max_hp),(expected,4 if kind=='hp' else 3))
            self.assertIsNot(f.game.player.health,old.player.health)
        f=owned(hp=1);f.choose(clear(f),'hp',main._new_stage_game)
        self.assertEqual((f.game.player.health.current_hp,f.game.player.health.max_hp),(2,4))
        f.choose(clear(f),'hp',main._new_stage_game)
        self.assertEqual((f.game.player.health.current_hp,f.game.player.health.max_hp),(3,5))

    def test_every_ordinary_transition_including_all_four_boss_entries(self):
        for chapter in range(1,5):
            f=owned(chapter,hp=1)
            for _ in range(4):
                old=f.game;r=f.run;f.choose(clear(f),'attack',main._new_stage_game)
                self.assertIs(f.run,r);self.assertEqual(f.game.player.health.current_hp,1)
                self.assertIsNot(old.player.health,f.game.player.health)
            self.assertEqual((f.game.stage_number,len(f.run.receipts)),(chapter*5,4));self.assertTrue(f.game.boss)

    def test_new_chapters_keep_the_full_build_and_heal(self):
        for chapter in (1,2,3):
            f=owned(chapter,hp=1)
            for kind in ('attack','hp','move','attack'):f.choose(clear(f),kind,main._new_stage_game)
            old=f.game;r=f.run;clear(f);g,_=f.enter_next_chapter(main._new_stage_game)
            self.assertEqual((g.player.health.current_hp,g.player.health.max_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(4,4,15,0))
            self.assertEqual(f.run.entry_build,r.build);self.assertTrue(r.retired)

    def test_game_over_all_chapters_and_boss_replay_all_four(self):
        for chapter in range(1,5):
            f=owned(chapter,hp=1)
            for kind in ('attack','hp','move','attack'):f.choose(clear(f),kind,main._new_stage_game)
            r=f.run;old=f.game;clear(f);g,_=f.restart(main._new_stage_game)
            self.assertIs(f.run,r);self.assertEqual((len(r.receipts),g.player.health.current_hp,g.player.health.max_hp),(4,4,4))
            self.assertIsNot(g.encounter.pulse,old.encounter.pulse)
            finish(g,'dead');g,_=f.restart(main._new_stage_game)
            self.assertTrue(r.retired);self.assertEqual((g.stage_number,g.player.health.current_hp,g.player.health.max_hp,len(f.run.receipts),f.run.stats.move_interval_ticks),((chapter-1)*5+1,3,3,0,18))

    def test_fresh_hurt_history_immunity_bonus_and_parry_do_not_transfer(self):
        f=owned();g=f.game;g.player.health.apply_damage(1,tick=0)
        g.resolver.player_invulnerable_until_tick=48;g.combat.grant_perfect_counter()
        attempt=g.parry.request(0);g.resolver.register_parry(attempt)
        f.choose(clear(f),'attack',main._new_stage_game);new=f.game
        self.assertEqual(new.player.health.current_hp,1);self.assertIsNone(new.player.health.last_damage_tick)
        self.assertEqual((new.player.health.last_damage_amount,new.resolver.player_invulnerable_until_tick,new.combat.pending_attack_bonus),(0,0,0))
        self.assertIsNone(new.parry.last_attempt)
        with self.assertRaises(ValueError):new.resolver.register_parry(attempt)

    def test_wrong_candidate_hp_or_synthetic_damage_rejected_before_prepare(self):
        for mode in ('full','too_low','damage','shared'):
            f=owned();o=clear(f);before=(state(f),f.game.player.health.current_hp);prepare=Mock()
            def broken(n,*,stats,initial_hp):
                if mode=='full':return main._new_stage_game(n,stats=stats)
                g=main._new_stage_game(n,stats=stats,initial_hp=1 if mode=='too_low' else initial_hp)
                if mode=='damage':g.player=Player(5,1,max_hp=stats.max_hp);g.player.health.apply_damage(1,tick=0);g.resolver.player=g.player
                if mode=='shared':g.player.health=f.game.player.health
                return g
            with self.assertRaises(ValueError):f.choose(o,'attack',broken,prepare)
            prepare.assert_not_called();self.assertEqual((state(f),f.game.player.health.current_hp),before)
            f.choose(o,'attack',main._new_stage_game);self.assertEqual(f.game.player.health.current_hp,2)

    def test_factory_and_input_failures_preserve_hurt_owner_and_retry(self):
        for mode in ('factory','input'):
            f=owned();o=clear(f);before=(state(f),f.game.player.health.current_hp);factory=Mock(side_effect=RuntimeError()) if mode=='factory' else main._new_stage_game
            with self.assertRaises(RuntimeError):f.choose(o,'hp',factory,Mock(side_effect=RuntimeError()))
            self.assertEqual((state(f),f.game.player.health.current_hp),before);self.assertIs(f.offer,o)
            f.choose(o,'hp',main._new_stage_game);self.assertEqual(f.game.player.health.current_hp,3)

    def test_offer_receipt_max_duplicate_and_dead_owner_guards(self):
        f=owned();o=clear(f);factory=Mock()
        for fake in (replace(o),clear(owned())):
            with self.assertRaises(ValueError):f.choose(fake,'attack',factory)
        factory.assert_not_called();f.choose(o,'move',main._new_stage_game)
        with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        o=clear(f)
        with patch.object(ChapterRun,'receipts',new_callable=PropertyMock,return_value=tuple(replace(r) for r in f.run.receipts)):
            with self.assertRaises(ValueError):f.choose(o,'hp',factory)
        f.choose(o,'move',main._new_stage_game);o=clear(f)
        with self.assertRaises(ValueError):f.choose(o,'move',factory)
        factory.assert_not_called()
        f=owned(hp=1);finish(f.game,'dead')
        with self.assertRaises(ValueError):f.choose(None,'hp',factory)

    def test_real_consecutive_three_stage_combat_carries_exact_survivor_hp(self):
        f=owned(hp=2);rows=[]
        for _ in range(3):
            row=fight(f);rows.append(row);self.assertEqual(row[1],'UPGRADE')
            hp=f.game.player.health.current_hp;f.choose(f.sync_offer(),'attack',main._new_stage_game)
            self.assertEqual(f.game.player.health.current_hp,hp)
        self.assertEqual(len(f.run.receipts),3)

    def test_main_keyboard_shows_carry_with_no_hurt_flash(self):
        factory=main._new_game
        games,snapshots,*_=run_loop([[key(49)],[],[]],initial_factory=lambda:factory(initial_hp=2))
        self.assertEqual([g.stage_number for g in games],[1,2]);self.assertEqual(games[-1].player.health.current_hp,2)
        self.assertIsNone(games[-1].player.health.last_damage_tick)

    def test_hurt_transition_matches_tick_strides_and_seven_render_rates(self):
        from simulation_clock import SimulationClock
        traces=[]
        for fps in (30,60,120,144,160,180,240):
            f=owned();clock=SimulationClock()
            for _ in range(fps*2):f.game.advance(clock.advance(1/fps))
            f.choose(clear(f),'hp',main._new_stage_game)
            traces.append((f.game.player.health.current_hp,f.game.player.health.max_hp,f.game.combat.tick,f.run.build))
        self.assertTrue(all(t==traces[0] for t in traces));self.assertEqual(traces[0][:3],(3,4,0))
        traces=[]
        for stride in (1,8):
            f=owned()
            for _ in range(120//stride):f.game.advance(stride)
            f.choose(clear(f),'attack',main._new_stage_game)
            traces.append((f.game.player.health.current_hp,f.game.combat.tick,f.run.build))
        self.assertEqual(*traces)
