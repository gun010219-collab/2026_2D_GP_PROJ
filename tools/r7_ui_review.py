"""Capture real combat UI states and measure warmed overlay draws at logical 1440×900."""
import argparse
import json
import os
from pathlib import Path
from statistics import median
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from chapter_art_renderer import LiveArenaArtPath
from attack_telegraph import TelegraphRenderer, warning_frame
from display_settings import DisplaySettings
from game_renderer import GameFlowRenderer
from main import _new_stage_game
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer
from stage_progression import StageProgression
from tests.test_hp_carryover import fight
from tools.chapter_art_play import session
from tools.stage5_art_preview import capture_png, open_preview
from ui_theme import current
from upgrade_renderer import UpgradeRenderer


def run(output, *, legacy=False):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    from pico2d import pico2d as canvas

    open_preview(canvas,capture=True)
    settings = art = None
    metrics = {}
    try:
        display, menu = DisplaySettings(canvas), SettingsMenu()
        settings = SettingsRenderer(canvas,themed=not legacy)
        art = LiveArenaArtPath(canvas,default_enabled=True,telegraph=TelegraphRenderer())
        overlay, rewards = GameFlowRenderer(official=True), UpgradeRenderer()
        output.mkdir(parents=True,exist_ok=True)

        def capture(game, name, offer=None):
            def draw_overlay():
                overlay.draw_stage_label(canvas,game)
                overlay.draw(canvas,game)
                if offer is not None:
                    rewards.draw(canvas,game,offer)
                settings.draw(menu,display)

            canvas.SDL_SetRenderDrawColor(canvas.renderer,0,0,0,255)
            canvas.SDL_RenderClear(canvas.renderer)
            assert art.draw(game,{})
            draw_overlay()
            capture_png(canvas,output/(name+'.png'))
            samples = []
            for _ in range(50):
                start = perf_counter_ns()
                draw_overlay()
                canvas.SDL_RenderFlush(canvas.renderer)
                samples.append((perf_counter_ns()-start)/1_000_000)
            samples.sort()
            metrics[name] = dict(median_ms=round(median(samples),4),p95_ms=round(samples[47],4))

        flow = StageProgression(_new_stage_game(1))
        capture(flow.game,'hud')
        assert fight(flow)[1]=='UPGRADE'
        capture(flow.game,'reward',flow.sync_offer())

        game, flow = session(24)
        assert fight(flow)[1]=='UPGRADE'
        offer = flow.sync_offer()
        assert any(option.is_max for option in offer.options)
        capture(game,'reward_max',offer)

        game = _new_stage_game(25)
        while game.playing and game.encounter.pulse.event is None:
            game.advance()
        assert game.playing and game.encounter.pulse.state=='PULSE_TELEGRAPH'
        capture(game,'pulse')
        game.advance(game.encounter.pulse.event.hit_tick-game.combat.tick-7)
        cells, hint = warning_frame(game)
        assert len(cells)==100 and hint.status=='perfect'
        capture(game,'pulse_parry')

        game, flow = session(25)
        assert fight(flow)[1]=='BOSS_CLEAR'
        capture(game,'final_boss')
        theme = current(canvas)
        if theme:
            metrics['cached_resources'] = dict(sprites=len(theme.sprites), fonts=len(theme.fonts),
                                               text=len(theme.textures))
        (output/'overlay_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
        return metrics
    finally:
        if art is not None:
            art.close()
        if settings is not None:
            settings.close()
        canvas.close_canvas()


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--legacy',action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.output,legacy=args.legacy),indent=2))
