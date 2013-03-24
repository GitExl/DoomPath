from doom.mapenum import *
from doom.trig import point_in_subsector, box_intersects_line
from util.rectangle import Rectangle
from util.vector import Vector3
import config


class PositionState(object):
        
    def __init__(self):
        self.pos = Vector3()
        self.bbox = Rectangle()
        
        self.reset(self.pos, 0, 0)
        

    def reset(self, pos, radius, height):
        self.pos.copy_from(pos)
        
        self.radius = radius
        self.height = height
        
        self.floorz = -0x8000
        self.ceilz = 0x8000
        
        self.blockline = False
        self.blockthing = False
        self.steep = False
        self.moves = False
        self.special_sector = None
        self.floor_plane = None

        self.bbox.set(
            pos.x - radius,
            pos.y - radius,
            pos.x + radius,
            pos.y + radius
        )
        

class Walker(object):
    
    def __init__(self, map_data, config):
        self.map_data = map_data
        self.config = config
        self.state = PositionState()
        
        
    def get_bb_floor_z(self, pos, radius, sector_index=None):
        if sector_index is not None:
            floorz = self.map_data.get_sector_floor_z(sector_index, pos.x - radius, pos.y)
            floorz = max(floorz, self.map_data.get_sector_floor_z(sector_index, pos.x + radius, pos.y))
            floorz = max(floorz, self.map_data.get_sector_floor_z(sector_index, pos.x - radius, pos.y + radius))
            floorz = max(floorz, self.map_data.get_sector_floor_z(sector_index, pos.x + radius, pos.y - radius))
        else:
            floorz = self.map_data.get_floor_z(pos.x - radius, pos.y)
            floorz = max(floorz, self.map_data.get_floor_z(pos.x + radius, pos.y))
            floorz = max(floorz, self.map_data.get_floor_z(pos.x - radius, pos.y + radius))
            floorz = max(floorz, self.map_data.get_floor_z(pos.x + radius, pos.y - radius))
        
        return floorz
    
    
    def get_bb_ceil_z(self, pos, radius, sector_index=None):
        if sector_index is not None:
            ceilz = self.map_data.get_sector_ceil_z(sector_index, pos.x - radius, pos.y)
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, pos.x + radius, pos.y))
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, pos.x - radius, pos.y + radius))
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, pos.x + radius, pos.y - radius))
        else:
            ceilz = self.map_data.get_ceil_z(pos.x - radius, pos.y)
            ceilz = min(ceilz, self.map_data.get_ceil_z(pos.x + radius, pos.y))
            ceilz = min(ceilz, self.map_data.get_ceil_z(pos.x - radius, pos.y + radius))
            ceilz = min(ceilz, self.map_data.get_ceil_z(pos.x + radius, pos.y - radius))
        
        return ceilz
    
        
    def check_position(self, pos, radius, height):
        state = self.state
        state.reset(pos, radius, height)
                
        subsector_index = point_in_subsector(self.map_data.c_mapdata, pos.x, pos.y)
        state.sector_index = self.map_data.subsector_sectors[subsector_index]
        state.base_sector_index = state.sector_index
            
        self.check_sector_position(state)
        
        p1 = self.map_data.blockmap.map_to_blockmap(state.bbox.p1)
        p2 = self.map_data.blockmap.map_to_blockmap(state.bbox.p2)
        rect = Rectangle(p1.x, p1.y, p2.x, p2.y)
        
        linedefs, things = self.map_data.blockmap.get_region(rect)
        if len(linedefs) > 0:
            linedefs = set(linedefs)
            self.check_block_linedefs(state, linedefs)
        if len(things) > 0:
            things = set(things)
            self.check_block_things(state, things)

        # Blocked by single-sided line or thing.
        if state.blockline == True or state.blockthing == True:
            collision = True
        
        # Ceiling is too low.
        elif state.pos.z + height > state.ceilz and state.special_sector is None:
            collision = True
        
        # Z is below floor.
        elif state.pos.z < state.floorz:
            collision = True
            
        else:
            collision = False
            
        return collision, state
    
    
    def check_block_linedefs(self, state, linedefs):
        for line_index in linedefs:
            linedef = self.map_data.linedefs[line_index]
            vertex1 = self.map_data.vertices[linedef[LINEDEF_VERTEX_1]]
            vertex2 = self.map_data.vertices[linedef[LINEDEF_VERTEX_2]]
            lx1 = vertex1[VERTEX_X]
            ly1 = vertex1[VERTEX_Y]
            lx2 = vertex2[VERTEX_X]
            ly2 = vertex2[VERTEX_Y] 
            
            # Ignore lines that do not intersect.                   
            if box_intersects_line(state.bbox, lx1, ly1, lx2, ly2) == False:
                continue
            
            # Cannot pass through impassible flagged lines.
            if (linedef[LINEDEF_FLAGS] & LINEDEF_FLAG_IMPASSIBLE) != 0:
                state.blockline = True
            
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


    def check_block_things(self, state, things):
        rect = Rectangle()
        
        for thing_index in things:
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

            rect.set(
                thing_x - thing_radius,
                thing_y - thing_radius,
                thing_x + thing_radius,
                thing_y + thing_radius
            )
            if state.bbox.intersects_with(rect) == False:
                continue
            
            # Determine z position.
            if (thing_flags & config.DEF_FLAG_HANGING) != 0:
                thing_z = self.map_data.get_ceil_z(thing_x, thing_y) - thing_height
            else:
                thing_z = self.map_data.get_floor_z(thing_x, thing_y)                            
                if self.map_data.is_hexen == True:
                    thing_z += thing[THING_HEXEN_Z]
                
            # Intersection with a thing.
            if state.pos.z + state.height >= thing_z and state.pos.z <= thing_z + thing_height:
                state.blockthing = True
                
            # Point is above this thing, move the floor up to it.
            if state.pos.z >= thing_z:
                state.floorz = max(state.floorz, thing_z + thing_height)
                state.special_sector = None
                
            # Below this thing, move the ceiling down to it.
            if state.pos.z + state.height <= thing_z + thing_height:
                state.ceilz = min(state.ceilz, thing_z)

    
    def check_sector_position(self, state):
        sector_extra = self.map_data.sector_extra[state.sector_index]

        # Find the floor and ceiling sectors to collide with.
        for stack in sector_extra.threedstack:
            sector_floor_z = self.map_data.get_sector_floor_z(stack[0], state.pos.x, state.pos.y)
            sector_ceil_z = self.map_data.get_sector_ceil_z(stack[1], state.pos.x, state.pos.y)
            
            if state.pos.z >= sector_floor_z and state.pos.z <= sector_ceil_z:
                floor_sector_index = stack[0]
                ceil_sector_index = stack[1]
                break
            
            # Test step up height.
            if state.pos.z + self.config.step_height >= sector_floor_z and state.pos.z + self.config.step_height <= sector_ceil_z:
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
                sector_floor_z = self.get_bb_floor_z(state.pos, state.radius, sector_index=floor_sector_index)
            else:
                sector_floor_z = self.get_bb_floor_z(state.pos, state.radius)
            if floor_plane.c < self.config.slope_steep:
                state.steep = True
        else:
            sector_floor_z = self.map_data.get_sector_floor_z(floor_sector_index, state.pos.x, state.pos.y)
        
        if self.map_data.sector_extra[ceil_sector_index].ceil_plane is not None:
            if state.sector_index != ceil_sector_index:
                sector_ceil_z = self.get_bb_ceil_z(state.pos, state.radius, sector_index=ceil_sector_index)
            else:
                sector_ceil_z = self.get_bb_ceil_z(state.pos, state.radius)
        else:
            sector_ceil_z = self.map_data.get_sector_ceil_z(ceil_sector_index, state.pos.x, state.pos.y)
            
        # Keep this new floor as the special floor.
        floor_extra = self.map_data.sector_extra[floor_sector_index]
        if sector_floor_z >= state.floorz and floor_extra.is_special == True:
            state.special_sector = floor_sector_index
        
        # Keep floor planes.
        if floor_extra.floor_plane is not None:
            state.floor_plane = floor_extra.floor_plane
            
        # Detect any moving sectors.
        state.moves = floor_extra.moves or state.moves
        
        # Choose tightest floor and ceiling fit.
        state.floorz = max(state.floorz, sector_floor_z)
        state.ceilz = min(state.ceilz, sector_ceil_z)
