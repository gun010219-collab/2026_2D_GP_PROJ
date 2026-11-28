"""Opt-in live Stage5 arena. Reads entities/ledger; never constructs a scene."""
import ctypes
import logging
from functools import lru_cache
from pathlib import Path
from math import cos,sin,pi
from arena_art_common import CAMERA, ArenaArtError, SessionArtPath, enlarge_sprite, sprite_layout
from board import is_light_tile
from config import BOARD_LEFT,BOARD_BOTTOM,TILE_SIZE
from render_motion import display_center
from health_renderer import HealthRenderer
from ui_theme import current as current_ui
from player_combat_guide import draw_aim, player_aim
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


def _polygon_data(points,color):
    import sdl2 as s
    vertices=(s.SDL_Vertex*len(points))();uv=((0,1),(1,1),(1,0),(0,0))
    for i,(x,y) in enumerate(points):
        vertices[i].position=s.SDL_FPoint(x,899-y);vertices[i].color=s.SDL_Color(*color)
        vertices[i].tex_coord=s.SDL_FPoint(*uv[i%4])
    indices=[i for j in range(1,len(points)-1) for i in (0,j,j+1)]
    return vertices,(ctypes.c_int*len(indices))(*indices)


# Only board and rim geometry is textured here. Cache CPU vertices without
# retaining session textures or caching moving actors' shadow coordinates.
_board_geometry = lru_cache(maxsize=128)(_polygon_data)
_board_tile = lru_cache(maxsize=100)(CAMERA.tile)


def polygon(c,points,color=(255,255,255,255),texture=None):
    import sdl2 as s
    vertices,indices = (_board_geometry if texture is not None else _polygon_data)(points,color)
    if s.SDL_RenderGeometry(c.renderer,texture,vertices,len(vertices),indices,len(indices)):
        raise Stage5ArtError('SDL geometry: '+s.SDL_GetError().decode())


def outline(c,points,color):
    for a,b in zip(points,points[1:]+points[:1]):c.draw_line(*a,*b,*color)


def cue_kind(g, *, show_result=True):
    t=g.combat.tick
    if not g.playing:return 'quiet'
    result=g.resolver.last_parry_result
    if show_result and result and result.successful and 0<=t-result.tick<18:
        return 'perfect_success' if result.status=='perfect' else 'parry_success'
    if any(e.attack_kind=='king_pulse' for e in g.encounter.ledger.telegraphs):return 'pulse'
    if g.parry.active_at(t):return 'parry_window'
    if g.encounter.ledger.telegraphs:return 'danger'
    if g.combat.active_attack is not None:return 'player_attack'
    return 'ready' if t>=g.parry.next_parry_tick else 'quiet'


class Stage5ArtRenderer:
    # Stage6 reuses this drawing pipeline through these two presentation hooks.
    files = FILES
    animation = animation_motion = None
    animation_failed = False
    enlarged = False
    vfx = telegraph = parry_hint = None
    player_combat_visual = False
    sprite_atlases = None
    player_armor = None

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

    def load_sprite_atlases(self, catalog, chapter):
        from sprite_atlas import SpriteAtlases

        self.sprite_atlases = SpriteAtlases(self.c, catalog, chapter,
                                            {self.animation_style(key) for key in self.images})

    def animation_style(self, kind):
        profile = getattr(self, 'profile', None)
        if profile is not None and kind in profile.pieces:
            return profile.pieces[kind].animation_profile
        return kind

    def close(self):
        if self.sprite_atlases is not None:
            self.sprite_atlases.close()
            self.sprite_atlases = None
        # Nulling the Pico2D handle makes its later __del__ safe and idempotent.
        for image in self.images.values():
            if image.texture:self.c.SDL_DestroyTexture(image.texture);image.texture=None
        self.images.clear()

    def image(self,key,x,y,w,h):
        self.draw_texture(self.images[key].texture, x, y, w, h)

    def draw_texture(self, texture, x, y, w, h):
        import sdl2 as s
        rect=s.SDL_FRect(x-w/2,899-y-h/2,w,h)
        if s.SDL_RenderCopyF(self.c.renderer,texture,None,ctypes.byref(rect)):
            raise Stage5ArtError('SDL texture copy: '+s.SDL_GetError().decode())

    def mark(self,cell,color):
        outline(self.c,CAMERA.tile(*cell),color)
        col,row=cell
        for t in (.15,.35,.55,.75):self.c.draw_line(*CAMERA.project(col+t,row+.12),*CAMERA.project(col+t+.12,row+.24),*color)

    def draw_frame(self):
        self.image('frame',720,450,1440,900)

    def draw_actor(self, g, actor, kind, layout, *, dead=False):
        texture = self.images[kind].texture
        atlases = self.sprite_atlases
        armor = None
        if kind == 'player' and self.player_armor is not None:
            max_hp = actor.max_hp if dead else actor.health.max_hp
            armor = self.player_armor.select(max_hp)
            if armor is not None:
                texture = armor.image.texture
                atlases = armor.sprites
                layout['armor_hp'] = max_hp
        if self.animation is not None and (not self.animation_failed or atlases is not None):
            pose, effect = self.animation.mesh_pose(g,actor,self.animation_motion)
            style = self.animation_style(kind)
            if atlases is not None and not dead:
                from sprite_atlas import SPRITE_COMPLETE

                label = atlases.draw(g, actor, style, layout, self.animation, pose)
                if label is SPRITE_COMPLETE:
                    from actor_mesh import deformation

                    pose = self.animation.locomotion_pose(g, actor, self.animation_motion)
                    effect = deformation(style, g.chapter, pose, improved=self.animation.improved)
                elif label is not None:
                    layout['animation'] = pose.state.value
                    layout['sprite_frame'] = True
                    return label
        if self.animation is not None and not self.animation_failed:
            from actor_mesh import draw_actor

            try:
                x, top = draw_actor(self.c,texture,style,g.chapter,layout,pose,effect=effect)
                layout['animation'] = pose.state.value
                return x, layout['hp_y'] + top - layout['top']
            except (OSError, ArenaArtError):
                LOG.exception('Actor animation unavailable; using the static sprites for this session')
                self.animation_failed = True
        if not dead:
            x, y = layout['center']
            size = layout['height']
            if armor is None:
                self.image(kind, x, y, size, size)
            else:
                self.draw_texture(texture, x, y, size, size)
        return layout['foot'][0], layout['hp_y']

    def draw(self,g,positions):
        self.draw_world(g,positions)
        self.draw_feedback(g)

    def draw_warnings(self,g):
        if self.telegraph is not None and not self.telegraph.failed:
            try:
                cells,self.parry_hint = self.telegraph.draw(self.c,g)
                self.warning_cells.extend(cells)
                return
            except ArenaArtError:
                self.telegraph.failed = True
                LOG.exception('Telegraph batch unavailable; restoring the original warnings')
        for event in g.encounter.ledger.telegraphs:
            for cell in event.target_cells:
                self.warning_cells.append(tuple(cell))
                self.mark(cell,(241,144,62) if event.attack_kind=='king_pulse' else (239,88,109))

    def draw_world(self,g,positions):
        c=self.c;self.warning_cells=[];self.order=[];self.bounds=[];self.actor_layouts={}
        self.image('background',720,450,1440,900);self.draw_frame()
        outer=((- .12,-.12),(10.12,-.12),(10.12,10.12),(-.12,10.12));inner=((0,0),(10,0),(10,10),(0,10))
        for lo,hi,gain in ((0,.18,.76),(.18,.82,1),(.82,1,1.1)):
            def ring(t):return tuple((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for a,b in zip(outer,inner))
            a,b=ring(lo),ring(hi)
            for i in range(4):
                j=(i+1)%4;value=min(255,round(200*gain*(1.05 if i in (2,3) else .94)))
                polygon(c,tuple(CAMERA.project(*p) for p in (a[i],a[j],b[j],b[i])),(value,value,value,255),self.images['light'].texture)
        for col in range(10):
            for row in range(10):polygon(c,_board_tile(col,row),texture=self.images['light' if is_light_tile(col,row) else 'dark'].texture)
        if self.vfx is not None:
            self.vfx.draw('ground', c, g)
        self.cue=cue_kind(g)
        # Keep the perimeter on its ordinary threat state during a perfect result.
        rail_cue = self.cue
        if self.cue=='perfect_success' and (self.vfx is not None or current_ui(c) is not None):
            rail_cue = cue_kind(g,show_result=False)
        color={'quiet':(80,84,91),'ready':(69,116,136),'player_attack':(137,123,89),'danger':(130,62,74),
               'parry_window':(95,149,166),'parry_success':(88,149,169),'perfect_success':(183,164,109),'pulse':(146,104,59)}[rail_cue]
        if rail_cue!='quiet':
            for side in range(4):
                intervals=((.46,.54),) if rail_cue=='ready' else ((.14,.32),(.68,.86)) if rail_cue in ('parry_window','parry_success','player_attack') else ((.025,.975),)
                for start,end in intervals:
                    def rail(t):return ((t*10,-.095),(10.095,t*10),((1-t)*10,10.095),(-.095,(1-t)*10))[side]
                    c.draw_line(*CAMERA.project(*rail(start)),*CAMERA.project(*rail(end)),*color)
        self.parry_hint = None
        if g.playing:
            if self.player_combat_visual and g.player.alive:
                draw_aim(c,player_aim(g))
            self.draw_warnings(g)
            if not self.player_combat_visual and g.combat.active_attack:
                self.mark(g.combat.active_attack.target_cell,(237,207,113))
        actors=[e for e in g.encounter.enemies if e.active and e.alive]
        if g.player.alive:actors.append(g.player)
        dead_ids = set()
        if self.animation is not None and not self.animation_failed:
            for dead in self.animation.deaths:
                actors.append(dead)
                dead_ids.add(dead.entity_instance_id)
        def cell(e):
            return self.pose(e,positions)
        # A live actor can enter a corpse's cell. Keep the captured death pose
        # in front on that exact tie instead of letting random UUIDs set order.
        actors.sort(key=lambda e:(-cell(e)[1],cell(e)[0],
                                 e.entity_instance_id in dead_ids,e.entity_instance_id))
        labels=[]
        for e in actors:
            kind=getattr(e,'kind','player');u,v,lift=cell(e);layout=self.layout(kind,u,v)
            shadow_height = layout['height']
            if self.enlarged:
                layout = enlarge_sprite(layout,kind)
            if lift:
                layout={**layout,'center':(layout['center'][0],layout['center'][1]+lift),
                        'top':layout['top']+lift,'hp_y':layout['hp_y']+lift,'elevation':lift}
            x,y=layout['foot'];top=layout['top']
            self.actor_layouts[e.entity_instance_id]=layout
            if e.entity_instance_id in dead_ids:
                self.draw_actor(g,e,kind,layout,dead=True)
                continue
            polygon(c,tuple((x+4+cos(i*pi/4)*shadow_height*.24,y-2+sin(i*pi/4)*4) for i in range(8)),(24,25,29,255))
            label_x,label_y=self.draw_actor(g,e,kind,layout)
            self.order.append(e.entity_instance_id)
            self.bounds.append((e.entity_instance_id,x,y,top));labels.append((e,label_x,label_y))
            if e is g.player and not self.player_combat_visual:
                dx,dy={'up':(0,1),'down':(0,-1),'left':(-1,0),'right':(1,0)}[e.facing]
                c.draw_line(*CAMERA.project(u+.5,v+.5),*CAMERA.project(u+.5+dx*.32,v+.5+dy*.32),101,201,244)
            hit=e.health.last_damage_tick
            if g.playing and hit is not None and 0<=g.combat.tick-hit<6:outline(c,CAMERA.tile(*e.position),(225,199,255))
        if self.vfx is not None:
            self.vfx.draw('front', c, g, self.actor_layouts)
        theme = current_ui(c)
        for e,x,y in labels:
            if theme:
                HealthRenderer.badge(theme,e.health,x,y)
                continue
            text=f'{e.health.current_hp}/{e.health.max_hp}';width=len(text)*8
            c.draw_rectangle(x-width/2-3,y-3,x+width/2+3,y+13,12,19,25,filled=True)
            HealthRenderer._text(c,text,x-width/2,y,color=HealthRenderer.HEALTH)
        if self.vfx is not None:
            self.vfx.draw('labels', c, g)

    def draw_feedback(self,g):
        c=self.c
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
        if self.telegraph is not None:
            theme = current_ui(c)
            if theme and g.playing and self.parry_hint is None and g.player.alive:
                theme.text('PARRY',49,748,size=15,color=(184,170,183),align='left')
                left = max(0,g.parry.next_parry_tick-g.combat.tick)
                theme.text(f'Ready in {left} ticks' if left else 'Ready',49,725,size=19,align='left')
            else:
                self.telegraph.draw_hint(c,self.parry_hint)


class Stage5ArtPath(SessionArtPath):
    def __init__(self,c,factory=Stage5ArtRenderer):
        super().__init__(c,factory,stage=5,flag='CHECKMATE_STAGE5_ART',logger=LOG)
