"""Opt-in live Stage5 arena. Reads entities/ledger; never constructs a scene."""
import ctypes
import logging
from pathlib import Path
from math import cos,sin,pi
from arena_art_common import CAMERA, ArenaArtError, SessionArtPath, sprite_layout
from board import is_light_tile
from config import BOARD_LEFT,BOARD_BOTTOM,TILE_SIZE
from render_motion import display_center
from health_renderer import HealthRenderer
from display_settings import logical_mouse_to_canvas

LOG=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parent
FILES={'background':'assets/themed_arena/royal.png','frame':'assets/aligned_board/royal_c.png',
       'light':'assets/polished_board/royal_light.png','dark':'assets/polished_board/royal_dark.png',
       **{k:'assets/character_concepts/'+('player' if k=='player' else 'ch1_'+k)+'.png' for k in ('player','pawn','rook','king')}}

# Stage5 presentation candidates only. PNGs, logical footprints and player stay unchanged.
ENEMY_SCALE={'pawn':1.16,'rook':1.11,'king':1.08}
HP_OFFSET={'pawn':7,'rook':8,'king':10,'player':5}
BASE_SIZE={'pawn':60,'rook':72,'king':78,'player':72}


def actor_layout(kind,u,v):
    return sprite_layout(kind,u,v,BASE_SIZE,ENEMY_SCALE,HP_OFFSET)


Stage5ArtError = ArenaArtError


def pick_event(x,y):
    point=logical_mouse_to_canvas(x,y)
    return None if point is None else CAMERA.pick(*point)


def polygon(c,points,color=(255,255,255,255),texture=None):
    import sdl2 as s
    vertices=(s.SDL_Vertex*len(points))();uv=((0,1),(1,1),(1,0),(0,0))
    for i,(x,y) in enumerate(points):
        vertices[i].position=s.SDL_FPoint(x,899-y);vertices[i].color=s.SDL_Color(*color)
        vertices[i].tex_coord=s.SDL_FPoint(*uv[i%4])
    indices=[i for j in range(1,len(points)-1) for i in (0,j,j+1)]
    if s.SDL_RenderGeometry(c.renderer,texture,vertices,len(points),(ctypes.c_int*len(indices))(*indices),len(indices)):
        raise Stage5ArtError('SDL geometry: '+s.SDL_GetError().decode())


def outline(c,points,color):
    for a,b in zip(points,points[1:]+points[:1]):c.draw_line(*a,*b,*color)


def cue_kind(g):
    t=g.combat.tick
    if not g.playing:return 'quiet'
    result=g.resolver.last_parry_result
    if result and result.successful and 0<=t-result.tick<18:
        return 'perfect_success' if result.status=='perfect' else 'parry_success'
    if any(e.attack_kind=='king_pulse' for e in g.encounter.ledger.telegraphs):return 'pulse'
    if g.parry.active_at(t):return 'parry_window'
    if g.encounter.ledger.telegraphs:return 'danger'
    if g.combat.active_attack is not None:return 'player_attack'
    return 'ready' if t>=g.parry.next_parry_tick else 'quiet'


class Stage5ArtRenderer:
    # Stage6 reuses this drawing pipeline through these two presentation hooks.
    files = FILES

    def layout(self,kind,u,v):
        return actor_layout(kind,u,v)

    def pose(self,entity,positions):
        x,y=display_center(entity,positions)
        return (x-BOARD_LEFT)/TILE_SIZE-.5,(y-BOARD_BOTTOM)/TILE_SIZE-.5,0.0

    def __init__(self,c,root=ROOT):
        self.c=c;self.images={};self.warning_cells=[];self.order=[];self.bounds=[]
        try:
            for key,name in self.files.items():
                path=root/name
                if not path.is_file():raise FileNotFoundError(path)
                self.images[key]=c.load_image(str(path))
            if c.SDL_SetTextureColorMod(self.images['background'].texture,190,190,190):raise Stage5ArtError('Background tint failed')
        except BaseException:self.close();raise

    def close(self):
        # Nulling the Pico2D handle makes its later __del__ safe and idempotent.
        for image in self.images.values():
            if image.texture:self.c.SDL_DestroyTexture(image.texture);image.texture=None
        self.images.clear()

    def image(self,key,x,y,w,h):
        import sdl2 as s
        rect=s.SDL_FRect(x-w/2,899-y-h/2,w,h)
        if s.SDL_RenderCopyF(self.c.renderer,self.images[key].texture,None,ctypes.byref(rect)):
            raise Stage5ArtError('SDL texture copy: '+s.SDL_GetError().decode())

    def mark(self,cell,color):
        outline(self.c,CAMERA.tile(*cell),color)
        col,row=cell
        for t in (.15,.35,.55,.75):self.c.draw_line(*CAMERA.project(col+t,row+.12),*CAMERA.project(col+t+.12,row+.24),*color)

    def draw(self,g,positions):
        c=self.c;self.warning_cells=[];self.order=[];self.bounds=[];self.actor_layouts={}
        self.image('background',720,450,1440,900);self.image('frame',720,450,1440,900)
        outer=((- .12,-.12),(10.12,-.12),(10.12,10.12),(-.12,10.12));inner=((0,0),(10,0),(10,10),(0,10))
        for lo,hi,gain in ((0,.18,.76),(.18,.82,1),(.82,1,1.1)):
            def ring(t):return tuple((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for a,b in zip(outer,inner))
            a,b=ring(lo),ring(hi)
            for i in range(4):
                j=(i+1)%4;value=min(255,round(200*gain*(1.05 if i in (2,3) else .94)))
                polygon(c,tuple(CAMERA.project(*p) for p in (a[i],a[j],b[j],b[i])),(value,value,value,255),self.images['light'].texture)
        for col in range(10):
            for row in range(10):polygon(c,CAMERA.tile(col,row),texture=self.images['light' if is_light_tile(col,row) else 'dark'].texture)
        self.cue=cue_kind(g)
        color={'quiet':(80,84,91),'ready':(69,116,136),'player_attack':(137,123,89),'danger':(130,62,74),
               'parry_window':(95,149,166),'parry_success':(88,149,169),'perfect_success':(183,164,109),'pulse':(146,104,59)}[self.cue]
        if self.cue!='quiet':
            for side in range(4):
                intervals=((.46,.54),) if self.cue=='ready' else ((.14,.32),(.68,.86)) if self.cue in ('parry_window','parry_success','player_attack') else ((.025,.975),)
                for start,end in intervals:
                    def rail(t):return ((t*10,-.095),(10.095,t*10),((1-t)*10,10.095),(-.095,(1-t)*10))[side]
                    c.draw_line(*CAMERA.project(*rail(start)),*CAMERA.project(*rail(end)),*color)
        if g.playing:
            for event in g.encounter.ledger.telegraphs:
                for cell in event.target_cells:
                    self.warning_cells.append(tuple(cell));self.mark(cell,(241,144,62) if event.attack_kind=='king_pulse' else (239,88,109))
            if g.combat.active_attack:self.mark(g.combat.active_attack.target_cell,(237,207,113))
        actors=[e for e in g.encounter.enemies if e.active and e.alive]
        if g.player.alive:actors.append(g.player)
        def cell(e):
            return self.pose(e,positions)
        actors.sort(key=lambda e:(-cell(e)[1],cell(e)[0],e.entity_instance_id))
        labels=[]
        for e in actors:
            kind=getattr(e,'kind','player');u,v,lift=cell(e);layout=self.layout(kind,u,v)
            if lift:
                layout={**layout,'center':(layout['center'][0],layout['center'][1]+lift),
                        'top':layout['top']+lift,'hp_y':layout['hp_y']+lift,'elevation':lift}
            x,y=layout['foot'];height=layout['height'];center=layout['center'][1];top=layout['top']
            self.actor_layouts[e.entity_instance_id]=layout
            polygon(c,tuple((x+4+cos(i*pi/4)*height*.24,y-2+sin(i*pi/4)*4) for i in range(8)),(24,25,29,255))
            self.image(kind,x,center,height,height);self.order.append(e.entity_instance_id)
            self.bounds.append((e.entity_instance_id,x,y,top));labels.append((e,x,layout['hp_y']))
            if e is g.player:
                dx,dy={'up':(0,1),'down':(0,-1),'left':(-1,0),'right':(1,0)}[e.facing]
                c.draw_line(*CAMERA.project(u+.5,v+.5),*CAMERA.project(u+.5+dx*.32,v+.5+dy*.32),101,201,244)
            hit=e.health.last_damage_tick
            if g.playing and hit is not None and 0<=g.combat.tick-hit<6:outline(c,CAMERA.tile(*e.position),(225,199,255))
        for e,x,y in labels:
            text=f'{e.health.current_hp}/{e.health.max_hp}';width=len(text)*8
            c.draw_rectangle(x-width/2-3,y-3,x+width/2+3,y+13,12,19,25,filled=True)
            HealthRenderer._text(c,text,x-width/2,y,color=HealthRenderer.HEALTH)
        if g.playing and g.parry.active_at(g.combat.tick):outline(c,CAMERA.tile(*g.player.position),(95,174,218))
        result=g.resolver.last_parry_result
        if g.playing and result and 0<=g.combat.tick-result.tick<18:
            text={'normal':'PARRY SUCCESS','perfect':'PERFECT PARRY','failed':'PARRY FAILED','unbound':'NO LINK'}.get(result.status)
            if text:
                HealthRenderer._text(c,text,44,692,color=(255,226,116) if result.status=='perfect' else (127,208,250))
            if result.successful:
                self.mark(result.player_cell,(255,226,116) if result.status=='perfect' else (112,207,246))
                if result.status=='perfect':
                    x,y=CAMERA.center(*result.player_cell)
                    for dx,dy in ((0,1),(1,0),(0,-1),(-1,0)):c.draw_line(x+dx*10,y+dy*10,x+dx*23,y+dy*23,255,226,116)
        HealthRenderer().draw(c,g.player,(),g.combat.tick,g.combat.pending_attack_bonus if g.playing else None,show_feedback=False)


class Stage5ArtPath(SessionArtPath):
    def __init__(self,c,factory=Stage5ArtRenderer):
        super().__init__(c,factory,stage=5,flag='CHECKMATE_STAGE5_ART',logger=LOG)
