from doom.mapenum import *
from doom.trig import box_intersects_line, box_intersects_box, point_in_subsector
import config


class PositionState(object):
        
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.radius = 0
        self.height = 0
        
        self.floorz = -0x8000
        self.ceilz = 0x8000
        
        self.blockline = False
        self.blockthing = False
        self.steep = False
        
        self.special_sector = None
        self.moves = False
        self.sector_index = 0
        self.base_sector_index = 0


class Walker(object):
    
    def __init__(self, map_data, config):
        self.map_data = map_data
        self.config = config
        
        
    def get_bb_floor_z(self, x, y, radius, sector_index=None):
        if sector_index is not None:
            floorz = self.map_data.get_sector_floor_z(sector_index, x - radius, y)
            floorz = max(floorz, self.map_data.get_sector_floor_z(sector_index, x + radius, y))
            floorz = max(floorz, self.map_data.get_sector_floor_z(sector_index, x - radius, y + radius))
            floorz = max(floorz, self.map_data.get_sector_floor_z(sector_index, x + radius, y - radius))
        else:
            floorz = self.map_data.get_floor_z(x - radius, y)
            floorz = max(floorz, self.map_data.get_floor_z(x + radius, y))
            floorz = max(floorz, self.map_data.get_floor_z(x - radius, y + radius))
            floorz = max(floorz, self.map_data.get_floor_z(x + radius, y - radius))
        
        return floorz
    
    
    def get_bb_ceil_z(self, x, y, radius, sector_index=None):
        if sector_index is not None:
            ceilz = self.map_data.get_sector_ceil_z(sector_index, x - radius, y)
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, x + radius, y))
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, x - radius, y + radius))
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, x + radius, y - radius))
        else:
            ceilz = self.map_data.get_ceil_z(x - radius, y)
            ceilz = min(ceilz, self.map_data.get_ceil_z(x + radius, y))
            ceilz = min(ceilz, self.map_data.get_ceil_z(x - radius, y + radius))
            ceilz = min(ceilz, self.map_data.get_ceil_z(x + radius, y - radius))
        
        return ceilz
    
        
    def check_position(self, x, y, z, radius, height):
        state = PositionState()
        state.x = x
        state.y = y
        state.z = z
        state.radius = radius
        state.height = height
        
        subsector_index = point_in_subsector(self.map_data.c_mapdata, x, y)
        state.sector_index = self.map_data.subsector_sectors[subsector_index]
        state.base_sector_index = state.sector_index
            
        self.check_sector_position(state)
        
        box_top = y + radius
        box_bottom = y - radius - 1
        box_right = x + radius - 1
        box_left = x - radius
           
        x1, y1 = self.map_data.blockmap.map_to_blockmap(box_left, box_bottom)
        x2, y2 = self.map_data.blockmap.map_to_blockmap(box_right, box_top)
        
        # Walk through blockmap blocks that need to be examined.
        cx = x1
        while cx <= x2:

            cy = y1
            while cy <= y2:

                block = self.map_data.blockmap.get(cx, cy)
                cy += 1
                if block is None:
                    continue
                
                # Linedef collisions.
                if len(block.linedefs) > 0:
                    for line_index in block.linedefs:
                        linedef = self.map_data.linedefs[line_index]
                        vertex1 = self.map_data.vertices[linedef[LINEDEF_VERTEX_1]]
                        vertex2 = self.map_data.vertices[linedef[LINEDEF_VERTEX_2]]
                        lx1 = vertex1[VERTEX_X]
                        ly1 = vertex1[VERTEX_Y]
                        lx2 = vertex2[VERTEX_X]
                        ly2 = vertex2[VERTEX_Y] 
                                                                                
                        if box_intersects_line(box_left, box_top, box_right, box_bottom, lx1, ly1, lx2, ly2) == True:                        
                            # Cannot pass through impassible flagged lines.
                            if (linedef[LINEDEF_FLAGS] & LINEDEF_FLAG_IMPASSIBLE) != 0:
                                state.blockline = True
                                continue
                            
                            # Test each sidedef on the line.
                            # Frontside.
                            sidedef_index = linedef[self.map_data.LINEDEF_SIDEDEF_FRONT]
                            if sidedef_index == SIDEDEF_NONE:
                                state.blockline = True
                            else:
                                sidedef = self.map_data.sidedefs[sidedef_index]
                                state.sector_index = sidedef[SIDEDEF_SECTOR]
                                if state.sector_index != state.base_sector_index:
                                    self.check_sector_position(state)
                            
                            # Backside.
                            sidedef_index = linedef[self.map_data.LINEDEF_SIDEDEF_BACK]
                            if sidedef_index == SIDEDEF_NONE:
                                state.blockline = True
                            else:
                                sidedef = self.map_data.sidedefs[sidedef_index]
                                state.sector_index = sidedef[SIDEDEF_SECTOR]
                                if state.sector_index != state.base_sector_index:
                                    self.check_sector_position(state)
                                
                # Thing collisions.
                if len(block.things) > 0:
                    for thing_index in block.things:
                        thing = self.map_data.things[thing_index]
                        thing_type = thing[self.map_data.THING_TYPE]
                        
                        # Parse custom bridge thing size.
                        if self.config.bridge_custom_type is not None and thing_type == self.config.bridge_custom_type:
                            thing_radius = thing[THING_HEXEN_ARG0]
                            thing_height = thing[THING_HEXEN_ARG1]
                            thing_flags = 0
                            
                        else:
                            thing_def = self.config.thing_dimensions.get(thing_type)
                            if thing_def is None:
                                continue
                             
                            thing_radius = thing_def.radius
                            thing_height = thing_def.height
                            thing_flags = thing_def.flags
                            
                        thing_x = thing[self.map_data.THING_X]
                        thing_y = thing[self.map_data.THING_Y]

                        left = thing_x - thing_radius
                        top = thing_y - thing_radius
                        right = thing_x + thing_radius
                        bottom = thing_y + thing_radius

                        if box_intersects_box(box_left, box_bottom, box_right, box_top, left, top, right, bottom) == True:
                            # Determine z position.
                            if (thing_flags & config.DEF_FLAG_HANGING) != 0:
                                thing_z = self.map_data.get_ceil_z(thing_x, thing_y) - thing_height
                            else:
                                thing_z = self.map_data.get_floor_z(thing_x, thing_y)                            
                                if self.map_data.is_hexen == True:
                                    thing_z += thing[THING_HEXEN_Z]
                                
                            # Intersection with a thing.
                            if z + height >= thing_z and z <= thing_z + thing_height:
                                state.blockthing = True
                                
                            # Above this thing, move the floor up to it.
                            if z >= thing_z:
                                state.floorz = max(state.floorz, thing_z + thing_height)
                                state.special_sector = None
                                
                            # Below this thing, move the ceiling down to it.
                            if z + height <= thing_z + thing_height:
                                state.ceilz = min(state.ceilz, thing_z)
            
            cx += 1
            
        collision = False
        
        # Blocked by single-sided line or thing.
        if state.blockline == True or state.blockthing == True:
            collision = True
        
        # Ceiling is too low.
        elif z + height > state.ceilz and state.special_sector is None:
            collision = True
        
        # Z is below floor.
        elif z < state.floorz:
            collision = True
            
        return collision, state
    
    
    def check_sector_position(self, state):
        sector_extra = self.map_data.sector_extra[state.sector_index]

        # Find the floor and ceiling sectors to collide with.
        for stack in sector_extra.threedstack:
            sector_floor_z = self.map_data.get_sector_floor_z(stack[0], state.x, state.y)
            sector_ceil_z = self.map_data.get_sector_ceil_z(stack[1], state.x, state.y)
            
            if state.z >= sector_floor_z and state.z <= sector_ceil_z:
                floor_sector_index = stack[0]
                ceil_sector_index = stack[1]
                break
            
            # Test step up height.
            if state.z + self.config.step_height >= sector_floor_z and state.z + self.config.step_height <= sector_ceil_z:
                floor_sector_index = stack[0]
                ceil_sector_index = stack[1]
                break
                
        else:
            floor_sector_index = state.sector_index
            ceil_sector_index = state.sector_index
                        
        # Get floor and ceiling z for sloped or normal sectors.
        # Sloped sectors are tested at all bounding box corners, non-sloped sector aren't.
        # Additionally, sloped 3dfloors need to check the bounding box corners in the control sector plane only. 
        floor_plane = self.map_data.sector_extra[floor_sector_index].floor_plane
        if floor_plane is not None:
            if state.sector_index != floor_sector_index:
                sector_floor_z = self.get_bb_floor_z(state.x, state.y, state.radius, sector_index=floor_sector_index)
            else:
                sector_floor_z = self.get_bb_floor_z(state.x, state.y, state.radius)
            if floor_plane.c < self.config.slope_steep:
                state.steep = True
        else:
            sector_floor_z = self.map_data.get_sector_floor_z(floor_sector_index, state.x, state.y)
        
        if self.map_data.sector_extra[ceil_sector_index].ceil_plane is not None:
            if state.sector_index != ceil_sector_index:
                sector_ceil_z = self.get_bb_ceil_z(state.x, state.y, state.radius, sector_index=ceil_sector_index)
            else:
                sector_ceil_z = self.get_bb_ceil_z(state.x, state.y, state.radius)
        else:
            sector_ceil_z = self.map_data.get_sector_ceil_z(ceil_sector_index, state.x, state.y)
            
        # Keep this new floor as the special floor.
        floor_extra = self.map_data.sector_extra[floor_sector_index]
        if sector_floor_z >= state.floorz and floor_extra.is_special == True:
            state.special_sector = floor_sector_index
            
        # Detect any moving sectors.
        state.moves = floor_extra.moves or state.moves
        
        # Choose tightest floor and ceiling fit.
        state.floorz = max(state.floorz, sector_floor_z)
        state.ceilz = min(state.ceilz, sector_ceil_z)
