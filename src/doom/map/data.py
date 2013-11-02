#!/usr/bin/env python
#coding=utf8

from doom.actions.list import ActionList
from doom.map import blockmap
from doom.map.objects import Thing, Linedef, Sidedef, Vertex, Segment, SubSector, Sector, Node
from doom.map.setup import MapSetup
from util.vector import Vector2, Vector3
import hashlib


class MapData(object):
    """
    handles map data from Doom and Hexen format WAD files.
    """
    
    def __init__(self, wad_file, lump_name):
        # Raw map data.
        self.vertices = None
        self.linedefs = None
        self.sectors = None
        self.sidedefs = None
        self.things = None
        self.nodes = None
        self.subsectors = None
        self.segments = None
        self.blockmap = None

        # Additional map data, generated from raw data.
        self.linedef_ids = None
        self.teleporters = None
        
        # Registered action types.
        self.actions = ActionList()
        
        # Hash of relevant map data.
        self.hasher = hashlib.md5()
        self.data_hash = None
        
        # If True, this map is stored in Hexen format, Doom format otherwise.
        self.is_hexen = False

        # Map bounds.
        self.min = Vector3(0x8000, 0x8000, 0x8000)
        self.max = Vector3()
        self.size = Vector3()

        # Find map header lump index.
        headerindex = wad_file.get_index(lump_name)
        if headerindex == -1:
            print 'Cannot find map lump {}'.format(lump_name)
            return
        
        # Detect Hexen mode from the presence of a BEHAVIOR lump.
        if len(wad_file.lumps) > headerindex + 11:
            if wad_file.lumps[headerindex + 11].name == 'BEHAVIOR':
                self.is_hexen = True
        
        # Read data lumps.
        self.things = self.read_data(wad_file, headerindex, Thing)
        self.linedefs = self.read_data(wad_file, headerindex, Linedef)
        self.sidedefs = self.read_data(wad_file, headerindex, Sidedef)
        self.vertices = self.read_data(wad_file, headerindex, Vertex)
        self.segments = self.read_data(wad_file, headerindex, Segment)
        self.subsectors = self.read_data(wad_file, headerindex, SubSector)
        self.nodes = self.read_data(wad_file, headerindex, Node)
        self.sectors = self.read_data(wad_file, headerindex, Sector)
        
        # Produce a hash of the final map data.
        self.data_hash = self.hasher.digest()
        self.hasher = None
        
        # Change indices to references where needed.
        self.set_data_references(self.linedefs)
        self.set_data_references(self.segments)
    
    
    def read_data(self, wad_file, index, source_class):
        """
        Reads struct data from a WAD lump.
        
        @param wad_file: WAD file object to read from.
        @param index: the index of the map header lump.
        @param source_class: a class definition describing how to load the lump's data.
        
        @return: a list of source_class objects with the data loaded into them.
        """ 

        data = wad_file.get_lump_index(index + source_class.WAD_INDEX).get_data()
        
        if self.is_hexen == True:
            item_struct = source_class.STRUCT_HEXEN
        else:
            item_struct = source_class.STRUCT_DOOM
        
        datalist = []
        offset = 0
        while offset < len(data):
            item = source_class()
            
            struct_data = data[offset:offset + item_struct.size]
            item_data = item_struct.unpack(struct_data)
            
            item.unpack_from(item_data, self.is_hexen)
            datalist.append(item)
            
            offset += item_struct.size
        
        self.hasher.update(data)
        
        return datalist
    
    
    def set_data_references(self, datalist):
        """
        Sets map object list indices to references.
        """
        
        for item in datalist:
            item.set_references(self)
                
        
    def setup(self, config):
        """
        Sets up additional map data.
        
        @param config: a configuration object containing action and thing information to process.
        """
        
        # Process map data.
        setup = MapSetup(self, config)
        setup.setup()
        
        # Build blockmap.
        self.blockmap = blockmap.BlockMap()
        self.blockmap.generate(self, config)
    
    
    def get_tag_sectors(self, tag):
        """
        Returns a list of sectors that have a specific tag.
        """
        
        sectorlist = []
        
        for sector_index, sector in enumerate(self.sectors):
            if sector.tag == tag:
                sectorlist.append(sector_index)
            
        return sectorlist
    
    
    def get_sector_center(self, sector_index):
        """
        Returns the center point of a sector, in map coordinates.
        """
        
        x_min = -0x8000
        y_min = -0x8000
        x_max = 0x8000
        y_max = 0x8000
        
        for linedef in self.sectors[sector_index].linedefs:
            x_min = max(linedef.vertex1.x, x_min)
            x_max = min(linedef.vertex2.x, x_max)
            y_min = max(linedef.vertex1.y, y_min)
            y_max = min(linedef.vertex2.y, y_max)
                
        return Vector2((x_max - x_min) / 2 + x_min, (y_max - y_min) / 2 + y_min)
    
    
    def get_thing_list(self, type_id):
        """
        Returns a list of things with a specific id.
        """
        
        output = []

        for thing in self.things:
            if thing.doomid == type_id:
                output.append(thing)
                
        return output
    
    
    def get_floor_z(self, x, y):
        """
        Returns the floor Z level at map coordinates x,y.
        """
        
        sector = self.sectors[self.get_sector(x, y)]
        if sector.floor_plane is None:
            return sector.floorz
        else:
            return sector.floor_plane.get_z(x, y)
        
        
    def get_ceil_z(self, x, y):
        """
        Returns the ceiling Z level at map coordinates x,y.
        """
        
        sector = self.sectors[self.get_sector(x, y)]
        if sector.ceiling_plane is None:
            return sector.ceilingz
        else:
            return sector.ceiling_plane.get_z(x, y)
    
    
    def get_sector(self, x, y):
        """
        Returns the sector index at map coordinates x,y.
        """
        
        return self.subsectors[self.point_in_subsector(x, y)].sector
        
        
    def get_sector_floor_z(self, sector_index, x, y):
        """
        Returns the floor Z level at map coordinates x,y inside a specific sector index.
        """
        
        sector = self.sectors[sector_index]
        if sector.floor_plane is None:
            return sector.floorz
        else:
            return sector.floor_plane.get_z(x, y)
    
    
    def get_sector_ceil_z(self, sector_index, x, y):
        """
        Returns the ceiling Z level at map coordinates x,y inside a specific sector index.
        """
        
        sector = self.sectors[sector_index]
        if sector.ceiling_plane is None:
            return sector.ceilingz
        else:
            return sector.ceiling_plane.get_z(x, y)

    
    def get_tid_in_sector(self, tid, sector_tag=None):
        """
        Returns a thing with the specified thing ID in the specified sector,
        or None if the thing could not be found.
        
        @param sector_tag: the sector tag that the thing should be in.
        @param tid: the thing ID of the thing to look for.
        """
        
        for thing in self.things:
            if thing.tid != tid:
                continue

            if sector_tag is not None:
                thing_sector_index = self.get_sector(thing.x, thing.y)
                if self.sectors[thing_sector_index].tag == sector_tag:
                    return thing
            else:
                return thing
            
        return None
            
    
    def get_thingtype_in_sector(self, sector_tag, thing_type):
        """
        Returns a thing with of the specified type in the specified sector,
        or None if the thing could not be found.
        
        @param sector_tag: the sector tag that the thing should be in.
        @param thing_type: the thing type of the thing to look for.
        """
        
        for thing in self.things:
            if thing.doomid != thing_type:
                continue

            if thing.sector.tag == sector_tag:
                return thing
        
        return None
    
    
    def get_line_destination(self, source_index):
        """
        Returns a linedef that is the destination of a line to line teleport special linedef.
        Returns None if no destination could be found.
        """
        
        linedef = self.linedefs[source_index]
        
        dest_line = None
        if self.is_hexen == True:
            dest_id = linedef.args[1]
            dest_line = self.linedef_ids.get(dest_id)
        else:
            dest_tag = linedef.tag
            dest_line = self.get_linedef_by_tag(dest_tag)
            
        return dest_line 
    
    
    def get_linedef_by_tag(self, tag):
        """
        Returns the first linedef with the specified tag, or None of the linedef could not be found.
        """
        
        for linedef in self.linedefs:
            if linedef.tag == tag:
                return linedef
            
        return None
    
    
    def get_line_center(self, line_index):
        """
        Returns the center x and y coordinates of the specified linedef index.
        """
        
        linedef = self.linedefs[line_index]
        x1 = linedef.vertex1.x
        y1 = linedef.vertex1.y
        x2 = linedef.vertex2.x
        y2 = linedef.vertex2.y
                    
        return int(x1 + (x2 - x1) / 2), int(y1 + (y2 - y1) / 2)
    
    
    def point_in_subsector(self, x, y):
        """
        Returns the subsector index that the specified coordinates are in.
        """
        
        node_index = len(self.nodes) - 1
        while (node_index & Node.FLAG_SUBSECTOR) == 0:
            node = self.nodes[node_index]
            
            # Determine on what side the requested coordinates lie.
            if node.delta_x == 0:
                if x <= node.x:
                    side = node.delta_y > 0
                else:
                    side = node.delta_y < 0
                
            elif node.delta_y == 0:
                if y <= node.y:
                    side = node.delta_x < 0
                else:
                    side = node.delta_x > 0
        
            else:
                nx = x - node.x
                ny = y - node.y
            
                if (node.delta_y ^ node.delta_x ^ nx ^ ny) < 0:
                    side = (node.delta_y ^ nx) < 0
                else:
                    side = ny * node.delta_x >= node.delta_y * nx
            
            # Choose the left or right child node.
            node_index = self.nodes[node_index].children[side]
            
        return node_index & ~Node.FLAG_SUBSECTOR


    def apply_extra_effect(self, sector_index, effect):
        """
        Applies an effect string to sector extra data.
        """
        
        sector = self.sectors[sector_index]
        
        if effect == 'damage5':
            sector.damage = 5
        elif effect == 'damage10':
            sector.damage = 10
        elif effect == 'damage20':
            sector.damage = 20
        elif effect == 'ignore':
            sector.flags |= Sector.FLAG_IGNORE
        elif effect == 'floor_moves':
            sector.flags |= Sector.FLAG_FLOOR_MOVES
        elif effect == 'ceiling_moves':
            sector.flags |= Sector.FLAG_CEILING_MOVES
        else:
            print 'Unknown sector effect "{}"!'.format(effect)
            
        sector.flags |= Sector.FLAG_SPECIAL