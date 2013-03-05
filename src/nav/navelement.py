from nav.navgrid import DIRECTION_RANGE


class NavElement(object):
    __slots__ = ('x', 'y', 'z', 'special_sector', 'flags', 'elements', 'area', 'index')
    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        self.special_sector = -1
        self.flags = 0
        
        self.elements = [None] * 4
        self.area = None
        
        self.index = -1
        
        
    def __repr__(self):
        return 'element x {}, y {}, z {}, flags {}, sector {}'.format(self.x, self.y, round(self.z, 2), self.flags, self.special_sector)
    
    def __getstate__(self):
        indices = [-1] * 4
        for direction in DIRECTION_RANGE:
            if self.elements[direction] is not None:
                indices[direction] = self.elements[direction].index
        
        return [self.x, self.y, self.z, self.special_sector, self.flags, self.index, indices]
    
    def __setstate__(self, state):
        self.x = state[0]
        self.y = state[1]
        self.z = state[2]
        self.special_sector = state[3]
        self.flags = state[4]
        self.index = state[5]
        self.elements = state[6]
        self.area = None
    
    def __eq__(self, other):
        if other is None:
            return False
        
        return (self.special_sector == other.special_sector and self.flags == other.flags and self.z == other.z)
    
    def __ne__(self, other):
        return not self.__eq__(other)