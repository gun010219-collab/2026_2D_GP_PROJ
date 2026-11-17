"""D0 development entry uses real combat; no forced clears or prior receipts."""
import contextlib
import io
import os
import pickle
import runpy
import unittest
from unittest.mock import Mock, patch

import main
from game import GameState
from stage10_art_renderer import LiveArenaArtPath
from stage_manager import StageCatalog
from tests.test_hp_carryover import fight
from tools.stage11_play import ROOT, session


class Stage11PlayTests(unittest.TestCase):
    def test_original_roster_and_fresh_owned_entry(self):
        g, flow = session()
        self.assertIs(flow.game, g)
        self.assertEqual((g.stage_number, g.chapter, g.boss), (11, 3, False))
        self.assertEqual((flow.run.entry_attack_level, g.resolver.player_damage,
                          g.player.health.current_hp, g.player.health.max_hp,
                          flow.run.stats.move_interval_ticks), (3, 4, 3, 3, 18))
        self.assertEqual((flow.run.receipts, flow.offer), ((), None))
        self.assertEqual((g.player.position, g.player.facing), ((5, 1), 'up'))
        self.assertEqual((g.state, g.combat.tick, g.encounter.tick), (GameState.PLAYING, 0, -1))
        self.assertFalse(g.resolver.stopped)
        self.assertIsNone(g.encounter.pulse)
        definition = StageCatalog.load().get_stage(11)
        self.assertEqual([(e.data_id, e.kind, e.position) for e in g.encounter.enemies],
                         [(e.data_id, e.kind, e.position) for e in definition.enemies])
        self.assertEqual([e.health.current_hp for e in g.encounter.enemies], [16, 16, 13, 13, 9])
        self.assertEqual([e.initial_delay_ticks for e in g.encounter.enemies], [48, 62, 75, 88, 101])
        self.assertTrue(all(e.active and e.state == 'initial_wait' for e in g.encounter.enemies))
        ledger = g.encounter.ledger
        self.assertFalse(ledger.pending)
        self.assertEqual((ledger.stage_instance_id, ledger.combat_session_id),
                         (g.combat.stage_instance_id, g.combat.combat_session_id))
        other, other_flow = session()
        self.assertNotEqual(flow.run.run_id, other_flow.run.run_id)
        self.assertNotEqual(g.combat.combat_session_id, other.combat.combat_session_id)
        self.assertNotEqual(g.combat.stage_instance_id, other.combat.stage_instance_id)
        self.assertIsNot(g.encounter.ledger, other.encounter.ledger)
        for a, b in zip((g.player, *g.encounter.enemies), (other.player, *other.encounter.enemies)):
            self.assertIsNot(a.health, b.health)
            self.assertNotEqual(a.entity_instance_id, b.entity_instance_id)

    def test_real_fight_upgrade_hp_transfer_and_fresh_stage12(self):
        g, flow = session()
        owner = flow.run
        result = fight(flow)
        self.assertEqual(result, (11, 'UPGRADE', 669, 2, 3))
        self.assertTrue(all(not e.alive for e in g.encounter.enemies))
        self.assertFalse(g.encounter.ledger.pending)
        offer = flow.sync_offer()
        next_game, _ = flow.choose(offer, 'hp', main._new_stage_game)
        self.assertIs(flow.run, owner)
        self.assertEqual((next_game.stage_number, next_game.chapter, next_game.combat.tick), (12, 3, 0))
        self.assertEqual((next_game.player.health.current_hp, next_game.player.health.max_hp), (3, 4))
        self.assertEqual(len(owner.receipts), 1)
        self.assertIs(owner.verify_receipt(owner.receipts[0]), owner.receipts[0])
        self.assertNotEqual(next_game.combat.combat_session_id, g.combat.combat_session_id)
        self.assertIsNot(next_game.encounter.ledger, g.encounter.ledger)
        with self.assertRaises(ValueError):
            flow.choose(offer, 'hp', main._new_stage_game)

    def test_real_no_input_death_and_chapter_restart(self):
        g, flow = session()
        old_run = flow.run
        g.advance(3600)
        self.assertEqual((g.state, g.end_tick), (GameState.GAME_OVER, 435))
        fresh, _ = flow.restart(main._new_stage_game)
        self.assertTrue(old_run.retired)
        self.assertIsNot(flow.run, old_run)
        self.assertEqual((fresh.stage_number, fresh.resolver.player_damage,
                          fresh.player.health.current_hp, flow.run.receipts), (11, 4, 3, ()))
        self.assertNotEqual(fresh.combat.combat_session_id, g.combat.combat_session_id)
        self.assertFalse(fresh.encounter.ledger.pending)

    def test_all_existing_opt_ins_and_future_flag_leave_stage11_legacy(self):
        g, _ = session()
        canvas = Mock()
        before = pickle.dumps(g)
        env = {f'CHECKMATE_STAGE{n}_ART': '1' for n in range(5, 12)}
        with patch.dict(os.environ, env):
            path = LiveArenaArtPath(canvas)
            try:
                for _ in range(3):
                    self.assertFalse(path.draw(g, {}))
            finally:
                path.close()
        canvas.load_image.assert_not_called()
        self.assertEqual(pickle.dumps(g), before)

    def test_script_entry_delegates_to_real_main_without_starting_a_window(self):
        output = io.StringIO()
        with patch.object(main, 'run_session') as runner, contextlib.redirect_stdout(output):
            runpy.run_path(str(ROOT / 'tools/stage11_play.py'), run_name='__main__')
        runner.assert_called_once()
        g, flow = runner.call_args.args
        self.assertEqual(g.stage_number, 11)
        self.assertIs(flow.game, g)
        self.assertEqual(flow.run.receipts, ())
        self.assertIn('No Chapter1/2 clear history', output.getvalue())
        self.assertIn('CHECKMATE_STAGE11_ART=1; otherwise original renderer', output.getvalue())
