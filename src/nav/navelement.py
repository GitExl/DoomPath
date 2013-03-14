from nav.navenum import *


class NavElement(object):
    __slots__ = ('x', 'y', 'z', 'plane', 'special_sector', 'flags', 'elements', 'area', 'index')

    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        self.plane = None
        self.special_sector = None
        self.flags = 0
        
        self.elements = [None] * 4
        self.area = None
        
        self.index = -1
        
        
    def __repr__(self):
        return 'element x {}, y {}, z {}, flags {}, sector {}, plane {}'.format(self.x, self.y, round(self.z, 2), self.flags, self.special_sector, self.plane)
    
    
    def __getstate__(self):
        indices = [-1] * 4
        for direction in DIRECTION_RANGE:
            if self.elements[direction] is not None:
                indices[direction] = self.elements[direction].index
        
        return [self.x, self.y, self.z, self.plane, self.special_sector, self.flags, self.index, indices]
    
    
    def __setstate__(self, state):
        self.x = state[0]
        self.y = state[1]
        self.z = state[2]
        self.plane = state[3]
        self.special_sector = state[4]
        self.flags = state[5]
        self.index = state[6]
        self.elements = state[7]
        self.area = None
   
    
    def __eq__(self, other):       
        if self.plane is not None and other.plane is not None:
            return self.special_sector == other.special_sector and self.flags == other.flags and self.plane == other.plane
        else:
            return self.special_sector == other.special_sector and self.flags == other.flags and self.z == other.z
    
    
    def __ne__(self, other):
        return not self.__eq__(other)