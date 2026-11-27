"""Measure four upgrade priorities in continuous runs and independent battles."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import _new_stage_game
from stage_progression import StageProgression
from tests.balance_driver import measure
from tests.test_hp_carryover import fight
from upgrades import ChapterBuild, UPGRADE_VALUES, UpgradeKind


PRIORITIES = {
    'attack': ('attack', 'hp', 'move'),
    'health': ('hp', 'attack', 'move'),
    'mobility': ('move', 'attack', 'hp'),
    'balanced': ('attack', 'hp', 'move'),
}


def choice(style, build, earned):
    priority = PRIORITIES[style]
    if style == 'balanced':
        offset = earned % len(priority)
        priority = priority[offset:] + priority[:offset]
    return next(kind for kind in priority
                if build.level(kind) + 1 < len(UPGRADE_VALUES[UpgradeKind(kind)]))


def ledger_receipts(game):
    return Counter(record.outcome for record in game.encounter.ledger._records.values())


def campaign(style, policy):
    flow = StageProgression(_new_stage_game(1))
    rows, choices = [], []
    while True:
        game = flow.game
        build = flow.run.build
        stats = build.stats
        start_hp = game.player.health.current_hp
        if (game.stage_number - 1) % 5 == 0:
            assert start_hp == stats.max_hp
        stage, result, ticks, hp, _ = fight(flow, guard=policy == 'guard')
        outcomes = ledger_receipts(game)
        rows.append(dict(stage=stage, result=result, ticks=ticks, start_hp=start_hp, hp=hp, damage=start_hp-hp,
                         perfect=outcomes['parried_perfect'], normal=outcomes['parried_normal'],
                         **asdict(stats)))
        if result == 'UPGRADE':
            kind = choice(style, build, len(choices))
            choices.append(kind)
            flow.choose(flow.sync_offer(), kind, _new_stage_game)
            assert flow.game.player.health.current_hp == hp + (kind == 'hp')
        elif result == 'BOSS_CLEAR' and stage < 25:
            flow.enter_next_chapter(_new_stage_game)
            assert flow.run.entry_build == build and not flow.run.receipts
        else:
            return dict(style=style, policy=policy, rows=rows, choices=choices,
                        completed=stage == 25 and result == 'BOSS_CLEAR')


def independent(style, policy):
    build = ChapterBuild()
    earned = 0
    rows = []
    for stage in range(1,26):
        rows.append(measure(style, stage, current=True, policy=policy, build=build))
        if stage % 5:
            build = build.upgraded(choice(style, build, earned))
            earned += 1
    return dict(style=style, policy=policy, rows=rows)


def run():
    scenarios = [(style,policy) for style in PRIORITIES for policy in ('pursue','guard')]
    return dict(campaigns=[campaign(style, policy) for style,policy in scenarios],
                independent=[independent(style, policy) for style,policy in scenarios])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    result = run()
    parser.parse_args().output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    for row in result['campaigns']:
        print(row['style'],row['policy'],len(row['rows']),row['rows'][-1]['result'],Counter(row['choices']))
