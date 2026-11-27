"""Chapter5 entry authentication, fresh runtime and failed preparation retry."""
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
from tests.test_stage_twenty import at20


def completed_four():
    f=at20();finish(f.game,'clear');return f


def entered_five():
    f=completed_four();f.enter_next_chapter(main._new_stage_game);return f


class ChapterFiveEntryTests(unittest.TestCase):
    def test_owned_clear_carries_full_build_and_retires_after_prepare(self):
        f = completed_four()
        old_game, old_run = f.game, f.run
        def prepare(stats):
            self.assertFalse(old_run.retired)
            self.assertIs(f.game, old_game)
            self.assertEqual(stats, DerivedStats(12, 5, 15))
            return 'prepared'
        g, prepared = f.enter_next_chapter(main._new_stage_game, prepare)
        self.assertEqual(prepared, 'prepared')
        self.assertEqual((g.stage_number, g.chapter, g.boss), (21, 5, False))
        self.assertEqual((f.run.entry_attack_level, f.run.build, f.run.receipts, f.offer), (11, ChapterBuild(11,2,1), (), None))
        self.assertTrue(old_run.retired)
        self.assertNotEqual(f.run.run_id, old_run.run_id)
        for receipt in old_run.receipts:
            with self.assertRaises(ValueError):
                f.run.verify_receipt(receipt)

    def test_new_objects_health_ledgers_clocks_and_bonuses_are_isolated(self):
        f = completed_four()
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
            f = completed_four()
            g = main._new_stage_game(20, stats=f.run.stats)
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
            f = completed_four()
            receipts = f.run.receipts
            if mode == 'missing':
                receipts = receipts[:-1]
            elif mode == 'reordered':
                receipts = tuple(reversed(receipts))
            elif mode == 'copied':
                receipts = (replace(receipts[0]), *receipts[1:])
            else:
                receipts = (completed_four().run.receipts[0], *receipts[1:])
            factory = Mock()
            with patch.object(ChapterRun, 'receipts', new_callable=PropertyMock, return_value=receipts):
                with self.assertRaises(ValueError):
                    f.enter_next_chapter(factory)
            factory.assert_not_called()
            self.assertFalse(f.run.retired)

    def test_wrong_build_terminal_counter_resolver_or_scope_rejected(self):
        for mode in ('build', 'count', 'end', 'resolver', 'foreign_game', 'foreign_run', 'retired'):
            f = completed_four()
            if mode == 'build': f.run._build = ChapterBuild(5, 1, 1)
            if mode == 'count': f.game._transition_count = 2
            if mode == 'end': f.game._end_tick = 1
            if mode == 'resolver': f.game.resolver._stopped = False
            if mode == 'foreign_game': f.game = completed_four().game
            if mode == 'foreign_run': f.run = completed_four().run
            if mode == 'retired': f.run.retire()
            factory = Mock()
            with self.assertRaises(ValueError): f.enter_next_chapter(factory)
            factory.assert_not_called()

    def test_factory_and_preparation_failure_preserve_boss_then_retry(self):
        for mode in ('factory', 'input', 'board'):
            f = completed_four()
            before = state(f)
            factory = Mock(side_effect=RuntimeError(mode)) if mode == 'factory' else main._new_stage_game
            prepare = Mock(side_effect=RuntimeError(mode)) if mode != 'factory' else lambda stats: None
            with self.assertRaises(RuntimeError): f.enter_next_chapter(factory, prepare)
            self.assertEqual(state(f), before)
            f.enter_next_chapter(main._new_stage_game)
            self.assertEqual(f.game.stage_number, 21)

    def test_invalid_candidates_preserve_boss_and_run(self):
        for mode in ('hp', 'player_hp', 'id', 'position', 'delay', 'session', 'ledger', 'health', 'bonus', 'stage', 'chapter', 'boss', 'spawn', 'stage_id', 'resolver_owner'):
            f = completed_four()
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
                if mode == 'stage': g._stage_number=20
                if mode == 'chapter': g._chapter=3
                if mode == 'boss': g._boss=True
                if mode == 'spawn': g.player._col=0
                if mode == 'stage_id': g.combat._stage_instance_id=f.game.combat.stage_instance_id
                if mode == 'resolver_owner': g.resolver.player=f.game.player
                return g
            with self.assertRaises(ValueError): f.enter_next_chapter(factory)
            self.assertEqual(state(f), before)
            f.enter_next_chapter(main._new_stage_game)

    def test_chapter_five_death_restores_entry_at_stage21(self):
        for number in (21,):
            f = entered_five()
            old = f.run
            finish(f.game, 'dead')
            before = state(f)
            with self.assertRaises(RuntimeError): f.restart(main._new_stage_game, Mock(side_effect=RuntimeError('input')))
            self.assertEqual(state(f), before)
            g, _ = f.restart(main._new_stage_game)
            self.assertTrue(old.retired)
            self.assertEqual((g.stage_number, f.run.chapter, f.run.entry_attack_level), (21, 5, 11))
            self.assertEqual((g.resolver.player_damage, g.player.health.current_hp, f.run.stats.move_interval_ticks), (12, 5, 15))
            self.assertEqual(f.run.receipts, ())

    def test_boss_replay_still_keeps_chapter_four_build_and_four_receipts(self):
        f = completed_four()
        run, build, receipts = f.run, f.run.build, f.run.receipts
        g, _ = f.restart(main._new_stage_game)
        self.assertIs(f.run, run)
        self.assertEqual((f.run.build, f.run.receipts), (build, receipts))
        self.assertEqual((g.stage_number, g.encounter.pulse.king.health.current_hp), (20, 100))

    def test_entry_cannot_repeat_from_chapter_five_or_upgrade(self):
        f = entered_five()
        factory = Mock()
        for cleared in (False, True):
            if cleared: clear(f)
            with self.assertRaises(ValueError): f.enter_next_chapter(factory)
        factory.assert_not_called()

    def test_mixed_chapter_four_upgrades_inherit_hp_move_and_preserve_boss_replay(self):
        r=ChapterRun(4,entry_attack_level=7)
        f=StageProgression(main._new_stage_game(16,stats=r.stats),r)
        for kind in ('hp','move','hp','attack'):f.choose(clear(f),kind,main._new_stage_game)
        self.assertEqual((r.stats.attack_damage,r.stats.max_hp,r.stats.move_interval_ticks),(9,5,15))
        f.game.player.health.apply_damage(4,tick=0);clear(f)
        replay,_=f.restart(main._new_stage_game)
        self.assertIs(f.run,r);self.assertEqual((replay.stage_number,replay.player.health.current_hp,len(r.receipts)),(20,5,4))
        clear(f);g,_=f.enter_next_chapter(main._new_stage_game)
        self.assertEqual((f.run.entry_attack_level,g.resolver.player_damage,g.player.health.current_hp,g.player.health.max_hp,f.run.stats.move_interval_ticks,len(f.run.receipts)),(8,9,5,5,15,0))
        self.assertTrue(r.retired)
