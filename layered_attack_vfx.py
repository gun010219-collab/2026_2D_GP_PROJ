"""Layered materials for R7-A2B. Geometry and textures follow existing receipts."""
from math import hypot, pi, sin

from arena_art_common import CAMERA
from attack_vfx import CRIMSON, center, projected_beams, projected_wave, wave_cells
LAVA_CORE = (255,179,69)


def charge(atlas, layer, x, y, kind, pulse, amount, style):
    if kind not in ('bishop','queen','king'):
        return
    size = {'bishop':44,'queen':39,'king':52 if pulse else 40}[kind]
    if layer == 'ground':
        # The moving marks surround the actor; actual danger cells draw above.
        atlas.stamp('runes',x,y,size,.46,style.color,.62,angle=.28*amount)
        atlas.stamp('runes',x,y,size*(.85-.39*amount),.46,style.edge,.62,
                    angle=-.4*amount)
        atlas.stamp('halo',x,y,size*.91,.39,style.shadow,.58)
    else:
        atlas.stamp('halo',x,y,14+15*amount,1,style.color,.55+.25*amount)
        atlas.stamp('flare',x,y,7+10*amount,1,style.edge,.75,angle=amount*.8)


def material(atlas, x, y, size, phase, fade, style):
    """Ground residue by mechanism, silhouette and motion, as well as palette."""
    color, edge, shadow = style.color, style.edge, style.shadow
    mat = style.material
    if mat == 'metal':
        atlas.stamp('runes',x,y,size,.43,color,.55*fade)
        atlas.stamp('flare',x,y,size*.43,.64,edge,.74*fade,angle=pi/4+phase*.3)
    elif mat == 'vine':
        for sign in (-1,1):
            sway = sin(phase*3+sign)*size*.21
            atlas.stamp('ribbon',x+sign*size*.24,y+sway*.3,size*.62,.31,color,.72*fade,
                        angle=sign*.69+phase*.27)
        atlas.stamp('halo',x,y,size*.65,.43,edge,.36*fade)
    elif mat == 'frost':
        atlas.stamp('halo',x,y,size,.52,color,.76*fade)
        atlas.stamp('crystal',x,y,size*.78,.64,edge,.72*fade,angle=phase*.43)
    elif mat == 'lava':
        atlas.stamp('smoke',x,y+phase*18,size,.58,shadow,.60*fade)
        atlas.stamp('ember',x,y+phase*22,size*.69,1.26,LAVA_CORE,.90*fade,
                    angle=.18*sin(phase*9))
    else:
        atlas.stamp('smoke',x-size*.12,y+phase*16,size*1.19,.74,shadow,.88*fade,
                    angle=.44+phase*.8)
        atlas.stamp('runes',x,y,size*.84,.44,CRIMSON,.81*fade,angle=-phase*.3)
        atlas.stamp('flare',x,y+2,size*.38,.85,color,.82*fade,angle=.38+phase)


def beam(atlas, fx, t, style):
    fade = 1-t
    for i,(a,b) in enumerate(projected_beams(fx.origin,fx.cells)):
        # Ribbon length and moving crest remain inside this contiguous ledger ray.
        dx,dy = b[0]-a[0],b[1]-a[1]
        if style.material == 'curse':
            atlas.quad('smoke',a,b,23+11*t,style.shadow,.92*fade)
        atlas.quad('ribbon',a,b,18+10*fade,style.color,.92*fade)
        atlas.quad('ribbon',a,b,3+5*fade,style.edge,.75*fade)
        pos = .09+.66*((t*1.45+i*.083)%1)
        lead = a[0]+dx*pos,a[1]+dy*pos
        end = lead[0]+dx*.15,lead[1]+dy*.15
        atlas.quad('ribbon',lead,end,10,style.edge,.93*fade)


def pulse_wave(atlas,fx,t,style):
    fade = 1-t
    cursed = style.material=='curse'
    bands = projected_wave(fx.origin,.25+t*14)
    for i,(a,b) in enumerate(bands):
        if cursed:
            drift = 7*sin(i*.83+t*12)
            ash = a[0],a[1]+drift
            end = b[0],b[1]+drift
            atlas.quad('smoke',ash,end,22+11*t,style.shadow,.78*fade)
        atlas.quad('ribbon',a,b,15+8*fade,style.color,.82*fade)
    if cursed and 0 < t < .68:
        # Delayed internal rupture trails the leading wave, still on the board.
        for a,b in projected_wave(fx.origin,max(.15,14*t-1.1)):
            atlas.quad('ribbon',a,b,8,CRIMSON,.71*fade)


def bishop_cells(atlas,fx,t,style):
    # Decorative glyphs ride the cast across only the published bishop cells.
    tile = {'metal':'runes','vine':'ribbon','frost':'crystal','lava':'ember','curse':'runes'}[style.material]
    radius = t*14
    for distance,x,y in wave_cells(fx.origin,fx.cells):
        energy = 1-abs(distance-radius)/1.4
        if energy > 0:
            size = 9+8*energy
            atlas.stamp(tile,x,y,size,.42,style.color,.72*energy,angle=.2*t)


def draw(atlas, layer, fx, age, t, style, time):
    x,y = center(fx.origin)
    tx,ty = center(fx.cell)
    fade = 1-t
    name = fx.name
    if layer == 'ground':
        if name == 'queen_fire':
            beam(atlas,fx,t,style)
        elif name in ('bishop_cast','king_pulse'):
            boss = name=='king_pulse'
            size = 33+(70 if boss else 39)*t
            material(atlas,x,y,size,t,fade,style)
            atlas.stamp('ripple',x,y,size,.45,style.edge,.66*fade)
            if boss and len(fx.cells)==100:
                pulse_wave(atlas,fx,t,style)
            if not boss:
                bishop_cells(atlas,fx,t,style)
        elif name in ('rook_impact','knight_land','boss_death'):
            if fx.landed is None and name!='boss_death':
                return
            elapsed = age if name=='boss_death' else time-fx.landed
            radius = (60 if name=='boss_death' else 30)+min(.45,elapsed)*145
            material(atlas,tx,ty,radius,t,fade,style)
            atlas.stamp('ripple',tx,ty,radius*1.22,.45,style.color,.9*fade)
        elif name=='king_strike':
            atlas.stamp('ripple',tx,ty,27+39*t,.45,style.color,.81*fade)
        return

    if name in ('pawn_thrust','rook_strike','knight_strike','king_strike'):
        fraction,height,width = {'pawn_thrust':(.97,20,9),'rook_strike':(.54,16,17),
                                 'knight_strike':(.47,30,12),'king_strike':(.94,20,23)}[name]
        dx,dy = tx-x,ty-y
        if name=='rook_strike':
            fraction = min(1.,54/max(1.,hypot(dx,dy)))
        end = x+dx*fraction,y+height+dy*fraction
        atlas.quad('ribbon',(x,y+height),end,width,style.color,.77*fade)
        if name in ('pawn_thrust','king_strike'):
            atlas.quad('ribbon',(x,y+height),end,width*.42,style.edge,.68*fade)
    elif name in ('rook_impact','knight_land'):
        if fx.travel_pose is not None and fx.landed is None:
            col,row,lift = fx.travel_pose
            cx,cy = CAMERA.project(col,row)
            spread = .27 if name=='rook_impact' else .19
            a = cx-(tx-x)*spread,cy-(ty-y)*spread+lift*.55+8
            b = cx,cy+lift+12
            atlas.quad('ribbon',a,b,17 if name=='rook_impact' else 12,style.color,.72)
        elif fx.landed is not None:
            flash = max(0.,1-(time-fx.landed)*7)
            atlas.stamp('flare',tx,ty+13,27,1,style.edge,.79*flash,angle=pi/4)
    elif name == 'boss_death':
        atlas.stamp('smoke',x,y+33+39*t,44+34*t,1.24,style.shadow,.8*fade,
                    angle=.42*t)
        atlas.stamp('flare',x,y+30,49+22*t,1.04,style.color,.87*fade,angle=t)
        atlas.stamp('flare',x,y+32,27,1,style.edge,.90*fade*fade)
    elif name in ('player_hit','player_hurt') or name.startswith('parry_'):
        color = {'player_hit':(255,239,161),'player_hurt':(255,111,107),
                 'parry_normal':(171,242,255),'parry_perfect':(255,218,115)}.get(name)
        if color:
            size = 42 if name=='parry_perfect' else 23
            atlas.stamp('flare',tx,ty+24,size,1,color,.6*fade*fade,angle=pi/4)
