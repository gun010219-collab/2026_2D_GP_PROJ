"""Read-only pacing observations around unchanged battle/campaign policies.

Candidates patch only EnemyEncounter's imported movement constants in this
process. No config file, health, input policy, AI, or event result is edited.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
import json
from pathlib import Path
import sys
from unittest.mock import patch

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import enemy_behaviors
from combat_resolution import CombatResolver, DamageResult
from tests.balance_driver import measure, STYLES
from tests.test_enemy_hp_rebalance import real_campaign

PROFILES = {'baseline': (2.20,1.20), 'A': (2.10,1.20),
            'B': (2.20,1.15), 'C': (2.10,1.15)}


@contextmanager
def candidate(name):
    pawn, rook = PROFILES[name]
    with patch.object(enemy_behaviors,'PAWN_MOVE_INTERVAL_SECONDS',pawn), \
         patch.object(enemy_behaviors,'ROOK_MOVE_INTERVAL_SECONDS',rook):
        yield


@contextmanager
def observe():
    observations = {}
    resolve = CombatResolver.resolve_current_tick
    enemy_attack = CombatResolver.resolve_enemy_attack

    def sample(self):
        key = self.combat.stage_instance_id
        if key not in observations:
            observations[key] = dict(moves=Counter(),positions={e.entity_instance_id:e.position for e in self.encounter.enemies},damage=[],due=Counter(),resolver=self)
        o = observations[key]
        result = resolve(self)
        for e in self.encounter.enemies:
            if e.position != o['positions'][e.entity_instance_id]:o['moves'][e.data_id] += 1
            o['positions'][e.entity_instance_id] = e.position
        cells = [e.position for e in self.encounter.enemies if e.active]
        assert len(cells)==len(set(cells)), 'Duplicate live occupancy'
        return result

    def adjudicate(self,event):
        o = observations[self.combat.stage_instance_id]
        tick = self.combat.tick
        result = enemy_attack(self,event)
        o['due'][tick] += 1
        if isinstance(result,DamageResult) and result.target_entity_instance_id==self.player.entity_instance_id:
            source=next(e.data_id for e in self.encounter.enemies if e.entity_instance_id==event.source_entity_instance_id)
            o['damage'].append(dict(tick=tick,source=source,kind=event.attack_kind,hp_after=result.hp_after,next_parry_tick=self.parry.next_parry_tick))
        return result

    with patch.object(CombatResolver,'resolve_current_tick',sample),patch.object(CombatResolver,'resolve_enemy_attack',adjudicate):
        yield observations


def summarize(o):
    r=o['resolver']; ledger=r.encounter.ledger
    records=list(ledger._records.values())
    starts=Counter(x.event.telegraph_start_tick for x in records)
    pulse=[dict(start=x.event.telegraph_start_tick,hit=x.event.hit_tick,state=x.state,outcome=x.outcome) for x in records if x.event.attack_kind=='king_pulse']
    return dict(moves=dict(o['moves']),move_count=sum(o['moves'].values()),
                attack_starts=len(records),first_attack_tick=min(starts,default=None),
                simultaneous_starts=sum(n-1 for n in starts.values() if n>1),
                simultaneous_due=sum(n-1 for n in o['due'].values() if n>1),
                cooldown_hits=sum(x['tick']<x['next_parry_tick'] for x in o['damage']),
                damage=o['damage'],pulse=pulse,
                survivors=[(e.data_id,e.health.current_hp) for e in r.encounter.enemies if e.alive])


def run(name):
    independent=[]; campaigns=[]
    with candidate(name):
        for stage in range(1,21):
            for style in STYLES:
                with observe() as records:row=measure(style,stage,limit=3600)
                row['observation']=summarize(next(iter(records.values())))
                independent.append(row)
        for style in STYLES:
            with observe() as records:flow,rows=real_campaign(style)
            campaigns.append(dict(style=style,rows=rows,observation=[summarize(o) for o in records.values()],
                                  stage=flow.game.stage_number,result=flow.game.state.value,tick=flow.game.combat.tick))
    return dict(profile=name,seconds=PROFILES[name],independent=independent,campaigns=campaigns)


def risks(base, trial):
    findings=[]
    for b,t in zip(base['independent'],trial['independent']):
        label=f"S{t['stage']} {t['style']}"
        if b['result']!='GAME_OVER' and t['result']=='GAME_OVER':findings.append(label+': new GAME_OVER')
        if b['result']=='GAME_OVER' and t['result']=='GAME_OVER' and t['ticks']<b['ticks']:findings.append(label+': earlier death')
        if t['received']>b['received'] or t['remaining_hp']<b['remaining_hp']:findings.append(label+': worse damage/remaining HP')
        if t['observation']['cooldown_hits']>b['observation']['cooldown_hits']:findings.append(label+': more hits during parry cooldown')
    for b,t in zip(base['campaigns'],trial['campaigns']):
        if t['stage']<b['stage'] or (t['stage']==b['stage'] and b['result']=='BOSS_CLEAR' and t['result']=='GAME_OVER'):
            findings.append(t['style']+': earlier campaign GAME_OVER')
    return findings


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args();out={}
    for name in PROFILES:
        out[name]=run(name)
        rows=out[name]['independent']
        print(name,sum(r['result'] in ('UPGRADE','BOSS_CLEAR') for r in rows),'/80',flush=True)
        if name!='baseline':out[name]['risks']=risks(out['baseline'],out[name]);print(out[name]['risks'],flush=True)
    Path(args.output).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
