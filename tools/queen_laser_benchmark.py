"""Explicit dummy/software SDL comparison against the preserved Task2-F renderer."""
from pathlib import Path
import sys, os, subprocess, statistics
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import sdl2 as s
from pico2d import pico2d as c
from enemy_attack_renderer import EnemyAttackRenderer
from enemy_attack import EnemyAttackLedger
from tests.test_queen import fixture

BASE='326fae6491b42bdae4694c8b3baac7bbebb91ae1'


def run(iterations=200):
    namespace={};exec(subprocess.check_output(['git','show',BASE+':enemy_attack_renderer.py'],encoding='utf-8'),namespace)
    geo={};exec(subprocess.check_output(['git','show',BASE+':queen_behavior.py'],encoding='utf-8'),geo)
    assert s.SDL_Init(s.SDL_INIT_VIDEO)==0
    c.window=s.SDL_CreateWindow(b'Laser cost',0,0,1440,900,s.SDL_WINDOW_HIDDEN)
    c.renderer=s.SDL_CreateRenderer(c.window,-1,s.SDL_RENDERER_SOFTWARE)
    c.canvas_width,c.canvas_height=1440,900
    assert c.window and c.renderer
    try:
        for two in (False,True):
            g,q,event=fixture(two=two);old=EnemyAttackLedger()
            for e in g.encounter.enemies:
                old.create(e.entity_instance_id,0,72,geo['diagonal_targets'](e.position,g.player.position,{x.position for x in g.encounter.enemies if x is not e}),attack_kind='queen_diagonal')
            r=EnemyAttackRenderer();r.source_cells={e.entity_instance_id:e.position for e in g.encounter.enemies};r.tick=60
            cases=[('old4_charge',namespace['EnemyAttackRenderer'](),old,60),('new8_charge',r,g.encounter.ledger,60)]
            def measure(renderer,ledger):
                samples=[]
                for _ in range(iterations):
                    s.SDL_SetRenderDrawColor(c.renderer,0,0,0,255);s.SDL_RenderClear(c.renderer)
                    start=perf_counter();renderer.draw(c,ledger);s.SDL_RenderPresent(c.renderer)
                    samples.append((perf_counter()-start)*1000)
                return statistics.mean(samples),sorted(samples)[int(.95*(len(samples)-1))]
            for name,renderer,ledger,tick in cases:
                renderer.tick=tick;mean,p95=measure(renderer,ledger)
                print(f'queens={2 if two else 1} {name} mean_ms={mean:.4f} p95_ms={p95:.4f}')
            g.advance(72)
            for name,tick in (('new8_fire',72),('new8_fade',76)):
                r.tick=tick;mean,p95=measure(r,g.encounter.ledger)
                print(f'queens={2 if two else 1} {name} mean_ms={mean:.4f} p95_ms={p95:.4f}')
    finally:
        s.SDL_DestroyRenderer(c.renderer);s.SDL_DestroyWindow(c.window);s.SDL_Quit()


if __name__=='__main__':run()
