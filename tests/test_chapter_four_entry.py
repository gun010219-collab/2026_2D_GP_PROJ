"""Chapter4 entry authentication, fresh runtime and failed preparation retry."""
from dataclasses import replace
import unittest
from unittest.mock import Mock, PropertyMock, patch
import main
from chapter_run import ChapterRun
from game import GameState
from stage_progression import StageProgression
from upgrades import ChapterBuild, DerivedStats
from tests.test_stage_transition import finish
from tests.test_upgrade_flow import clear
from tests.test_chapter_three_entry import state
from tests.test_stage_fifteen import at15


def completed_three():
    f=at15();finish(f.game,'clear');return f


def entered_four():
    f=completed_three();f.enter_next_chapter(main._new_stage_game);return f


class ChapterFourEntryTests(unittest.TestCase):
    def test_owned_clear_carries_attack_only_and_retires_after_prepare(self):
        f = completed_three()
        old_game, old_run = f.game, f.run
        def prepare(stats):
            self.assertFalse(old_run.retired)
            self.assertIs(f.game, old_game)
            self.assertEqual(stats, DerivedStats(8, 3, 18))
            return 'prepared'
        g, prepared = f.enter_next_chapter(main._new_stage_game, prepare)
        self.assertEqual(prepared, 'prepared')
        self.assertEqual((g.stage_number, g.chapter, g.boss), (16, 4, False))
        self.assertEqual((f.run.entry_attack_level, f.run.build, f.run.receipts, f.offer), (7, ChapterBuild(7), (), None))
        self.assertTrue(old_run.retired)
        self.assertNotEqual(f.run.run_id, old_run.run_id)
        for receipt in old_run.receipts:
            with self.assertRaises(ValueError):
                f.run.verify_receipt(receipt)

    def test_new_objects_health_ledgers_clocks_and_bonuses_are_isolated(self):
        f = completed_three()
        old = f.game
        old.combat.grant_perfect_counter()
        old.resolver.player_invulnerable_until_tick = 48
        g, _ = f.enter_next_chapter(main._new_stage_game)
        for name in ('player', 'combat', 'parry', 'encounter', 'resolver'):
            self.assertIsNot(getattr(g, name), getattr(old, name))
        self.assertIsNot(g.encounter.ledger, old.encounter.ledger)
        self.assertNotEqual(g.combat.stage_instance_id, old.combat.stage_instance_id)
        self.assertNotEqual(g.combat.combat_session_id, old.combat.combat_session_id)
        self.assertEqual((g.combat.tick, g.encounter.tick, g.combat.pending_attack_bonus,
                          g.resolver.player_invulnerable_until_tick), (0, -1, 0, 0))
        self.assertIsNone(g.parry.last_attempt)
        self.assertFalse(g.encounter.ledger.pending)
        old_health = {id(old.player.health), *(id(e.health) for e in old.encounter.enemies)}
        self.assertTrue(old_health.isdisjoint({id(g.player.health), *(id(e.health) for e in g.encounter.enemies)}))

    def test_king_only_or_player_death_never_authorizes_entry(self):
        for dead in (False, True):
            f = completed_three()
            g = main._new_stage_game(15, stats=f.run.stats)
            f = StageProgression(g, f.run)
            k = g.encounter.pulse.king
            k.health.apply_damage(k.health.max_hp, tick=0)
            g.encounter.deactivate(k.entity_instance_id, tick=0)
            if dead:
                g.player.health.apply_damage(g.player.health.current_hp, tick=0)
            g.update_state()
            self.assertEqual(g.state, GameState.GAME_OVER if dead else GameState.PLAYING)
            factory = Mock()
            with self.assertRaises(ValueError):
                f.enter_next_chapter(factory)
            factory.assert_not_called()

    def test_missing_reordered_copied_or_foreign_receipts_rejected_before_factory(self):
        for mode in ('missing', 'reordered', 'copied', 'foreign'):
            f = completed_three()
            receipts = f.run.receipts
            if mode == 'missing':
                receipts = receipts[:-1]
            elif mode == 'reordered':
                receipts = tuple(reversed(receipts))
            elif mode == 'copied':
                receipts = (replace(receipts[0]), *receipts[1:])
            else:
                receipts = (completed_three().run.receipts[0], *receipts[1:])
            factory = Mock()
            with patch.object(ChapterRun, 'receipts', new_callable=PropertyMock, return_value=receipts):
                with self.assertRaises(ValueError):
                    f.enter_next_chapter(factory)
            factory.assert_not_called()
            self.assertFalse(f.run.retired)

    def test_wrong_build_terminal_counter_resolver_or_scope_rejected(self):
        for mode in ('build', 'count', 'end', 'resolver', 'foreign_game', 'foreign_run', 'retired'):
            f = completed_three()
            if mode == 'build': f.run._build = ChapterBuild(5, 1, 1)
            if mode == 'count': f.game._transition_count = 2
            if mode == 'end': f.game._end_tick = 1
            if mode == 'resolver': f.game.resolver._stopped = False
            if mode == 'foreign_game': f.game = completed_three().game
            if mode == 'foreign_run': f.run = completed_three().run
            if mode == 'retired': f.run.retire()
            factory = Mock()
            with self.assertRaises(ValueError): f.enter_next_chapter(factory)
            factory.assert_not_called()

    def test_factory_and_preparation_failure_preserve_boss_then_retry(self):
        for mode in ('factory', 'input', 'board'):
            f = completed_three()
            before = state(f)
            factory = Mock(side_effect=RuntimeError(mode)) if mode == 'factory' else main._new_stage_game
            prepare = Mock(side_effect=RuntimeError(mode)) if mode != 'factory' else lambda stats: None
            with self.assertRaises(RuntimeError): f.enter_next_chapter(factory, prepare)
            self.assertEqual(state(f), before)
            f.enter_next_chapter(main._new_stage_game)
            self.assertEqual(f.game.stage_number, 16)

    def test_invalid_candidates_preserve_boss_and_run(self):
        for mode in ('hp', 'player_hp', 'id', 'position', 'delay', 'session', 'ledger', 'health', 'bonus', 'stage', 'chapter', 'boss', 'spawn', 'stage_id', 'resolver_owner'):
            f = completed_three()
            before = state(f)
            def factory(n, *, stats):
                g = main._new_stage_game(n, stats=stats)
                e = g.encounter.enemies[0]
                if mode == 'hp': e.health.apply_damage(1, tick=0)
                if mode == 'player_hp': g.player.health.apply_damage(1, tick=0)
                if mode == 'id': e.data_id = 'tampered'
                if mode == 'position': e.col = 0
                if mode == 'delay': e.initial_delay = .9
                if mode == 'session': g.combat._combat_session_id = f.game.combat.combat_session_id
                if mode == 'ledger': g.encounter.ledger = f.game.encounter.ledger
                if mode == 'health': e.health = f.game.encounter.enemies[0].health
                if mode == 'bonus': g.combat.grant_perfect_counter()
                if mode == 'stage': g._stage_number=15
                if mode == 'chapter': g._chapter=3
                if mode == 'boss': g._boss=True
                if mode == 'spawn': g.player._col=0
                if mode == 'stage_id': g.combat._stage_instance_id=f.game.combat.stage_instance_id
                if mode == 'resolver_owner': g.resolver.player=f.game.player
                return g
            with self.assertRaises(ValueError): f.enter_next_chapter(factory)
            self.assertEqual(state(f), before)
            f.enter_next_chapter(main._new_stage_game)

    def test_chapter_four_death_restores_entry_at_stage16(self):
        for number in (16,):
            f = entered_four()
            old = f.run
            finish(f.game, 'dead')
            before = state(f)
            with self.assertRaises(RuntimeError): f.restart(main._new_stage_game, Mock(side_effect=RuntimeError('input')))
            self.assertEqual(state(f), before)
            g, _ = f.restart(main._new_stage_game)
            self.assertTrue(old.retired)
            self.assertEqual((g.stage_number, f.run.chapter, f.run.entry_attack_level), (16, 4, 7))
            self.assertEqual((g.resolver.player_damage, g.player.health.current_hp, f.run.stats.move_interval_ticks), (8, 3, 18))
            self.assertEqual(f.run.receipts, ())

    def test_boss_replay_still_keeps_chapter_three_build_and_four_receipts(self):
        f = completed_three()
        run, build, receipts = f.run, f.run.build, f.run.receipts
        g, _ = f.restart(main._new_stage_game)
        self.assertIs(f.run, run)
        self.assertEqual((f.run.build, f.run.receipts), (build, receipts))
        self.assertEqual((g.stage_number, g.encounter.pulse.king.health.current_hp), (15, 60))

    def test_entry_cannot_repeat_from_chapter_four_or_upgrade(self):
        f = entered_four()
        factory = Mock()
        for cleared in (False, True):
            if cleared: clear(f)
            with self.assertRaises(ValueError): f.enter_next_chapter(factory)
        factory.assert_not_called()
