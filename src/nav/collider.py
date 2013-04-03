from doom.map.objects import Linedef, Sector
from util.rectangle import Rectangle
from util.vector import Vector3
import config


class PositionState(object):
    """
    Keeps track of the collider's current test state.
    """
        
    def __init__(self):
        # Current position.
        self.pos = Vector3()
        
        # Current bounding box to test.
        self.bbox = Rectangle()
        
        self.reset(self.pos, 0, 0)
        

    def reset(self, pos, radius, height):
        # Size to test.
        self.radius = radius
        self.height = height
        
        # Outermost z coordinates.
        self.floorz = -0x8000
        self.ceilz = 0x8000
        
        # Blocked by a linedef.
        self.blockline = False
        
        # Blocked by a thing.
        self.blockthing = False
        
        # Blocked by a steep slope.
        self.steep = False
        
        # The element's sector's ceiling or floor can move during gameplay.
        self.floor_moves = False
        self.ceiling_moves = False
        
        # This position's special sector index.
        self.special_sector = None
        
        # This position's floor plane.
        self.floor_plane = None

        self.pos.copy_from(pos)
        self.bbox.set(
            pos.x - radius,
            pos.y - radius,
            pos.x + radius,
            pos.y + radius
        )
        

class Collider(object):
    """
    Performs collision tests on a Doom map.
    """
    
    def __init__(self, map_data, config):
        self.map_data = map_data
        self.config = config
        self.state = PositionState()
        
        # Temporary rectangle to avoid excessive allocation.
        self.temp_rect = Rectangle()
        
        
    def get_bb_floor_z(self, pos, radius, sector_index=None):
        """
        Returns the outermost floor z coordinate in a bounding box.
        
        @param pos: the position to test.
        @param radius: the radius of the bounding box.
        @param sector_index: the sector index to test in. If this is None, each coordinate will be tested in it's
                             own sector.
        
        @return: a Z height.
        """ 
        
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
    
    
    def get_bb_ceil_z(self, pos2, radius, sector_index=None):
        """
        Returns the outermost ceiling z coordinate in a bounding box.
        
        @param pos: the position to test.
        @param radius: the radius of the bounding box.
        @param sector_index: the sector index to test in. If this is None, each coordinate will be tested in it's
                             own sector.
        
        @return: a Z height.
        """ 
        
        if sector_index is not None:
            ceilz = self.map_data.get_sector_ceil_z(sector_index, pos2.x - radius, pos2.y)
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, pos2.x + radius, pos2.y))
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, pos2.x - radius, pos2.y + radius))
            ceilz = min(ceilz, self.map_data.get_sector_ceil_z(sector_index, pos2.x + radius, pos2.y - radius))
        else:
            ceilz = self.map_data.get_ceil_z(pos2.x - radius, pos2.y)
            ceilz = min(ceilz, self.map_data.get_ceil_z(pos2.x + radius, pos2.y))
            ceilz = min(ceilz, self.map_data.get_ceil_z(pos2.x - radius, pos2.y + radius))
            ceilz = min(ceilz, self.map_data.get_ceil_z(pos2.x + radius, pos2.y - radius))
        
        return ceilz
    
        
    def check_position(self, pos3, radius, height):
        """
        Check a position for collision.
        
        @param pos3: the 3d position to test.
        @param radius: the radius to test.
        @param height: the height of the test.   
        """
        
        state = self.state
        state.reset(pos3, radius, height)
                
        # Select a starting sector.
        subsector_index = self.map_data.point_in_subsector(pos3.x, pos3.y)
        state.sector_index = self.map_data.subsectors[subsector_index].sector
        state.base_sector_index = state.sector_index
            
        self.check_sector_position(state)
        
        # Set the blockmap region to test in.
        x1, y1 = self.map_data.blockmap.map_to_blockmap(state.bbox.p1)
        x2, y2 = self.map_data.blockmap.map_to_blockmap(state.bbox.p2)
        rect = self.temp_rect
        rect.set(x1, y1, x2, y2)
        
        # Get all testable items in a region and test against them.
        linedefs, things = self.map_data.blockmap.get_region(rect)
        if len(linedefs) > 0:
            linedefs = set(linedefs)
            self.check_linedefs(state, linedefs)
        if len(things) > 0:
            things = set(things)
            self.check_things(state, things)

        # Blocked by single-sided line or thing.
        if state.blockline == True or state.blockthing == True:
            collision = True
        
        # Ceiling is too low.
        elif state.pos.z + height > state.ceilz:
            if state.special_sector is None:
                collision = True
            
            # No moving ceiling in the special sector means we should still collide.
            elif (self.map_data.sectors[state.special_sector].flags & Sector.FLAG_CEILING_MOVES) == 0:
                collision = True
                
            else:
                collision = False
        
        # Z is below floor.
        elif state.pos.z < state.floorz:
            collision = True
            
        else:
            collision = False
            
        return collision, state
    
    
    def check_linedefs(self, state, linedefs):
        """
        Check linedefs for collision and update state.
        """
        
        for line_index in linedefs:
            linedef = self.map_data.linedefs[line_index]
            lx1 = linedef.vertex1.x
            ly1 = linedef.vertex1.y
            lx2 = linedef.vertex2.x
            ly2 = linedef.vertex2.y 
            
            # Ignore lines that do not intersect.                   
            if state.bbox.intersects_with_line(lx1, ly1, lx2, ly2) == False:
                continue
            
            # Cannot pass through impassible flagged lines.
            if (linedef.flags & Linedef.FLAG_IMPASSIBLE) != 0:
                state.blockline = True
            
            # Test each sidedef on the line.
            # Frontside.
            sidedef_index = linedef.sidedef_front
            if sidedef_index == Linedef.SIDEDEF_NONE:
                state.blockline = True
            else:
                sidedef = self.map_data.sidedefs[sidedef_index]
                state.sector_index = sidedef.sector
                if state.sector_index != state.base_sector_index:
                    self.check_sector_position(state)
            
            # Backside.
            sidedef_index = linedef.sidedef_back
            if sidedef_index == Linedef.SIDEDEF_NONE:
                state.blockline = True
            else:
                sidedef = self.map_data.sidedefs[sidedef_index]
                state.sector_index = sidedef.sector
                if state.sector_index != state.base_sector_index:
                    self.check_sector_position(state)


    def check_things(self, state, things):
        """
        Check things for collision and update state.
        """
        
        for thing_index in things:
            thing = self.map_data.things[thing_index]
            thing_type = thing.doomid
            
            # Parse custom bridge thing size.
            if self.config.bridge_custom_type is not None and thing_type == self.config.bridge_custom_type:
                thing_radius = thing.args[0]
                thing_height = thing.args[1]
                thing_flags = 0
                
            else:
                thing_def = self.config.thing_dimensions.get(thing_type)
                if thing_def is None:
                    continue
                 
                thing_radius = thing_def.radius
                thing_height = thing_def.height
                thing_flags = thing_def.flags
                
            # Test against thing rectangle.
            thing_x = thing.x
            thing_y = thing.y
            rect = self.temp_rect
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
                    thing_z += thing.z
                
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
        """
        Check against the state's current sector.
        """
        
        sector = self.map_data.sectors[state.sector_index]

        # Find the floor and ceiling sectors to collide with.
        for stack in sector.threedstack:
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
        floor_plane = self.map_data.sectors[floor_sector_index].floor_plane
        if floor_plane is not None:
            if state.sector_index != floor_sector_index:
                sector_floor_z = self.get_bb_floor_z(state.pos, state.radius, sector_index=floor_sector_index)
            else:
                sector_floor_z = self.get_bb_floor_z(state.pos, state.radius)
            if floor_plane.c < self.config.slope_steep:
                state.steep = True
        else:
            sector_floor_z = self.map_data.get_sector_floor_z(floor_sector_index, state.pos.x, state.pos.y)
        
        if self.map_data.sectors[ceil_sector_index].ceiling_plane is not None:
            if state.sector_index != ceil_sector_index:
                sector_ceil_z = self.get_bb_ceil_z(state.pos, state.radius, sector_index=ceil_sector_index)
            else:
                sector_ceil_z = self.get_bb_ceil_z(state.pos, state.radius)
        else:
            sector_ceil_z = self.map_data.get_sector_ceil_z(ceil_sector_index, state.pos.x, state.pos.y)
            
        # Keep this new floor as the special floor.
        floor_sector = self.map_data.sectors[floor_sector_index]
        if sector_floor_z >= state.floorz and (floor_sector.flags & Sector.FLAG_SPECIAL) != 0:
            state.special_sector = floor_sector_index
        
        # Keep floor planes.
        if floor_sector.floor_plane is not None:
            state.floor_plane = floor_sector.floor_plane
            
        # Detect any moving sectors.
        state.floor_moves = ((floor_sector.flags & Sector.FLAG_FLOOR_MOVES) != 0) or state.floor_moves
        state.ceiling_moves = ((floor_sector.flags & Sector.FLAG_CEILING_MOVES) != 0) or state.ceiling_moves
        
        # Choose tightest floor and ceiling fit.
        state.floorz = max(state.floorz, sector_floor_z)
        state.ceilz = min(state.ceilz, sector_ceil_z)
