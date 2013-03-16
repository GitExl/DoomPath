from nav.navenum import *


class NavArea(object):
    __slots__ = (
        'x1', 'y1',
        'x2', 'y2',
        'z',
        
        'sector',
        'flags',
        'elements',
        'plane',
        
        'inside_x1', 'inside_y1',
        'inside_x2', 'inside_y2'
    )


    def __init__(self, x1, y1, x2, y2, z):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.z = z
        
        self.sector = -1
        self.flags = 0
        self.elements = []
        self.plane = None
        
        self.inside_x1 = 0
        self.inside_y1 = 0
        self.inside_x2 = 0
        self.inside_y2 = 0


    def get_side(self, side):
        if side == SIDE_TOP:
            return self.x1, self.y1, self.x2, self.y1
        
        elif side == SIDE_RIGHT:
            return self.x2, self.y1, self.x2, self.y2
            
        elif side == SIDE_BOTTOM:
            return self.x1, self.y2, self.x2, self.y2
            
        elif side == SIDE_LEFT:
            return self.x1, self.y1, self.x1, self.y2
        
        return None
    
    
    def __repr__(self):
        return 'x1 {}, y1 {}, x2 {}, y2 {}, z {}, sector {}, width {}, height {}, plane {}'.format(self.x1, self.y1, self.x2, self.y2, self.z, self.sector, self.x2 - self.x1, self.y2 - self.y1, self.plane) 