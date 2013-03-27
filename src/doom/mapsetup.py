from doom.mapobjects import Teleporter, Segment, Linedef, Sector
from doom.plane import plane_setup
from util.vector import Vector2


# 3D floor line special flag values.
THREED_KIND_SOLID = 0x01
THREED_KIND_SWIMMABLE = 0x02
THREED_KIND_NONSOLID = 0x04
THREED_FLAG_IGNORE_BOTTOM = 0x08


class MapSetup(object):
    
    def __init__(self, map_data):
        self.map_data = map_data
        
    
    def setup(self):
        self.setup_sector_data()
        self.setup_bounds()
        
        self.setup_slopes()
        self.setup_threed_floors()
        self.setup_stairs()
        self.setup_movers()
        self.setup_lineids()
        self.setup_teleporters()
    
    
    def setup_teleporters(self):
        """
        Builds a list of teleporter objects that reference teleport source and destination locations.
        """
        
        self.map_data.teleporters = []
        for line_index, linedef in enumerate(self.map_data.linedefs):
            
            # Line to thing teleporters.
            if linedef.action in self.map_data.config.thing_teleport_specials:
                kind = Teleporter.TELEPORTER_THING
                target_thing = self.map_data.get_destination_from_teleport(line_index)
                if target_thing is None:
                    print 'Teleporter linedef {} has no valid destination thing.'.format(line_index)
                    continue
                
                dest = Vector2(target_thing.x, target_thing.y)
                
            # Line to line teleporters.
            elif linedef.action in self.map_data.config.line_teleport_specials:
                kind = Teleporter.TELEPORTER_LINE
                dest_line = self.map_data.get_line_destination(line_index)
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
                
            self.map_data.teleporters.append(teleporter)
            
    
    def setup_bounds(self):
        """
        Determines the minimum and maximum bounds of the map based on vertex coordinates.
        """
        
        # Calculate map width and height.
        for vertex in self.map_data.vertices:
            self.map_data.min_x = min(self.map_data.min_x, vertex.x)
            self.map_data.max_x = max(self.map_data.max_x, vertex.x)
            self.map_data.min_y = min(self.map_data.min_y, vertex.y)
            self.map_data.max_y = max(self.map_data.max_y, vertex.y)
        self.map_data.size.x = self.map_data.max_x - self.map_data.min_x
        self.map_data.size.y = self.map_data.max_y - self.map_data.min_y
    
        # Detect map depth.
        for sector in self.map_data.sectors:
            floorz = sector.floorz
            ceilz = sector.ceilingz
            self.map_data.min_z = min(floorz, min(ceilz, self.map_data.min_z))
            self.map_data.max_z = max(floorz, max(ceilz, self.map_data.max_z))
        self.map_data.size.z = self.map_data.max_z - self.map_data.min_z
    
    
    def setup_sector_data(self):
        """
        Processes additional sector data and generates extra structures for them.
        """
        
        # Build a list of subsector to sector mappings.
        # Each subsector's first segment is taken. This segment's linedef is taken, then the
        # sidedef on the segment's side is taken from the linedef. This sidedef contains the
        # sector for the subsector.
        for subsector in self.map_data.subsectors:
            segment = self.map_data.segments[subsector.first_segment]
            if segment.direction == Segment.DIRECTION_OPPOSITE:
                sidedef = self.map_data.sidedefs[segment.linedef.sidedef_back]
            else:
                sidedef = self.map_data.sidedefs[segment.linedef.sidedef_front]
            
            subsector.sector = sidedef.sector
        
        # Build a list of linedefs contained in each sector.
        for linedef in self.map_data.linedefs:
            if linedef.sidedef_front != Linedef.SIDEDEF_NONE:
                sidedef = self.map_data.sidedefs[linedef.sidedef_front]
            if linedef.sidedef_back != Linedef.SIDEDEF_NONE:
                sidedef = self.map_data.sidedefs[linedef.sidedef_back]
            
            self.map_data.sectors[sidedef.sector].linedefs.append(linedef)
        
        
    def setup_stairs(self):
        """
        Detects sectors that are affected by stair builder specials.
        """
    
        for linedef in self.map_data.linedefs:
            action = linedef.action
            
            is_boom = (action >= 0x3000 and action <= 0x33FF)
            if not action in self.map_data.config.stair_specials and not is_boom:
                continue
            
            # Stair actions start at 0x3000. floor texture ignorance starts at 0x200 in stair action, shifted by 9 bits.
            if is_boom:
                action = action - 0x3000
                ignore_floor_texture = (((action - 0x0200) >> 9) & 0x1) == 0
            else:
                ignore_floor_texture = False
            
            if self.map_data.is_hexen:
                tag = linedef.args[0]
            else:
                tag = linedef.tag
                
            # Build stair list for each starting sector.
            start_sectors = self.map_data.get_tag_sectors(tag)
            for sector_index in start_sectors:
                current_sector_index = sector_index
                
                # Sectors with a linedef facing into the current sector are added until either
                # there is no more shared linedef or the floor texture is different. 
                while True:
                    current_sector = self.map_data.sectors[current_sector_index]
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
                        sidedef = self.map_data.sidedefs[sector_linedef.sidedef_front]
                        if sidedef.sector == current_sector_index:
                            sidedef = self.map_data.sidedefs[sector_linedef.sidedef_back]
                            next_sector_index = sidedef.sector
                            break
                    else:
                        break
    
                    if ignore_floor_texture == False:
                        next_sector = self.map_data.sectors[next_sector_index]
                        if next_sector.texture_floor != current_sector.texture_floor:
                            break
                    current_sector_index = next_sector_index 
                
        
    def setup_threed_floors(self):
        """
        Sets up 3d floor stacks.
        """
        
        threed_count = 0
        
        # Create lists of 3d floors in each sector.
        if self.map_data.config.threedfloor_special is not None:
            for linedef in self.map_data.linedefs:
                if linedef.action == self.map_data.config.threedfloor_special:
                    sidedef = linedef.sidedef_front
                    if sidedef == Linedef.SIDEDEF_NONE:
                        continue
                    
                    control_sector_index = self.map_data.sidedefs[sidedef].sector
                    control_sector = self.map_data.sectors[control_sector_index]
                    tag = linedef.args[0]
                    kind = linedef.args[1]
                    
                    target_sectors = self.map_data.get_tag_sectors(tag)
                    if len(target_sectors) == 0:
                        continue
                    
                    # 3d floor is non-solid or swimmable, ignore it.
                    if (kind & THREED_KIND_SWIMMABLE) != 0 or (kind & THREED_KIND_NONSOLID) != 0:
                        continue
                    
                    # Solid, swap top and bottom.
                    if (kind & THREED_KIND_SOLID) != 0:
                        control_sector.ceilingz, control_sector.floorz = control_sector.floorz, control_sector.ceiling
                    
                    for sector_index in target_sectors:
                        self.map_data.sectors[sector_index].threedfloors.append(control_sector_index)
                        
                    threed_count += 1
                
        # Create sector_floor, sector_ceiling stacks. Even sectors without 3d floors get a single item on the stack.
        for sector_index, sector in enumerate(self.map_data.sectors):
            if len(sector.threedfloors) == 0:
                data = (sector_index, sector_index)
                sector.threedstack.append(data)
            
            else:
                # Sort threed floors by their floor height at the center of the target sector.
                center = self.map_data.get_sector_center(sector_index)
                sector.threedfloors = sorted(sector.threedfloors, key=lambda threed: self.map_data.get_sector_ceil_z(threed, center.x, center.y))
                
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
        
        if self.map_data.config.slope_special is None:
            return
        
        ALIGN_NONE = 0
        ALIGN_FRONT = 1
        ALIGN_BACK = 2
        
        floor_slopes = 0
        ceil_slopes = 0
        
        for line in self.map_data.linedefs:
            line_action = line.action
            
            sloped = False
            if self.map_data.is_hexen:
                # Hexen slope floor special.
                if line_action == self.map_data.config.slope_special:
                    align_floor = line.args[0] & 3
                    align_ceiling = line.args[1] & 3
                    if align_ceiling == 0:
                        align_ceiling = (line.args[0] >> 2) & 3
                        
                    sloped = True
                
            # Doom style sloped floors.
            elif line_action >= self.map_data.config.slope_special and line_action <= self.map_data.config.slope_special + 7:
                line_action -= self.map_data.config.slope_special
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
                frontside = self.map_data.sidedefs[line.sidedef_front]
                frontsector_index = frontside.sector
                
                backside = self.map_data.sidedefs[line.sidedef_back]
                backsector_index = backside.sector
                
                # Floor plane?
                if align_floor == ALIGN_FRONT:
                    plane = plane_setup(self.map_data, frontsector_index, self.map_data.sectors[frontsector_index].linedefs, line, True)
                    self.map_data.sectors[frontsector_index].floor_plane = plane
                    floor_slopes += 1
                elif align_floor == ALIGN_BACK:
                    plane = plane_setup(self.map_data, backsector_index, self.map_data.sectors[backsector_index].linedefs, line, True)
                    self.map_data.sectors[backsector_index].floor_plane = plane
                    floor_slopes += 1
                    
                # Ceiling plane?
                if align_ceiling == ALIGN_FRONT:
                    plane = plane_setup(self.map_data, frontsector_index, self.map_data.sectors[frontsector_index].linedefs, line, False)
                    self.map_data.sectors[frontsector_index].ceiling_plane = plane
                    ceil_slopes += 1
                elif align_ceiling == ALIGN_BACK:
                    plane = plane_setup(self.map_data, backsector_index, self.map_data.sectors[backsector_index].linedefs, line, False)
                    self.map_data.sectors[backsector_index].ceiling_plane = plane
                    ceil_slopes += 1
        
        if floor_slopes > 0:
            print 'Found {} floor slopes.'.format(floor_slopes)
        if ceil_slopes > 0:
            print 'Found {} ceiling slopes.'.format(ceil_slopes)
    
    
    def setup_lineids(self):
        """
        Detect and store linedefs with an id assigned to them.
        """
        
        if self.map_data.is_hexen == True:
            self.map_data.linedef_ids = {}
            for index, linedef in enumerate(self.map_data.linedefs):
                if linedef.action in self.map_data.config.line_identification_specials:
                    line_id = linedef.args[0] + (linedef.args[4] * 256)
                    self.map_data.linedef_ids[line_id] = index
        
    
    def setup_movers(self):
        """
        Analyzes the map and marks sectors that are going to move during gameplay.
        """ 
        
        # Detect tagged and special sectors, these are likely going to move.
        for sector_index, sector in enumerate(self.map_data.sectors):
            special = sector.action
            tag = sector.tag
            value = self.map_data.config.sector_types.get(special)
            
            # Special tags.
            if tag == 667 or tag == 666:
                self.map_data.apply_extra_effect(sector_index, 'moves')
            
            # Registered special sector type.
            elif value is not None:
                self.map_data.apply_extra_effect(sector_index, value)
                
            # Boom generalized sector types.
            else:
                for flag, value in self.map_data.config.sector_generalized_types.iteritems():
                    if (special & flag) != 0:
                        self.map_data.apply_extra_effect(sector_index, value)
            
        # Detect linedef activation.
        for linedef in self.map_data.linedefs:
            line_type = linedef.action
            if self.map_data.is_hexen:
                line_tag = linedef.args[0]
            else:
                line_tag = linedef.tag
                
            # Activates sector on back side?
            if line_tag == 0 and line_type in self.map_data.config.backside_activation_specials:
                sidedef = linedef.sidedef_back
                if sidedef != Linedef.SIDEDEF_NONE:
                    sidedef = self.map_data.sidedefs[sidedef]
                    sector_index = sidedef.sector
                    self.map_data.apply_extra_effect(sector_index, 'moves')
            
            # Activates tagged sector?
            elif line_tag != 0 and (line_type in self.map_data.config.tag_activation_specials or line_type in self.map_data.config.backside_activation_specials):
                target_sectors = self.map_data.get_tag_sectors(line_tag)
                for sector_index in target_sectors:
                    self.map_data.apply_extra_effect(sector_index, 'moves')
                    
            # Boom generalized linedef?
            elif self.map_data.config.generalized_specials is not None and line_type >= 0x2F80:
                for shift in self.map_data.config.generalized_specials:
                    
                    # Sector tag activation of switch, walk and shoot triggers.
                    activation_type = ((line_type - shift) & 0x7)
                    if line_tag != 0:
                        target_sectors = self.map_data.get_tag_sectors(line_tag)
                        for sector_index in target_sectors:
                            self.map_data.apply_extra_effect(sector_index, 'moves')
                    
                    # Backside activation of door triggers.
                    elif activation_type >= 6 and line_tag == 0:
                        sidedef = linedef.sidedef_back
                        if sidedef != Linedef.SIDEDEF_NONE:
                            sidedef = self.map_data.sidedefs[sidedef]
                            sector_index = sidedef.sector
                            self.map_data.apply_extra_effect(sector_index, 'moves')