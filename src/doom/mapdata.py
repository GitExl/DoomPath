#!/usr/bin/env python
#coding=utf8

from ctypes import create_string_buffer
from doom import blockmap
from doom.mapenum import *
from doom.trig import point_in_subsector
from lib import mapdata_create, mapdata_put_nodes
from plane import plane_setup
import struct


# Map data structures.
VERTEX_DATA = struct.Struct('<hh')
SECTOR_DATA = struct.Struct('<hh8s8shhh')
SIDEDEF_DATA = struct.Struct('<hh8s8s8sh')
NODE_DATA = struct.Struct('<hhhhhhhhhhhhHH')
SUBSECTOR_DATA = struct.Struct('<HH')
SEGMENT_DATA = struct.Struct('<HHhHhh')

# Doom specific map data structures.
THINGS_DATA_DOOM = struct.Struct('<hhHHH')
LINEDEF_DATA_DOOM = struct.Struct('<HHHHHHH')

# Hexen specific map data structures.
THINGS_DATA_HEXEN = struct.Struct('<HhhhHHHBBBBBB')
LINEDEF_DATA_HEXEN = struct.Struct('<HHHBBBBBBHH')


class SectorExtra(object):
    """
    Container for additional sector information.
    """

    THREEDFLOOR_SECTOR_BOTTOM = 0
    THREEDFLOOR_SECTOR_TOP = 1
    
    
    def __init__(self):
        self.linedefs = []
        self.ceil_plane = None
        self.floor_plane = None
        self.threedfloors = []
        self.threedstack = []
        
        self.is_special = False
        self.moves = False
        self.ignore = False
        self.damage = 0
        
        
class Teleporter(object):
    """
    Container for teleporter data.
    """
    
    TELEPORTER_THING = 0
    TELEPORTER_LINE = 1
    
    
    def __init__(self):
        self.source_line = None
        self.dest_line = None
        self.kind = Teleporter.TELEPORTER_THING
        self.dest_x = 0
        self.dest_y = 0


class MapData(object):
    """
    Reads map data from Doom and Hexen format WAD files.
    
    Does preprocessing for 3d floors, slopes and marks special sectors that may move during gameplay.
    """
    
    # Normalized thing data indices.
    THING_X = 0
    THING_Y = 0
    THING_ANGLE = 0
    THING_TYPE = 0
    THING_FLAGS = 0
    
    # Normalized linedef data indices.
    LINEDEF_ACTION = 0
    LINEDEF_SIDEDEF_FRONT = 0
    LINEDEF_SIDEDEF_BACK = 0
    

    def __init__(self, wad_file, lumpname):
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
        self.subsector_sectors = None
        self.sector_extra = None
        self.linedef_ids = None
        self.teleporters = None

        self.nodes_data = None
        
        # If True, this map is stored in Hexen format, Doom format otherwise.
        self.is_hexen = False

        # Map bounds.
        self.min_x = 0x80000
        self.max_x = 0
        self.min_y = 0x80000
        self.max_y = 0
        self.min_z = 0x80000
        self.max_z = 0
        
        self.width = 0
        self.height = 0
        self.depth = 0
        
        self.config = None

        # Get header lump index.
        headerindex = wad_file.get_index(lumpname)
        if len(wad_file.lumps) > headerindex + 11:
            if wad_file.lumps[headerindex + 11].name == 'BEHAVIOR':
                self.is_hexen = True
                
        # Set indices for Hexen\Doom format access. 
        if self.is_hexen == True:
            self.THING_X = THING_HEXEN_X
            self.THING_Y = THING_HEXEN_Y
            self.THING_ANGLE = THING_HEXEN_ANGLE
            self.THING_TYPE = THING_HEXEN_TYPE
            self.THING_FLAGS = THING_HEXEN_FLAGS
            
            self.LINEDEF_ACTION = LINEDEF_HEXEN_ACTION
            self.LINEDEF_SIDEDEF_FRONT = LINEDEF_HEXEN_SIDEDEF_FRONT
            self.LINEDEF_SIDEDEF_BACK = LINEDEF_HEXEN_SIDEDEF_BACK
            
        else:
            self.THING_X = THING_DOOM_X
            self.THING_Y = THING_DOOM_Y
            self.THING_ANGLE = THING_DOOM_ANGLE
            self.THING_TYPE = THING_DOOM_TYPE
            self.THING_FLAGS = THING_DOOM_FLAGS
            
            self.LINEDEF_ACTION = LINEDEF_DOOM_TYPE
            self.LINEDEF_SIDEDEF_FRONT = LINEDEF_DOOM_SIDEDEF_FRONT
            self.LINEDEF_SIDEDEF_BACK = LINEDEF_DOOM_SIDEDEF_BACK

        # Read format-specific data.
        if self.is_hexen == True:
            self.things, self.things_data = self.read_datalump(wad_file, headerindex + 1, THINGS_DATA_HEXEN)
            self.linedefs, self.linedefs_data = self.read_datalump(wad_file, headerindex + 2, LINEDEF_DATA_HEXEN)
        else:
            self.things, self.things_data = self.read_datalump(wad_file, headerindex + 1, THINGS_DATA_DOOM)
            self.linedefs, self.linedefs_data = self.read_datalump(wad_file, headerindex + 2, LINEDEF_DATA_DOOM)
        
        # Read other data lumps.
        self.sidedefs, self.sidedefs_data = self.read_datalump(wad_file, headerindex + 3, SIDEDEF_DATA)
        self.vertices, self.vertices_data = self.read_datalump(wad_file, headerindex + 4, VERTEX_DATA)
        self.segments, self.segments_data = self.read_datalump(wad_file, headerindex + 5, SEGMENT_DATA)
        self.subsectors, self.subsectors_data = self.read_datalump(wad_file, headerindex + 6, SUBSECTOR_DATA)
        self.nodes, self.nodes_data = self.read_datalump(wad_file, headerindex + 7, NODE_DATA)
        self.sectors, self.sectors_data = self.read_datalump(wad_file, headerindex + 8, SECTOR_DATA)
                
        # Create native map data buffers.
        self.c_mapdata = mapdata_create()
        nodes_buffer = create_string_buffer(self.nodes_data, len(self.nodes_data))
        mapdata_put_nodes(self.c_mapdata, len(self.nodes), nodes_buffer)
        
        
    def setup(self, config):
        """
        Sets up additional map data.
        
        @param config: a configuration object containing action and thing information to process.
        """
        
        self.config = config
        
        self.setup_sector_data()
        self.calculate_map_size()
        self.analyze()
        self.setup_lineids()
        self.build_teleporters()
        
        # Build blockmap.
        self.blockmap = blockmap.BlockMap()
        self.blockmap.generate(self)
        
    
    def build_teleporters(self):
        """
        Builds a list of teleporter objects that reference teleport source and destination locations.
        """
        
        self.teleporters = []
        for line_index, linedef in enumerate(self.linedefs):
            
            # Line to thing teleporters.
            if linedef[self.LINEDEF_ACTION] in self.config.thing_teleport_specials:
                kind = Teleporter.TELEPORTER_THING
                target_thing = self.get_destination_from_teleport(line_index)
                if target_thing is None:
                    print 'Teleporter linedef {} has no valid destination thing.'.format(line_index)
                    continue
                
                dest_x = target_thing[self.THING_X]
                dest_y = target_thing[self.THING_Y]
                
            # Line to line teleporters.
            elif linedef[self.LINEDEF_ACTION] in self.config.line_teleport_specials:
                kind = Teleporter.TELEPORTER_LINE
                dest_line = self.get_line_destination(line_index)
                if dest_line is None:
                    print 'Teleporter linedef {} has no valid destination linedef.'.format(line_index)
                    continue

            else:
                continue

            teleporter = Teleporter()
            teleporter.kind = kind        
            teleporter.source_line = line_index
            if kind == Teleporter.TELEPORTER_THING:
                teleporter.dest_x = dest_x
                teleporter.dest_y = dest_y
            elif kind == Teleporter.TELEPORTER_LINE:
                teleporter.dest_line = dest_line
                
            self.teleporters.append(teleporter)
            

    def calculate_map_size(self):
        """
        Determines the minimum and maximum bounds of the map based on vertex coordinates.
        """
        
        # Calculate map width and height.
        for vertex in self.vertices:
            self.min_x = min(self.min_x, vertex[VERTEX_X])
            self.max_x = max(self.max_x, vertex[VERTEX_X])
            self.min_y = min(self.min_y, vertex[VERTEX_Y])
            self.max_y = max(self.max_y, vertex[VERTEX_Y])
        self.width = self.max_x - self.min_x
        self.height = self.max_y - self.min_y

        # Detect map depth.
        for sector in self.sectors:
            floorz = sector[SECTOR_FLOORZ]
            ceilz = sector[SECTOR_CEILZ]
            self.min_z = min(floorz, min(ceilz, self.min_z))
            self.max_z = max(floorz, max(ceilz, self.max_z))
        self.depth = self.max_z - self.min_z


    def setup_sector_data(self):
        """
        Processes additional sector data and generates extra structures for them.
        """
        
        # Initialise sector extra data list.
        self.sector_extra = [None] * len(self.sectors)
        for sector_index in range(len(self.sectors)):
            self.sector_extra[sector_index] = SectorExtra()            
        
        # Build a list of subsector to sector mappings.
        # Each subsector's first segment is taken. This segment's linedef is taken, then the
        # sidedef on the segment's side is taken from the linedef. This sidedef contains the
        # sector for the subsector.
        self.subsector_sectors = []
        for subsector in self.subsectors:
            segment = self.segments[subsector[SUBSECTOR_FIRST_SEG]]
            
            linedef = self.linedefs[segment[SEGMENT_LINEDEF]]
            if segment[SEGMENT_SIDE] == 1:
                sidedef = linedef[self.LINEDEF_SIDEDEF_BACK]
            else:
                sidedef = linedef[self.LINEDEF_SIDEDEF_FRONT]
            
            self.subsector_sectors.append(self.sidedefs[sidedef][SIDEDEF_SECTOR])
        
        # Build a list of linedefs contained in each sector.
        for linedef in self.linedefs:
            front = linedef[self.LINEDEF_SIDEDEF_FRONT]
            back = linedef[self.LINEDEF_SIDEDEF_BACK]
            
            if front != SIDEDEF_NONE:
                sector = self.sidedefs[front][SIDEDEF_SECTOR]
                self.sector_extra[sector].linedefs.append(linedef)
            if back != SIDEDEF_NONE:
                sector = self.sidedefs[back][SIDEDEF_SECTOR]
                self.sector_extra[sector].linedefs.append(linedef)

        # Generate other sector structures.
        self.setup_slopes()
        self.setup_threed_floors()
        self.setup_stairs()
        
        
    def setup_stairs(self):
        """
        Detects sectors that are affected by stair builder specials.
        """
        
        for linedef in self.linedefs:
            action = linedef[self.LINEDEF_ACTION]
            
            is_boom = (action >= 0x3000 and action <= 0x33FF)
            if not action in self.config.stair_specials and not is_boom:
                continue
            
            # Stair actions start at 0x3000. floor texture ignorance starts at 0x200 in stair action, shifted by 9 bits.
            if is_boom:
                action = action - 0x3000
                ignore_floor_texture = (((action - 0x0200) >> 9) & 0x1) == 0
            else:
                ignore_floor_texture = False
            
            if self.is_hexen:
                tag = linedef[LINEDEF_DOOM_TAG]
            else:
                tag = linedef[LINEDEF_HEXEN_ARG0]
                
            # Build stair list for each starting sector.
            start_sectors = self.get_tag_sectors(tag)
            for sector_index in start_sectors:
                current_sector_index = sector_index
                
                # Sectors with a linedef facing into the current sector are added until either
                # there is no more shared linedef or the floor texture is different. 
                while True:
                    current_sector = self.sectors[current_sector_index]
                    sector_extra = self.sector_extra[current_sector_index]
                    sector_extra.moves = True
                    sector_extra.is_special = True
                    
                    # Find next sector to mark as special.
                    for sector_linedef in sector_extra.linedefs:
                        
                        # Ignore lindefs with only one side.
                        if (sector_linedef[LINEDEF_FLAGS] & LINEDEF_FLAG_TWOSIDED) == 0:
                            continue
                        if sector_linedef[self.LINEDEF_SIDEDEF_FRONT] == SIDEDEF_NONE:
                            continue
                        if sector_linedef[self.LINEDEF_SIDEDEF_BACK] == SIDEDEF_NONE:
                            continue
                        
                        # If the front sidedef points to the current sector, the back sidedef references the new sector.
                        sidedef_front = self.sidedefs[sector_linedef[self.LINEDEF_SIDEDEF_FRONT]]
                        sidedef_back = self.sidedefs[sector_linedef[self.LINEDEF_SIDEDEF_BACK]]
                        if sidedef_front[SIDEDEF_SECTOR] == current_sector_index:
                            next_sector_index = sidedef_back[SIDEDEF_SECTOR]
                            break
                    else:
                        break

                    if ignore_floor_texture == False:
                        next_sector = self.sectors[next_sector_index]
                        if next_sector[SECTOR_FLOORTEX] != current_sector[SECTOR_FLOORTEX]:
                            break
                    current_sector_index = next_sector_index 
                
        
    def setup_threed_floors(self):
        """
        Sets up 3d floor stacks.
        """
        
        threed_count = 0
        
        # Create lists of 3d floors in each sector.
        if self.config.threedfloor_special is not None:
            for linedef in self.linedefs:
                action = linedef[self.LINEDEF_ACTION]
                if action == self.config.threedfloor_special:
                    
                    sidedef = linedef[self.LINEDEF_SIDEDEF_FRONT]
                    if sidedef == SIDEDEF_NONE:
                        continue
                    
                    control_sector_index = self.sidedefs[sidedef][SIDEDEF_SECTOR]
                    control_sector = self.sectors[control_sector_index]
                    tag = linedef[LINEDEF_HEXEN_ARG0]
                    kind = linedef[LINEDEF_HEXEN_ARG1]
                    
                    target_sectors = self.get_tag_sectors(tag)
                    if len(target_sectors) == 0:
                        continue
                    
                    # 3d floor is non-solid or swimmable, ignore it.
                    if (kind & THREED_KIND_SWIMMABLE) != 0 or (kind & THREED_KIND_NONSOLID) != 0:
                        continue
                    
                    # Solid, swap top and bottom.
                    if (kind & THREED_KIND_SOLID) != 0:
                        temp = control_sector[SECTOR_CEILZ]
                        control_sector[SECTOR_CEILZ] = control_sector[SECTOR_FLOORZ]
                        control_sector[SECTOR_FLOORZ] = temp
                    
                    for sector_index in target_sectors:
                        self.sector_extra[sector_index].threedfloors.append(control_sector_index)
                        
                    threed_count += 1
                
        # Create sector_floor, sector_ceiling stacks. Even sectors without 3d floors get a single item on the stack.
        for sector_index, sector_extra in enumerate(self.sector_extra):
            if len(sector_extra.threedfloors) == 0:
                data = (sector_index, sector_index)
                sector_extra.threedstack.append(data)
            
            else:
                # Sort threed floors by their floor height at the center of the target sector.
                center_x, center_y = self.get_sector_center(sector_index)
                sector_extra.threedfloors = sorted(sector_extra.threedfloors, key=lambda threed: self.get_sector_ceil_z(threed, center_x, center_y))
                
                # Create stack of 3d floor top and bottom sector indices.
                sector_top = sector_extra.threedfloors[0]
                data = (sector_index, sector_top)
                sector_extra.threedstack.append(data)

                sector_bottom = sector_top
                for threed_index in range(len(sector_extra.threedfloors)):
                    if threed_index == len(sector_extra.threedfloors) - 1:
                        sector_top = sector_index
                    else:
                        sector_top = sector_extra.threedfloors[threed_index + 1]
                
                    data = (sector_bottom, sector_top)
                    sector_extra.threedstack.append(data)
                    
                    sector_bottom = sector_top
                            
        if threed_count > 0:
            print 'Found {} 3D floors.'.format(threed_count)
                    
    
    def setup_slopes(self):
        """
        Sets up slope planes from slope specials.
        """
        
        if self.config.slope_special is None:
            return
        
        ALIGN_NONE = 0
        ALIGN_FRONT = 1
        ALIGN_BACK = 2
        
        floor_slopes = 0
        ceil_slopes = 0
        
        for line in self.linedefs:
            line_action = line[self.LINEDEF_ACTION]
            
            sloped = False
            if self.is_hexen:
                # Hexen slope floor special.
                if line_action == self.config.slope_special:
                    align_floor = line[LINEDEF_HEXEN_ARG0] & 3
                    align_ceiling = line[LINEDEF_HEXEN_ARG1] & 3
                    if align_ceiling == 0:
                        align_ceiling = (line[LINEDEF_HEXEN_ARG0] >> 2) & 3
                        
                    sloped = True
                
            # Doom style sloped floors.
            elif line_action >= self.config.slope_special and line_action <= self.config.slope_special + 7:
                line_action -= self.config.slope_special
                if line_action == 0:
                    align_floor = ALIGN_FRONT
                    align_ceiling = ALIGN_NONE
                elif line_action == 1:
                    align_floor = ALIGN_NONE
                    align_ceiling = ALIGN_FRONT
                elif line_action == 2:
                    align_floor = ALIGN_FRONT
                    align_ceiling = ALIGN_FRONT
                elif line_action == 3:
                    align_floor = ALIGN_BACK
                    align_ceiling = ALIGN_NONE
                elif line_action == 4:
                    align_floor = ALIGN_NONE
                    align_ceiling = ALIGN_BACK
                elif line_action == 5:
                    align_floor = ALIGN_BACK
                    align_ceiling = ALIGN_BACK
                elif line_action == 6:
                    align_floor = ALIGN_BACK
                    align_ceiling = ALIGN_FRONT
                elif line_action == 7:
                    align_floor = ALIGN_FRONT
                    align_ceiling = ALIGN_BACK
                
                sloped = True
            
            if sloped == True:
                front = line[self.LINEDEF_SIDEDEF_FRONT]
                frontsector = self.sidedefs[front][SIDEDEF_SECTOR] 
                
                back = line[self.LINEDEF_SIDEDEF_BACK]
                backsector = self.sidedefs[back][SIDEDEF_SECTOR]
                
                # Floor plane?
                if align_floor == ALIGN_FRONT:
                    plane = plane_setup(self, frontsector, self.sector_extra[frontsector].linedefs, line, True)
                    self.sector_extra[frontsector].floor_plane = plane
                    floor_slopes += 1
                elif align_floor == ALIGN_BACK:
                    plane = plane_setup(self, backsector, self.sector_extra[backsector].linedefs, line, True)
                    self.sector_extra[backsector].floor_plane = plane
                    floor_slopes += 1
                    
                # Ceiling plane?
                if align_ceiling == ALIGN_FRONT:
                    plane = plane_setup(self, frontsector, self.sector_extra[frontsector].linedefs, line, False)
                    self.sector_extra[frontsector].ceil_plane = plane
                    ceil_slopes += 1
                elif align_ceiling == ALIGN_BACK:
                    plane = plane_setup(self, backsector, self.sector_extra[backsector].linedefs, line, False)
                    self.sector_extra[backsector].ceil_plane = plane
                    ceil_slopes += 1
        
        if floor_slopes > 0:
            print 'Found {} floor slopes.'.format(floor_slopes)
        if ceil_slopes > 0:
            print 'Found {} ceiling slopes.'.format(ceil_slopes)
    
    
    def apply_extra_effect(self, sector_index, effect):
        """
        Applies an effect string to sector extra data.
        """
        
        sector_extra = self.sector_extra[sector_index]
        
        if effect == 'damage5':
            sector_extra.damage = 5
        elif effect == 'damage10':
            sector_extra.damage = 10
        elif effect == 'damage20':
            sector_extra.damage = 20
        elif effect == 'ignore':
            sector_extra.ignore = True
        elif effect == 'moves':
            sector_extra.moves = True
        else:
            print 'Unknown sector effect "{}"!'.format(effect)
            
        sector_extra.is_special = True


    def setup_lineids(self):
        """
        Detect and store linedefs with an id assigned to them.
        """
        
        if self.is_hexen == True:
            self.linedef_ids = {}
            for index, linedef in enumerate(self.linedefs):
                if linedef[self.LINEDEF_ACTION] in self.config.line_identification_specials:
                    line_id = linedef[LINEDEF_HEXEN_ARG0] + (linedef[LINEDEF_HEXEN_ARG4] * 256)
                    self.linedef_ids[line_id] = index
        
    
    def analyze(self):
        """
        Analyzes the map and marks sectors that are going to move during gameplay.
        """ 
        
        # Detect tagged and special sectors, these are likely going to move.
        for sector_index, sector in enumerate(self.sectors):
            special = sector[SECTOR_SPECIAL]
            tag = sector[SECTOR_TAG]
            value = self.config.sector_types.get(special)
            
            # Special tags.
            if tag == 667 or tag == 666:
                self.apply_extra_effect(sector_index, 'moves')
            
            # Registered special sector type.
            elif value is not None:
                self.apply_extra_effect(sector_index, value)
                
            # Boom generalized sector types.
            else:
                for flag, value in self.config.sector_generalized_types.iteritems():
                    if (special & flag) != 0:
                        self.apply_extra_effect(sector_index, value)
            
        # Detect linedef activation.
        for linedef in self.linedefs:
            line_type = linedef[self.LINEDEF_ACTION]
            if self.is_hexen:
                line_tag = linedef[LINEDEF_HEXEN_ARG0]
            else:
                line_tag = linedef[LINEDEF_DOOM_TAG]
                
            # Activates sector on back side?
            if line_tag == 0 and line_type in self.config.backside_activation_specials:
                sidedef = linedef[self.LINEDEF_SIDEDEF_BACK]
                if sidedef != SIDEDEF_NONE:
                    sidedef = self.sidedefs[sidedef]
                    sector_index = sidedef[SIDEDEF_SECTOR]
                    self.apply_extra_effect(sector_index, 'moves')
            
            # Activates tagged sector?
            elif line_tag != 0 and (line_type in self.config.tag_activation_specials or line_type in self.config.backside_activation_specials):
                target_sectors = self.get_tag_sectors(line_tag)
                for sector_index in target_sectors:
                    self.apply_extra_effect(sector_index, 'moves')
                    
            # Boom generalized linedef?
            elif self.config.generalized_specials is not None and line_type >= 0x2F80:
                for shift in self.config.generalized_specials:
                    
                    # Sector tag activation of switch, walk and shoot triggers.
                    activation_type = ((line_type - shift) & 0x7)
                    if line_tag != 0:
                        target_sectors = self.get_tag_sectors(line_tag)
                        for sector_index in target_sectors:
                            self.apply_extra_effect(sector_index, 'moves')
                    
                    # Backside activation of door triggers.
                    elif activation_type >= 6 and line_tag == 0:
                        sidedef = linedef[self.LINEDEF_SIDEDEF_BACK]
                        if sidedef != SIDEDEF_NONE:
                            sidedef = self.sidedefs[sidedef]
                            sector_index = sidedef[SIDEDEF_SECTOR]
                            self.apply_extra_effect(sector_index, 'moves')
                  

    def read_datalump(self, wad_file, index, datastruct):
        """
        Reads struct data from a WAD lump.
        
        @param wad_file: WAD file object to read from.
        @param index: the lump index to read.
        @param datastruct: a Struct object that determines the data format to read.
        
        @return: a tuple containing a list of data that was read, and the raw data itself.
        """ 
        
        datalist = []
        data = wad_file.get_lump_index(index).get_data()
        datasize = datastruct.size

        for index in range(0, len(data), datasize):
            item = list(datastruct.unpack(data[index:index + datasize]))
            datalist.append(item)
        
        return datalist, data
    
    
    def get_tag_sectors(self, tag):
        """
        Returns a list of sectors that have a specific tag.
        """
        
        sectors = []
        
        for sector_index, sector in enumerate(self.sectors):
            if sector[SECTOR_TAG] == tag:
                sectors.append(sector_index)
            
        return sectors
    
    
    def get_sector_center(self, sector_index):
        """
        Returns the center point of a sector, in map coordinates.
        """
        
        x_min = -0x8000
        y_min = -0x8000
        x_max = 0x8000
        y_max = 0x8000
        
        for linedef in self.sector_extra[sector_index].linedefs:
            vertex1 = self.vertices[linedef[LINEDEF_VERTEX_1]]
            vertex2 = self.vertices[linedef[LINEDEF_VERTEX_2]]
            
            x1 = vertex1[VERTEX_X]
            y1 = vertex1[VERTEX_Y]
            x2 = vertex2[VERTEX_X]
            y2 = vertex2[VERTEX_Y]
            
            x_min = max(x1, x_min)
            x_max = min(x2, x_max)
            y_min = max(y1, y_min)
            y_max = min(y2, y_max)
                
        return (x_max - x_min) / 2 + x_min, (y_max - y_min) / 2 + y_min
    
    
    def get_thing_list(self, type_id):
        """
        Returns a list of things with a specific id.
        """
        
        output = []

        for thing in self.things:
            if thing[self.THING_TYPE] == type_id:
                output.append(thing)
                
        return output
    
    
    def get_floor_z(self, x, y):
        """
        Returns the floor Z level at map coordinates x,y.
        """
        
        sector_index = self.get_sector(x, y)
        
        plane = self.sector_extra[sector_index].floor_plane
        if plane is None:
            sector = self.sectors[sector_index]
            return sector[SECTOR_FLOORZ]
        else:
            return plane.get_z(x, y)
        
        
    def get_ceil_z(self, x, y):
        """
        Returns the ceiling Z level at map coordinates x,y.
        """
        
        sector_index = self.get_sector(x, y)
        
        plane = self.sector_extra[sector_index].ceil_plane
        if plane is None:
            sector = self.sectors[sector_index]
            return sector[SECTOR_CEILZ]
        else:
            return plane.get_z(x, y)
    
    
    def get_sector(self, x, y):
        """
        Returns the sector index at map coordinates x,y.
        """
        
        subsector_index = point_in_subsector(self.c_mapdata, x, y)
        sector_index = self.subsector_sectors[subsector_index]
        
        return sector_index 
        
        
    def get_sector_floor_z(self, sector_index, x, y):
        """
        Returns the floor Z level at map coordinates x,y inside a specific sector index.
        """
        
        plane = self.sector_extra[sector_index].floor_plane
      
        if plane is None:
            return self.sectors[sector_index][SECTOR_FLOORZ]
        else:
            return plane.get_z(x, y)
    
    
    def get_sector_ceil_z(self, sector_index, x, y):
        """
        Returns the ceiling Z level at map coordinates x,y inside a specific sector index.
        """
        
        plane = self.sector_extra[sector_index].ceil_plane
      
        if plane is None:
            return self.sectors[sector_index][SECTOR_CEILZ]
        else:
            return plane.get_z(x, y)
    
    
    def get_destination_from_teleport(self, line_index):
        """
        Returns a teleport destination thing for a linedef that has a teleport special,
        or None if the teleport is not valid.
        """
        
        linedef = self.linedefs[line_index]
        
        # Hexen style teleporters can have a TID target and a sector tag.
        if self.is_hexen == True:
            dest_tid = linedef[LINEDEF_HEXEN_ARG0]
            dest_tag = linedef[LINEDEF_HEXEN_ARG1]
            if dest_tag <= 0:
                dest_tag = None
            
            target_thing = self.get_tid_in_sector(dest_tid, dest_tag)
        
        # Doom style teleporters teleport to a fixed thing type in a tagged sector.
        else:
            dest_tag = linedef[LINEDEF_DOOM_TAG]
            target_thing = self.get_thingtype_in_sector(dest_tag, self.config.teleport_thing_type) 
        
        return target_thing

    
    def get_tid_in_sector(self, tid, sector_tag=None):
        """
        Returns a thing with the specified thing ID in the specified sector,
        or None if the thing could not be found.
        
        @param sector_tag: the sector tag that the thing should be in.
        @param tid: the thing ID of the thing to look for.
        """
        
        for thing in self.things:
            if thing[THING_HEXEN_ID] != tid:
                continue

            if sector_tag is not None:
                thing_sector_index = self.get_sector(thing[self.THING_X], thing[self.THING_Y])
                if self.sectors[thing_sector_index][SECTOR_TAG] == sector_tag:
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
            if thing[self.THING_TYPE] != thing_type:
                continue

            thing_sector_index = self.get_sector(thing[self.THING_X], thing[self.THING_Y])
            if self.sectors[thing_sector_index][SECTOR_TAG] == sector_tag:
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
            dest_id = linedef[LINEDEF_HEXEN_ARG1]
            dest_line = self.linedef_ids.get(dest_id)
        else:
            dest_tag = linedef[LINEDEF_DOOM_TAG]
            dest_line = self.get_linedef_by_tag(dest_tag)
            
        return dest_line 
    
    
    def get_linedef_by_tag(self, tag):
        """
        Returns the first linedef with the specified tag, or None of the linedef could not be found.
        """
        
        for linedef in self.linedefs:
            if linedef[LINEDEF_DOOM_TAG] == tag:
                return linedef
            
        return None
    
    
    def get_line_center(self, line_index):
        """
        Returns the center x and y coordinates of the specified linedef index.
        """
        
        linedef = self.linedefs[line_index]
        vertex1 = self.vertices[linedef[LINEDEF_VERTEX_1]]
        vertex2 = self.vertices[linedef[LINEDEF_VERTEX_2]]
        
        x1 = vertex1[VERTEX_X]
        y1 = vertex1[VERTEX_Y]
        x2 = vertex2[VERTEX_X]
        y2 = vertex2[VERTEX_Y]
        
        return x1 + int((x2 - x1) / 2), y1 + int((y2 - y1) / 2)