"""Exact enemy telegraph cells; queried ledger state never consumes attacks."""
from board import tile_bounds
from config import cell_center
from queen_behavior import RAY_STEPS, queen_ray_targets


class EnemyAttackRenderer:
    # Presentation only; main supplies logical cells, never interpolated pixels.
    tick = 0
    active = True
    source_cells = None
    GLOW_TICKS = 12

    def __init__(self):
        self._session = None
        self._beams = {}

    def _queen_lasers(self, canvas, ledger):
        session = (ledger.combat_session_id, ledger.stage_instance_id)
        if session != self._session or not self.active:
            self._beams.clear()
            self._session = session
        if not self.active:
            return
        events = ledger.laser_visuals(self.tick, self.GLOW_TICKS)
        live = set()
        for event in events:
            if self.source_cells is not None and event.source_entity_instance_id not in self.source_cells:
                continue
            live.add(event.key)
            if event.key not in self._beams:
                origin = (self.source_cells.get(event.source_entity_instance_id)
                          if self.source_cells is not None else None)
                if origin is None:
                    # Standalone renderer compatibility; calculated once per event.
                    cells = set(event.target_cells)
                    origin = next(((x,y) for y in range(10) for x in range(10)
                                   if set(queen_ray_targets((x,y))) == cells), None)
                if origin is None:
                    continue
                beams = []
                ox, oy = cell_center(*origin)
                targets = set(event.target_cells)
                for dx, dy in RAY_STEPS:
                    x,y = origin
                    while (x+dx,y+dy) in targets:
                        x,y=x+dx,y+dy
                    if (x,y) != origin:
                        ex,ey=cell_center(x,y)
                        beams.append((ox+dx*42,oy+dy*42,ex+dx*42,ey+dy*42))
                self._beams[event.key] = (origin, tuple(beams))
            age = self.tick-event.hit_tick
            charging = ledger.state(event) in ('telegraph','due')
            if charging:
                progress = max(0.0,min(1.0,(self.tick-event.start_tick)/(event.hit_tick-event.start_tick)))
                color = (100+int(125*progress),105+int(90*progress),245)
                for col,row in event.target_cells:
                    l,b,r,t=tile_bounds(col,row)
                    canvas.draw_rectangle(l+3,b+3,r-4,t-4,25,17,55)
                    canvas.draw_rectangle(l+5,b+5,r-6,t-6,*color)
                for x,y,ex,ey in self._beams[event.key][1]:
                    canvas.draw_line(x,y,ex,ey,*color)
                ox,oy=cell_center(*self._beams[event.key][0])
                canvas.draw_circle(ox,oy,round(18+12*progress),*color)
            else:
                # One tick's hit is followed by a cosmetic 12-tick afterimage.
                color = (255,244,210) if age < 3 else (158,112,205)
                spread = 3 if age < 3 else 1
                for x,y,ex,ey in self._beams[event.key][1]:
                    for offset in range(-spread,spread+1):
                        canvas.draw_line(x+offset,y,ex+offset,ey,75,38,119)
                        canvas.draw_line(x,y+offset,ex,ey+offset,75,38,119)
                    canvas.draw_line(x,y,ex,ey,*color)
        self._beams = {k:v for k,v in self._beams.items() if k in live}

    def draw(self, canvas, ledger):
        self._queen_lasers(canvas, ledger)
        for event in ledger.telegraphs:
            if event.attack_kind == "queen_diagonal":
                continue
            pulse = event.attack_kind == 'king_pulse'
            for col, row in event.target_cells:
                left, bottom, right, top = tile_bounds(col, row)
                canvas.draw_rectangle(left, bottom, right - 1, top - 1, 47, 14, 25)
                color = (255, 156, 65) if pulse else (231, 87, 111)
                canvas.draw_rectangle(left + 2, bottom + 2, right - 3, top - 3, *color)
                if pulse:
                    canvas.draw_line(left + 8, top - 10, left + 22, top - 24, *color)
                    canvas.draw_line(right - 22, top - 24, right - 8, top - 10, *color)
                # Dashed in-cell stripes distinguish danger from gold attacks/blue defense.
                for offset in range(10, right - left - 8, 14):
                    canvas.draw_line(left + offset, bottom + 10,
                                     left + offset + 6, bottom + 16, 209, 104, 120)
