"""Stage16 original six-enemy lava combat and held Stage17 upgrade."""
import unittest
from unittest.mock import Mock,patch
import main
from game import GameState
from renderer import BoardRenderer
from upgrade_renderer import UpgradeRenderer
from tests.test_chapter_four_entry import entered_four
from tests.test_chapter_three_entry import state
from tests.test_upgrade_flow import clear
from tests.balance_driver import STYLES,measure


class StageSixteenTests(unittest.TestCase):
    def test_exact_roster_and_original_delays_health_and_theme(self):
        g=main._new_stage_game(16);other=main._new_stage_game(16)
        self.assertEqual((g.chapter,g.boss,g.player.position,g.encounter.pulse),(4,False,(5,1),None))
        self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay_ticks,e.health.max_hp) for e in g.encounter.enemies],
          [('s16_rook_1','rook',(2,4),48,16),('s16_rook_2','rook',(7,4),62,16),
           ('s16_knight_1','knight',(3,6),75,13),('s16_knight_2','knight',(6,6),88,13),
           ('s16_bishop_1','bishop',(2,8),101,13),('s16_pawn_1','pawn',(1,6),114,10)])
        self.assertEqual(g.encounter.enemies[-1].forward,(0,-1))
        for a,b in zip(g.encounter.enemies,other.encounter.enemies):
            self.assertIsNot(a.health,b.health);self.assertNotEqual(a.entity_instance_id,b.entity_instance_id)
        board=BoardRenderer(chapter=4);self.assertEqual(board.theme.name,'Obsidian Caldera')
        self.assertNotEqual(board.theme,BoardRenderer(chapter=3).theme);board.draw(Mock())

    def test_clear_holds_first_offer_without_factory_or_retry_error(self):
        f=entered_four();f.choose(clear(f),'attack',main._new_stage_game);g=f.game;g.advance(120);pending=g.encounter.ledger.pending;o=clear(f);before=state(f)
        self.assertEqual((g.state,f.run.current_stage,len(f.run.receipts),o.stage),(GameState.UPGRADE,17,1,17))
        self.assertIs(f.sync_offer(),o);factory=Mock()
        for kind in ('attack','hp','move'):
            with self.assertRaisesRegex(ValueError,'Stage 18 is not available'):f.choose(o,kind,factory)
        factory.assert_not_called();g.advance(999);self.assertEqual(state(f),before)
        for ev in pending:self.assertEqual(g.encounter.ledger.state(ev),'cancelled')
        with patch.object(UpgradeRenderer,'_text') as text:UpgradeRenderer().draw(Mock(),g,o,error=True)
        labels=[c.args[1] for c in text.call_args_list]
        self.assertIn('STAGE 18 NOT AVAILABLE',labels);self.assertIn('UPGRADE ON HOLD',labels)
        self.assertFalse(any('TRY AGAIN' in s for s in labels))
        self.assertIsNone(g.next_stage_number);self.assertIsNone(g.restart_stage_number)

    def test_bishop_actual_warning_damage_miss_and_parry(self):
        for mode in ('hit','miss','normal','perfect'):
            g=main._new_stage_game(16)
            # Timing fixture only; full original roster combat is measured separately.
            for e in g.encounter.enemies:
                if e.kind!='bishop':e.next_action_tick=1000
            g.advance(101);b=g.encounter.enemies[4];ev=b.current_attack
            self.assertEqual((ev.start_tick,ev.hit_tick,len(ev.target_cells)),(101,209,50))
            if mode=='miss':g.player.move('right',occupied=g.encounter.occupied_cells)
            if mode in ('normal','perfect'):
                delta=18 if mode=='normal' else 7
                g.advance(ev.hit_tick-delta-g.combat.tick);g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.advance(ev.hit_tick-g.combat.tick)
            self.assertEqual(g.encounter.ledger.outcome(ev),'parried_'+mode if mode in ('normal','perfect') else mode)
            self.assertEqual(g.player.health.current_hp,2 if mode=='hit' else 3)
            self.assertIsNone(g.resolver.resolve_enemy_attack(ev))
            if mode=='perfect':self.assertEqual((b.stun_until_tick,g.combat.pending_attack_bonus),(269,2))

    def test_sources_die_cancel_pending_and_others_continue(self):
        for index in range(6):
            g=main._new_stage_game(16);g.advance(120);e=g.encounter.enemies[index];ev=e.current_attack
            e.health.apply_damage(e.health.current_hp,tick=120);g.encounter.deactivate(e.entity_instance_id,tick=120);g.update_state()
            self.assertTrue(g.playing)
            if ev:self.assertEqual(g.encounter.ledger.state(ev),'cancelled')
        g=main._new_stage_game(16)
        for e in g.encounter.enemies:e.health.apply_damage(e.health.current_hp,tick=0)
        g.player.health.apply_damage(3,tick=0);g.update_state();self.assertEqual(g.state,GameState.GAME_OVER)

    def test_original_six_mixed_combat_one_and_eight_ticks(self):
        traces=[]
        for stride in (1,8):
            g=main._new_stage_game(16)
            for _ in range(640//stride):g.advance(stride)
            traces.append((g.combat.tick,g.state,g.player.health.current_hp,[(e.position,e.state,e.next_action_tick) for e in g.encounter.enemies],[(r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()]))
        self.assertEqual(*traces)

    def test_four_builds_clear_actual_roster(self):
        for style in STYLES:
            r=measure(style,16,limit=3600)
            self.assertEqual(r['result'],'UPGRADE');self.assertEqual(r['hp'],[16,16,13,13,13,10]);self.assertGreater(r['remaining_hp'],0)
