from doom.trig import Rectangle
from nav.navenum import *


class NavArea(object):
    __slots__ = (
        'rect',
        'z',
        
        'sector',
        'flags',
        'elements',
        'plane',
        'connections',
        
        'inside_rect'
    )


    def __init__(self, x1, y1, x2, y2, z):
        self.rect = Rectangle(x1, y1, x2, y2)
        self.z = z
        
        self.sector = -1
        self.flags = 0
        self.elements = []
        self.plane = None
        self.connections = []
        
        self.inside_rect = Rectangle()


    def get_side(self, side):
        if side == SIDE_TOP:
            return self.rect.left, self.rect.top, self.rect.right, self.rect.top
        
        elif side == SIDE_RIGHT:
            return self.rect.right, self.rect.top, self.rect.right, self.rect.bottom
            
        elif side == SIDE_BOTTOM:
            return self.rect.left, self.rect.bottom, self.rect.right, self.rect.bottom
            
        elif side == SIDE_LEFT:
            return self.rect.left, self.rect.top, self.rect.left, self.rect.bottom
        
        return None
    
    
    def __repr__(self):
        return 'area {}, z {}, sector {}, width {}, height {}, plane {}, flags {}, connections {}'.format(self.rect, self.z, self.sector, self.rect.get_width(), self.rect.get_height(), self.plane, self.flags, len(self.connections)) 