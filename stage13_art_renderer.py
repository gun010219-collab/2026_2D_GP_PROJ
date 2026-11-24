"""Opt-in Frozen Queen profile; combat and warning geometry belong to the ledger."""
import logging

from arena_art_common import CAMERA,ArenaArtError,SessionArtPath,sprite_layout
from stage7_art_renderer import Stage7ArtRenderer
from stage11_art_renderer import FILES as ELEVEN_FILES
from stage12_art_renderer import actor_layout as previous_layout
from stage12_art_renderer import LiveArenaArtPath as PreviousArtPath

FILES={**{k:p for k,p in ELEVEN_FILES.items() if k!='rook'},
       'queen':'assets/chapter3_units/queen.png'}
QUEEN_HEIGHT=90
QUEEN_BASE_SIZE=QUEEN_HEIGHT*256/220/(CAMERA.sprite_scale*1.10)


def actor_layout(kind,u,v):
    if kind!='queen':return previous_layout(kind,u,v)
    return sprite_layout(kind,u,v,{'queen':QUEEN_BASE_SIZE},{},{'queen':12},{'queen':(18,238)})


class Stage13ArtRenderer(Stage7ArtRenderer):
    files=FILES

    def __init__(self,c,root=None,*,motion=None):
        super().__init__(c,root=root,motion=motion)
        try:
            for key,image in self.images.items():
                if not image.texture:raise ArenaArtError('Stage13 texture creation failed: '+key)
        except BaseException:
            self.close();raise

    def layout(self,kind,u,v):return actor_layout(kind,u,v)


class Stage13ArtPath(SessionArtPath):
    def __init__(self,c,factory=Stage13ArtRenderer,*,motion=None):
        super().__init__(c,lambda canvas:factory(canvas,motion=motion),stage=13,
                         flag='CHECKMATE_STAGE13_ART',logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    def __init__(self,c,*,motion=None,previous_factory=PreviousArtPath,stage13_factory=Stage13ArtRenderer):
        self.previous=previous_factory(c,motion=motion)
        self.stage13=Stage13ArtPath(c,stage13_factory,motion=motion)

    def draw(self,g,positions):
        if g.stage_number!=13:
            thirteen=self.stage13.draw(g,positions)
            previous=self.previous.draw(g,positions)
            return previous or thirteen
        previous=self.previous.draw(g,positions)
        thirteen=self.stage13.draw(g,positions)
        return previous or thirteen

    def close(self):
        self.previous.close();self.stage13.close()
