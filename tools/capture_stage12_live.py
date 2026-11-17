"""Actual Stage12 captures: original color50 ledger and real parry outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
import pickle
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from game import StageGame
from game_renderer import GameFlowRenderer
from render_motion import RenderMotion
from stage12_art_renderer import Stage12ArtRenderer
from tools.stage12_play import session
from tools.stage5_art_preview import Scene,snapshot,open_preview,capture_png
from upgrade_renderer import UpgradeRenderer


def capture(out):
    from pico2d import pico2d as c
    out=Path(out);out.mkdir(parents=True,exist_ok=True);renderer=None;rows=[]
    try:
        open_preview(c,capture=True);motion=RenderMotion();renderer=Stage12ArtRenderer(c,motion=motion)
        def sync(g,elapsed):
            frozen=(g.player.entity_instance_id,) if g.combat.active_attack or g.parry.active_at(g.combat.tick) else ()
            motion.update((g.player,*g.encounter.enemies),elapsed,session=g.combat.combat_session_id,frozen=frozen)
        def fresh():
            g,f=session();sync(g,0);return g,f
        def advance(g,t):
            for _ in range(t-g.combat.tick):g.advance();sync(g,1/60)
        def save(name,g,flow=None):
            before=pickle.dumps((g,motion));renderer.draw(g,motion.positions)
            GameFlowRenderer().draw_stage_label(c,g);GameFlowRenderer().draw(c,g)
            if flow and flow.offer:UpgradeRenderer().draw(c,g,flow.offer,flow.error)
            expected=[tuple(cell) for e in g.encounter.ledger.telegraphs for cell in e.target_cells] if g.playing else []
            assert renderer.warning_cells==expected and pickle.dumps((g,motion))==before
            names={e.entity_instance_id:e.data_id for e in g.encounter.enemies};names[g.player.entity_instance_id]='player'
            p=out/(name+'.png');capture_png(c,p)
            rows.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),state=snapshot(Scene('live Stage12',g)),
                             cue=renderer.cue,warning_cells=renderer.warning_cells,order=[names[k] for k in renderer.order],
                             layouts={names[k]:v for k,v in renderer.actor_layouts.items()},
                             warnings=[dict(source=names[e.source_entity_instance_id],attack_id=e.attack_id,hit_tick=e.hit_tick,cells=e.target_cells) for e in g.encounter.ledger.telegraphs]))
        g,_=fresh();save('normal',g)
        advance(g,48);a=g.encounter.enemies[0].current_attack;assert len(a.target_cells)==50;save('bishop_even',g)
        advance(g,149);assert g.encounter.enemies[1].current_attack is None;save('mixed_warning',g)
        advance(g,156);assert all(e.current_attack is None for e in g.encounter.enemies[:2]);save('serialized_gap',g)
        advance(g,157);b=g.encounter.enemies[1].current_attack
        assert len(b.target_cells)==50 and not set(a.target_cells)&set(b.target_cells);save('bishop_odd',g)
        advance(g,265);assert b not in g.encounter.ledger.telegraphs;save('second_resolved',g)
        for delta,status in ((18,'normal'),(7,'perfect')):
            g,_=fresh();advance(g,156-delta);event=g.encounter.enemies[0].current_attack
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            if status=='normal':save('parry_window',g)
            advance(g,156);assert (g.resolver.last_parry_result.status,g.resolver.last_parry_result.enemy_event_key)==(status,event.key)
            save('parry_'+status,g)
        from tests.test_hp_carryover import fight
        g,flow=fresh();resolve=StageGame.resolve_current_tick;seen=set()
        def observe(game):
            result=resolve(game)
            if game is g:
                sync(g,1/60)
                if g.combat.active_attack and 'attack' not in seen:
                    save('player_attack',g);seen.add('attack')
            return result
        with patch.object(StageGame,'resolve_current_tick',observe):result=fight(flow)
        assert result==(12,'UPGRADE',669,3,4) and seen=={'attack'}
        flow.sync_offer();save('upgrade',g,flow)
        next_game,_=flow.choose(flow.offer,'attack',__import__('main')._new_stage_game)
        assert (next_game.stage_number,next_game.player.health.current_hp,len(flow.run.receipts))==(13,3,2)
        g,_=fresh();advance(g,471);assert g.state.value=='GAME_OVER';save('game_over',g)
        manifest=dict(status='Live Stage12 combat captures; human Windows GUI/performance pending',
                      preparation='Fresh Chapter3 dev entry level3/damage4; AUTOMATED original Stage11 clear669/HP2/3, genuine HP choice; Stage12 HP3/4 MOVE18 Receipt1. No synthetic receipt or human campaign-clear claim.',
                      bishop_rule='Stationary own-color50, opposite-color serialized with one-tick gap; no diagonal ray/movement',
                      stage12_result=result,stage13=dict(hp=3,max_hp=4,receipts=2,legacy_display=True),captures=rows)
        (out/'capture_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        print('CAPTURED',len(rows),'actual Stage12 frames;',result,'Stage13 HP3/4 Receipt2')
        return manifest
    finally:
        if renderer is not None:renderer.close()
        if c.window:c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture-dir',required=True,type=Path)
    capture(parser.parse_args().capture_dir)
