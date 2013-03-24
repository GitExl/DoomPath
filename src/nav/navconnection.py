from util.rectangle import Rectangle
import math


CONNECTION_FLAG_AB = 0x1
CONNECTION_FLAG_BA = 0x2
CONNECTION_FLAG_TELEPORTER = 0x4

flag_names = {
    CONNECTION_FLAG_AB: 'A->B',
    CONNECTION_FLAG_BA: 'B->A',
    CONNECTION_FLAG_TELEPORTER: 'teleport'
}


class NavConnection(object):
    __slots__ = (
        'rect',
        'flags',
        
        'area_a', 'area_b',
        'linedef'
    )

    
    def __init__(self):
        self.rect = Rectangle()
        self.flags = 0
        
        self.area_a = None
        self.area_b = None
        self.linedef = None

    
    def __repr__(self):
        flagstrings = []
        for bit in range(0, 3):
            mask = int(math.pow(2, bit))
            if (self.flags & mask) != 0:
                flagstrings.append(flag_names[mask])
        flagstring = ', '.join(flagstrings)
        
        return 'connection {}, {}, linedef {}'.format(self.rect, flagstring, self.linedef)