from util.vector import Vector3


class NavElement(object):
    """
    A single square grid element on a map that the player can stand at.
    """
    
    __slots__ = (
        'pos',
        'plane',
        'special_sector',
        'flags',
        
        'elements',
        'area',
        'connection',
        
        'index'
    )
    
    
    # Element connection direction.
    DIR_UP = 0
    DIR_RIGHT = 1
    DIR_DOWN = 2
    DIR_LEFT = 3
    DIR_RANGE = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT]
    
    # Flags describing properties of this element.
    FLAG_DAMAGE_LOW = 0x0001
    FLAG_DAMAGE_MEDIUM = 0x0002
    FLAG_DAMAGE_HIGH = 0x0004
    FLAG_JUMP_NORTH = 0x0008
    FLAG_JUMP_EAST = 0x0010
    FLAG_JUMP_SOUTH = 0x0020
    FLAG_JUMP_WEST = 0x0040

    
    def __init__(self, x, y, z):
        # Absolute position on the map.
        self.pos = Vector3(x, y, z)
        
        # A plane that is linked to this element.
        self.plane = None
        
        # A sector that is linked to this element.
        self.special_sector = None
        
        # FLags describing this element's properties.
        self.flags = 0
        
        # Elements that this element is connected to.
        self.elements = [None] * 4
        
        # The navigation area that this element belongs to.
        self.area = None
        
        # TODO: ???
        self.connection = [None] * 4
        
        # The index of this element. TODO: Remove and fix element saving to reflect.
        self.index = -1
        
        
    def __repr__(self):
        return 'element {}, flags {}, sector {}, plane {}'.format(self.pos, self.flags, self.special_sector, self.plane)
   
    
    def is_similar(self, other):
        """
        Returns True if this element is similar, but not necessarily equal to, another element. Returns False otherwise.
        """
               
        if self.plane is not None or other.plane is not None:
            return self.special_sector == other.special_sector and self.flags == other.flags and self.plane == other.plane
        else:
            return self.special_sector == other.special_sector and self.flags == other.flags and self.pos.z == other.pos.z