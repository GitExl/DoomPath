from doom.map.objects import Sector, Teleporter
from nav.navelement import NavElement
from nav.walker import Walker
from util.vector import Vector3, Vector2
import struct


# Grid file structures.
GRID_FILE_ID = 'DPGRID'
GRID_FILE_VERSION = 1
GRID_FILE_HEADER = struct.Struct('<6sII')
GRID_FILE_ELEMENT = struct.Struct('<hhhiiiiiii')

# Grid collision reasons.
REASON_NONE = 0
REASON_BLOCK_LINE = 1
REASON_SLOPE_TOO_STEEP = 2
REASON_CANNOT_FIT = 3
REASON_LINE_BLOCK = 4
REASON_THING_BLOCK = 5
REASON_IGNORE = 6
REASON_TOO_HIGH = 7
REASON_LEAK = 8


class NavGrid(object):
    """
    A grid of elements, describing where a player can walk on the map.
    """
    
    def __init__(self, map_data, config, resolution):
        self.config = config
        self.map_data = map_data
        
        # The size of a single element.
        self.element_size = config.player_radius / resolution
        self.element_height = config.player_height
        
        # The dimensions of this grid.
        self.size = Vector2(self.map_data.size.x / self.element_size, self.map_data.size.y / self.element_size)
        
        # Collision detection handler.
        self.walker = Walker(map_data, config)
        
        # All elements in this grid.
        self.elements = []
        
        # A list of elements that still need to be examined.
        self.element_tasks = []
        
        # A (x + y * width) positional dictionary with element lists.
        self.element_hash = {}
        
        # A set of elements that need to be pruned when calling remove_pruned_elements.
        self.element_prune = set()
        
        # The map position currently being examined for collision.
        self.check_pos = Vector3()
        
        
    def add_walkable_element(self, pos):
        """
        Adds a new element to the grid at a point where the player can stand.
        """
        
        x, y = self.map_to_element(pos)
        element = self.add_element_xyz(x, y, pos.z)
        
        # Set the element's sector-related data.
        sector_index = self.map_data.get_sector(x, y)
        sector = self.map_data.sectors[sector_index]
        self.set_element_properties(sector_index, element)
        
        if (sector.flags & Sector.FLAG_MOVES) != 0:
            element.special_sector = sector_index
        
        # Schedule for examination.
        self.element_tasks.append(element)
        
    
    def add_element_xyz(self, x, y, z):
        """
        Adds a new element at a specific location in the grid.
        
        @return: the new NavElement object.
        """
        
        element = NavElement(x, y, z)

        element_hash = x + (y * self.size.x)
        elements = self.element_hash.get(element_hash)
        if elements is None:
            elements = {}
            self.element_hash[element_hash] = elements
        elements[z] = element
        
        self.elements.append(element)
        
        return element
    
    
    def place_starts(self):
        """
        Place elements at starting thing locations.
        """
        
        # Create a list of things that the grid generation starts at.
        start_things = []
        for thing_type in self.config.start_thing_types:
            start_things.extend(self.map_data.get_thing_list(thing_type))
        
        # Add the initial things as initial elements to the navigation grid.
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
        """
        Remove elements from the elements_prune set from the element list.
        """
        
        # Filter prune elements from the element list.
        self.elements = filter(lambda element: element not in self.element_prune, self.elements)
        
        # Remove pruned elements from the element hash table.
        for element in self.element_prune:
            element_hash = element.pos.x + (element.pos.y * self.size.x)
            elements = self.element_hash.get(element_hash)
            if elements is None:
                return
                
            del elements[element.pos.z]
            if len(elements) == 0:
                del self.element_hash[element_hash]
                
        # Remove the now invalid element connections.
        for element in self.elements:
            for direction in NavElement.DIR_RANGE:
                if element.elements[direction] in self.element_prune:
                    element.elements[direction] = None
        
        self.element_prune.clear() 
                
    
    def write(self, filename):
        """
        Writes this grid to a file.
        """
        
        # Assign element indices.
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
            
                # Gather indices for each element's direction and write it as a single struct.    
                for direction in NavElement.DIR_RANGE:
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
        """
        Reads a grid file from disk.
        """
        
        with open(filename, 'rb') as f:
            file_id, version, element_count = GRID_FILE_HEADER.unpack(f.read(GRID_FILE_HEADER.size))
            
            # Validate header.
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
                
                # Find matching planes in sectors.
                for sector in self.map_data.sectors:
                    if hash(sector.floor_plane) == plane_hash:
                        element.plane = sector.floor_plane
                        break
                else:
                    print 'Cannot find sector floor plane at element coordinates {}.'.format(element.pos)
                
                if element.special_sector == -1:
                    element.special_sector = None
                
                self.elements.append(element)

        # Set element references from stored indices.
        for element in self.elements:
            for direction in NavElement.DIR_RANGE:
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
        """
        Returns an element at the x,y,z coordinates, or None if no element exists at
        those coordinates.
        """
        
        element_hash = x + (y * self.size.x)
        elements = self.element_hash.get(element_hash)
        if elements is not None:
            return elements.get(z)

        return None
    
    
    def get_element_list(self, pos2):
        """
        Returns a list of elements at the 2d coordinates, or None if no list exists at
        those coordinates.
        """
        
        element_hash = pos2.x + (pos2.y * self.size.x)
        return self.element_hash.get(element_hash)
        

    def map_to_element(self, pos2):
        """
        Maps a 2d map position to an element position.
        """
        
        return ((pos2.x / self.element_size) + 1, (pos2.y / self.element_size) + 1)
    
    
    def element_to_map(self, pos2):
        """
        Maps the center of a 2d element position to a map position.
        """
        
        return ((pos2.x * self.element_size) - (self.element_size / 2), (pos2.y * self.element_size) - (self.element_size / 2))

    
    def create_walkable_elements(self, config):
        """
        Traverse the map, starting at already placed starting elements, and place elements where a
        player can walk.
        """
        
        pos = Vector3()
        
        # Keep testing elements until the task list is empty.
        while 1:
            if len(self.element_tasks) == 0:
                break
            element = self.element_tasks.pop()
            
            if len(self.elements) % 5000 == 0:
                print '{} elements, {} tasks left...'.format(len(self.elements), len(self.element_tasks))
            
            # Test each direction for walkability.
            for direction in NavElement.DIR_RANGE:
                pos.x = element.pos.x
                pos.y = element.pos.y
                pos.z = element.pos.z
                
                if direction == NavElement.DIR_UP:
                    pos.y -= 1
                elif direction == NavElement.DIR_RIGHT:
                    pos.x += 1
                elif direction == NavElement.DIR_DOWN:
                    pos.y += 1
                elif direction == NavElement.DIR_LEFT:
                    pos.x -= 1
                
                # See if an adjoining element already exists.
                new_element = self.get_element_xyz(pos.x, pos.y, pos.z)
                if new_element is None:
                    
                    # If not, test if an element can be placed there.
                    reason, new_element = self.test_element(pos, direction, element)
                    if reason != REASON_NONE:
                        continue
                    
                element.elements[direction] = new_element

        
    def test_element(self, pos3, direction, element):
        """
        Test if an adjoining element can be placed at the specified location.
        
        @param pos: the 3d map position to test.
        @param direction: the direction of the new element relative to it's previous element.
        @param element: the previous origin element. 
        """
        
        map_x, map_y = self.element_to_map(pos3)
        if map_x < self.map_data.min.x or map_x > self.map_data.max.x or map_y < self.map_data.min.y or map_y > self.map_data.max.y:
            print 'Grid leak at ({}, {})'.format(map_x, map_y)
            return REASON_LEAK, None
        
        # Test collision.
        check_pos = self.check_pos
        check_pos.x = map_x
        check_pos.y = map_y
        check_pos.z = pos3.z
        collision, state = self.walker.check_position(check_pos, self.element_size, self.element_height)
        
        # Ignore sectors flagged as such.
        if state.special_sector is not None:
            sector = self.map_data.sectors[state.special_sector]
            if (sector.flags & Sector.FLAG_IGNORE) != 0:
                return REASON_IGNORE, None
        
        jump = False
        if collision == True:
            
            # Blocked by impassable line.
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
            if direction == NavElement.DIR_UP:
                element.flags |= NavElement.FLAG_JUMP_NORTH
            elif direction == NavElement.DIR_RIGHT:
                element.flags |= NavElement.FLAG_JUMP_EAST
            elif direction == NavElement.DIR_DOWN:
                element.flags |= NavElement.FLAG_JUMP_SOUTH
            elif direction == NavElement.DIR_LEFT:
                element.flags |= NavElement.FLAG_JUMP_WEST
        
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
            
            # Set new element properties to match collision results.
            if state.special_sector is not None:
                self.set_element_properties(state.special_sector, new_element)
            if state.floor_plane is not None:
                new_element.plane = state.floor_plane                
            if state.moves == True:
                new_element.special_sector = state.special_sector
            
            self.element_tasks.append(new_element)
            
        return REASON_NONE, new_element
            
            
    def set_element_properties(self, sector_index, element):
        """
        Sets an element's properties (but not flags) from sector flags.
        """
        
        sector = self.map_data.sectors[sector_index]
                            
        # Set sector damage flag.
        if sector.damage > 0:
            if sector.damage <= 5:
                element.flags |= NavElement.FLAG_DAMAGE_LOW
            elif sector.damage <= 10:
                element.flags |= NavElement.FLAG_DAMAGE_MEDIUM
            elif sector.damage >= 20:
                element.flags |= NavElement.FLAG_DAMAGE_HIGH