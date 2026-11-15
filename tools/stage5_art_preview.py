"""Frozen Stage5 design review; never patches or replaces live game renderers.

1..6 choose an authentic combat snapshot, B switches original/design,
F11 uses the existing fullscreen adapter, SETTINGS uses the existing menu.
This is a rendering review, not a playable campaign or a timing demonstration.
"""
import argparse
import ctypes
from dataclasses import dataclass
import gc
import json
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter, sleep

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main as game_main
from attack_renderer import AttackRenderer
from board import is_light_tile, tile_bounds
from config import BOARD_LEFT, BOARD_BOTTOM, BOARD_RIGHT, BOARD_TOP, TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT, cell_center
from display_settings import DisplaySettings, logical_mouse_to_canvas
from enemy_attack_renderer import EnemyAttackRenderer
from enemy_renderer import EnemyRenderer
from game_renderer import GameFlowRenderer
from health_renderer import HealthRenderer
from parry_renderer import ParryRenderer, ParryResultRenderer
from player import DIRECTIONS
from player_renderer import PlayerRenderer
from renderer import BoardRenderer
from settings_menu import SettingsMenu
from settings_renderer import SettingsRenderer

SCENARIOS = ('normal', 'player_attack', 'enemy_warning', 'parry_normal', 'parry_perfect', 'pulse')
ASSET_DIR = ROOT / 'assets/art_samples/stage5_r2'
REQUIRED_ASSETS = ('player', 'pawn', 'rook', 'king', 'tile_light', 'tile_dark')
BODY_SIZE = {'player': 64, 'pawn': 52, 'rook': 64, 'king': 68}


@dataclass
class Scene:
    name: str
    game: object
    player_attack: object = None


def make_scene(name):
    """Run the original Stage5 AI to a real snapshot; do not fabricate results."""
    if name not in SCENARIOS:
        raise ValueError('Unknown frozen scenario')
    g = game_main._new_stage_game(5)
    if name == 'player_attack':
        return Scene(name, g, g.combat.request_attack(g.player))
    if name in ('enemy_warning', 'parry_normal', 'parry_perfect'):
        rook = next(e for e in g.encounter.enemies if e.kind == 'rook')
        while g.playing and rook.current_attack is None and g.combat.tick < 900:
            g.advance()
        event = rook.current_attack
        if event is None:
            raise RuntimeError('Original Stage5 did not issue a Rook warning')
        if name.startswith('parry_'):
            delta = 18 if name == 'parry_normal' else 7
            g.advance(event.hit_tick - delta - g.combat.tick)
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            g.advance(delta)
            expected = 'normal' if delta == 18 else 'perfect'
            if g.resolver.last_parry_result.status != expected:
                raise RuntimeError('Parry fixture failed genuine adjudication')
    elif name == 'pulse':
        while g.playing and g.encounter.pulse.event is None and g.combat.tick < 900:
            g.advance()
        event = g.encounter.pulse.event
        if event is None:
            raise RuntimeError('Original Stage5 did not issue a Pulse')
        g.advance(60)
    return Scene(name, g)


def snapshot(scene):
    g = scene.game
    return dict(scenario=scene.name, tick=g.combat.tick, state=g.state.value,
                player=dict(cell=g.player.position, facing=g.player.facing, hp=g.player.health.current_hp),
                enemies=[dict(id=e.data_id, kind=e.kind, cell=e.position, hp=e.health.current_hp,
                              state=e.state, next_tick=e.next_action_tick) for e in g.encounter.enemies],
                events=[dict(source=next(e.data_id for e in g.encounter.enemies if e.entity_instance_id==r.event.source_entity_instance_id),
                             kind=r.event.attack_kind, cells=r.event.target_cells, state=r.state,
                             hit=r.event.hit_tick, outcome=r.outcome)
                        for r in g.encounter.ledger._records.values()],
                parry=None if g.resolver.last_parry_result is None else dict(
                    status=g.resolver.last_parry_result.status, cell=g.resolver.last_parry_result.player_cell,
                    tick=g.resolver.last_parry_result.tick))


class ArtResources:
    """Pico2D Image resources are loaded once; __del__ owns texture destruction."""
    def __init__(self, canvas, directory=ASSET_DIR):
        self.images = {}
        self.load_count = 0
        paths = {name: Path(directory)/(name+'.png') for name in REQUIRED_ASSETS}
        missing = [str(p) for p in paths.values() if not p.is_file()]
        if missing:
            raise FileNotFoundError('Art sample assets missing: '+', '.join(missing)+'; use --baseline-only while awaiting assets')
        try:
            for name, path in paths.items():
                self.images[name] = canvas.load_image(str(path))
                self.load_count += 1
            path = Path(directory)/'background.png'
            if path.is_file():
                self.images['background'] = canvas.load_image(str(path))
                self.load_count += 1
        except Exception:
            self.close()
            raise

    def close(self):
        self.images.clear()
        gc.collect()  # Destroy Image textures before the native renderer closes.


class SampleRenderer:
    def __init__(self, canvas, resources=None):
        self.canvas, self.resources = canvas, resources
        self.board = BoardRenderer(chapter=1)
        self.player = PlayerRenderer()
        self.enemies = EnemyRenderer()
        self.enemy_attack = EnemyAttackRenderer()
        self.attack = AttackRenderer()
        self.parry = ParryRenderer()
        self.parry_result = ParryResultRenderer()
        self.health = HealthRenderer()
        self.flow = GameFlowRenderer()

    def draw_art_board(self):
        c = self.canvas
        images = self.resources.images
        if 'background' in images:
            images['background'].draw(WINDOW_WIDTH/2, WINDOW_HEIGHT/2, WINDOW_WIDTH, WINDOW_HEIGHT)
        else:
            c.draw_rectangle(0,0,WINDOW_WIDTH-1,WINDOW_HEIGHT-1,10,16,28,filled=True)
        # Raised slab: cast shadow, bevelled metal rim and recessed board bed.
        # All depth stays outside the unchanged playable rectangle.
        c.draw_rectangle(BOARD_LEFT-18,BOARD_BOTTOM-25,BOARD_RIGHT+24,BOARD_TOP+15,5,8,13,filled=True)
        for inset, color in ((22,(43,34,25)),(20,(124,99,61)),(14,(81,61,36)),(8,(25,27,34)),(4,(8,13,20))):
            c.draw_rectangle(BOARD_LEFT-inset,BOARD_BOTTOM-inset,BOARD_RIGHT+inset-1,BOARD_TOP+inset-1,*color,filled=True)
        for offset, bright, shade in ((20,(209,184,126),(45,34,23)),(19,(179,151,96),(54,41,26)),(15,(148,119,73),(37,29,23)),(8,(15,20,27),(108,88,58))):
            l,b,r,t=BOARD_LEFT-offset,BOARD_BOTTOM-offset,BOARD_RIGHT+offset-1,BOARD_TOP+offset-1
            c.draw_line(l,t,r,t,*bright);c.draw_line(l,b,l,t,*bright)
            c.draw_line(l,b,r,b,*shade);c.draw_line(r,b,r,t,*shade)
        for col in range(10):
            for row in range(10):
                x,y=cell_center(col,row)
                images['tile_light' if is_light_tile(col,row) else 'tile_dark'].draw(x,y,84,84)
                l,b,r,t=tile_bounds(col,row)
                c.draw_rectangle(l,b,r-1,t-1,39,39,46)
        for x in (BOARD_LEFT-12, BOARD_RIGHT+12):
            for y in (BOARD_BOTTOM-12, BOARD_TOP+12):
                c.draw_line(x-5,y,x,y+5,215,184,111)
                c.draw_line(x,y+5,x+5,y,215,184,111)
                c.draw_line(x+5,y,x,y-5,215,184,111)
                c.draw_line(x,y-5,x-5,y,215,184,111)

    def sprite(self, kind, cell):
        x,y=cell_center(*cell)
        self.resources.images[kind].draw(x,y-6,BODY_SIZE[kind],BODY_SIZE[kind])

    def facing(self, cell, facing):
        x,y=cell_center(*cell);dx,dy=DIRECTIONS[facing]
        tip=(x+dx*38,y+dy*38);base=(x+dx*30,y+dy*30)
        a=(base[0]-dy*5,base[1]+dx*5);b=(base[0]+dy*5,base[1]-dx*5)
        for start,end in ((a,tip),(tip,b),(b,a)):
            self.canvas.draw_line(*start,*end,9,19,31)
            self.canvas.draw_line(start[0]+1,start[1],end[0]+1,end[1],110,208,245)

    def draw(self, scene, *, art=False):
        c,g=self.canvas,scene.game
        if art and self.resources is None:
            raise RuntimeError('Design assets have not been loaded')
        if art:self.draw_art_board()
        else:self.board.draw(c)
        self.enemy_attack.tick=g.combat.tick
        self.enemy_attack.source_cells={e.entity_instance_id:e.position for e in g.encounter.enemies if e.active}
        self.enemy_attack.draw(c,g.encounter.ledger)
        self.attack.draw(c,scene.player_attack)
        if art:
            for e in g.encounter.enemies:
                if e.active:self.sprite(e.kind,e.position)
            self.sprite('player',g.player.position);self.facing(g.player.position,g.player.facing)
        else:
            self.enemies.draw(c,g.encounter.enemies);self.player.draw(c,g.player)
        self.parry.draw(c,g.player,g.parry,g.combat.tick)
        self.health.draw(c,g.player,g.encounter.enemies,g.combat.tick,g.combat.pending_attack_bonus)
        self.parry_result.draw(c,g.resolver.last_parry_result,g.combat.tick)
        self.flow.draw_stage_label(c,g)
        # Art-only review label sits below the existing King HUD. The original
        # game still occludes this result label; do not patch that live UI here.
        result=g.resolver.last_parry_result
        if (art and result is not None and result.successful
                and 0 <= g.combat.tick-result.tick < ParryResultRenderer.FEEDBACK_TICKS):
            label='PERFECT PARRY' if result.status=='perfect' else 'PARRY SUCCESS'
            color=ParryResultRenderer.PERFECT if result.status=='perfect' else ParryResultRenderer.NORMAL
            c.draw_rectangle(30,492,270,526,17,22,27,filled=True)
            HealthRenderer._text(c,label,44,505,scale=3,color=color)
        text=HealthRenderer._text
        for label,y in ((('ART DESIGN SAMPLE' if art else 'ORIGINAL RENDERERS'),475),
                        ('STILL COMBAT SNAPSHOT',453),(scene.name.upper().replace('_',' '),431),
                        (f'TICK {g.combat.tick}',409),('1 TO 6 SCENES',367),('B COMPARE',345),
                        ('F11 DISPLAY',323),('NOT LIVE GAMEPLAY',301)):
            text(c,label,30,y,scale=2)

    def contact_sheet(self):
        c=self.canvas
        c.draw_rectangle(0,0,1439,899,10,16,28,filled=True)
        text=HealthRenderer._text
        text(c,'STAGE 5 ART SCALE STUDY',100,837,scale=5)
        text(c,'EACH CELL 84PX  BODY 52 TO 68PX  NOT COMBAT',100,795,scale=3)
        for label,x in (('LIGHT TILE',530),('DARK TILE',745),('SILHOUETTE',975)):
            text(c,label,x-40,733,scale=3)
        for index,kind in enumerate(('player','pawn','rook','king')):
            y=650-index*135
            text(c,kind.upper(),150,y-7,scale=4)
            for x,variant in ((530,'tile_light'),(745,'tile_dark'),(1000,'tile_light')):
                self.resources.images[variant].draw(x,y,84,84)
                c.draw_rectangle(x-42,y-42,x+41,y+41,172,145,87)
                pic=self.resources.images[kind]
                if x==1000:c.SDL_SetTextureColorMod(pic.texture,0,0,0)
                try:pic.draw(x,y-6,BODY_SIZE[kind],BODY_SIZE[kind])
                finally:
                    if x==1000:c.SDL_SetTextureColorMod(pic.texture,255,255,255)
        text(c,'PLAYER FACING MARKERS',100,100,scale=3)
        for index,facing in enumerate(DIRECTIONS):
            x=530+index*150;y=83
            self.resources.images['tile_dark'].draw(x,y,84,84)
            self.resources.images['player'].draw(x,y-6,64,64)
            # Translate grid-only facing convention to a contact-sheet pixel cell.
            dx,dy=DIRECTIONS[facing]
            c.draw_circle(x+dx*36,y+dy*36,3,110,208,245)


def capture_png(canvas, path):
    import sdl2 as s
    from sdl2.sdlimage import IMG_SavePNG
    surface=s.SDL_CreateRGBSurfaceWithFormat(0,WINDOW_WIDTH,WINDOW_HEIGHT,32,s.SDL_PIXELFORMAT_RGBA32)
    if not surface:raise RuntimeError('Cannot allocate SDL capture surface')
    try:
        if s.SDL_RenderReadPixels(canvas.renderer,None,s.SDL_PIXELFORMAT_RGBA32,surface.contents.pixels,surface.contents.pitch)!=0:
            raise RuntimeError('Cannot read SDL render pixels')
        if IMG_SavePNG(surface,str(path).encode('utf-8'))!=0:raise RuntimeError('Cannot save PNG: '+str(path))
    finally:s.SDL_FreeSurface(surface)


def open_preview(canvas, *, capture=False):
    # Pico2D 1.5.1 accelerated open_canvas does not reliably fall back from a
    # ctypes NULL renderer on SDL dummy. Own this preview-only native lifecycle.
    if canvas.SDL_Init(canvas.SDL_INIT_VIDEO | canvas.SDL_INIT_EVENTS) != 0:
        raise RuntimeError('Cannot initialize preview SDL video')
    canvas.IMG_Init(canvas.IMG_INIT_PNG)
    canvas.TTF_Init()
    canvas.audio_on = False
    canvas.canvas_width, canvas.canvas_height = WINDOW_WIDTH, WINDOW_HEIGHT
    flags = canvas.SDL_WINDOW_HIDDEN if capture else canvas.SDL_WINDOW_SHOWN
    canvas.window = canvas.SDL_CreateWindow(b'CHECKMATE ART REVIEW', 0, 0,
                                             WINDOW_WIDTH, WINDOW_HEIGHT, flags)
    render_flags = canvas.SDL_RENDERER_SOFTWARE if capture else canvas.SDL_RENDERER_ACCELERATED
    canvas.renderer = canvas.SDL_CreateRenderer(canvas.window, -1, render_flags)
    if not canvas.renderer and not capture:
        canvas.renderer = canvas.SDL_CreateRenderer(canvas.window, -1, canvas.SDL_RENDERER_SOFTWARE)


def run(args):
    from pico2d import pico2d as c
    resources=settings=None
    try:
        open_preview(c, capture=bool(args.capture_dir))
        if not c.window or not c.renderer:raise RuntimeError('Cannot create SDL preview renderer')
        c.hide_lattice();c.SDL_SetWindowTitle(c.window,b'CHECKMATE STAGE 5 ART REVIEW - FROZEN SNAPSHOTS')
        display=DisplaySettings(c);menu=SettingsMenu();settings=SettingsRenderer(c)
        if not args.baseline_only:resources=ArtResources(c,args.assets)
        renderer=SampleRenderer(c,resources)
        scenes=[make_scene(name) for name in SCENARIOS]
        original=[snapshot(scene) for scene in scenes]
        if args.capture_dir:
            out=Path(args.capture_dir);out.mkdir(parents=True,exist_ok=True)
            records=[]
            for scene in scenes:
                for art in ((False,) if args.baseline_only else (False,True)):
                    elapsed=[]
                    for _ in range(args.benchmark_frames):
                        start=perf_counter();renderer.draw(scene,art=art);settings.draw(menu,display)
                        elapsed.append((perf_counter()-start)*1000)
                    name=('art_' if art else 'original_')+scene.name+'.png'
                    capture_png(c,out/name);c.update_canvas()
                    elapsed.sort()
                    records.append(dict(file=name,render_work_mean_ms=mean(elapsed),render_work_p95_ms=elapsed[max(0,__import__('math').ceil(.95*len(elapsed))-1)],render_work_p99_ms=elapsed[max(0,__import__('math').ceil(.99*len(elapsed))-1)],render_work_max_ms=max(elapsed),samples=len(elapsed)))
            if resources:
                renderer.contact_sheet();capture_png(c,out/'contact_sheet.png');c.update_canvas()
            assert original==[snapshot(scene) for scene in scenes], 'Rendering modified combat state'
            import sdl2 as sdl
            info=sdl.SDL_RendererInfo()
            backend={}
            if sdl.SDL_GetRendererInfo(c.renderer,ctypes.byref(info))==0:
                backend=dict(video_driver=sdl.SDL_GetCurrentVideoDriver().decode('utf-8'),renderer=info.name.decode('utf-8'),flags=info.flags,vsync=bool(info.flags&sdl.SDL_RENDERER_PRESENTVSYNC))
            (out/'capture_manifest.json').write_text(json.dumps(dict(render_backend=backend,width=1440,height=900,tile=84,board=[300,30,840,840],frozen_snapshots=original,textures_loaded=0 if resources is None else resources.load_count,render_cost_only_not_live_fps=records),indent=2)+'\n',encoding='utf-8')
            print('Captured frozen SDL snapshots; combat unchanged; '+str(out))
            return
        active=0;art=not args.baseline_only;running=True
        while running:
            for event in c.get_events():
                if event.type==c.SDL_QUIT:running=False
                elif event.type==c.SDL_KEYDOWN:
                    if event.key==c.SDLK_ESCAPE:
                        if menu.is_open:menu.is_open=False
                        else:running=False
                    elif event.key==c.SDLK_F11:display.toggle()
                    elif not menu.is_open:
                        if c.SDLK_1<=event.key<=c.SDLK_6:active=event.key-c.SDLK_1
                        elif event.key==c.SDLK_b and resources:art=not art
                elif event.type==c.SDL_MOUSEBUTTONDOWN and event.button==c.SDL_BUTTON_LEFT:
                    action=menu.click(logical_mouse_to_canvas(event.x,event.y))
                    if action=='toggle_fullscreen':display.toggle()
            renderer.draw(scenes[active],art=art);settings.draw(menu,display);c.update_canvas();sleep(1/180)
        assert original==[snapshot(scene) for scene in scenes], 'Rendering modified combat state'
    finally:
        if settings is not None:settings.close()
        if resources is not None:resources.close()
        c.close_canvas()
        c.window = c.renderer = None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,default=ASSET_DIR)
    parser.add_argument('--capture-dir',type=Path)
    parser.add_argument('--baseline-only',action='store_true')
    parser.add_argument('--benchmark-frames',type=int,default=30,help='frozen draw work samples per mode; not gameplay FPS')
    args=parser.parse_args()
    if not 1<=args.benchmark_frames<=600:parser.error('benchmark frames must be 1..600')
    try:run(args)
    except FileNotFoundError as error:parser.exit(2,str(error)+'\n')


if __name__=='__main__':main()
