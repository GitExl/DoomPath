#!/usr/bin/env python
#coding=utf8

from doom import blockmap
from doom.mapobjects import Thing, Linedef, Sidedef, Vertex, Segment, SubSector, Sector, Node
from plane import plane_setup
from util.vector import Vector2, Vector3


# 3D floor line special flag values.
THREED_KIND_SOLID = 0x01
THREED_KIND_SWIMMABLE = 0x02
THREED_KIND_NONSOLID = 0x04
THREED_FLAG_IGNORE_BOTTOM = 0x08

        
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
        self.dest = Vector2()


class MapData(object):
    """
    Reads map data from Doom and Hexen format WAD files.
    
    Does preprocessing for 3d floors, slopes and marks special sectors that may move during gameplay.
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
        self.subsector_sectors = None
        self.linedef_ids = None
        self.teleporters = None
        
        # If True, this map is stored in Hexen format, Doom format otherwise.
        self.is_hexen = False

        # Map bounds.
        self.min_x = 0x80000
        self.max_x = 0
        self.min_y = 0x80000
        self.max_y = 0
        self.min_z = 0x80000
        self.max_z = 0
        
        self.size = Vector3()
        
        self.config = None

        # Find header lump index.
        headerindex = wad_file.get_index(lump_name)
        if headerindex == -1:
            print 'Cannot find map lump {}'.format(lump_name)
        
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
        
        return datalist
    
    
    def set_data_references(self, datalist):
        for item in datalist:
            item.set_references(self)
                
        
    def setup(self, config):
        """
        Sets up additional map data.
        
        @param config: a configuration object containing action and thing information to process.
        """
        
        self.config = config
        
        self.setup_sector_data()
        self.setup_slopes()
        self.setup_threed_floors()
        self.setup_stairs()
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
            if linedef.action in self.config.thing_teleport_specials:
                kind = Teleporter.TELEPORTER_THING
                target_thing = self.get_destination_from_teleport(line_index)
                if target_thing is None:
                    print 'Teleporter linedef {} has no valid destination thing.'.format(line_index)
                    continue
                
                dest = Vector2(target_thing.x, target_thing.y)
                
            # Line to line teleporters.
            elif linedef.action in self.config.line_teleport_specials:
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
                teleporter.dest = dest
            elif kind == Teleporter.TELEPORTER_LINE:
                teleporter.dest_line = dest_line
                
            self.teleporters.append(teleporter)
            

    def calculate_map_size(self):
        """
        Determines the minimum and maximum bounds of the map based on vertex coordinates.
        """
        
        # Calculate map width and height.
        for vertex in self.vertices:
            self.min_x = min(self.min_x, vertex.x)
            self.max_x = max(self.max_x, vertex.x)
            self.min_y = min(self.min_y, vertex.y)
            self.max_y = max(self.max_y, vertex.y)
        self.size.x = self.max_x - self.min_x
        self.size.y = self.max_y - self.min_y

        # Detect map depth.
        for sector in self.sectors:
            floorz = sector.floorz
            ceilz = sector.ceilingz
            self.min_z = min(floorz, min(ceilz, self.min_z))
            self.max_z = max(floorz, max(ceilz, self.max_z))
        self.size.z = self.max_z - self.min_z


    def setup_sector_data(self):
        """
        Processes additional sector data and generates extra structures for them.
        """
        
        # Build a list of subsector to sector mappings.
        # Each subsector's first segment is taken. This segment's linedef is taken, then the
        # sidedef on the segment's side is taken from the linedef. This sidedef contains the
        # sector for the subsector.
        self.subsector_sectors = []
        for subsector in self.subsectors:
            segment = self.segments[subsector.first_segment]
            if segment.direction == Segment.DIRECTION_OPPOSITE:
                sidedef = self.sidedefs[segment.linedef.sidedef_back]
            else:
                sidedef = self.sidedefs[segment.linedef.sidedef_front]
            
            self.subsector_sectors.append(sidedef.sector)
        
        # Build a list of linedefs contained in each sector.
        for linedef in self.linedefs:
            if linedef.sidedef_front != Linedef.SIDEDEF_NONE:
                sidedef = self.sidedefs[linedef.sidedef_front]
            if linedef.sidedef_back != Linedef.SIDEDEF_NONE:
                sidedef = self.sidedefs[linedef.sidedef_back]
            
            self.sectors[sidedef.sector].linedefs.append(linedef)
        
        
    def setup_stairs(self):
        """
        Detects sectors that are affected by stair builder specials.
        """

        for linedef in self.linedefs:
            action = linedef.action
            
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
                tag = linedef.args[0]
            else:
                tag = linedef.tag
                
            # Build stair list for each starting sector.
            start_sectors = self.get_tag_sectors(tag)
            for sector_index in start_sectors:
                current_sector_index = sector_index
                
                # Sectors with a linedef facing into the current sector are added until either
                # there is no more shared linedef or the floor texture is different. 
                while True:
                    current_sector = self.sectors[current_sector_index]
                    current_sector.flags |= Sector.FLAG_MOVES | Sector.FLAG_SPECIAL
                    
                    # Find next sector to mark as special.
                    for sector_linedef in current_sector.linedefs:
                        
                        # Ignore lindefs with only one side.
                        if (sector_linedef.flags & Linedef.FLAG_TWOSIDED) == 0:
                            continue
                        if sector_linedef.sidedef_front == Linedef.SIDEDEF_NONE:
                            continue
                        if sector_linedef.sidedef_back == Linedef.SIDEDEF_NONE:
                            continue
                        
                        # If the front sidedef points to the current sector, the back sidedef references the new sector.
                        sidedef = self.sidedefs[sector_linedef.sidedef_front]
                        if sidedef.sector == current_sector_index:
                            sidedef = self.sidedefs[sector_linedef.sidedef_back]
                            next_sector_index = sidedef.sector
                            break
                    else:
                        break

                    if ignore_floor_texture == False:
                        next_sector = self.sectors[next_sector_index]
                        if next_sector.texture_floor != current_sector.texture_floor:
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
                if linedef.action == self.config.threedfloor_special:
                    sidedef = linedef.sidedef_front
                    if sidedef == Linedef.SIDEDEF_NONE:
                        continue
                    
                    control_sector_index = self.sidedefs[sidedef].sector
                    control_sector = self.sectors[control_sector_index]
                    tag = linedef.args[0]
                    kind = linedef.args[1]
                    
                    target_sectors = self.get_tag_sectors(tag)
                    if len(target_sectors) == 0:
                        continue
                    
                    # 3d floor is non-solid or swimmable, ignore it.
                    if (kind & THREED_KIND_SWIMMABLE) != 0 or (kind & THREED_KIND_NONSOLID) != 0:
                        continue
                    
                    # Solid, swap top and bottom.
                    if (kind & THREED_KIND_SOLID) != 0:
                        control_sector.ceilingz, control_sector.floorz = control_sector.floorz, control_sector.ceiling
                    
                    for sector_index in target_sectors:
                        self.sectors[sector_index].threedfloors.append(control_sector_index)
                        
                    threed_count += 1
                
        # Create sector_floor, sector_ceiling stacks. Even sectors without 3d floors get a single item on the stack.
        for sector_index, sector in enumerate(self.sectors):
            if len(sector.threedfloors) == 0:
                data = (sector_index, sector_index)
                sector.threedstack.append(data)
            
            else:
                # Sort threed floors by their floor height at the center of the target sector.
                center = self.get_sector_center(sector_index)
                sector.threedfloors = sorted(sector.threedfloors, key=lambda threed: self.get_sector_ceil_z(threed, center.x, center.y))
                
                # Create stack of 3d floor top and bottom sector indices.
                sector_top = sector.threedfloors[0]
                data = (sector_index, sector_top)
                sector.threedstack.append(data)

                sector_bottom = sector_top
                for threed_index in range(len(sector.threedfloors)):
                    if threed_index == len(sector.threedfloors) - 1:
                        sector_top = sector_index
                    else:
                        sector_top = sector.threedfloors[threed_index + 1]
                
                    data = (sector_bottom, sector_top)
                    sector.threedstack.append(data)
                    
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
            line_action = line.action
            
            sloped = False
            if self.is_hexen:
                # Hexen slope floor special.
                if line_action == self.config.slope_special:
                    align_floor = line.args[0] & 3
                    align_ceiling = line.args[1] & 3
                    if align_ceiling == 0:
                        align_ceiling = (line.args[0] >> 2) & 3
                        
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
                frontside = self.sidedefs[line.sidedef_front]
                frontsector_index = frontside.sector
                
                backside = self.sidedefs[line.sidedef_back]
                backsector_index = backside.sector
                
                # Floor plane?
                if align_floor == ALIGN_FRONT:
                    plane = plane_setup(self, frontsector_index, self.sectors[frontsector_index].linedefs, line, True)
                    self.sectors[frontsector_index].floor_plane = plane
                    floor_slopes += 1
                elif align_floor == ALIGN_BACK:
                    plane = plane_setup(self, backsector_index, self.sectors[backsector_index].linedefs, line, True)
                    self.sectors[backsector_index].floor_plane = plane
                    floor_slopes += 1
                    
                # Ceiling plane?
                if align_ceiling == ALIGN_FRONT:
                    plane = plane_setup(self, frontsector_index, self.sectors[frontsector_index].linedefs, line, False)
                    self.sectors[frontsector_index].ceiling_plane = plane
                    ceil_slopes += 1
                elif align_ceiling == ALIGN_BACK:
                    plane = plane_setup(self, backsector_index, self.sectors[backsector_index].linedefs, line, False)
                    self.sectors[backsector_index].ceiling_plane = plane
                    ceil_slopes += 1
        
        if floor_slopes > 0:
            print 'Found {} floor slopes.'.format(floor_slopes)
        if ceil_slopes > 0:
            print 'Found {} ceiling slopes.'.format(ceil_slopes)
    
    
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
        elif effect == 'moves':
            sector.flags |= Sector.FLAG_MOVES
        else:
            print 'Unknown sector effect "{}"!'.format(effect)
            
        sector.flags |= Sector.FLAG_SPECIAL


    def setup_lineids(self):
        """
        Detect and store linedefs with an id assigned to them.
        """
        
        if self.is_hexen == True:
            self.linedef_ids = {}
            for index, linedef in enumerate(self.linedefs):
                if linedef.action in self.config.line_identification_specials:
                    line_id = linedef.args[0] + (linedef.args[4] * 256)
                    self.linedef_ids[line_id] = index
        
    
    def analyze(self):
        """
        Analyzes the map and marks sectors that are going to move during gameplay.
        """ 
        
        # Detect tagged and special sectors, these are likely going to move.
        for sector_index, sector in enumerate(self.sectors):
            special = sector.action
            tag = sector.tag
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
            line_type = linedef.action
            if self.is_hexen:
                line_tag = linedef.args[0]
            else:
                line_tag = linedef.tag
                
            # Activates sector on back side?
            if line_tag == 0 and line_type in self.config.backside_activation_specials:
                sidedef = linedef.sidedef_back
                if sidedef != Linedef.SIDEDEF_NONE:
                    sidedef = self.sidedefs[sidedef]
                    sector_index = sidedef.sector
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
                        sidedef = linedef.sidedef_back
                        if sidedef != Linedef.SIDEDEF_NONE:
                            sidedef = self.sidedefs[sidedef]
                            sector_index = sidedef.sector
                            self.apply_extra_effect(sector_index, 'moves')
    
    
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
        
        return self.subsector_sectors[self.point_in_subsector(x, y)]
        
        
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
    
    
    def get_destination_from_teleport(self, line_index):
        """
        Returns a teleport destination thing for a linedef that has a teleport special,
        or None if the teleport is not valid.
        """
        
        linedef = self.linedefs[line_index]
        
        # Hexen style teleporters can have a TID target and a sector tag.
        if self.is_hexen == True:
            dest_tid = linedef.args[0]
            dest_tag = linedef.args[1]
            if dest_tag <= 0:
                dest_tag = None
            
            target_thing = self.get_tid_in_sector(dest_tid, dest_tag)
        
        # Doom style teleporters teleport to a fixed thing type in a tagged sector.
        else:
            dest_tag = linedef.tag
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

            thing_sector_index = self.get_sector(thing.x, thing.y)
            if self.sectors[thing_sector_index].tag == sector_tag:
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


    def point_on_node_side(self, x, y, node):
        if node.delta_x == 0:
            if x <= node.x:
                return node.delta_y > 0
            else:
                return node.delta_y < 0
            
        elif node.delta_y == 0:
            if y <= node.y:
                return node.delta_x < 0
            else:
                return node.delta_x > 0
    
        x -= node.x
        y -= node.y
    
        if (node.delta_y ^ node.delta_x ^ x ^ y) < 0:
            return (node.delta_y ^ x) < 0
        
        return y * node.delta_x >= node.delta_y * x
    
    
    def point_in_subsector(self, x, y):
        node_index = len(self.nodes) - 1
    
        while (node_index & Node.FLAG_SUBSECTOR) == 0:
            if self.point_on_node_side(x, y, self.nodes[node_index]) == 0:
                node_index = self.nodes[node_index].child_right
            else:
                node_index = self.nodes[node_index].child_left
    
        return node_index & ~Node.FLAG_SUBSECTOR