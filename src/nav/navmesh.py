from nav.navenum import *
from nav.navarea import NavArea
import pygame


COLOR_FILL = pygame.Color(15, 15, 15, 255)
COLOR_BORDER = pygame.Color(127, 63, 0, 255)


class NavMesh(object):
    
    def __init__(self):
        self.areas = []
        self.nav_grid = None
        
        self.max_elements = 0
        self.max_ratio = 0


    def create_from_grid(self, nav_grid):
        self.nav_grid = nav_grid
        self.max_size_elements = AREA_SIZE_MAX / self.nav_grid.element_size
        
        left = nav_grid.map_data.min_x / nav_grid.element_size
        top = nav_grid.map_data.min_y / nav_grid.element_size
        right = left + nav_grid.width
        bottom = top + nav_grid.height
        
        for min_side in range(self.max_size_elements, 0, -1):
            print 'Size iteration {}...'.format(min_side)
            self.generate_iteration(left, top, right, bottom, min_side)
        
        print 'Merging...'
        while 1:
            old_len = len(self.areas)
            self.areas = filter(self.area_merge_filter, self.areas)
            new_len = len(self.areas)
            
            if new_len == old_len:
                break
            
            print 'Merged down to {} navigation areas.'.format(new_len)

        return True
    
    
    def generate_iteration(self, left, top, right, bottom, size):
        x = left
        y = top
        iteration = 0
        
        while 1:
            iteration += 1
            if iteration % 40000 == 0:
                print '{} navigation areas in iteration {}...'.format(len(self.areas), iteration)
            
            move_x = 1
            elements = self.nav_grid.get_element_list(x, y)
            if elements is not None:
                for element in elements.itervalues():
                    if element.area is None:
                        if self.find_largest_area(element, size) == False:
                            continue
                        
                        area = self.add_area(element, size, size)
                        area.sector = element.special_sector
                        area.flags = element.flags
                        area.plane = element.plane
                        self.areas.append(area)
                        move_x = max(move_x, (area.x2 - area.x1) / self.nav_grid.element_size)
                    else:
                        move_x = max(move_x, (element.area.x2 - element.area.x1) / self.nav_grid.element_size)
            
            x += move_x
            if x >= right:
                x = left
                y += 1
                if y >= bottom:
                    break

    
    def area_merge_filter(self, area):
        for side in SIDE_RANGE:
            x1, y1, x2, y2 = area.get_side(side)
            
            # Select a grid element on the current side.
            if side == SIDE_TOP:
                ex, ey = x1, y1 - self.nav_grid.element_size
            elif side == SIDE_RIGHT:
                ex, ey = x2 + self.nav_grid.element_size, y1
            elif side == SIDE_BOTTOM:
                ex, ey = x1, y2 + self.nav_grid.element_size
            elif side == SIDE_LEFT:
                ex, ey = x1 - self.nav_grid.element_size, y1
            
            ex, ey = self.nav_grid.map_to_element(ex, ey)
            element = self.nav_grid.get_element(ex, ey, area.z)
            if element is None:
                continue
            
            # Select the navigation area that the selected element is a part of.
            # Ignore ourselves as a merge candidate.
            merge_area = element.area
            if merge_area is None or merge_area == area:
                continue
            
            # Ignore areas that do not have similar contents.
            if not (area.elements[0] == merge_area.elements[0]):
                continue
            
            # See if the two areas have matching opposite sides.
            merge_x1, merge_y1, merge_x2, merge_y2 = merge_area.get_side(SIDE_RANGE_OPPOSITE[side])
            if x1 != merge_x1 or y1 != merge_y1 or x2 != merge_x2 or y2 != merge_y2:
                continue
            
            # Get the size of the new merged area.
            if side == SIDE_TOP:
                width = area.x2 - area.x1
                height = area.y2 - merge_area.y1 
            elif side == SIDE_RIGHT:
                width = merge_area.x2 - area.x1
                height = area.y2 - area.y1
            elif side == SIDE_BOTTOM:
                width = area.x2 - area.x1
                height = merge_area.y2 - area.y1
            elif side == SIDE_LEFT:
                width = area.x2 - merge_area.x1
                height = area.y2 - area.y1
                
            # Abort merging if the area dimensions are not good.
            if width > AREA_SIZE_MAX or height > AREA_SIZE_MAX:
                continue
            
            # Merge the area surface.
            if side == SIDE_TOP:
                merge_area.y2 = area.y2
            elif side == SIDE_RIGHT:
                merge_area.x1 = area.x1
            elif side == SIDE_BOTTOM:
                merge_area.y1 = area.y1
            elif side == SIDE_LEFT:
                merge_area.x2 = area.x2
                
            # Merge the area elements.
            merge_area.elements.extend(area.elements)
            for element in area.elements:
                element.area = merge_area
                
            return False
        
        return True

    
    def add_area(self, element, width, height):
        # Create a new nav area of the found width and height.
        ex1, ey1 = self.nav_grid.element_to_map(element.x, element.y)
        ex2, ey2 = self.nav_grid.element_to_map(element.x + width, element.y + height)
        ex1 -= (self.nav_grid.element_size / 2)
        ey1 -= (self.nav_grid.element_size / 2)
        ex2 -= (self.nav_grid.element_size / 2)
        ey2 -= (self.nav_grid.element_size / 2)

        area = NavArea(ex1, ey1, ex2, ey2, element.z)
        
        # Assign this area to all the elements in it.
        xelement = element
        for _ in range(0, width):
            
            yelement = xelement
            for _ in range(0, height):
                yelement.area = area
                area.elements.append(yelement)
                
                yelement = yelement.elements[DIRECTION_DOWN]
            
            xelement = xelement.elements[DIRECTION_RIGHT]
        
        return area
    
    
    def find_largest_area(self, element, size):
        x = element.x
        y = element.y

        xelement = element
        cx = x
        while cx < x + size:
            
            yelement = xelement
            cy = y
            while cy < y + size:
                if yelement is None or yelement.area is not None or (not yelement == element):
                    return False
                
                cy += 1
                yelement = yelement.elements[DIRECTION_DOWN]
                
            cx += 1
            xelement = xelement.elements[DIRECTION_RIGHT]

        return True
    
    
    def render(self, surface, camera):
        for area in self.areas:
            x, y = camera.map_to_screen(area.x1, area.y1)
            width, height = ((area.x2 - area.x1) * camera.zoom, (area.y2 - area.y1) * camera.zoom)
            
            x += 1
            y += 1
            width -= 1
            height -= 1
            
            if x < 0:
                width -= abs(x)
                x = 0
            if y < 0:
                height -= abs(y)
                y = 0
            if x + width >= surface.get_width():
                width = surface.get_width() - x
            if y + height >= surface.get_height():
                height = surface.get_height() - y
                
            if width < 1 or height < 1:
                continue
            
            rect = pygame.Rect(x, y, width, height)
            
            surface.fill(COLOR_FILL, rect, special_flags=pygame.BLEND_SUB)
            pygame.draw.rect(surface, COLOR_BORDER, rect, 1)