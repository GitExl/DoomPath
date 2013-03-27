from doom.mapdata import Teleporter
from nav.navelement import NavElement
from nav.navenum import *
from nav.walker import Walker
from util.vector import Vector3
import struct


GRID_FILE_ID = 'DPGRID'
GRID_FILE_VERSION = 1
GRID_FILE_HEADER = struct.Struct('<6sII')
GRID_FILE_ELEMENT = struct.Struct('<hhhiiiiiii')

REASON_NONE = 0
REASON_BLOCK_LINE = 1
REASON_SLOPE_TOO_STEEP = 2
REASON_CANNOT_FIT = 3
REASON_LINE_BLOCK = 4
REASON_THING_BLOCK = 5
REASON_IGNORE = 6
REASON_TOO_HIGH = 7
REASON_LEAK = 8

reason_text = {
    REASON_NONE: 'None',
    REASON_BLOCK_LINE: 'Blocked by line',
    REASON_SLOPE_TOO_STEEP: 'Slope is too steep',
    REASON_CANNOT_FIT: 'Cannot fit',
    REASON_LINE_BLOCK: 'Blocked by line',
    REASON_THING_BLOCK: 'Blocked by thing',
    REASON_IGNORE: 'Ignoring sector',
    REASON_TOO_HIGH: 'Height difference too much',
    REASON_LEAK: 'Grid leak'
}


class NavGrid(object):
    
    def __init__(self, map_data, config, resolution):
        self.config = config
        self.map_data = map_data
        
        self.element_size = config.player_radius / resolution
        self.element_height = config.player_height
        
        self.width = self.map_data.size.x/ self.element_size
        self.height = self.map_data.size.y / self.element_size
        
        self.walker = Walker(map_data, config)
        
        self.elements = []
        self.element_tasks = []
        self.element_hash = {}
        self.element_prune = set()
        
        self.check_pos = Vector3()
        
        
    def add_walkable_element(self, pos):
        element_pos = self.map_to_element(pos)
        element = self.add_element_xyz(element_pos[0], element_pos[1], pos.z)
        
        sector_index = self.map_data.get_sector(element_pos[0], element_pos[1])
        self.set_element_extra(sector_index, element)
        
        sector_extra = self.map_data.sector_extra[sector_index]
        if sector_extra.moves == True:
            element.special_sector = sector_index
        
        self.element_tasks.append(element)
        
    
    def add_element_xyz(self, x, y, z):
        element = NavElement(x, y, z)

        element_hash = x + (y * self.width)
        elements = self.element_hash.get(element_hash)
        if elements is None:
            elements = {}
            self.element_hash[element_hash] = elements
        elements[z] = element
        
        self.elements.append(element)
        
        return element
    
    
    def place_starts(self):
        # Create a list of things that grid generation starts at.
        start_things = []
        for thing_type in self.config.start_thing_types:
            start_things.extend(self.map_data.get_thing_list(thing_type))
        
        # Add the initial things as initial elements to the nav grid.
        for thing in start_things:
            pos = Vector3()
            pos.x = thing.x
            pos.y = thing.y
            pos.z = self.map_data.get_floor_z(pos.x, pos.y)
            
            collision, _ = self.walker.check_position(pos, self.config.player_radius, self.config.player_height)
            if collision == True:
                print 'Thing at {} has no room to spawn, ignoring.'.format(pos)
                continue
            
            self.add_walkable_element(pos)
        
        # Add teleporter destinations as starting elements.
        for teleporter in self.map_data.teleporters:
            
            if teleporter.kind == Teleporter.TELEPORTER_THING:
                dest = Vector3()
                dest.x = teleporter.dest.x
                dest.y = teleporter.dest.y
            else:
                dest = Vector3()
                dest.x, dest.y = self.map_data.get_line_center(teleporter.dest_line)
                
            dest.z = self.map_data.get_floor_z(dest.x, dest.y)
            
            collision, _ = self.walker.check_position(dest, self.config.player_radius, self.config.player_height)
            if collision == True:
                print 'Teleporter destination at {} has no room to spawn, ignoring.'.format(dest)
                continue
            
            self.add_walkable_element(dest)
        
        print 'Added {} starting elements.'.format(len(start_things))
    
    
    def remove_pruned_elements(self):
        # Filter prune elements from the element list.
        self.elements = filter(lambda element: element not in self.element_prune, self.elements)
        
        # Remove pruned elements from the element hash table.
        for element in self.element_prune:
            element_hash = element.pos.x + (element.pos.y * self.width)
            elements = self.element_hash.get(element_hash)
            if elements is None:
                return
                
            del elements[element.pos.z]
            if len(elements) == 0:
                del self.element_hash[element_hash]
                
        # Remove now invalid element connections.
        for element in self.elements:
            for direction in DIRECTION_RANGE:
                if element.elements[direction] in self.element_prune:
                    element.elements[direction] = None
        
        self.element_prune.clear() 
                
    
    def write(self, filename):
        for index, element in enumerate(self.elements):
            element.index = index
        
        with open(filename, 'wb') as f:            
            header = GRID_FILE_HEADER.pack(GRID_FILE_ID, GRID_FILE_VERSION, len(self.elements))
            f.write(header)

            indices = [0] * 4            
            for element in self.elements:
                if element.plane is None:
                    plane_hash = 0
                else:
                    plane_hash = hash(element.plane)
                
                for direction in DIRECTION_RANGE:
                    if element.elements[direction] is None:
                        indices[direction] = -1
                    else:
                        indices[direction] = element.elements[direction].index
                    
                    if element.special_sector is None:
                        special_sector = -1
                    else:
                        special_sector = element.special_sector
                        
                element_data = GRID_FILE_ELEMENT.pack(element.pos.x, element.pos.y, element.pos.z, plane_hash, special_sector, element.flags, indices[0], indices[1], indices[2], indices[3])
                f.write(element_data)
           
                
    def read(self, filename):
        with open(filename, 'rb') as f:
            file_id, version, element_count = GRID_FILE_HEADER.unpack(f.read(GRID_FILE_HEADER.size))
            if file_id != GRID_FILE_ID:
                print 'Invalid grid file.'
                return
            
            if version != GRID_FILE_VERSION:
                print 'Unsupported grid version {}'.format(version)
                return
            
            self.elements = []
            for _ in range(element_count):
                element = NavElement(0, 0, 0)
                element.pos.x, element.pos.y, element.pos.z, plane_hash, element.special_sector, element.flags, element.elements[0], element.elements[1], element.elements[2], element.elements[3] = GRID_FILE_ELEMENT.unpack(f.read(GRID_FILE_ELEMENT.size))
                
                for sector_extra in self.map_data.sector_extra:
                    if hash(sector_extra.floor_plane) == plane_hash:
                        element.plane = sector_extra.floor_plane
                        break
                
                if element.special_sector == -1:
                    element.special_sector = None
                
                self.elements.append(element)

        # Set element references from stored indices.
        for element in self.elements:
            for direction in DIRECTION_RANGE:
                if element.elements[direction] != -1:
                    element.elements[direction] = self.elements[element.elements[direction]]
                else:
                    element.elements[direction] = None
            
        # Rebuild element position hash.
        for element in self.elements:
            element_hash = element.x + (element.y * self.width)
            elements = self.element_hash.get(element_hash)
            if elements is None:
                elements = {}
                self.element_hash[element_hash] = elements
            elements[element.z] = element 
            
    
    def get_element_xyz(self, x, y, z):
        element_hash = x + (y * self.width)
        elements = self.element_hash.get(element_hash)
        if elements is not None:
            return elements.get(z)

        return None
    
    
    def get_element_list(self, pos):
        element_hash = pos.x + (pos.y * self.width)
        return self.element_hash.get(element_hash)
        

    def map_to_element(self, pos):
        return ((pos.x / self.element_size) + 1, (pos.y / self.element_size) + 1)
    
    
    def element_to_map(self, pos):
        return ((pos.x * self.element_size) - (self.element_size / 2), (pos.y * self.element_size) - (self.element_size / 2))

    
    def create_walkable_elements(self, config):
        pos = Vector3()
        
        while 1:
            if len(self.element_tasks) == 0:
                break
            element = self.element_tasks.pop()
            
            if len(self.elements) % 5000 == 0:
                print '{} elements, {} tasks left...'.format(len(self.elements), len(self.element_tasks))
            
            for direction in DIRECTION_RANGE:
                pos.copy_from(element.pos)
                if direction == DIRECTION_UP:
                    pos.y -= 1
                elif direction == DIRECTION_RIGHT:
                    pos.x += 1
                elif direction == DIRECTION_DOWN:
                    pos.y += 1
                elif direction == DIRECTION_LEFT:
                    pos.x -= 1
                
                # See if an adjoining element already exists.
                new_element = self.get_element_xyz(pos.x, pos.y, pos.z)
                if new_element is None:
                    reason, new_element = self.test_element(pos, direction, element, new_element)
                    if reason != REASON_NONE:
                        continue
                    
                element.elements[direction] = new_element

        
    def test_element(self, pos, direction, element, new_element):
        # See if an adjoining element can be placed.
        map_pos = self.element_to_map(pos)
        if map_pos[0] < self.map_data.min_x or map_pos[0] > self.map_data.max_x or map_pos[1] < self.map_data.min_y or map_pos[1] > self.map_data.max_y:
            print 'Grid leak at {}'.format(map_pos)
            return REASON_LEAK, None
        
        check_pos = self.check_pos
        check_pos.x = map_pos[0]
        check_pos.y = map_pos[1]
        check_pos.z = pos.z
        collision, state = self.walker.check_position(check_pos, self.element_size, self.element_height)
        
        if state.special_sector is not None:
            sector_extra = self.map_data.sector_extra[state.special_sector]
            if sector_extra.ignore == True:
                return REASON_IGNORE, None
        
        jump = False
        if collision == True:
            # Blocked by impassible line.
            if state.blockline == True:
                return REASON_BLOCK_LINE, None

            elif state.floorz > check_pos.z:
                
                # If the player can step up to a higher floor, do so.
                if state.floorz - check_pos.z <= self.config.step_height:
                    check_pos.z = state.floorz
                
                # If the player can jump up to a higher floor, do so.
                elif self.config.jump_height > 0 and state.floorz - check_pos.z <= self.config.jump_height:
                    check_pos.z = state.floorz
                    jump = True
                    
                # If the sector moves during the game, ignore any higher height difference.
                elif state.moves == False:
                    return REASON_TOO_HIGH, None
                
        # Steep slopes cannot be walked up, only down.
        if state.steep == True and state.floorz > element.pos.z:
            return REASON_SLOPE_TOO_STEEP, None
        
        # Snap to moving sector floor.
        if state.moves == True:
            check_pos.z = state.floorz
        
        # Set origin element jumping flags.
        if jump == True:
            if direction == DIRECTION_UP:
                element.flags |= FLAG_JUMP_NORTH
            elif direction == DIRECTION_RIGHT:
                element.flags |= FLAG_JUMP_EAST
            elif direction == DIRECTION_DOWN:
                element.flags |= FLAG_JUMP_SOUTH
            elif direction == DIRECTION_LEFT:
                element.flags |= FLAG_JUMP_WEST
        
        # Drop to the lowest floor.
        check_pos.z = min(check_pos.z, state.floorz)
        
        # Player cannot fit in the sector.
        if (check_pos.z < state.floorz or check_pos.z + self.element_height > state.ceilz) and (state.moves == False or state.blockthing == True): 
            return REASON_CANNOT_FIT, None
                              
        # See if an element exists in the updated location.
        new_pos = self.map_to_element(check_pos)
        new_element = self.get_element_xyz(new_pos[0], new_pos[1], check_pos.z)
        
        if new_element is None:
            new_element = self.add_element_xyz(new_pos[0], new_pos[1], check_pos.z)
            if state.special_sector is not None:
                self.set_element_extra(state.special_sector, new_element)
                
            if state.floor_plane is not None:
                new_element.plane = state.floor_plane
                
            if state.moves == True:
                new_element.special_sector = state.special_sector
            
            self.element_tasks.append(new_element)
            
        return REASON_NONE, new_element
            
            
    def set_element_extra(self, sector_index, element):
        sector_extra = self.map_data.sector_extra[sector_index]
                            
        # Set sector damage flag.
        if sector_extra.damage > 0:
            if sector_extra.damage <= 5:
                element.flags |= FLAG_DAMAGE_LOW
            elif sector_extra.damage <= 10:
                element.flags |= FLAG_DAMAGE_MEDIUM
            elif sector_extra.damage >= 20:
                element.flags |= FLAG_DAMAGE_HIGH