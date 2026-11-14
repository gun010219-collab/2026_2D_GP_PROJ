"""Y-A runtime balance and entry attack ownership; no SDL."""
from dataclasses import replace, FrozenInstanceError
from math import ceil
import unittest
from unittest.mock import Mock
import main
from combat_balance import PROFILES, CombatProfile, profile_for
from chapter_run import ChapterRun
from upgrades import ChapterBuild, DerivedStats, UpgradeKind
from enemy import load_stage1_enemies, Enemy
from enemy_factory import create_stage_enemies
from stage_manager import StageCatalog
from tests.test_upgrade_flow import flow_at_boss, clear
from tests.test_stage_transition import finish
from health import Health


class CombatBalanceTests(unittest.TestCase):
    def test_all_attack_levels_and_rejected_values(self):
        for n in range(16):self.assertEqual(ChapterBuild(n).stats.attack_damage,n+1)
        for v in (-1,16,True,False,1.5,None):
            with self.assertRaises(ValueError):ChapterBuild(v)
        for v in (-1,0,17,True,False,1.5,None):
            with self.assertRaises(ValueError):DerivedStats(v,3,18)

    def test_max_attack_keeps_other_options_and_does_not_consume(self):
        r=ChapterRun(2,entry_attack_level=15);o=r.offer_after_clear(6,'max')
        self.assertFalse(o.options[0].enabled)
        with self.assertRaises(ValueError):r.select(o,'attack')
        self.assertIs(r.active_offer,o);self.assertEqual(r.receipts,())
        r.select(o,'hp');self.assertEqual(r.stats,DerivedStats(16,4,18))

    def test_exact_profiles_are_read_only_and_strict(self):
        expected=((3,6,5,5,22),(5,9,7,7,40),(7,12,10,10,60),(10,16,13,13,85),(13,20,16,16,110))
        for chapter,row in enumerate(expected,1):
            self.assertEqual(tuple(profile_for(chapter).hp(k) for k in ('pawn','rook','knight','bishop','king')),row)
        for v in (True,0,6,1.0,None):
            with self.assertRaises(ValueError):profile_for(v)
        with self.assertRaises(TypeError):PROFILES[1]=profile_for(2)
        with self.assertRaises(FrozenInstanceError):profile_for(1).pawn=99
        with self.assertRaises(ValueError):CombatProfile(1,True,1,1,1,1)

    def test_stage_one_and_catalog_factory_use_same_runtime_hp(self):
        legacy=load_stage1_enemies()
        factory=create_stage_enemies(StageCatalog.load().get_stage(1),profile=profile_for(1))
        self.assertEqual([e.health.current_hp for e in legacy],[3,3])
        self.assertEqual([e.health.max_hp for e in factory],[3,3])

    def test_original_boss_metadata_and_runtime_hp_are_distinct(self):
        for n,original,runtime in ((5,8,22),(10,10,40),(15,12,60),(20,14,85),(25,16,110)):
            d=StageCatalog.load().get_stage(n);self.assertEqual(d.boss_hp,original)
            # Later Queen encounters remain unsupported; verify King alone.
            from enemy_factory import create_enemy
            king=create_enemy(d.enemies[0],boss_hp=profile_for(d.chapter).king)
            self.assertEqual(king.health.max_hp,runtime)
            self.assertEqual(d.boss_hp,original)

    def test_runtime_spawns_preserve_all_original_fields_and_health_isolation(self):
        for n in range(1,11):
            d=StageCatalog.load().get_stage(n);g=main._new_stage_game(n)
            self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay) for e in g.encounter.enemies],
                             [(e.data_id,e.kind,e.position,e.initial_delay) for e in d.enemies])
            self.assertEqual([e.health.max_hp for e in g.encounter.enemies],
                             [profile_for(d.chapter).hp(e.kind) for e in d.enemies])
            self.assertTrue(all(e.health.current_hp==e.health.max_hp for e in g.encounter.enemies))

    def test_inheritance_is_attack_only_and_old_receipts_cannot_cross(self):
        f=flow_at_boss(('attack','attack','hp','move'));old=f.run;receipt=old.receipts[0]
        finish(f.game,'clear');g,_=f.enter_next_chapter(main._new_stage_game)
        self.assertEqual((f.run.entry_attack_level,f.run.build,f.run.receipts),(2,ChapterBuild(2),()))
        self.assertEqual((g.resolver.player_damage,g.player.health.current_hp),(3,3))
        with self.assertRaises(ValueError):f.run.verify_receipt(receipt)
        self.assertTrue(old.retired)

    def test_death_restores_entry_attack_not_current_attack(self):
        from stage_progression import StageProgression
        r=ChapterRun(2,entry_attack_level=4)
        f=StageProgression(main._new_stage_game(6,stats=r.stats),r)
        f.choose(clear(f),'attack',main._new_stage_game)
        f.choose(clear(f),'attack',main._new_stage_game)
        self.assertEqual(f.run.stats.attack_damage,7)
        finish(f.game,'dead');before=(f.run,f.game,f.run.build)
        with self.assertRaises(RuntimeError):f.restart(Mock(side_effect=RuntimeError('prepare')))
        self.assertEqual((f.run,f.game,f.run.build),before)
        g,_=f.restart(main._new_stage_game)
        self.assertEqual((f.run.entry_attack_level,g.stage_number,g.resolver.player_damage,f.run.receipts),(4,6,5,()))

    def test_later_chapters_model_inherits_without_enabling_execution(self):
        r=ChapterRun()
        for chapter in range(1,6):
            for _ in range(4):
                o=r.offer_after_clear(r.current_stage,str(r.current_stage))
                r.select(o,'attack' if r.stats.attack_damage<16 else 'hp' if r.build.hp_level<3 else 'move')
            if chapter<5:
                attack=r.build.attack_level;r=r.start_chapter(chapter+1)
                self.assertEqual((r.entry_attack_level,r.build,r.receipts),(attack,ChapterBuild(attack),()))
        self.assertEqual(r.stats.attack_damage,16)
        for n in range(19,26):
            with self.assertRaises(ValueError):main._new_stage_game(n)

    def test_candidate_low_high_damaged_and_wrong_profile_health_rejected(self):
        from stage_progression import StageProgression
        for mode in ('low','high','damaged','wrong'):
            f=StageProgression(main._new_game());o=clear(f)
            def factory(n,*,stats):
                g=main._new_stage_game(n,stats=stats);e=g.encounter.enemies[0]
                if mode=='damaged':e.health.apply_damage(1,tick=0)
                else:e.health=Health(e.health.max_hp+(-1 if mode=='low' else 1 if mode=='high' else 3))
                return g
            with self.assertRaises(ValueError):f.choose(o,'attack',factory)
            self.assertIs(f.offer,o);self.assertEqual(f.run.receipts,())

    def test_actual_base16_and_perfect18_damage_single_consumption(self):
        for bonus,damage in ((False,16),(True,18)):
            g=main._new_stage_game(5,stats=ChapterBuild(15).stats)
            k=g.encounter.pulse.king;k.col,k.row=5,2
            if bonus:g.combat.grant_perfect_counter()
            event=g.combat.request_attack(g.player);result=g.resolver.resolve_player_attack(event)
            self.assertEqual(result.amount,damage)
            self.assertEqual(k.health.current_hp,22-damage)
            self.assertIsNone(g.resolver.resolve_player_attack(event))
            self.assertEqual(g.combat.pending_attack_bonus,0)

    def test_hits_to_kill_baselines(self):
        for hp,attack,count in ((3,1,3),(3,2,2),(3,3,1),(22,3,8),(22,5,5),(40,5,8),(40,9,5)):
            self.assertEqual(ceil(hp/attack),count)

    def test_factory_rejects_wrong_profile_and_queen(self):
        d=StageCatalog.load().get_stage(6)
        with self.assertRaises(ValueError):create_stage_enemies(d,profile=profile_for(1))
        es=create_stage_enemies(StageCatalog.load().get_stage(13),profile=profile_for(3))
        self.assertTrue(any(e.kind=='queen' and e.health.max_hp==14 for e in es))
        with self.assertRaises(ValueError):main._new_stage_game(19)

    def test_later_chapter_nonqueen_rosters_can_use_profile_without_play_permission(self):
        for n in (11,16,23):
            d=StageCatalog.load().get_stage(n)
            enemies=create_stage_enemies(d,profile=profile_for(d.chapter))
            self.assertEqual([e.health.max_hp for e in enemies],[profile_for(d.chapter).hp(e.kind) for e in d.enemies])
            if n in (11,16):
                self.assertEqual([e.health.max_hp for e in main._new_stage_game(n).encounter.enemies],
                                 [e.health.max_hp for e in enemies])
            else:
                with self.assertRaises(ValueError):main._new_stage_game(n)

    def test_four_build_styles_clear_all_ten_real_rosters(self):
        from tests.balance_driver import measure, STYLES
        for style in STYLES:
            for stage in range(1,11):
                with self.subTest(style=style,stage=stage):
                    result=measure(style,stage)
                    self.assertEqual(result['result'],'BOSS_CLEAR' if stage in (5,10) else 'UPGRADE')
                    self.assertGreater(result['hits'],0)
                    self.assertGreater(result['remaining_hp'],0)

    def test_attack16_max_keyboard_mouse_and_other_card_main(self):
        from types import SimpleNamespace
        from tests.test_stage_transition import run_loop, key
        click=SimpleNamespace(type=1025,button=1,x=450,y=500)
        factory=main._new_stage_game
        created,snapshots,*_=run_loop([[key(49)],[click],[key(50)]],initial_stage=6,
            entry_attack_level=15,initial_factory=lambda:factory(6,stats=ChapterBuild(15).stats))
        self.assertEqual([g.stage_number for g in created],[6,7])
        self.assertEqual([s['stage'] for s in snapshots],[6,6,7])
        self.assertEqual((created[-1].resolver.player_damage,created[-1].player.health.max_hp),(16,4))

    def test_two_digit_attack_render_is_read_only(self):
        from unittest.mock import patch
        from upgrade_renderer import UpgradeRenderer
        for level in (14,15):
            r=ChapterRun(2,entry_attack_level=level);o=r.offer_after_clear(6,'render')
            g=main._new_stage_game(6,stats=r.stats);before=(r.build,r.receipts)
            with patch.object(UpgradeRenderer,'_text') as text:
                UpgradeRenderer().draw(Mock(),g,o)
            labels=[c.args[1] for c in text.call_args_list]
            self.assertIn('LEVEL '+str(level),labels)
            self.assertIn('NOW '+str(level+1),labels)
            self.assertIn('NEXT 16' if level==14 else 'MAX',labels)
            self.assertEqual((r.build,r.receipts),before)
