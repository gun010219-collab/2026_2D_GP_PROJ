"""Apply derived stats through real combat APIs without altering main factories."""
import unittest

import main
from chapter_run import ChapterRun
from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from enemy_factory import create_stage_enemies
from game import StageGame
from input_controller import InputController
from parry import Parry
from player import Player, load_stage1_player
from stage_manager import StageCatalog
from upgrades import ChapterBuild


def session(build,stage_number=5):
    """Test-only composition of existing public constructors, not a main route."""
    definition=StageCatalog.load().get_stage(stage_number)
    stats=build.stats
    p=Player(*definition.player_spawn,max_hp=stats.max_hp)
    c,q=Combat(),Parry()
    e=EnemyEncounter(create_stage_enemies(definition),combat_session_id=c.combat_session_id,
                     stage_instance_id=c.stage_instance_id,boss=definition.boss)
    r=CombatResolver(p,c,e,parry=q,player_damage=stats.attack_damage)
    game=StageGame(p,c,e,q,r,stage_number=definition.number,chapter=definition.chapter,boss=definition.boss)
    return game,InputController(move_interval_ticks=stats.move_interval_ticks)


def melee(build,kind='king',hp=8):
    p,c,q=Player(5,1,max_hp=build.stats.max_hp),Combat(),Parry()
    source=Enemy('source',5,2,None,0,kind=kind,**({'boss_hp':hp} if kind=='king' else {}))
    e=EnemyEncounter((source,),combat_session_id=c.combat_session_id,stage_instance_id=c.stage_instance_id)
    r=CombatResolver(p,c,e,parry=q,player_damage=build.stats.attack_damage)
    r.resolve_current_tick()
    return p,c,q,e,r


class UpgradeCombatTests(unittest.TestCase):
    def test_base_and_hp_levels_create_new_full_health_and_ids(self):
        players=[Player(5,1,max_hp=ChapterBuild(hp_level=i).stats.max_hp) for i in range(4)]
        self.assertEqual([(p.health.current_hp,p.health.max_hp) for p in players],[(3,3),(4,4),(5,5),(6,6)])
        self.assertEqual(len({p.entity_instance_id for p in players}),4)
        self.assertEqual(len({id(p.health) for p in players}),4)

    def test_existing_player_and_loader_still_have_hp_three(self):
        self.assertEqual(Player(5,1).health.max_hp,3)
        self.assertEqual(load_stage1_player().health.current_hp,3)
        for bad in (True,False,0,-1,3.0,'4',None):
            with self.assertRaises((ValueError,TypeError)):
                Player(5,1,max_hp=bad)

    def test_damage_stays_reduced_in_same_session_but_new_health_is_full(self):
        old,_=session(ChapterBuild(hp_level=2))
        old.player.health.apply_damage(3,tick=0)
        self.assertEqual(old.player.health.current_hp,2)
        for _ in range(3):
            self.assertEqual(ChapterBuild(hp_level=2).stats.max_hp,5)
            self.assertEqual(old.player.health.current_hp,2)
        fresh,_=session(ChapterBuild(hp_level=2))
        self.assertEqual(fresh.player.health.current_hp,5)
        self.assertIsNone(fresh.player.health.last_damage_tick)

    def test_attack_levels_apply_real_one_two_three_damage_once(self):
        for level,damage in enumerate((1,2,3)):
            p,c,q,e,r=melee(ChapterBuild(attack_level=level))
            event=c.request_attack(p)
            result=r.resolve_player_attack(event)
            self.assertEqual((result.amount,e.enemies[0].health.current_hp),(damage,8-damage))
            for _ in range(4):
                self.assertIsNone(r.resolve_player_attack(event))
            self.assertEqual(e.enemies[0].health.current_hp,8-damage)

    def test_fatal_upgraded_space_cancels_existing_enemy_attack_and_occupancy(self):
        p,c,q,e,r=melee(ChapterBuild(attack_level=2),hp=3)
        event=e.enemies[0].current_attack
        result=r.resolve_player_attack(c.request_attack(p))
        self.assertEqual(result.amount,3)
        self.assertEqual(e.ledger.state(event),'cancelled')
        self.assertNotIn((5,2),e.occupied_cells)
        r.advance(48)
        self.assertEqual(p.health.current_hp,3)

    def test_real_melee_perfect_adds_two_to_each_attack_level_without_reflection(self):
        for level,damage in enumerate((3,4,5)):
            p,c,q,e,r=melee(ChapterBuild(attack_level=level))
            r.advance(41)
            r.resolve_player_attack(c.request_attack(p))
            before=e.enemies[0].health.current_hp
            attempt=q.request(c.tick)
            r.register_parry(attempt)
            r.advance(7)
            self.assertEqual((r.parry_result(attempt).status,c.next_attack_tick,c.pending_attack_bonus),('perfect',48,2))
            self.assertEqual(e.enemies[0].health.current_hp,before)
            self.assertEqual(e.enemies[0].stun_until_tick,108)
            attack=c.request_attack(p)
            result=r.resolve_player_attack(attack)
            self.assertEqual(result.amount,min(damage,before))
            self.assertEqual(attack.damage_bonus,2)
            self.assertEqual(c.pending_attack_bonus,0)

    def test_perfect_bonus_is_nonstacking_and_accepted_miss_spends_once(self):
        p,c,q,e,r=melee(ChapterBuild(attack_level=2))
        c.grant_perfect_counter(); c.grant_perfect_counter()
        self.assertEqual(c.pending_attack_bonus,2)
        p.move('left',e.occupied_cells)
        event=c.request_attack(p)
        self.assertEqual(event.damage_bonus,2)
        self.assertIsNone(r.resolve_player_attack(event))
        self.assertIsNone(r.resolve_player_attack(event))
        self.assertEqual((c.pending_attack_bonus,e.enemies[0].health.current_hp),(0,8))

    def test_pulse_perfect_reflects_exactly_two_independent_of_attack_upgrade(self):
        for level in range(3):
            g,_=session(ChapterBuild(attack_level=level,hp_level=3))
            g.advance(378)
            event=g.encounter.pulse.event
            self.assertEqual((event.start_tick,event.hit_tick),(265,385))
            before=g.encounter.pulse.king.health.current_hp
            attempt=g.parry.request(g.combat.tick)
            g.resolver.register_parry(attempt)
            g.advance(7)
            self.assertEqual(g.encounter.pulse.king.health.current_hp,before-2)
            self.assertEqual(g.combat.pending_attack_bonus,2)
            self.assertEqual(g.resolver.last_parry_result.status,'perfect')
            for _ in range(3):
                self.assertIsNone(g.resolver.resolve_enemy_attack(event))
            self.assertEqual(g.encounter.pulse.king.health.current_hp,before-2)

    def test_player_upgrades_never_change_general_or_boss_hp(self):
        for build in (ChapterBuild(),ChapterBuild(2,3,2)):
            g,_=session(build)
            self.assertEqual([e.health.max_hp for e in g.encounter.enemies],[8,4,2,2])

    def test_new_sessions_keep_only_stats_not_attacks_stuns_invulnerability_or_input(self):
        build=ChapterBuild(1,2,1)
        old,old_controls=session(build)
        old.advance(270)
        pulse=old.encounter.pulse.event
        attack=old.combat.request_attack(old.player)
        attempt=old.parry.request(old.combat.tick)
        old.resolver.register_parry(attempt)
        old.combat.grant_perfect_counter()
        old.resolver.player_invulnerable_until_tick=999
        old_controls.key_down('up',old.player,tick=270,occupied=old.encounter.occupied_cells)
        old.resolver.stop()
        fresh,controls=session(build)
        self.assertEqual((fresh.combat.tick,fresh.encounter.tick,fresh.combat.next_attack_tick,fresh.parry.next_parry_tick,
                          fresh.combat.pending_attack_bonus,fresh.resolver.player_invulnerable_until_tick),(0,-1,0,0,0,0))
        self.assertEqual((fresh.player.health.current_hp,fresh.resolver.player_damage,controls.move_interval_ticks),(5,2,15))
        self.assertNotEqual(old.combat.combat_session_id,fresh.combat.combat_session_id)
        self.assertNotEqual(old.combat.stage_instance_id,fresh.combat.stage_instance_id)
        self.assertTrue({e.entity_instance_id for e in old.encounter.enemies}.isdisjoint(e.entity_instance_id for e in fresh.encounter.enemies))
        self.assertEqual((fresh.encounter.pulse.state,fresh.encounter.pulse.event,fresh.encounter.pulse._remaining),('NORMAL',None,{}))
        self.assertEqual(fresh.encounter.ledger.pending,())
        self.assertIsNone(fresh.resolver.last_parry_result)
        self.assertIsNone(fresh.parry.last_attempt)
        self.assertTrue(all(e.stun_until_tick==0 for e in fresh.encounter.enemies))
        for action in (lambda:fresh.resolver.resolve_enemy_attack(pulse),lambda:fresh.resolver.resolve_player_attack(attack),
                       lambda:fresh.resolver.register_parry(attempt)):
            with self.assertRaises(ValueError):
                action()
        self.assertEqual(controls.next_move_tick,0)

    def test_four_pure_choices_can_feed_fresh_sessions_and_boss_replay(self):
        run=ChapterRun()
        for stage,kind in enumerate(('attack','hp','move','hp'),1):
            g,_=session(run.build,stage)
            self.assertEqual(g.player.health.current_hp,run.stats.max_hp)
            # Explicit model fixture: no claim that this StageGame has cleared.
            o=run.offer_after_clear(stage,g.combat.stage_instance_id)
            run.select(o,kind)
        boss,_=session(run.build)
        boss.player.health.apply_damage(1,tick=0)
        self.assertEqual(run.boss_replay_stats(),run.stats)
        replay,_=session(run.build)
        self.assertEqual((replay.player.health.current_hp,replay.resolver.player_damage),(5,2))
        fresh=run.restart_after_game_over()
        reset,_=session(fresh.build,1)
        self.assertEqual((reset.player.health.current_hp,reset.resolver.player_damage),(3,1))

    def test_main_factories_and_progress_still_use_original_unupgraded_paths(self):
        for stage in range(1,6):
            g=main._new_stage_game(stage)
            self.assertEqual((g.player.health.max_hp,g.resolver.player_damage),(3,1))
        g=main._new_stage_game(4)
        for e in g.encounter.enemies:
            e.health.apply_damage(e.health.current_hp,tick=0)
        g.update_state()
        self.assertEqual(g.next_stage_number,5)


if __name__=='__main__':
    unittest.main()
