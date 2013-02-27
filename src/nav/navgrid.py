from doom.mapenum import *
from nav.walker import Walker
import pygame


DIRECTION_NORTH = 0
DIRECTION_EAST = 1
DIRECTION_SOUTH = 2
DIRECTION_WEST = 3

COLOR_ELEMENT_SPECIAL = pygame.Color(255, 0, 255, 255)
COLOR_ELEMENT = pygame.Color(255, 255, 255, 255)
COLOR_ELEMENT_HIGHLIGHT = pygame.Color(0, 255, 255, 255)

FLAG_DAMAGE_LOW = 0x0001
FLAG_DAMAGE_MEDIUM = 0x0002
FLAG_DAMAGE_HIGH = 0x0004
FLAG_JUMP_NORTH = 0x0008
FLAG_JUMP_EAST = 0x0010
FLAG_JUMP_SOUTH = 0x0020
FLAG_JUMP_WEST = 0x0040

REASON_NONE = 0
REASON_BLOCK_LINE = 1
REASON_SLOPE_TOO_STEEP = 2
REASON_CANNOT_FIT = 3
REASON_LINE_BLOCK = 4
REASON_THING_BLOCK = 5
REASON_IGNORE = 6
REASON_TOO_HIGH = 7

reason_text = {
    REASON_NONE: 'None',
    REASON_BLOCK_LINE: 'Blocked by line',
    REASON_SLOPE_TOO_STEEP: 'Slope is too steep',
    REASON_CANNOT_FIT: 'Cannot fit',
    REASON_LINE_BLOCK: 'Blocked by line',
    REASON_THING_BLOCK: 'Blocked by thing',
    REASON_IGNORE: 'Ignoring sector',
    REASON_TOO_HIGH: 'Height difference too much'
}


class NavElement(object):
    __slots__ = ('x', 'y', 'z', 'area', 'special_sector', 'flags', 'elements')
    
    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.area = None
        self.special_sector = -1
        self.flags = 0
        self.elements = [None] * 4
        
        
    def __repr__(self):
        return 'element x {}, y {}, z {}, flags {}, sector {}'.format(self.x, self.y, round(self.z, 2), self.flags, self.special_sector)
        

class NavGrid(object):
    
    def __init__(self, map_data, config):
        self.config = config
        self.map_data = map_data
        
        self.element_size = config.player_radius
        self.element_height = config.player_height
        
        self.walker = Walker(map_data, config)
        
        self.elements = []
        self.element_tasks = []
        self.element_hash = {}
        
        self.colors = [None] * 256
        for index in range(0, 255):
            v = index / 255.0
            self.colors[index] = pygame.Color(int(COLOR_ELEMENT.r * v), int(COLOR_ELEMENT.g * v), int(COLOR_ELEMENT.b * v), 255)
        
        self.colors_special = [None] * 256
        for index in range(0, 255):
            v = index / 255.0
            self.colors_special[index] = pygame.Color(int(COLOR_ELEMENT_SPECIAL.r * v), int(COLOR_ELEMENT_SPECIAL.g * v), int(COLOR_ELEMENT_SPECIAL.b * v), 255)
        
        
    def add_walkable_element(self, x, y, z):
        ex, ey, ez = self.map_to_element(x, y, z)
        element = self.add_element(ex, ey, ez)
        
        sector_index = self.map_data.get_sector(x, y)
        self.set_element_extra(sector_index, element)
        
        sector_extra = self.map_data.sector_extra[sector_index]
        if sector_extra.moves == True:
            element.special_sector = sector_index
        
        self.element_tasks.append(element)
        
    
    def add_element(self, x, y, z):
        element = NavElement(x, y, z)

        element_hash = x + (y * (self.map_data.width / self.element_size))
        elements = self.element_hash.get(element_hash)
        if elements is None:
            elements = {}
            self.element_hash[element_hash] = elements
        elements[z] = element
        
        self.elements.append(element)
        
        return element
    
    
    def get_element(self, x, y, z):
        element_hash = x + (y * (self.map_data.width / self.element_size))
        elements = self.element_hash.get(element_hash)
        if elements is not None:
            return elements.get(z)

        return None
    
    
    def get_element_list(self, x, y):
        element_hash = x + (y * (self.map_data.width / self.element_size))
        return self.element_hash.get(element_hash)
        

    def map_to_element(self, x, y, z):
        return (x / self.element_size) + 1, (y / self.element_size) + 1, z
    
    
    def element_to_map(self, x, y, z):
        return (x * self.element_size) - (self.element_size / 2), (y * self.element_size) - (self.element_size / 2), z

    
    def render_elements(self, surface, camera, sx, sy):        
        rect = pygame.Rect((0, 0), (self.element_size * camera.zoom, self.element_size * camera.zoom))
        z_mod = 255.0 / self.map_data.depth
        
        for element in self.elements:
            x, y, _ = self.element_to_map(element.x, element.y, element.z)
            x, y = camera.map_to_screen(x, y)
            rect.top = y - (self.element_size / 2) * camera.zoom
            rect.left = x - (self.element_size / 2) * camera.zoom
            
            v = int((element.z - self.map_data.min_z) * z_mod)
            if element.special_sector != -1:
                color = self.colors_special[v]
            else:
                color = self.colors[v]
            
            pygame.draw.rect(surface, color, rect, 1)
        
        rect = pygame.Rect((0, 0), (self.element_size * camera.zoom, self.element_size * camera.zoom))
        sx, sy, _ = self.map_to_element(sx, sy, 0)
        element_hash = sx + (sy * (self.map_data.width / self.element_size))
        element = self.element_hash.get(element_hash)
        if element is not None:
            element = element[element.keys()[0]]

            color = COLOR_ELEMENT_HIGHLIGHT
            x, y, _ = self.element_to_map(element.x, element.y, element.z)
            x, y = camera.map_to_screen(x, y)
            rect.top = y - (self.element_size / 2) * camera.zoom
            rect.left = x - (self.element_size / 2) * camera.zoom

            pygame.draw.rect(surface, color, rect, 1)
            
            for direction in range(0, 4):
                if element.elements[direction] is not None:
                    start = (rect.left + (self.element_size * camera.zoom) / 2, rect.top + (self.element_size * camera.zoom) / 2)
                    
                    if direction == DIRECTION_NORTH:
                        end = (start[0], start[1] - (self.element_size * camera.zoom))
                    elif direction == DIRECTION_EAST:
                        end = (start[0] + (self.element_size * camera.zoom), start[1])
                    elif direction == DIRECTION_SOUTH:
                        end = (start[0], start[1] + (self.element_size * camera.zoom))
                    elif direction == DIRECTION_WEST:
                        end = (start[0] - (self.element_size * camera.zoom), start[1])
                        
                    pygame.draw.line(surface, color, start, end, 1)
        
    
    def create_walkable_elements(self, config, iterations=-1):       
        iteration = 0
        direction_range = range(0, 4)
        
        while True:
            iteration += 1
            if iterations != -1 and iteration >= iterations:
                return
            
            if len(self.element_tasks) == 0:
                break
            element = self.element_tasks.pop()
            
            if len(self.elements) % 2500 == 0:
                print '{} elements, {} tasks left...'.format(len(self.elements), len(self.element_tasks))
            
            for direction in direction_range:
                if direction == DIRECTION_NORTH:
                    x = element.x
                    y = element.y - 1
                elif direction == DIRECTION_EAST:
                    x = element.x + 1
                    y = element.y
                elif direction == DIRECTION_SOUTH:
                    x = element.x
                    y = element.y + 1
                elif direction == DIRECTION_WEST:
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
        map_x, map_y, map_z = self.element_to_map(x, y, z)
        collision, state = self.walker.check_position(map_x, map_y, map_z, self.element_size, self.element_height)
        
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
            if direction == DIRECTION_NORTH:
                element.flags |= FLAG_JUMP_NORTH
            elif direction == DIRECTION_EAST:
                element.flags |= FLAG_JUMP_EAST
            elif direction == DIRECTION_SOUTH:
                element.flags |= FLAG_JUMP_SOUTH
            elif direction == DIRECTION_WEST:
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