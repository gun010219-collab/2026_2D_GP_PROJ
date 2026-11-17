"""Stage12 Frozen profile; stationary Bishops read the unchanged combat ledger."""
import logging

from arena_art_common import CAMERA,ArenaArtError,SessionArtPath,sprite_layout
from stage7_art_renderer import Stage7ArtRenderer
from stage11_art_renderer import FILES as ELEVEN_FILES,actor_layout as eleven_layout
from stage11_art_renderer import LiveArenaArtPath as PreviousArtPath

FILES={**{k:p for k,p in ELEVEN_FILES.items() if k!='knight'},
       'bishop':'assets/chapter3_units/bishop.png'}
BISHOP_HEIGHT=84
BISHOP_BASE_SIZE=BISHOP_HEIGHT*256/220/(CAMERA.sprite_scale*1.10)


def actor_layout(kind,u,v):
    if kind!='bishop':return eleven_layout(kind,u,v)
    return sprite_layout(kind,u,v,{'bishop':BISHOP_BASE_SIZE},{},{'bishop':10},{'bishop':(18,238)})


class Stage12ArtRenderer(Stage7ArtRenderer):
    files=FILES

    def __init__(self,c,root=None,*,motion=None):
        super().__init__(c,root=root,motion=motion)
        try:
            for key,image in self.images.items():
                if not image.texture:raise ArenaArtError('Stage12 texture creation failed: '+key)
        except BaseException:
            self.close();raise

    def layout(self,kind,u,v):return actor_layout(kind,u,v)


class Stage12ArtPath(SessionArtPath):
    def __init__(self,c,factory=Stage12ArtRenderer,*,motion=None):
        super().__init__(c,lambda canvas:factory(canvas,motion=motion),stage=12,
                         flag='CHECKMATE_STAGE12_ART',logger=logging.getLogger(__name__))


class LiveArenaArtPath:
    def __init__(self,c,*,motion=None,previous_factory=PreviousArtPath,stage12_factory=Stage12ArtRenderer):
        self.previous=previous_factory(c,motion=motion)
        self.stage12=Stage12ArtPath(c,stage12_factory,motion=motion)

    def draw(self,g,positions):
        previous=self.previous.draw(g,positions)
        twelve=self.stage12.draw(g,positions)
        return previous or twelve

    def close(self):
        self.previous.close();self.stage12.close()
