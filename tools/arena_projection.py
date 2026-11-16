"""Pure display-only homographies. Logical combat coordinates never change."""
from dataclasses import dataclass
from math import floor,isfinite


@dataclass(frozen=True)
class ArenaCamera:
    name: str
    corners: tuple  # front-left, front-right, rear-right, rear-left; canvas y-up
    thickness: float
    sprite_scale: float

    @property
    def coefficients(self):
        (x0,y0),(x1,y1),(x2,y2),(x3,y3)=self.corners
        dx1,dx2,dx3=x1-x2,x3-x2,x0-x1+x2-x3
        dy1,dy2,dy3=y1-y2,y3-y2,y0-y1+y2-y3
        if abs(dx3)+abs(dy3)<1e-12:g=h=0.0
        else:
            det=dx1*dy2-dx2*dy1
            g=(dx3*dy2-dx2*dy3)/det;h=(dx1*dy3-dx3*dy1)/det
        return x1-x0+g*x1,x3-x0+h*x3,x0,y1-y0+g*y1,y3-y0+h*y3,y0,g,h

    def project(self,col,row):
        if not isfinite(col) or not isfinite(row):raise ValueError('Finite coordinates required')
        a,b,c,d,e,f,g,h=self.coefficients;u,v=col/10,row/10
        z=g*u+h*v+1
        return (a*u+b*v+c)/z,(d*u+e*v+f)/z

    def inverse(self,x,y):
        if not isfinite(x) or not isfinite(y):return None
        a,b,c,d,e,f,g,h=self.coefficients
        aa,bb,dd,ee=a-x*g,b-x*h,d-y*g,e-y*h
        det=aa*ee-bb*dd
        if abs(det)<1e-12:return None
        return 10*((x-c)*ee-bb*(y-f))/det,10*(aa*(y-f)-(x-c)*dd)/det

    def pick(self,x,y):
        point=self.inverse(x,y)
        if point is None:return None
        u,v=point
        # Same half-open rule as the original board; internal lines belong to
        # the right/upper cell. Snap only floating point error at grid lines.
        if abs(u-round(u))<1e-9:u=float(round(u))
        if abs(v-round(v))<1e-9:v=float(round(v))
        return (floor(u),floor(v)) if 0<=u<10 and 0<=v<10 else None

    def tile(self,col,row):
        if type(col) is not int or type(row) is not int or not (0<=col<10 and 0<=row<10):
            raise ValueError('Tile must be in the 10x10 logical board')
        return tuple(self.project(c,r) for c,r in ((col,row),(col+1,row),(col+1,row+1),(col,row+1)))

    def center(self,col,row):return self.project(col+.5,row+.5)


CAMERAS=(
    ArenaCamera('A ENHANCED TOP DOWN',((300,30),(1140,30),(1140,870),(300,870)),12,1.0),
    ArenaCamera('B CINEMATIC 2 5D',((340,165),(1130,165),(1055,690),(425,690)),32,1.10),
    ArenaCamera('C STRONG ISOMETRIC',((740,95),(1180,390),(740,705),(300,390)),42,1.0),
)
