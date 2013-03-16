from nav.navenum import *


class NavElement(object):
    __slots__ = (
        'x', 'y', 'z',
        
        'plane',
        'special_sector',
        'flags',
        
        'elements',
        'area',
        'connection',
        
        'index'
    )

    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        self.plane = None
        self.special_sector = None
        self.flags = 0
        
        self.elements = [None] * 4
        self.area = None
        self.connection = [None] * 4
        
        self.index = -1
        
        
    def __repr__(self):
        return 'element {}, {}, {}, flags {}, sector {}, plane {}'.format(self.x, self.y, round(self.z, 2), self.flags, self.special_sector, self.plane)
   
    
    def is_similar(self, other):       
        if self.plane is not None and other.plane is not None:
            return self.special_sector == other.special_sector and self.flags == other.flags and self.plane == other.plane
        else:
            return self.special_sector == other.special_sector and self.flags == other.flags and self.z == other.z