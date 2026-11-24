"""Actual Stage13 captures: original color50 ledger and real parry outcomes."""
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
from stage13_art_renderer import Stage13ArtRenderer
from tools.stage13_play import session
from tools.stage5_art_preview import Scene,snapshot,open_preview,capture_png
from upgrade_renderer import UpgradeRenderer


def capture(out):
    from pico2d import pico2d as c
    out=Path(out);out.mkdir(parents=True,exist_ok=True);renderer=None;rows=[]
    try:
        open_preview(c,capture=True);motion=RenderMotion();renderer=Stage13ArtRenderer(c,motion=motion)
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
            rows.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),state=snapshot(Scene('live Stage13',g)),
                             cue=renderer.cue,warning_cells=renderer.warning_cells,order=[names[k] for k in renderer.order],
                             layouts={names[k]:v for k,v in renderer.actor_layouts.items()},
                             warnings=[dict(source=names[e.source_entity_instance_id],attack_id=e.attack_id,hit_tick=e.hit_tick,cells=e.target_cells) for e in g.encounter.ledger.telegraphs]))
        g,_=fresh();save('normal',g)
        advance(g,48);assert g.encounter.enemies[0].position==(5,6);save('queen_reposition',g)
        advance(g,49);event=g.encounter.enemies[0].current_attack
        assert len(event.target_cells)==33;save('queen_rays',g)
        advance(g,80);assert len(g.encounter.ledger.telegraphs)==2;save('mixed_warning',g)
        advance(g,101);assert abs(motion.ground_pose(g.encounter.enemies[1])[1]-18)<1e-6;save('knight_peak',g)
        advance(g,121);assert event not in g.encounter.ledger.telegraphs;save('queen_resolved',g)
        advance(g,302);assert g.encounter.enemies[0].position==(5,3);save('queen_second_origin',g)
        for delta,status in ((18,'normal'),(7,'perfect')):
            g,_=fresh();advance(g,121-delta);event=g.encounter.enemies[0].current_attack
            g.resolver.register_parry(g.parry.request(g.combat.tick))
            if status=='normal':save('parry_window',g)
            advance(g,121);assert (g.resolver.last_parry_result.status,g.resolver.last_parry_result.enemy_event_key)==(status,event.key)
            save('parry_'+status,g)
        from input_controller import InputController
        g,_=fresh();advance(g,103);g.resolver.register_parry(g.parry.request(103))
        InputController().key_down('left',g.player,occupied=g.encounter.occupied_cells,tick=103)
        advance(g,121);assert g.resolver.last_parry_result.status=='failed';save('parry_evaded',g)
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
        assert result==(13,'UPGRADE',543,3,4) and seen=={'attack'}
        flow.sync_offer();save('upgrade',g,flow)
        next_game,_=flow.choose(flow.offer,'hp',__import__('main')._new_stage_game)
        assert (next_game.stage_number,next_game.player.health.current_hp,next_game.player.health.max_hp,len(flow.run.receipts))==(14,4,5,3)
        g,_=fresh();advance(g,374);assert g.state.value=='GAME_OVER';save('game_over',g)
        manifest=dict(status='Live Stage13 combat captures; human Windows GUI/performance pending',
                      preparation='Fresh Chapter3 dev entry level3/damage4; AUTOMATED original Stage11/12 fights and real HP/attack choices. Stage13 HP3/4 damage5 MOVE18 Receipt2. No synthetic receipt, forced kill or human campaign-clear claim.',
                      queen_rule='Original 8 rays, origin excluded, through board edges. Spawn31 is not a live warning: first real reposition5,6 then ledger33 at tick49/hit121. Real second origin5,3 at301/302.',
                      stage13_result=result,stage14=dict(hp=4,max_hp=5,receipts=3,legacy_display=True),captures=rows)
        (out/'capture_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        print('CAPTURED',len(rows),'actual Stage13 frames;',result,'Stage14 HP4/5 Receipt3')
        return manifest
    finally:
        if renderer is not None:renderer.close()
        if c.window:c.close_canvas();c.window=c.renderer=None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture-dir',required=True,type=Path)
    capture(parser.parse_args().capture_dir)
