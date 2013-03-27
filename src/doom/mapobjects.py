#!/usr/bin/env python
#coding=utf8

from util.rectangle import Rectangle
import struct


class MapObject(object):
    __slots__ = ()
    
    STRUCT_DOOM = None
    STRUCT_HEXEN = None
    WAD_INDEX = None
    
    
    def unpack_from(self, data, is_hexen):
        raise Exception('Undefined unpack_from in MapObject child.')
    
    def set_references(self, map_data):
        pass
    
    def __repr__(self):
        raise Exception('Undefined __repr__ in MapObject child.')


class Vertex(MapObject):
    __slots__ = (
        'x',
        'y'
    )
    
    STRUCT_DOOM = struct.Struct('<hh')
    STRUCT_HEXEN = struct.Struct('<hh')
    WAD_INDEX = 4
    
    
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        
        
    def unpack_from(self, data, is_hexen):
        self.x = data[0]
        self.y = data[1]
    
    
    def set_references(self, map_data):
        pass


    def __repr__(self):
        return 'Vertex: x {}, y {}'.format(self.x, self.y)


class Linedef(MapObject):
    __slots__ = (
        'vertex1',
        'vertex2',
        
        'flags',
        
        'action',
        'tag',
        'args',
        
        'sidedef_front',
        'sidedef_back'
    )
    
    STRUCT_DOOM = struct.Struct('<HHHHHHH')
    STRUCT_HEXEN = struct.Struct('<HHHBBBBBBHH')
    WAD_INDEX = 2

    # Common flags.
    FLAG_IMPASSIBLE = 0x0001
    FLAG_BLOCKMONSTERS = 0x0002
    FLAG_TWOSIDED = 0x0004
    FLAG_UPPERUNPEG = 0x0008
    FLAG_LOWERUNPEG = 0x0010
    FLAG_SECRET = 0x0020
    FLAG_BLOCKSOUND = 0x0040
    FLAG_DONTDRAW = 0x0080
    FLAG_ALWAYSDRAW = 0x0100
    
    # Hexen flags.
    FLAG_HEXEN_REPEATEDUSE = 0x0200
    FLAG_HEXEN_PLAYERUSE = 0x0400
    FLAG_HEXEN_MONSTERCROSS = 0x0800
    FLAG_HEXEN_PROJECTILEUSE = 0x0C00
    FLAG_HEXEN_PLAYERBUMP = 0x1000
    FLAG_HEXEN_PROJECTILECROSS = 0x1400
    FLAG_HEXEN_PLAYERUSE_PASSTHROUGH = 0x1800
    FLAG_HEXEN_PLAYERSANDMONSTERS = 0x2000
    FLAG_HEXEN_UNUSED = 0x4000
    FLAG_HEXEN_BLOCKALL = 0x8000
    
    # Unused sidedef indicator.
    SIDEDEF_NONE = 0xFFFF

    
    def __init__(self, vertex1=None, vertex2=None):
        self.vertex1 = vertex1
        self.vertex2 = vertex2
        
        self.flags = 0
        
        self.action = 0
        self.tag = 0
        self.args = [0] * 5
        
        self.sidedef_front = Linedef.SIDEDEF_NONE
        self.sidedef_back = Linedef.SIDEDEF_NONE
    
    
    def unpack_from(self, data, is_hexen):
        if is_hexen == True:
            self.vertex1 = data[0]
            self.vertex2 = data[1]
            
            self.flags = data[2]
            
            self.action = data[3]
            self.args[0] = data[4]
            self.args[1] = data[5]
            self.args[2] = data[6]
            self.args[3] = data[7]
            self.args[4] = data[8]
            
            self.sidedef_front = data[9]
            self.sidedef_back = data[10]
        
        else:
            self.vertex1 = data[0]
            self.vertex2 = data[1]
            
            self.flags = data[2]
            
            self.action = data[3]
            self.tag = data[4]
            
            self.sidedef_front = data[5]
            self.sidedef_back = data[6]
    
    
    def set_references(self, map_data):
        self.vertex1 = map_data.vertices[self.vertex1]
        self.vertex2 = map_data.vertices[self.vertex2]
    
    
    def __repr__(self):
        return 'Linedef: front {}, back {}, flags {}, action {}, args {}'.format(self.sidedef_front, \
                                                                self.sidedef_back, self.flags, self.action, self.args)
        
    
class Sidedef(MapObject):
    __slots__ = (
        'offset_x',
        'offset_y',
        
        'texture_upper',
        'texture_lower',
        'texture_middle',
        
        'sector'
    )
    
    STRUCT_DOOM = struct.Struct('<hh8s8s8sh')
    STRUCT_HEXEN = struct.Struct('<hh8s8s8sh')
    WAD_INDEX = 3
    
    
    def __init__(self, sector=-1):
        self.offset_x = 0
        self.offset_y = 0
        
        self.texture_upper = None
        self.texture_lower = None
        self.texture_middle = None
        
        self.sector = sector
    
    
    def unpack_from(self, data, is_hexen):
        self.offset_x = data[0]
        self.offset_y = data[1]
        
        self.texture_upper = data[2]
        self.texture_lower = data[3]
        self.texture_middle = data[4]
        
        self.sector = data[5]
    
    
    def set_references(self, map_data):
        pass
    
    
    def __repr__(self):
        return 'Sidedef: upper {}, lower {}, middle {}, sector {}'.format(self.texture_upper, self.texture_lower, \
                                                                          self.texture_middle, self.sector)


class Sector(MapObject):
    __slots__ = (
        'floorz',
        'ceilingz',
        
        'texture_floor',
        'texture_ceiling',
        
        'lightlevel',
        
        'action',
        'tag'
    )
    
    STRUCT_DOOM = struct.Struct('<hh8s8shhh')
    STRUCT_HEXEN = struct.Struct('<hh8s8shhh')
    WAD_INDEX = 8


    def __init__(self):
        self.floorz = 0
        self.ceilingz = 128
        
        self.texture_floor = None
        self.texture_ceiling = None
        
        self.lightlevel = 255
        
        self.action = 0
        self.tag = 0
        
    
    def unpack_from(self, data, is_hexen):
        self.floorz = data[0]
        self.ceilingz = data[1]
        
        self.texture_floor = data[2]
        self.texture_ceiling = data[3]
        
        self.lightlevel = data[4]
        
        self.action = data[5]
        self.tag = data[6]
    
    
    def set_references(self, map_data):
        pass
    
    
    def __repr__(self):
        return 'Sector: floorz {}, ceilingz {}, floor {}, ceiling {}, light {}, tag {}'.format(self.floorz, \
                                self.ceilingz, self.texture_floor, self.texture_ceiling, self.lightlevel, self.tag)
        

class Thing(MapObject):
    __slots__ = (
        'x',
        'y',
        'z',
        'angle',
        
        'doomid',
        'flags',
        
        'tid',
        'action',
        'args'
    )
    
    STRUCT_DOOM = struct.Struct('<hhHHH')
    STRUCT_HEXEN = struct.Struct('<HhhhHHHBBBBBB')
    WAD_INDEX = 1

    # Common flags.
    FLAG_EASY = 0x0001
    FLAG_MEDIUM = 0x0002
    FLAG_HARD = 0x0004
    FLAG_AMBUSH = 0x0008
    
    # Doom flags.
    FLAG_DOOM_NOTSINGLE = 0x0010
    FLAG_DOOM_NOTDM = 0x0020
    FLAG_DOOM_NOTCOOP = 0x0040
    
    # Hexen flags.
    FLAG_HEXEN_DORMANT = 0x0010
    FLAG_HEXEN_FIGHTER = 0x0020
    FLAG_HEXEN_CLERIC = 0x0040
    FLAG_HEXEN_MAGE = 0x0080
    FLAG_HEXEN_SP = 0x0100
    FLAG_HEXEN_COOP = 0x0200
    FLAG_HEXEN_DM = 0x0400

    
    def __init__(self, doomid=0, x=0, y=0):
        self.x = x
        self.y = y
        self.z = 0
        self.angle = 0
        
        self.doomid = 0
        self.flags = 0
        
        self.tid = 0
        self.action = 0
        self.args = [0] * 5
    
    
    def unpack_from(self, data, is_hexen):
        if is_hexen == True:
            self.tid = data[0]
            
            self.x = data[1]
            self.y = data[2]
            self.z = data[3]
            self.angle = data[4]
            
            self.doomid = data[5]
            self.flags = data[6]
            
            self.action = data[7]
            self.args[0] = data[8]
            self.args[1] = data[9]
            self.args[2] = data[10]
            self.args[3] = data[11]
            self.args[4] = data[12]
        
        else:
            self.x = data[0]
            self.y = data[1]
            self.angle = data[2]

            self.doomid = data[3]
            self.flags = data[4]
    
    
    def set_references(self, map_data):
        pass
    
    
    def __repr__(self):
        return 'Thing: x {}, y {}, z {}, angle {}, id {}, flags {}, action {}, args {}'.format(self.x, self.y, \
                                                self.z, self.angle, self.doomid, self.flags, self.action, self.args)


class Segment(MapObject):
    __slots__ = (
        'vertex_start',
        'vertex_end',
        'linedef',
        
        'angle',
        'direction',
        'offset'
    )
    
    STRUCT_DOOM = struct.Struct('<HHhHhh')
    STRUCT_HEXEN = struct.Struct('<HHhHhh')
    WAD_INDEX = 5
    
    # Segment direction. Same or opposite of linedef direction.
    DIRECTION_SAME = 0
    DIRECTION_OPPOSITE = 1
    
    
    def __init__(self, vertex_start=None, vertex_end=None):
        self.vertex_start = vertex_start
        self.vertex_end = vertex_end
        self.linedef = None
        
        self.angle = 0
        self.direction = Segment.DIRECTION_SAME
        self.offset = 0
    
    
    def unpack_from(self, data, is_hexen):
        self.vertex_start = data[0]
        self.vertex_end = data[1]
        self.angle = data[2]
        self.linedef = data[3]
        self.direction = data[4]
        self.offset = data[5]
    
    
    def set_references(self, map_data):
        self.vertex_start = map_data.vertices[self.vertex_start]
        self.vertex_end = map_data.vertices[self.vertex_end]
        self.linedef = map_data.linedefs[self.linedef]
    
    
    def __repr__(self):
        return 'Segment: start {}, end {}, angle {}, direction {}, offset {}'.format(self.vertex_start, \
                                                            self.vertex_end, self.angle, self.direction, self.offset)
        
        
class Node(MapObject):
    __slots__ = (
        'x',
        'y',
        
        'delta_x',
        'delta_y',
        
        'bb_right',
        'bb_left',
        'child_left',
        'child_right'
    )
    
    STRUCT_DOOM = struct.Struct('<hhhhhhhhhhhhHH')
    STRUCT_HEXEN = struct.Struct('<hhhhhhhhhhhhHH')
    WAD_INDEX = 7

    # Indicates that the node index is actually a subsector index.
    FLAG_SUBSECTOR = 0x8000
    
    
    def __init__(self, x=0, y=0):
        self.x = 0
        self.y = 0
        
        self.delta_x = 0
        self.delta_y = 0
        
        self.bb_right = Rectangle()
        self.bb_left = Rectangle()
        self.child_right = 0
        self.child_left = 0
    
    
    def unpack_from(self, data, is_hexen):
        self.x = data[0]
        self.y = data[1]
        
        self.delta_x = data[2]
        self.delta_y = data[3]
        
        self.bb_right.set(data[4], data[5], data[6], data[7])
        self.bb_left.set(data[8], data[9], data[10], data[11])
        
        self.child_right = data[12]
        self.child_left = data[13]
    
    
    def set_references(self, map_data):
        pass


    def __repr__(self):
        return 'Node: x {}, y {}, right {}, left {}'.format(self.x, self.y, self.bb_right, self.bb_left)
        

class SubSector(MapObject):
    __slots__ = (
        'segment_count',
        'first_segment'
    )
    
    STRUCT_DOOM = struct.Struct('<HH')
    STRUCT_HEXEN = struct.Struct('<HH')
    WAD_INDEX = 6
    
    
    def __init__(self, first_segment=0):
        self.segment_count = 0
        self.first_segment = first_segment
    
    
    def unpack_from(self, data, is_hexen):
        self.segment_count = data[0]
        self.first_segment = data[1]
    
    
    def set_references(self, map_data):
        pass

    
    def __repr__(self):
        return 'SubSector: segments {}'.format(self.segment_count)