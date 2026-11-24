import pickle
import unittest

import main
from presentation_events import PresentationEvents
from tests.test_combat_resolution import pawn, setup
from tests.test_king_pulse import parry, pulse_battle
from tools.stage11_play import session


class PresentationEventTests(unittest.TestCase):
    def test_player_swing_and_damage_receipt_are_distinct_and_single_use(self):
        for col, expected in ((6, ['attack_start']), (5, ['attack_start', 'hit', 'hurt'])):
            player, combat, encounter, resolver = setup((pawn(col=col),))
            feed = encounter.ledger.presentation = PresentationEvents()
            attack = combat.request_attack(player)
            self.assertEqual(feed.drain(), ())
            result = resolver.resolve_player_attack(attack)
            batch = feed.drain()
            self.assertEqual([event.kind for event in batch], expected)
            self.assertTrue(all(event.cause_key == attack.key for event in batch))
            if result:
                self.assertIs(batch[-1].payload, result)
                self.assertEqual(result.hp_before - result.hp_after, result.amount)
            resolver.resolve_player_attack(attack)
            resolver.resolve_current_tick()
            self.assertEqual(feed.drain(), ())

    def test_real_pulse_parry_grades_reflection_and_death(self):
        for delta, grade in ((19, 'failed'), (18, 'normal'), (7, 'perfect')):
            parts = pulse_battle(hp=1)
            player, combat, _, encounter, resolver = parts
            feed = encounter.ledger.presentation = PresentationEvents()
            resolver.advance(1)
            attack = encounter.pulse.event
            attempt = parry(parts, delta)
            batch = feed.drain()
            kinds = [event.kind for event in batch]
            self.assertEqual(kinds.count('parry_' + grade), 1)
            self.assertEqual(kinds.count('attack_start'), 1)
            self.assertEqual(batch[0].kind, 'telegraph')
            self.assertIs(batch[0].payload, attack)
            self.assertEqual(len(set(e.key for e in batch)), len(batch))
            self.assertEqual('hurt' in kinds, grade != 'normal')
            self.assertEqual('stun' in kinds, grade == 'perfect')
            self.assertEqual('death' in kinds, grade == 'perfect')
            if grade == 'perfect':
                self.assertEqual(batch[-1].payload.source_entity_instance_id, player.entity_instance_id)
                self.assertEqual(batch[-1].payload.hp_after, 0)
            resolver.register_parry(attempt)
            resolver.resolve_enemy_attack(attack)
            self.assertEqual(feed.drain(), ())

    def test_catchup_drain_and_restart_transfer_preserve_actual_session(self):
        game, flow = session()
        reference = pickle.loads(pickle.dumps(game))
        events = flow.enable_presentation()
        self.assertIs(flow.enable_presentation(), events)
        self.assertEqual(game.advance(435), reference.advance(435))
        self.assertEqual((game.state, game.end_tick), (reference.state, reference.end_tick))
        self.assertIn('death', [event.kind for event in events.drain()])
        previous = game
        game, _ = flow.restart(main._new_stage_game)
        (transition,) = events.drain()
        self.assertEqual((transition.kind, transition.payload), ('stage_transition', (11, 11)))
        self.assertEqual(transition.cause_key, (game.combat.combat_session_id, game.combat.stage_instance_id))
        self.assertIsNone(previous.encounter.ledger.presentation)
        self.assertIs(game.encounter.ledger.presentation, events)
        self.assertEqual(events.drain(), ())
