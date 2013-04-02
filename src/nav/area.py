from util.rectangle import Rectangle


class Area(object):
    """
    A navigation area.
    
    This describes a rectangle in which movement is freely possible. Connections to other
    navigation areas allow pathfinding throughout a map.
    """
    
    __slots__ = (
        'rect',
        'z',
        
        'sector',
        'flags',
        'plane',
        'connections',

        'elements',        
        'inside_rect',
        
        'path',
        'visited'
    )
    

    # Sides of a navigation area.    
    SIDE_TOP = 0
    SIDE_RIGHT = 1
    SIDE_BOTTOM = 2
    SIDE_LEFT = 3
    
    SIDE_RANGE = [SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM, SIDE_LEFT]
    SIDE_RANGE_OPPOSITE = [SIDE_BOTTOM, SIDE_LEFT, SIDE_TOP, SIDE_RIGHT]
    
    
    def __init__(self, x1, y1, x2, y2, z):
        # Position and size.
        self.rect = Rectangle(x1, y1, x2, y2)
        
        # Average Z location of this area. If the area has a slope, this
        # should not be used.
        self.z = z
        
        # Can refer to a sector index to which this navigation area is linked. If the
        # sector's floor or ceiling moves, this area will need to be updated along with it. 
        self.sector = None
        
        # Flags, taken from a NavElement object.
        self.flags = 0
        
        # A plane describing the surface of this area.
        self.plane = None
        
        # Connection objects leading into other navigation areas.
        self.connections = []
        
        # For internal use, to track elements belonging to this area.
        self.elements = []
        self.inside_rect = Rectangle()
        
        self.path = False
        self.visited = False


    def get_side(self, side):
        """
        Returns the start and end coordinates of a side of this area.
        """
        
        if side == Area.SIDE_TOP:
            return self.rect.left, self.rect.top, self.rect.right, self.rect.top
        elif side == Area.SIDE_RIGHT:
            return self.rect.right, self.rect.top, self.rect.right, self.rect.bottom            
        elif side == Area.SIDE_BOTTOM:
            return self.rect.left, self.rect.bottom, self.rect.right, self.rect.bottom
        elif side == Area.SIDE_LEFT:
            return self.rect.left, self.rect.top, self.rect.left, self.rect.bottom
        
        return None
    
    
    def __repr__(self):
        return 'area {}, z {}, sector {}, width {}, height {}, plane {}, flags {}, connections {}'.format(self.rect, self.z, self.sector, self.rect.get_width(), self.rect.get_height(), self.plane, self.flags, len(self.connections)) 