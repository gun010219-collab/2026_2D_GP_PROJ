"""Temporary, resource-free outcome overlay; settings are rendered above it."""
from game import GameState
from health_renderer import HealthRenderer
from config import WINDOW_HEIGHT, WINDOW_WIDTH
from settings_menu import Rect
from ui_theme import PALE, ROSE, current


class GameFlowRenderer:
    def __init__(self, *, official=False):
        self.official = official

    def draw(self, canvas, game, error=False):
        if game.playing:
            return
        theme = current(canvas)
        if theme:
            self._draw_themed(theme,game,error)
            return
        if self.official and game.stage_number == 25 and game.state is GameState.BOSS_CLEAR:
            self._center(canvas,'FINAL BOSS DEFEATED',65,3,(224,192,116))
            return
        boundary = game.state is GameState.DEV_BOUNDARY or (game.state is GameState.UPGRADE and not game.upgrade_selection_enabled)
        clear = boundary or game.state in (GameState.UPGRADE, GameState.STAGE_CLEAR, GameState.BOSS_CLEAR)
        accent = (224, 192, 116) if clear else (196, 112, 107)
        x, y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
        canvas.draw_rectangle(x - 300, y - 165, x + 300, y + 165, *accent, filled=True)
        canvas.draw_rectangle(x - 296, y - 161, x + 296, y + 161, 17, 20, 28, filled=True)
        if game.stage_number == 25 and game.state is GameState.BOSS_CLEAR:
            for label, row, scale in (('CHECKMATE', 558, 6), ('ALL 25 STAGES CLEARED', 516, 3),
                                      ('FINAL BOSS DEFEATED', 475, 3), ('R TO REPLAY BOSS', 399, 3),
                                      ('ESC TO EXIT', 343, 3), ('SETTINGS / F11', 310, 2)):
                self._center(canvas, label, row, scale, accent)
            if error:
                self._center(canvas, 'COULD NOT START STAGE  TRY AGAIN', 268, 2, (231, 130, 115))
            return
        title = (f'STAGE {game.stage_number} CLEAR' if boundary else 'UPGRADE' if game.state is GameState.UPGRADE else
                 'BOSS CLEAR' if game.state is GameState.BOSS_CLEAR else 'STAGE CLEAR' if clear else 'GAME OVER')
        self._center(canvas, title, 558, 6, accent)
        self._center(canvas, f'CHAPTER {game.chapter} DEVELOPMENT' if boundary else f'STAGE {game.stage_number}',
                     516, 3, (225, 218, 197))
        health = game.player.health
        self._center(canvas, f'HP {health.current_hp}/{health.max_hp}', 475, 4, (231, 230, 220))
        alive = sum(enemy.alive for enemy in game.encounter.enemies)
        label = 'PAWNS' if all(e.kind == 'pawn' for e in game.encounter.enemies) else 'ENEMIES'
        self._center(canvas, f'{label} LEFT {alive}/{len(game.encounter.enemies)}', 439, 3,
                     (202, 204, 209))
        if game.next_stage_number is not None:
            self._center(canvas, f'N TO CHAPTER {game.chapter + 1}', 409, 3, (224, 192, 116))
        if boundary:
            self._center(canvas, f'STAGE {game.stage_number + 1} NOT AVAILABLE', 399, 3, (224, 192, 116))
        restart = ('R TO RESTART' if game.restart_stage_number == game.stage_number
                   else f'R TO STAGE {game.restart_stage_number}')
        if game.restart_stage_number is not None:
            self._center(canvas, restart, 384, 4, (224, 192, 116))
        hint = 'ESC TO MAIN MENU' if self.official else 'ESC TO EXIT'
        self._center(canvas,hint,343,3,(213,214,218))
        self._center(canvas, 'SETTINGS / F11', 310, 2, (180, 184, 193))
        if error:
            self._center(canvas, 'COULD NOT START STAGE  TRY AGAIN', 268, 2, (231, 130, 115))

    def draw_stage_label(self, canvas, game):
        """Small live stage label in the left margin; no outcome panel."""
        if game.playing:
            theme = current(canvas)
            if theme:
                theme.combat_frame('stage',30,848)
                theme.text(f'CHAPTER {game.chapter:02}',48,870,size=17,align='left',color=PALE)
                theme.text(f'Stage {game.stage_number:02}',258,870,size=25,display=True,align='right')
                if game.boss:
                    self._themed_boss(theme,game)
                if self.official:
                    theme.text('L CTRL  ·  ATTACK',34,104,size=17,align='left',color=PALE)
                    theme.text('L ALT  ·  PARRY',34,82,size=17,align='left',color=PALE)
                return
            HealthRenderer._text(canvas, f'STAGE {game.stage_number}', 44, 862, scale=3)
            if game.boss:
                self._draw_boss(canvas, game)
            if self.official:
                HealthRenderer._text(canvas,'L CTRL ATTACK',44,101)
                HealthRenderer._text(canvas,'L ALT PARRY',44,82)

    @staticmethod
    def _draw_boss(canvas, game):
        pulse = game.encounter.pulse
        hp = pulse.king.health
        canvas.draw_rectangle(30, 530, 280, 687, 17, 22, 27, filled=True)
        HealthRenderer._text(canvas, f'KING HP {hp.current_hp}/{hp.max_hp}', 44, 660, scale=3)
        color = (255, 156, 65)
        HealthRenderer._text(canvas, 'CHECKMATE PULSE', 44, 629, color=color)
        labels = {'NORMAL': 'READY' if game.combat.tick >= pulse.next_use_tick else 'RECHARGING',
                  'DRAINING': 'WAITING FOR ATTACKS', 'PULSE_TELEGRAPH': 'PARRY THE PULSE',
                  'PULSE_RESOLUTION': 'RESOLVING', 'CLEANUP': 'CLEANUP'}
        label = labels[pulse.state] if hp.alive else 'KING DEFEATED'
        HealthRenderer._text(canvas, label, 44, 602, color=color)
        if pulse.state == 'PULSE_TELEGRAPH':
            left = max(0, pulse.event.hit_tick - game.combat.tick)
            HealthRenderer._text(canvas, f'HIT IN {left} TICKS', 44, 576)
        elif pulse.state == 'CLEANUP' and pulse.resume_tick is not None:
            HealthRenderer._text(canvas, f'RESUME IN {max(0, pulse.resume_tick-game.combat.tick)}', 44, 576)
        if hp.last_damage_tick is not None and 0 <= game.combat.tick-hp.last_damage_tick < 6:
            HealthRenderer._text(canvas, 'KING HIT', 44, 546, color=HealthRenderer.HIT)

    @staticmethod
    def _center(canvas, text, y, scale, color):
        theme = current(canvas)
        if theme:
            theme.text(text,WINDOW_WIDTH/2,y,size=max(17,8*scale),color=color,width=1200)
            return
        width = (len(text) * 4 - 1) * scale
        HealthRenderer._text(canvas, text, WINDOW_WIDTH / 2 - width / 2, y, scale=scale, color=color)

    def _draw_themed(self,theme,game,error):
        if game.state is GameState.UPGRADE and game.upgrade_selection_enabled:
            return
        boss_clear = game.state is GameState.BOSS_CLEAR
        if boss_clear and game.stage_number==25 and self.official:
            theme.combat_frame('final',492,333)
            theme.sprite('crown',Rect(699,467,42,44))
            theme.text('BOSS CLEAR',720,437,size=48,display=True)
            theme.text('Final King defeated',720,397,size=22,color=ROSE)
            return
        lost = game.state is GameState.GAME_OVER
        boundary = game.state in (GameState.DEV_BOUNDARY,GameState.UPGRADE)
        title = 'GAME OVER' if lost else 'CHAPTER CLEAR' if boss_clear and self.official else (
            'BOSS CLEAR' if boss_clear else 'STAGE CLEAR')
        theme.combat_frame('result',411,275)
        theme.sprite('knight' if lost else 'crown',Rect(698,564,44,43))
        theme.text(title,720,537,size=58,display=True,color=ROSE if lost else (241,234,237),width=566)
        caption = 'BOSS CLEAR  ·  KING DEFEATED' if boss_clear and self.official else f'STAGE {game.stage_number:02}'
        theme.text(caption,720,486,size=18,display=True,color=PALE)
        theme.rule(720,461,228)
        hp=game.player.health
        theme.text(f'HP {hp.current_hp}/{hp.max_hp}  ·  Enemies left {sum(e.alive for e in game.encounter.enemies)}',
                   720,433,size=22)
        actions = []
        if game.next_stage_number is not None:
            actions.append(f'N  ·  Chapter {game.chapter+1}')
        if game.restart_stage_number is not None:
            actions.append('R  ·  Replay final boss' if boss_clear and game.stage_number==25
                           else f'R  ·  Stage {game.restart_stage_number}')
        if boundary:
            theme.text(f'Stage {game.stage_number+1} not available',720,397,size=21,color=ROSE)
        theme.text('     '.join(actions),720,372,size=22,color=ROSE)
        theme.text('ESC  ·  Main menu' if self.official else 'ESC  ·  Exit',720,320,size=19,color=PALE)
        if error:
            theme.text('Could not start stage. Try again.',720,248,size=20,color=ROSE)

    @staticmethod
    def _themed_boss(theme,game):
        pulse = game.encounter.pulse
        hp = pulse.king.health
        charging = pulse.state == 'PULSE_TELEGRAPH'
        theme.combat_frame('boss',30,530)
        theme.sprite('crown',Rect(45,637,36,35))
        theme.text('King HP',91,654,size=21,display=True,align='left')
        theme.text(f'{hp.current_hp}/{hp.max_hp}',256,654,size=23,align='right')
        theme.health_bar(hp,49,628,210)
        theme.text('CHECKMATE PULSE',49,607,size=16,display=True,align='left',color=PALE)
        labels = {'NORMAL': 'READY' if game.combat.tick>=pulse.next_use_tick else 'RECHARGING',
                  'DRAINING': 'WAITING FOR ATTACKS','PULSE_TELEGRAPH': 'PARRY THE PULSE',
                  'PULSE_RESOLUTION': 'RESOLVING','CLEANUP': 'CLEANUP'}
        theme.text(labels[pulse.state] if hp.alive else 'KING DEFEATED',49,583,
                   size=21,align='left',color=ROSE if charging else PALE)
        if charging:
            remaining = max(0,pulse.event.hit_tick-game.combat.tick)
            duration = pulse.event.hit_tick-pulse.event.telegraph_start_tick
            theme.fill(Rect(49,554,96,4),(68,46,61))
            progress = round(96*(1-remaining/duration))
            if progress:
                theme.fill(Rect(49,554,progress,4),ROSE)
            theme.text(f'{remaining} ticks',257,556,size=17,align='right',color=ROSE)
        elif pulse.state=='CLEANUP' and pulse.resume_tick is not None:
            theme.text(f'Resume in {max(0,pulse.resume_tick-game.combat.tick)} ticks',46,554,
                       size=18,align='left',color=PALE)
        elif hp.last_damage_tick is not None and 0<=game.combat.tick-hp.last_damage_tick<6:
            theme.text('KING HIT',46,554,size=18,align='left',color=ROSE)
