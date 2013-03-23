from doom.mapdata import Teleporter
from doom.mapenum import *
from nav.navelement import NavElement
from nav.navenum import *
from nav.walker import Walker
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
        
        self.width = self.map_data.width / self.element_size
        self.height = self.map_data.height / self.element_size
        
        self.walker = Walker(map_data, config)
        
        self.elements = []
        self.element_tasks = []
        self.element_hash = {}
        self.element_prune = set()
        
        
    def add_walkable_element(self, x, y, z):
        ex, ey = self.map_to_element(x, y)
        element = self.add_element(ex, ey, z)
        
        sector_index = self.map_data.get_sector(x, y)
        self.set_element_extra(sector_index, element)
        
        sector_extra = self.map_data.sector_extra[sector_index]
        if sector_extra.moves == True:
            element.special_sector = sector_index
        
        self.element_tasks.append(element)
        
    
    def add_element(self, x, y, z):
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
            x = thing[self.map_data.THING_X]
            y = thing[self.map_data.THING_Y]
            z = self.map_data.get_floor_z(x, y)
            
            collision, _ = self.walker.check_position(x, y, z, self.config.player_radius, self.config.player_height)
            if collision == True:
                print 'Thing at {}, {} has no room to spawn, ignoring.'.format(x, y)
                continue
            
            self.add_walkable_element(x, y, z)
        
        # Add teleporter destinations as starting elements.
        for teleporter in self.map_data.teleporters:
            if teleporter.kind == Teleporter.TELEPORTER_THING:
                x = teleporter.dest_x
                y = teleporter.dest_y
            else:
                x, y = self.map_data.get_line_center(teleporter.dest_line)
                
            z = self.map_data.get_floor_z(x, y)  
            
            collision, _ = self.walker.check_position(x, y, z, self.config.player_radius, self.config.player_height)
            if collision == True:
                print 'Teleporter destination at {}, {} has no room to spawn, ignoring.'.format(x, y)
                continue
            
            self.add_walkable_element(x, y, z)
        
        print 'Added {} starting elements.'.format(len(start_things))
    
    
    def remove_pruned_elements(self):
        # Filter prune elements from the element list.
        self.elements = filter(lambda element: element not in self.element_prune, self.elements)
        
        # Remove pruned elements from the element hash table.
        for element in self.element_prune:
            element_hash = element.x + (element.y * self.width)
            elements = self.element_hash.get(element_hash)
            if elements is None:
                return
                
            del elements[element.z]
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
                        
                element_data = GRID_FILE_ELEMENT.pack(element.x, element.y, element.z, plane_hash, special_sector, element.flags, indices[0], indices[1], indices[2], indices[3])
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
                element.x, element.y, element.z, plane_hash, element.special_sector, element.flags, element.elements[0], element.elements[1], element.elements[2], element.elements[3] = GRID_FILE_ELEMENT.unpack(f.read(GRID_FILE_ELEMENT.size))
                
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
            
    
    def get_element(self, x, y, z):
        element_hash = x + (y * self.width)
        elements = self.element_hash.get(element_hash)
        if elements is not None:
            return elements.get(z)

        return None
    
    
    def get_element_list(self, x, y):
        element_hash = x + (y * self.width)
        return self.element_hash.get(element_hash)
        

    def map_to_element(self, x, y):
        return (x / self.element_size) + 1, (y / self.element_size) + 1
    
    
    def element_to_map(self, x, y):
        return (x * self.element_size) - (self.element_size / 2), (y * self.element_size) - (self.element_size / 2)

    
    def create_walkable_elements(self, config):       
        while 1:
            if len(self.element_tasks) == 0:
                break
            element = self.element_tasks.pop()
            
            if len(self.elements) % 2500 == 0:
                print '{} elements, {} tasks left...'.format(len(self.elements), len(self.element_tasks))
            
            for direction in DIRECTION_RANGE:
                if direction == DIRECTION_UP:
                    x = element.x
                    y = element.y - 1
                elif direction == DIRECTION_RIGHT:
                    x = element.x + 1
                    y = element.y
                elif direction == DIRECTION_DOWN:
                    x = element.x
                    y = element.y + 1
                elif direction == DIRECTION_LEFT:
                    x = element.x - 1
                    y = element.y
                z = element.z
                
                # See if an adjoining element already exists.
                new_element = self.get_element(x, y, z)
                if new_element is None:
                    reason, new_element = self.test_element(x, y, z, direction, element, new_element)
                    if reason != REASON_NONE:
                        continue
                    
                element.elements[direction] = new_element

                
    def test_element(self, x, y, z, direction, element, new_element):
        jump = False

        # See if an adjoining element can be placed.
        map_x, map_y = self.element_to_map(x, y)
        if map_x < self.map_data.min_x or map_x > self.map_data.max_x or map_y < self.map_data.min_y or map_y > self.map_data.max_y:
            print 'Grid leak at {}, {}'.format(map_x, map_y)
            return REASON_LEAK, None
        
        collision, state = self.walker.check_position(map_x, map_y, z, self.element_size, self.element_height)
        
        if state.special_sector is not None:
            sector_extra = self.map_data.sector_extra[state.special_sector]
            if sector_extra.ignore == True:
                return REASON_IGNORE, None
        
        if collision == True:
            # Blocked by impassible line.
            if state.blockline == True:
                return REASON_BLOCK_LINE, None

            elif state.floorz > z:
                
                # If the player can step up to a higher floor, do so.
                if state.floorz - z <= self.config.step_height:
                    z = state.floorz
                
                # If the player can jump up to a higher floor, do so.
                elif self.config.jump_height > 0 and state.floorz - z <= self.config.jump_height:
                    z = state.floorz
                    jump = True
                    
                # If the sector moves during the game, ignore any higher height difference.
                elif state.moves == False:
                    return REASON_TOO_HIGH, None
                
        # Steep slopes cannot be walked up, only down.
        if state.steep == True and state.floorz > element.z:
            return REASON_SLOPE_TOO_STEEP, None
        
        # Snap to moving sector floor.
        if state.moves == True:
            z = state.floorz
        
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
        z = min(z, state.floorz)
        
        # Player cannot fit in the sector.
        if (z < state.floorz or z + self.element_height > state.ceilz) and (state.moves == False or state.blockthing == True): 
            return REASON_CANNOT_FIT, None
                              
        # See if an element exists in the updated location.
        new_element = self.get_element(x, y, z)
        if new_element is None:
            new_element = self.add_element(x, y, z)
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