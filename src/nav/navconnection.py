from util.rectangle import Rectangle
import math


class NavConnection(object):
    """
    A connection between two navigation areas.
    """
    
    __slots__ = (
        'rect',
        'flags',        
        'area_a', 'area_b',
        'linedef'
    )

    
    # Flags to determine connection properties.
    FLAG_AB = 0x1
    FLAG_BA = 0x2
    FLAG_TELEPORTER = 0x4
    
    flag_names = {
        FLAG_AB: 'A->B',
        FLAG_BA: 'B->A',
        FLAG_TELEPORTER: 'teleport'
    }

    
    def __init__(self):
        # Describes this connection's area.
        self.rect = Rectangle()
        
        # Flags to determine the connection type and properties.
        self.flags = 0
        
        # The areas that this connection sits in between. 
        self.area_a = None
        self.area_b = None
        
        # Can refer to a linedef that belongs to this connection, in case of a teleporter.
        self.linedef = None


    def get_flags_string(self):
        """
        Returns a string with the names of this connection's set flags.
        """
        
        flagstrings = []
        for bit in range(0, 3):
            mask = int(math.pow(2, bit))
            if (self.flags & mask) != 0:
                flagstrings.append(self.flag_names[mask])
        
        return ', '.join(flagstrings)
        
    
    def __repr__(self):
        return 'connection {}, {}, linedef {}'.format(self.rect, self.get_flags_string(), self.linedef)