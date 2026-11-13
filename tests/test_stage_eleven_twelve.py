"""Original Chapter3 rosters, real combat, one choice, and a held next offer."""
from dataclasses import replace
import unittest
from unittest.mock import Mock, patch

import main
from combat import Combat
from combat_resolution import CombatResolver
from enemy_factory import create_stage_enemies
from enemy_behaviors import EnemyEncounter
from game import GameState
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from parry import Parry
from player import Player
from renderer import BoardRenderer
from combat_balance import profile_for
from stage_manager import StageCatalog
from upgrades import ChapterBuild
from upgrade_renderer import UpgradeRenderer
from tests.test_chapter_three_entry import entered_three, state
from tests.test_upgrade_flow import clear


class StageElevenTwelveTests(unittest.TestCase):
    def test_exact_original_rosters_ids_delays_hp_and_metadata(self):
        for n, kinds, positions, hp in (
                (11, ['rook','rook','knight','knight','pawn'], [(2,4),(7,4),(3,6),(6,6),(1,6)], [12,12,10,10,7]),
                (12, ['bishop','bishop','rook','pawn','pawn'], [(2,8),(7,8),(2,4),(1,6),(8,6)], [10,10,12,7,7])):
            g = main._new_stage_game(n)
            d = StageCatalog.load().get_stage(n)
            self.assertEqual((g.chapter, g.boss, d.boss_hp, g.player.position), (3, False, None, (5,1)))
            self.assertIsNone(g.encounter.pulse)
            self.assertEqual([e.data_id for e in g.encounter.enemies], [e.data_id for e in d.enemies])
            self.assertEqual([e.kind for e in g.encounter.enemies], kinds)
            self.assertEqual([e.position for e in g.encounter.enemies], positions)
            self.assertEqual([e.initial_delay_ticks for e in g.encounter.enemies], [48,62,75,88,101])
            self.assertEqual([e.health.current_hp for e in g.encounter.enemies], hp)
            self.assertEqual([e.health.max_hp for e in g.encounter.enemies], hp)

    def test_repeated_factories_have_fresh_entities_health_ledgers_and_ids(self):
        for n in (11,12):
            a, b = main._new_stage_game(n), main._new_stage_game(n)
            self.assertNotEqual(a.combat.stage_instance_id,b.combat.stage_instance_id)
            self.assertNotEqual(a.combat.combat_session_id,b.combat.combat_session_id)
            self.assertIsNot(a.encounter.ledger,b.encounter.ledger)
            for left,right in zip((a.player,*a.encounter.enemies),(b.player,*b.encounter.enemies)):
                self.assertNotEqual(left.entity_instance_id,right.entity_instance_id)
                self.assertIsNot(left.health,right.health)

    def test_first_offer_single_consumption_stats_and_full_heal(self):
        for kind in ('attack','hp','move'):
            f = entered_three()
            f.game.player.health.apply_damage(1,tick=0)
            o = clear(f)
            self.assertIs(f.sync_offer(),o)
            self.assertEqual((o.stage,len(f.run.receipts)),(11,0))
            run=f.run
            g,_=f.choose(o,kind,main._new_stage_game)
            self.assertIs(f.run,run)
            self.assertEqual((g.stage_number,len(run.receipts)),(12,1))
            self.assertEqual(g.resolver.player_damage,run.stats.attack_damage)
            self.assertEqual(g.player.health.current_hp,run.stats.max_hp)
            with self.assertRaises(ValueError):f.choose(o,kind,Mock())

    def test_first_choice_factory_input_and_corrupt_candidate_are_atomic(self):
        for mode in ('factory','input','hp'):
            f=entered_three();o=clear(f);before=state(f)
            def factory(n,*,stats):
                if mode=='factory':raise RuntimeError(mode)
                g=main._new_stage_game(n,stats=stats)
                if mode=='hp':g.encounter.enemies[0].health.apply_damage(1,tick=0)
                return g
            prepare=Mock(side_effect=RuntimeError(mode)) if mode=='input' else lambda stats:None
            with self.assertRaises((ValueError,RuntimeError)):f.choose(o,'hp',factory,prepare)
            self.assertEqual(state(f),before)
            f.choose(o,'hp',main._new_stage_game)
            self.assertEqual(f.game.stage_number,12)

    def test_first_choice_copied_or_foreign_offer_never_calls_factory(self):
        f=entered_three();o=clear(f);other=entered_three();foreign=clear(other)
        factory=Mock()
        for candidate in (replace(o),foreign):
            with self.assertRaises(ValueError):f.choose(candidate,'attack',factory)
        factory.assert_not_called()
        self.assertIs(f.offer,o)

    def test_stage_twelve_clear_issues_one_held_offer_and_freezes_combat(self):
        f=entered_three();f.choose(clear(f),'hp',main._new_stage_game)
        g=f.game;g.advance(80)
        pending=g.encounter.ledger.pending
        o=clear(f)
        tick=g.combat.tick
        self.assertEqual((g.state,o.stage,f.run.current_stage,len(f.run.receipts)),(GameState.UPGRADE,12,12,1))
        self.assertTrue(g.upgrade_selection_enabled)
        self.assertIs(f.sync_offer(),o)
        self.assertIsNone(g.restart_stage_number)
        self.assertIsNone(g.next_stage_number)
        g.advance(500)
        self.assertEqual((g.combat.tick,g.transition_count),(tick,1))
        for event in pending:self.assertEqual(g.encounter.ledger.state(event),'cancelled')

    def test_boundary_rejects_every_choice_before_factory_or_receipt(self):
        f=entered_three();f.choose(clear(f),'attack',main._new_stage_game)
        f.choose(clear(f),'hp',main._new_stage_game)
        o=clear(f);before=state(f);factory=Mock();prepare=Mock()
        with patch.object(f.run,'select',wraps=f.run.select) as select:
            for kind in ('attack','hp','move'):
                with self.assertRaisesRegex(ValueError,'Stage 14 is not available'):
                    f.choose(o,kind,factory,prepare)
            select.assert_not_called()
        factory.assert_not_called();prepare.assert_not_called()
        self.assertEqual(state(f),before)

    def test_boundary_renderer_explains_hold_without_retry_or_card_prompts(self):
        f=entered_three();f.choose(clear(f),'hp',main._new_stage_game);f.choose(clear(f),'hp',main._new_stage_game);o=clear(f)
        before=state(f)
        with patch.object(UpgradeRenderer,'_text') as text:
            UpgradeRenderer().draw(Mock(),f.game,o,error=True)
        labels=[c.args[1] for c in text.call_args_list]
        for label in ('UPGRADE','STAGE 13 CLEAR','STAGE 14 NOT AVAILABLE','UPGRADE ON HOLD'):
            self.assertIn(label,labels)
        self.assertFalse(any('TRY AGAIN' in s or 'CHOOSE ONE' in s or 'N TO' in s for s in labels))
        self.assertEqual(state(f),before)

    def test_boss_next_chapter_prompts_are_dynamic(self):
        from tests.test_stage_transition import finish
        for n,chapter in ((5,2),(10,3)):
            g=main._new_stage_game(n);finish(g,'clear')
            with patch.object(HealthRenderer,'_text') as text:GameFlowRenderer().draw(Mock(),g)
            self.assertIn('N TO CHAPTER '+str(chapter),[c.args[1] for c in text.call_args_list])

    def test_frozen_palette_and_geometry_are_existing_visuals_only(self):
        b=BoardRenderer(chapter=3);t=b.theme
        self.assertEqual((t.name,t.background,t.tile_light,t.tile_dark,t.frame,t.accent),
                         ('Frozen Palace',(16,26,40),(204,226,234),(52,82,108),(38,62,82),(132,190,214)))
        self.assertNotEqual(t,BoardRenderer(chapter=2).theme)
        commands=b._commands;b.draw(Mock());self.assertIs(b._commands,commands)

    def test_stage13_through25_and_queen_factory_still_rejected(self):
        for n in range(14,26):
            with self.assertRaises(ValueError):main._new_stage_game(n)
        enemies=create_stage_enemies(StageCatalog.load().get_stage(13),profile=profile_for(3))
        self.assertTrue(any(e.kind=='queen' and e.health.max_hp==14 for e in enemies))
        with self.assertRaises(ValueError):
            create_stage_enemies(StageCatalog.load().get_stage(13),profile=profile_for(2))

    def test_original_two_bishops_serialize_opposite_colors_and_parry(self):
        # Isolate the two JSON Bishops to observe exact scheduling; full mixed fights below.
        definition=StageCatalog.load().get_stage(12)
        enemies=create_stage_enemies(definition,profile=profile_for(3))[:2]
        player,combat,parry=Player(5,1),Combat(),Parry()
        enc=EnemyEncounter(enemies)
        r=CombatResolver(player,combat,enc,parry=parry)
        r.advance(149)
        first=enemies[0].current_attack
        self.assertEqual((first.start_tick,first.hit_tick,len(first.target_cells)),(48,156,50))
        self.assertIsNone(enemies[1].current_attack)
        r.register_parry(parry.request(149));r.advance(7)
        self.assertEqual(enc.ledger.outcome(first),'parried_perfect')
        r.advance()
        second=enemies[1].current_attack
        self.assertEqual((second.start_tick,second.hit_tick,len(second.target_cells)),(157,265,50))
        self.assertTrue(set(first.target_cells).isdisjoint(second.target_cells))
        self.assertTrue(player.move('up',occupied=enc.occupied_cells))
        r.advance(90);r.register_parry(parry.request(247));r.advance(18)
        self.assertEqual(enc.ledger.outcome(second),'parried_normal')
        self.assertEqual(player.health.current_hp,3)
        self.assertIsNone(r.resolve_enemy_attack(second))

    def test_bishop_death_cancels_plan_and_releases_other_color(self):
        g=main._new_stage_game(12);g.advance(100)
        a,b=g.encounter.enemies[:2];event=a.current_attack
        self.assertIsNone(b.current_attack)
        a.health.apply_damage(a.health.max_hp,tick=100)
        g.encounter.deactivate(a.entity_instance_id,tick=100)
        g.advance()
        self.assertEqual(g.encounter.ledger.state(event),'cancelled')
        self.assertEqual(b.current_attack.start_tick,101)

    def test_both_full_mixed_rosters_are_deterministic_with_eight_tick_frames(self):
        for n in (11,12):
            traces=[]
            for stride in (1,8):
                g=main._new_stage_game(n)
                for _ in range(800//stride):g.advance(stride)
                traces.append((g.combat.tick,g.state,g.player.health.current_hp,
                    [(e.position,e.state,e.health.current_hp,e.next_action_tick) for e in g.encounter.enemies],
                    [(r.event.start_tick,r.event.hit_tick,r.event.target_cells,r.event.attack_kind,r.state,r.outcome)
                     for r in g.encounter.ledger._records.values()]))
            self.assertEqual(traces[0],traces[1])

    def test_eight_real_attack_movement_parry_measurements_clear_with_inheritance(self):
        from tests.balance_driver import measure,STYLES
        for style,entry_attack in (('attack',9),('survival',3),('evasion',5),('balanced',5)):
            for n in (11,12):
                with self.subTest(style=style,stage=n):
                    r=measure(style,n,limit=3600)
                    self.assertEqual(r['result'],'UPGRADE')
                    self.assertGreater(r['remaining_hp'],0)
                    self.assertGreater(r['hits'],0)
                    if n==11:self.assertEqual(r['attack'],entry_attack)


if __name__ == '__main__':
    unittest.main()
