"""Explicit developer preview, never a StageGame or an unlock of Stage13."""
import argparse
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from chapter_run import ChapterRun
from combat import Combat
from combat_balance import profile_for
from combat_resolution import CombatResolver
from enemy import Enemy
from enemy_behaviors import EnemyEncounter
from game import GameState
from health_renderer import HealthRenderer
from parry import Parry
from player import Player


class PreviewCombat:
    """Terminal lifecycle only; existing resolver and main own all simulation/input."""
    chapter = 3
    stage_number = 0
    boss = False
    next_stage_number = restart_stage_number = None
    upgrade_selection_enabled = False

    def __init__(self, chapter=3, scenario='solo'):
        profile=profile_for(chapter)
        self.chapter=chapter
        self.player,self.combat,self.parry=Player(5,1),Combat(),Parry()
        enemies=[Enemy('preview_queen',4,6,None,0,kind='queen',max_hp=profile.hp('queen'))]
        if scenario in ('mixed','pulse'):
            for kind,x,y in (('rook',1,5),('bishop',8,7),('pawn',7,4)):
                enemies.append(Enemy('preview_'+kind,x,y,(0,-1) if kind=='pawn' else None,.8,
                                     kind=kind,max_hp=profile.hp(kind)))
        if scenario in ('double','pulse'):
            enemies.append(Enemy('preview_queen2',7,7,None,.4,kind='queen',max_hp=profile.hp('queen')))
        if scenario=='pulse':
            enemies.append(Enemy('preview_king',5,9,None,0,kind='king',boss_hp=profile.king))
        self.encounter=EnemyEncounter(enemies,combat_session_id=self.combat.combat_session_id,
                                     stage_instance_id=self.combat.stage_instance_id,boss=scenario=='pulse')
        self.resolver=CombatResolver(self.player,self.combat,self.encounter,parry=self.parry)
        self.state=GameState.PLAYING

    @property
    def playing(self): return self.state is GameState.PLAYING

    def update_state(self):
        if self.playing and (not self.player.alive or all(not e.alive for e in self.encounter.enemies)):
            self.state=GameState.GAME_OVER if not self.player.alive else GameState.STAGE_CLEAR
            self.resolver.stop()

    def resolve_current_tick(self):
        self.update_state()
        result=self.resolver.resolve_current_tick() if self.playing else ()
        self.update_state()
        return result

    def advance(self,ticks=1):
        result=list(self.resolve_current_tick())
        for _ in range(ticks):
            if not self.playing:break
            self.combat.advance();result.extend(self.resolve_current_tick())
        return tuple(result)


class PreviewFlow:
    offer=None
    error=False
    def __init__(self,chapter):self.run=ChapterRun(chapter)
    def sync_offer(self):return None


class PreviewRenderer:
    def draw_stage_label(self,canvas,game):
        text=HealthRenderer._text
        text(canvas,'QUEEN DEV PREVIEW',24,862,scale=3)
        text(canvas,'NOT STAGE 13',24,833)
        text(canvas,f'TICK {game.combat.tick}',24,805)
        y=770
        for e in game.encounter.enemies:
            if e.kind=='queen':
                text(canvas,f'QUEEN HP {e.health.current_hp}/{e.health.max_hp}',24,y)
                text(canvas,game.encounter.queen_steps[e.entity_instance_id].upper().replace('_',' '),24,y-24)
                if e.current_attack:text(canvas,e.current_attack.attack_kind.upper().replace('_',' '),24,y-48)
                y-=90
    def draw(self,canvas,game,error=False):
        if not game.playing:
            HealthRenderer._text(canvas,'PREVIEW '+game.state.value.replace('_',' '),350,680,scale=4)
            HealthRenderer._text(canvas,'ESC TO EXIT',350,640,scale=3)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chapter',type=int,choices=(3,4,5),default=3)
    parser.add_argument('--scenario',choices=('solo','mixed','double','pulse'),default='solo')
    args=parser.parse_args()
    from main import run_session
    run_session(PreviewCombat(args.chapter,args.scenario),PreviewFlow(args.chapter),game_renderer=PreviewRenderer())


if __name__=='__main__':main()
