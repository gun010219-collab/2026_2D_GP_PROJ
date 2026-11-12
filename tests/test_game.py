"""Stage 1 outcome/session tests with real pure combat and integer ticks."""
import unittest

import main
from combat import Combat
from combat_resolution import CombatResolver
from enemy import Enemy, load_stage1_enemies
from enemy_behaviors import PawnEncounter
from game import GameState, StageOneGame
from parry import Parry
from player import Player, load_stage1_player


def fixture(enemies=None, player=None):
    player = player if player is not None else Player(5, 1)
    combat, parry = Combat(), Parry()
    enemies = enemies if enemies is not None else load_stage1_enemies()
    encounter = PawnEncounter(enemies, combat_session_id=combat.combat_session_id,
                              stage_instance_id=combat.stage_instance_id)
    resolver = CombatResolver(player, combat, encounter, parry=parry)
    return StageOneGame(player, combat, encounter, parry, resolver)


def kill_enemies(game):
    for enemy in game.encounter.enemies:
        enemy.health.apply_damage(enemy.health.max_hp, tick=game.combat.tick)
        game.encounter.deactivate(enemy.entity_instance_id)


class GameStateTests(unittest.TestCase):
    def test_normal_stage_one_stays_playing_and_uses_original_data(self):
        game = main._new_game()
        self.assertEqual(game.state, GameState.PLAYING)
        self.assertEqual((game.player.health.current_hp, game.player.position), (3, (5, 1)))
        self.assertEqual([(e.data_id, e.position, e.health.current_hp) for e in game.encounter.enemies],
                         [('s1_pawn_1', (1, 6), 3), ('s1_pawn_2', (8, 6), 3)])
        self.assertFalse(game.update_state())
        self.assertEqual((game.transition_count, game.end_tick), (0, None))

    def test_player_zero_hp_latches_game_over_once(self):
        game = fixture()
        game.player.health.apply_damage(9, tick=0)
        self.assertTrue(game.update_state())
        self.assertEqual((game.state, game.end_tick, game.transition_count), (GameState.GAME_OVER, 0, 1))
        for _ in range(20):
            self.assertFalse(game.update_state())
        self.assertEqual(game.transition_count, 1)

    def test_both_dead_pawns_clear_but_one_dead_pawn_does_not(self):
        game = fixture()
        first, second = game.encounter.enemies
        first.health.apply_damage(3, tick=0)
        game.encounter.deactivate(first.entity_instance_id)
        self.assertFalse(game.update_state())
        self.assertTrue(game.playing)
        second.health.apply_damage(3, tick=0)
        self.assertTrue(game.update_state())
        self.assertEqual(game.state, GameState.UPGRADE)
        self.assertFalse(game.update_state())
        self.assertEqual(game.transition_count, 1)

    def test_inactive_but_alive_pawn_is_not_falsely_counted_as_a_kill(self):
        game = fixture()
        for enemy in game.encounter.enemies:
            game.encounter.deactivate(enemy.entity_instance_id)
        self.assertFalse(game.update_state())
        self.assertEqual(game.state, GameState.PLAYING)

    def test_death_has_priority_when_both_conditions_are_true(self):
        game = fixture()
        kill_enemies(game)
        game.player.health.apply_damage(3, tick=0)
        game.update_state()
        self.assertEqual(game.state, GameState.GAME_OVER)
        self.assertEqual(game.transition_count, 1)

    def test_actual_fatal_hit_stops_at_exact_tick_during_bulk_advance(self):
        game = fixture((Enemy('source', 4, 2, (0, -1), 0),
                        Enemy('later', 8, 6, (0, -1), 1)))
        game.player.health.apply_damage(2, tick=0)
        game.advance(100)
        self.assertEqual((game.state, game.combat.tick, game.encounter.tick), (GameState.GAME_OVER, 39, 39))
        self.assertEqual(game.player.health.current_hp, 0)
        self.assertEqual(game.encounter.enemies[1].position, (8, 6))
        game.advance(1000)
        self.assertEqual((game.combat.tick, game.encounter.tick), (39, 39))

    def test_clear_freezes_ai_clock_and_all_resolver_entry_points(self):
        game = fixture()
        attack = game.combat.request_attack(game.player)
        attempt = game.parry.request(game.combat.tick)
        kill_enemies(game)
        game.update_state()
        before = (game.combat.tick, game.encounter.tick, game.player.health.current_hp,
                  game.combat.pending_attack_bonus)
        for _ in range(20):
            self.assertEqual(game.advance(8), ())
            self.assertEqual(game.resolver.advance(8), ())
            self.assertIsNone(game.resolver.resolve_player_attack(attack))
            self.assertIsNone(game.resolver.register_parry(attempt))
        self.assertEqual((game.combat.tick, game.encounter.tick, game.player.health.current_hp,
                          game.combat.pending_attack_bonus), before)
        self.assertTrue(game.resolver.stopped)

    def test_game_over_cancels_unresolved_attacks_and_link_without_overwriting_past_results(self):
        game = fixture((Enemy('source', 4, 2, (0, -1), 0),))
        game.advance(32)
        event = game.encounter.ledger.telegraphs[0]
        attempt = game.parry.request(game.combat.tick)
        game.resolver.register_parry(attempt)
        game.player.health.apply_damage(3, tick=32)
        game.update_state()
        self.assertEqual(game.encounter.ledger.state(event), 'cancelled')
        self.assertEqual(game.encounter.ledger.telegraphs, ())
        self.assertIsNone(game.encounter.enemies[0].current_attack)
        self.assertEqual(game.resolver.parry_result(attempt).status, 'failed')
        self.assertIsNone(game.resolver.resolve_enemy_attack(event))
        self.assertEqual(game.combat.pending_attack_bonus, 0)
        self.assertFalse(game.resolver.stop())

    def test_stop_preserves_already_resolved_perfect_history(self):
        game = fixture((Enemy('source', 4, 2, (0, -1), 0),))
        game.advance(32)
        event = game.encounter.ledger.telegraphs[0]
        attempt = game.parry.request(32)
        game.resolver.register_parry(attempt)
        game.advance(7)
        result = game.resolver.last_parry_result
        kill_enemies(game)
        game.update_state()
        self.assertEqual(game.encounter.ledger.outcome(event), 'parried_perfect')
        self.assertIs(game.resolver.last_parry_result, result)
        self.assertFalse(game.encounter.ledger.consume(event, game.player.entity_instance_id))

    def test_last_pawn_death_before_due_cancels_its_same_tick_attack(self):
        source = Enemy('last', 4, 2, (0, -1), 0)
        source.health.apply_damage(1, tick=0)
        game = fixture((source,))
        game.advance(38)
        event = game.encounter.ledger.telegraphs[0]
        game.combat.advance()
        game.player.move('left')
        game.player.move('up', occupied=game.encounter.occupied_cells)
        game.resolver.resolve_player_attack(game.combat.request_attack(game.player))
        game.resolve_current_tick()
        self.assertEqual((game.state, game.end_tick, game.player.health.current_hp),
                         (GameState.UPGRADE, 39, 3))
        self.assertEqual(game.encounter.ledger.state(event), 'cancelled')
        self.assertIsNone(game.resolver.resolve_enemy_attack(event))

    def test_finished_outcome_does_not_flip_after_later_mutation(self):
        game = fixture()
        kill_enemies(game)
        game.update_state()
        game.player.health.apply_damage(3, tick=0)
        self.assertFalse(game.update_state())
        self.assertEqual(game.state, GameState.UPGRADE)
        self.assertEqual(game.transition_count, 1)

    def test_invalid_step_counts_are_rejected_without_advancing(self):
        game = fixture()
        for value in (True, .5, '1', None):
            with self.subTest(value=value), self.assertRaises(TypeError):
                game.advance(value)
        with self.assertRaises(ValueError):
            game.advance(-1)
        self.assertEqual((game.combat.tick, game.encounter.tick), (0, -1))


class FreshSessionTests(unittest.TestCase):
    def test_fresh_factory_resets_entities_hp_positions_directions_and_all_timers(self):
        old = main._new_game()
        old.player.move('right')
        old.player.health.apply_damage(1, tick=0)
        old.combat.request_attack(old.player)
        old.resolver.register_parry(old.parry.request(0))
        old.resolver.player_invulnerable_until_tick = 48
        old.advance(20)
        old.combat.grant_perfect_counter()
        old.encounter.stun(old.encounter.enemies[0].entity_instance_id, old.combat.tick)
        old.player.health.apply_damage(2, tick=20)
        old.update_state()
        new = main._new_game()
        self.assertEqual((new.player.position, new.player.facing, new.player.health.current_hp), ((5, 1), 'up', 3))
        self.assertNotEqual(new.player.entity_instance_id, old.player.entity_instance_id)
        self.assertEqual([e.position for e in new.encounter.enemies], [(1, 6), (8, 6)])
        for a, b in zip(old.encounter.enemies, new.encounter.enemies):
            self.assertNotEqual(a.entity_instance_id, b.entity_instance_id)
            self.assertEqual((b.health.current_hp, b.state, b.stun_until_tick), (3, 'initial_wait', 0))
            self.assertIsNone(b.current_attack)
            self.assertIsNone(b.health.last_damage_tick)
        self.assertEqual((new.combat.tick, new.combat.next_attack_tick, new.parry.next_parry_tick,
                          new.combat.pending_attack_bonus, new.resolver.player_invulnerable_until_tick),
                         (0, 0, 0, 0, 0))
        self.assertIsNone(new.combat.active_attack)
        self.assertIsNone(new.parry.last_attempt)
        self.assertIsNone(new.resolver.last_parry_result)
        self.assertIsNone(new.player.health.last_damage_tick)
        self.assertEqual((new.state, new.transition_count, new.end_tick), (GameState.PLAYING, 0, None))
        self.assertEqual(new.encounter.ledger.telegraphs, ())
        self.assertFalse(new.resolver.stopped)

    def test_old_player_and_parry_events_are_rejected_even_when_numeric_ids_repeat(self):
        old = main._new_game()
        attack = old.combat.request_attack(old.player)
        attempt = old.parry.request(0)
        old.resolver.register_parry(attempt)
        kill_enemies(old)
        old.update_state()
        new = main._new_game()
        fresh_attack = new.combat.request_attack(new.player)
        fresh_attempt = new.parry.request(0)
        self.assertEqual((attack.attack_id, fresh_attack.attack_id, attempt.parry_id, fresh_attempt.parry_id), (1, 1, 1, 1))
        self.assertNotEqual(attack.key, fresh_attack.key)
        self.assertNotEqual(attempt.key, fresh_attempt.key)
        with self.assertRaises(ValueError):
            new.resolver.resolve_player_attack(attack)
        with self.assertRaises(ValueError):
            new.resolver.register_parry(attempt)
        self.assertEqual([e.health.current_hp for e in new.encounter.enemies], [3, 3])
        self.assertEqual(new.combat.attack_state(fresh_attack), 'pending')

    def test_old_enemy_event_cannot_damage_fresh_session(self):
        old = fixture((Enemy('source', 4, 2, (0, -1), 0),))
        old.resolve_current_tick()
        event = old.encounter.ledger.telegraphs[0]
        old.player.health.apply_damage(3, tick=0)
        old.update_state()
        new = main._new_game()
        with self.assertRaises(ValueError):
            new.resolver.resolve_enemy_attack(event)
        self.assertIsNone(old.resolver.resolve_enemy_attack(event))
        self.assertEqual(new.player.health.current_hp, 3)
        self.assertEqual(new.encounter.ledger.state(event), 'unknown')

    def test_repeated_sessions_have_fresh_scopes_without_mutating_old_ledgers(self):
        scopes, players = set(), set()
        for _ in range(20):
            game = main._new_game()
            scopes.add((game.combat.combat_session_id, game.combat.stage_instance_id))
            players.add(game.player.entity_instance_id)
            kill_enemies(game)
            game.update_state()
            self.assertTrue(game.resolver.stopped)
        self.assertEqual((len(scopes), len(players)), (20, 20))
