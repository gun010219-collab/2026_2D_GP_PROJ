"""Read-only campaign QA: unchanged real battle policy and owned progression APIs."""
import argparse
from collections import deque
from contextlib import contextmanager
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import main
from chapter_run import ChapterRun
from combat_resolution import CombatResolver, DamageResult
from game import GameState
from input_controller import InputController
from player import DIRECTIONS
from stage_progression import StageProgression
from tests.balance_driver import measure, STYLES
from tests.test_hp_carryover import fight
from tools.action_pacing_experiment import observe, summarize


def choice(style, stage, index):
    if style == 'attack' and stage == 19:
        return 'hp'
    if style == 'attack' and 21 <= stage <= 24:
        return 'move' if stage == 24 else 'hp'
    return STYLES[style][index]


@contextmanager
def trace_damage():
    """Observe decisions and alternatives; never change an input or result."""
    moves = deque(maxlen=8)
    traces = {}
    move, attack = InputController.key_down, CombatResolver.resolve_enemy_attack

    def moving(self, direction, player, **kw):
        before = player.position
        ready = self.next_move_tick
        result = move(self, direction, player, **kw)
        moves.append(dict(tick=kw.get('tick'), direction=direction,
                          before=before, after=player.position, next_move_before=ready, next_move_after=self.next_move_tick))
        return result

    def attacking(self, event):
        cell = self.player.position
        occupied = sorted(self.encounter.occupied_cells)
        danger = set().union(*(set(r.event.target_cells)
            for r in self.encounter.ledger._records.values()
            if r.state in ('telegraph', 'due')
            and 0 <= r.event.hit_tick-self.combat.tick <= 18))
        neighbors = [(cell[0]+dx, cell[1]+dy) for dx,dy in DIRECTIONS.values()]
        local_safe = [c for c in neighbors if 0 <= c[0]<10 and 0 <= c[1]<10
                      and c not in occupied and c not in danger]
        result = attack(self, event)
        if isinstance(result, DamageResult) and result.target_entity_instance_id == self.player.entity_instance_id:
            source = next(e.data_id for e in self.encounter.enemies
                          if e.entity_instance_id == event.source_entity_instance_id)
            traces.setdefault(self.combat.stage_instance_id, []).append(dict(
                tick=self.combat.tick, source=source, kind=event.attack_kind,
                hp_before=result.hp_before, hp_after=result.hp_after,
                player_cell=cell, next_parry_tick=self.parry.next_parry_tick,
                warning_cells=sorted(danger), occupied_cells=occupied,
                adjacent_safe_in_next18=local_safe, recent_inputs=list(moves)))
        return result

    with patch.object(InputController, 'key_down', moving),          patch.object(CombatResolver, 'resolve_enemy_attack', attacking):
        yield traces


def campaign(style, *, chapter5_only=False):
    run = ChapterRun()
    if chapter5_only:
        # Synthetic prior chapter growth, explicitly NOT a full campaign clear.
        for chapter in range(1,5):
            for i in range(4):
                stage=run.current_stage
                run.select(run.offer_after_clear(stage, 'synthetic-entry-'+str(stage)),
                           choice(style, stage, i))
            run=run.start_chapter(chapter+1)
    flow=StageProgression(main._new_stage_game(run.current_stage, stats=run.stats),run)
    rows=[]; transitions=[]; choices=[]; seen=set()
    def fresh(g):
        ids=(g.combat.combat_session_id,g.combat.stage_instance_id)
        assert not any(i in seen for i in ids)
        seen.update(ids)
    fresh(flow.game)
    with trace_damage() as traces, observe() as observations:
        while True:
            g=flow.game; r=flow.run; start=g.player.health.current_hp
            before_stats=(r.stats.attack_damage,r.stats.max_hp,r.stats.move_interval_ticks)
            result=fight(flow)
            row=dict(stage=g.stage_number,chapter=g.chapter,start_hp=start,
                     result=result[1],ticks=result[2],remaining_hp=result[3],
                     max_hp=result[4],attack=before_stats[0],move_ticks=before_stats[2],
                     receipt_count=len(r.receipts),
                     damage_trace=traces.get(g.combat.stage_instance_id,[]))
            rows.append(row)
            for receipt in r.receipts:r.verify_receipt(receipt)
            if g.state is GameState.UPGRADE:
                assert len(r.receipts)==(g.stage_number-1)%5
                offer=flow.sync_offer();assert flow.sync_offer() is offer
                kind=choice(style,g.stage_number,len(r.receipts))
                choices.append(dict(stage=g.stage_number,choice=kind))
                new,_=flow.choose(offer,kind,main._new_stage_game)
                assert flow.run is r and new.player.health is not g.player.health
                assert new.player.health.current_hp==result[3]+(kind=='hp')
                assert len(r.receipts)==row['receipt_count']+1 and r.active_offer is None
                try:flow.choose(offer,kind,main._new_stage_game)
                except ValueError:pass
                else:raise AssertionError('Duplicate offer accepted')
                fresh(new)
            elif g.state is GameState.BOSS_CLEAR and g.stage_number<25:
                assert len(r.receipts)==4 and flow.sync_offer() is None
                attack_level=r.build.attack_level
                new,_=flow.enter_next_chapter(main._new_stage_game)
                assert r.retired and flow.run is not r
                assert flow.run.entry_attack_level==attack_level
                assert (new.player.health.current_hp,new.player.health.max_hp,
                        flow.run.stats.move_interval_ticks,len(flow.run.receipts))==(3,3,18,0)
                transitions.append([g.stage_number,new.stage_number]);fresh(new)
            else:
                break
        summary=[summarize(o) for o in observations.values()]
    terminal=flow.game
    post={}
    if terminal.state is GameState.GAME_OVER:
        old=flow.run
        new,_=flow.restart(main._new_stage_game)
        assert old.retired and new.stage_number==(old.chapter-1)*5+1
        assert (new.player.health.current_hp,flow.run.stats.move_interval_ticks,
                len(flow.run.receipts))==(3,18,0)
        assert flow.run.entry_attack_level==old.entry_attack_level
        fresh(new);post=dict(kind='restart_only_not_continued',stage=new.stage_number)
    elif terminal.state is GameState.BOSS_CLEAR:
        assert terminal.stage_number==25 and len(flow.run.receipts)==4
        assert flow.sync_offer() is None and terminal.next_stage_number is None
        try:flow.enter_next_chapter(main._new_stage_game)
        except ValueError:pass
        else:raise AssertionError('Chapter6 accepted')
        old=flow.run;new,_=flow.restart(main._new_stage_game)
        assert flow.run is old and len(old.receipts)==4
        assert new.player.health.current_hp==old.stats.max_hp
        fresh(new);post=dict(kind='boss_replay_only_not_refought',stage=new.stage_number)
    return dict(style=style,scope='chapter5_synthetic_entry' if chapter5_only else 'stage1_actual_campaign',
                rows=rows,choices=choices,transitions=transitions,observation=summary,
                completed=terminal.state is GameState.BOSS_CLEAR and terminal.stage_number==25,
                last_stage=terminal.stage_number,last_cleared_stage=max(
                    (r['stage'] for r in rows if r['result'] in ('UPGRADE','BOSS_CLEAR')),default=0),
                post_run_check=post)


def run():
    baseline=json.loads((ROOT/'docs/BALANCE_STAGE25.json').read_text(encoding='utf-8'))
    independent=[];factory=main._new_stage_game
    for stage in range(1,26):
        for style in STYLES:
            metadata={}
            def capture(n,**kw):
                stats=kw['stats'];metadata.update(max_hp=stats.max_hp,move_ticks=stats.move_interval_ticks)
                return factory(n,**kw)
            with patch.object(main,'_new_stage_game',capture):
                row=measure(style,stage,limit=3600)
            independent.append(dict(battle=row,**metadata))
    assert json.loads(json.dumps(independent))==baseline['independent']
    campaigns=[campaign(s) for s in STYLES]
    chapter5=[campaign(s,chapter5_only=True) for s in STYLES]
    for actual,old in zip(chapter5,baseline['continuous']):
        for a,b in zip(actual['rows'],old['rows']):
            assert all(a[k]==v for k,v in b.items())
        assert len(actual['rows'])==len(old['rows'])
        assert json.loads(json.dumps(actual['observation']))==old['observation']
    return dict(independent_equal_to='BALANCE_STAGE25.json',independent=independent,
                campaigns=campaigns,chapter5=chapter5)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    result=run()
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Independent100 exact match; clears95/100; Chapter5 historical rows exact match')
    for row in result['campaigns']:
        print(row['style'],row['completed'],'last',row['last_stage'],
              'last_clear',row['last_cleared_stage'],row['transitions'])
