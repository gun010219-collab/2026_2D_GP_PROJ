"""Task 3-F2 HP experiment: real battles and terminal fixtures are distinguished."""
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
from unittest.mock import Mock, patch
import unittest

import main
from chapter_run import ChapterRun
from combat_balance import PROFILES, CombatProfile, profile_for
from game import GameState
from simulation_clock import SimulationClock
from stage_manager import StageCatalog
from stage_progression import StageProgression
from tests.balance_driver import STYLES, measure
from tests.test_hp_carryover import fight, owned
from tests.test_upgrade_flow import clear
from tests.test_stage_transition import finish


EXPECTED = ((4,8,7,7,28,None), (7,12,9,9,50,None),
            (9,16,13,13,75,18), (13,21,18,18,100,24),
            (13,20,16,16,110,22))
FAILURES = {(16,'survival'): (408,3,3), (19,'evasion'): (395,3,4),
            (20,'survival'): (838,6,8)}


def chapter_run(style, chapter):
    # Prior chapter upgrades derive entry attack; these are not combat clears.
    run = ChapterRun()
    for n in range(1,chapter):
        for kind in STYLES[style]:
            run.select(run.offer_after_clear(run.current_stage, str(run.current_stage)), kind)
        run = run.start_chapter(n+1)
    return run


def real_campaign(style):
    flow = StageProgression(main._new_stage_game(1))
    rows = []
    while True:
        game = flow.game
        start_hp = game.player.health.current_hp
        row = fight(flow)
        rows.append((row[0],start_hp,*row[1:]))
        if game.state is GameState.UPGRADE:
            kind = 'hp' if style == 'attack' and game.stage_number == 19 else STYLES[style][len(flow.run.receipts)]
            hp = game.player.health.current_hp
            old = game.player.health
            flow.choose(flow.sync_offer(), kind, main._new_stage_game)
            assert flow.game.player.health.current_hp == hp + (kind == 'hp')
            assert flow.game.player.health is not old
        elif game.state is GameState.BOSS_CLEAR and game.stage_number < 20:
            flow.enter_next_chapter(main._new_stage_game)
            assert flow.game.player.health.current_hp == 3
        else:
            return flow, rows


class EnemyHPRebalanceTests(unittest.TestCase):
    def test_exact_approved_profiles_including_unchanged_chapter_five(self):
        for chapter, values in enumerate(EXPECTED,1):
            p = profile_for(chapter)
            self.assertEqual((p.pawn,p.rook,p.knight,p.bishop,p.king,p.queen), values)

    def test_profile_immutability_and_invalid_chapter_and_hp(self):
        with self.assertRaises(TypeError): PROFILES[1] = PROFILES[2]
        with self.assertRaises(FrozenInstanceError): PROFILES[4].king = 1
        for value in (0,6,True,1.0,None):
            with self.assertRaises(ValueError): profile_for(value)
        for value in (0,-1,True,1.5,None):
            for field in ('pawn','rook','knight','bishop','king'):
                with self.assertRaises(ValueError): replace(PROFILES[4], **{field:value})
            if value is not None:
                with self.assertRaises(ValueError): replace(PROFILES[4],queen=value)
        self.assertIsNone(replace(PROFILES[4],queen=None).queen)
        with self.assertRaises(ValueError): CombatProfile(1,1,1,1,1,1,1)

    def test_all_twenty_original_rosters_and_isolated_runtime_health(self):
        catalog = StageCatalog.load()
        for n in range(1,21):
            a,b = main._new_stage_game(n), main._new_stage_game(n)
            d = catalog.get_stage(n)
            self.assertEqual([(e.data_id,e.kind,e.position,e.initial_delay,e.forward) for e in a.encounter.enemies],
                             [(e.data_id,e.kind,e.position,e.initial_delay,e.options.get('forward')) for e in d.enemies])
            for x,y in zip(a.encounter.enemies,b.encounter.enemies):
                self.assertEqual((x.health.current_hp,x.health.max_hp), (profile_for(a.chapter).hp(x.kind),)*2)
                self.assertIsNot(x.health,y.health)
                self.assertNotEqual(x.entity_instance_id,y.entity_instance_id)
            self.assertEqual(len({id(e.health) for e in a.encounter.enemies}),len(d.enemies))

    def test_original_json_boss_hp_and_new_runtime_totals(self):
        source = Path(__file__).resolve().parents[1] / 'stage_data.json'
        self.assertEqual(sha256(source.read_bytes()).hexdigest(), 'f4432b361dc736b6bd3be999584160255efcd7e803c8cd3873d548df6d92d55f')
        for n,original,runtime in ((5,8,28),(10,10,50),(15,12,75),(20,14,100)):
            g = main._new_stage_game(n)
            self.assertEqual(StageCatalog.load().get_stage(n).boss_hp, original)
            self.assertEqual(g.encounter.pulse.king.health.current_hp, runtime)
        self.assertEqual([e.health.max_hp for e in main._new_stage_game(1).encounter.enemies],[4,4])
        self.assertEqual([e.health.max_hp for e in main._new_stage_game(20).encounter.enemies],[100,24,18,18,18,13])
        self.assertEqual(sum(e.health.max_hp for e in main._new_stage_game(20).encounter.enemies),191)

    def test_candidate_wrong_profile_rejected_before_consuming_hurt_offer(self):
        f = owned(4,hp=1); offer = clear(f); before = (f.game,f.run.build,f.run.receipts,f.game.player.health.current_hp)
        prepare = Mock()
        def bad(n, **kwargs):
            g = main._new_stage_game(n, **kwargs)
            g.encounter.enemies[0].health.apply_damage(1,tick=0)
            return g
        with self.assertRaises(ValueError): f.choose(offer,'attack',bad,prepare)
        prepare.assert_not_called()
        self.assertEqual((f.game,f.run.build,f.run.receipts,f.game.player.health.current_hp),before)
        self.assertIs(f.offer,offer)
        f.choose(offer,'attack',main._new_stage_game)
        self.assertEqual(f.game.player.health.current_hp,1)

    def test_eighty_real_battles_report_exact_experimental_failures(self):
        failures = {}
        for stage in range(1,21):
            for style in STYLES:
                with self.subTest(stage=stage,style=style):
                    row = measure(style,stage,limit=3600)
                    self.assertEqual(row['hp'],[profile_for((stage-1)//5+1).hp(e.kind) for e in StageCatalog.load().get_stage(stage).enemies])
                    self.assertGreater(row['hits'],0)
                    if (stage,style) in FAILURES:
                        self.assertEqual(row['result'],'GAME_OVER')
                        self.assertEqual(row['remaining_hp'],0)
                        failures[stage,style] = row['ticks'],row['received'],row['perfect']
                    else:
                        self.assertEqual(row['result'],'BOSS_CLEAR' if stage%5 == 0 else 'UPGRADE')
                        self.assertGreater(row['remaining_hp'],0)
                        self.assertLess(row['ticks'],3600)
        self.assertEqual(failures,FAILURES)

    def test_failed_battles_stop_once_and_record_real_lethal_sources(self):
        factory = main._new_stage_game
        for stage,style,source in ((16,'survival','s16_knight_2'),(19,'evasion','s19_rook_2'),(20,'survival','s20_knight_1')):
            captured = []
            def capture(*a,**kw):
                g = factory(*a,**kw); captured.append(g); return g
            with patch.object(main,'_new_stage_game',capture): measure(style,stage)
            g = captured[0]; tick = g.combat.tick
            self.assertEqual((g.state,g.transition_count),(GameState.GAME_OVER,1))
            self.assertTrue(g.resolver.stopped)
            self.assertTrue(any(e.alive for e in g.encounter.enemies))
            self.assertFalse(g.encounter.ledger.pending)
            lethal = [r.event for r in g.encounter.ledger._records.values() if r.event.hit_tick==tick and r.outcome=='hit']
            self.assertEqual([next(e.data_id for e in g.encounter.enemies if e.entity_instance_id==ev.source_entity_instance_id) for ev in lethal],[source])
            g.advance(1000); self.assertEqual(g.combat.tick,tick)

    def test_base16_counter18_and_no_duplicate_hit_under_new_king_hp(self):
        from upgrades import ChapterBuild
        for bonus,expected in ((False,16),(True,18)):
            g = main._new_stage_game(20,stats=ChapterBuild(15).stats)
            king = g.encounter.pulse.king; king.col,king.row = 5,2
            if bonus: g.combat.grant_perfect_counter()
            ev = g.combat.request_attack(g.player)
            self.assertEqual(g.resolver.resolve_player_attack(ev).amount,expected)
            self.assertEqual(king.health.current_hp,100-expected)
            self.assertIsNone(g.resolver.resolve_player_attack(ev))

    def test_king_death_survivors_annihilation_and_player_death_priority(self):
        # Terminal branch fixtures; clear feasibility is measured above without damage edits.
        for dead in (False,True):
            g = main._new_stage_game(20); k = g.encounter.pulse.king
            k.health.apply_damage(100,tick=0); g.encounter.deactivate(k.entity_instance_id,tick=0)
            g.update_state(); self.assertTrue(g.playing)
            self.assertEqual(sum(e.alive for e in g.encounter.enemies),5)
            for e in g.encounter.enemies[1:]: e.health.apply_damage(e.health.current_hp,tick=0)
            if dead: g.player.health.apply_damage(3,tick=0)
            g.update_state()
            self.assertEqual(g.state,GameState.GAME_OVER if dead else GameState.BOSS_CLEAR)
            self.assertTrue(g.resolver.stopped)

    def test_hurt_upgrade_carry_and_hp_plus_one_all_chapters(self):
        for chapter in range(1,5):
            for kind in ('attack','move','hp'):
                f = owned(chapter,hp=1); old = f.game.player.health
                f.choose(clear(f),kind,main._new_stage_game)
                self.assertEqual((f.game.player.health.current_hp,f.game.player.health.max_hp), (2,4) if kind=='hp' else (1,3))
                self.assertIsNot(old,f.game.player.health)
                self.assertIsNone(f.game.player.health.last_damage_tick)
                self.assertEqual(f.game.resolver.player_invulnerable_until_tick,0)

    def test_real_five_stage_attack_runs_carry_health_in_all_four_chapters(self):
        for chapter in range(1,5):
            r = chapter_run('attack',chapter)
            f = StageProgression(main._new_stage_game(r.current_stage,stats=r.stats),r)
            for index in range(5):
                self.assertEqual(fight(f)[1],'BOSS_CLEAR' if index==4 else 'UPGRADE')
                if index<4:
                    hp = f.game.player.health.current_hp
                    kind = 'hp' if chapter==4 and index==3 else 'attack'
                    f.choose(f.sync_offer(),kind,main._new_stage_game)
                    self.assertEqual(f.game.player.health.current_hp,hp+(kind=='hp'))
            self.assertEqual(len(f.run.receipts),4)

    def test_full_campaigns_expose_carryover_risk_without_healing(self):
        for style,stage,tick in (('attack',20,654),('survival',16,408),('evasion',18,123),('balanced',19,149)):
            f,rows = real_campaign(style)
            self.assertEqual((f.game.stage_number,f.game.combat.tick),(stage,tick))
            self.assertEqual(len(rows),stage)
            self.assertEqual(f.game.state,GameState.BOSS_CLEAR if style=='attack' else GameState.GAME_OVER)
            self.assertEqual(len(f.run.receipts),4 if style=='attack' else stage-16)

    def test_replay_reset_new_chapter_policies_are_unchanged(self):
        # Outcome fixtures isolate transition contracts under the new enemy profile.
        for chapter in range(1,5):
            f = owned(chapter,hp=1)
            for kind in ('attack','hp','move','attack'): f.choose(clear(f),kind,main._new_stage_game)
            old = f.game; run = f.run; clear(f)
            g,_ = f.restart(main._new_stage_game)
            self.assertIs(f.run,run); self.assertEqual(g.player.health.current_hp,4)
            self.assertIsNot(g.encounter.pulse,old.encounter.pulse)
            finish(g,'dead');g,_ = f.restart(main._new_stage_game)
            self.assertTrue(run.retired)
            self.assertEqual((g.stage_number,g.player.health.current_hp,len(f.run.receipts)),((chapter-1)*5+1,3,0))
        for chapter in (1,2,3):
            f = owned(chapter,hp=1)
            for _ in range(4): f.choose(clear(f),'attack',main._new_stage_game)
            clear(f); f.enter_next_chapter(main._new_stage_game)
            self.assertEqual((f.run.chapter,f.game.player.health.current_hp,len(f.run.receipts)),(chapter+1,3,0))

    def test_seven_render_rates_and_tick_strides_leave_identical_combat(self):
        def snapshot(g):
            return (g.combat.tick,g.state,g.player.health.current_hp,
                    tuple((e.position,e.health.current_hp,e.state,e.next_action_tick) for e in g.encounter.enemies),
                    tuple((r.event.attack_kind,r.event.hit_tick,r.event.target_cells,r.state,r.outcome) for r in g.encounter.ledger._records.values()))
        traces = []
        for fps in (30,60,120,144,160,180,240):
            g = main._new_stage_game(20); clock = SimulationClock()
            for _ in range(fps*8): g.advance(clock.advance(1/fps))
            traces.append(snapshot(g))
        self.assertTrue(all(x==traces[0] for x in traces))
        traces = []
        for stride in (1,8):
            g = main._new_stage_game(20)
            for _ in range(480//stride): g.advance(stride)
            traces.append(snapshot(g))
        self.assertEqual(*traces)

    def test_unsupported_chapter_five_rejected_before_catalog(self):
        with patch.object(main.StageCatalog,'load') as load:
            for n in range(25,26):
                with self.assertRaises(ValueError): main._new_stage_game(n)
            load.assert_not_called()
