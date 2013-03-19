from nav import navconnection
from nav.navarea import NavArea
from nav.navenum import *


class NavMesh(object):
    
    def __init__(self):
        self.areas = []
        self.nav_grid = None
        
        self.max_elements = 0
        self.max_ratio = 0


    def create_from_grid(self, nav_grid, max_area_size, max_area_size_merged):
        self.max_area_size = max_area_size
        self.max_area_size_merged = max_area_size_merged
        
        self.nav_grid = nav_grid
        self.max_size_elements = self.max_area_size / self.nav_grid.element_size
        
        # Determine the locations where to test for elements.
        left = nav_grid.map_data.min_x / nav_grid.element_size
        top = nav_grid.map_data.min_y / nav_grid.element_size
        right = left + nav_grid.width
        bottom = top + nav_grid.height
        
        min_side = self.max_size_elements
        while min_side > 0:
            print 'Size iteration {}...'.format(min_side)
            self.generate_iteration(left, top, right, bottom, min_side)            
            min_side -= 1
        
        print 'Merging...'
        while 1:
            old_len = len(self.areas)
            self.areas = filter(self.area_merge_filter, self.areas)
            new_len = len(self.areas)
            
            if new_len == old_len:
                break
            
            print 'Merged to {} navigation areas.'.format(new_len)

        print 'Pruning elements...'
        self.prune_elements()
        
        print 'Connecting areas...'
        count = self.connect_areas()
        print 'Generated {} connections.'.format(count)
        
        return True


    def prune_elements(self):
        """
        Prunes elements that make up the inside of all navigation areas.
        """
        
        for area in self.areas:
            x1, y1 = self.nav_grid.map_to_element(area.x1, area.y1)
            x2, y2 = self.nav_grid.map_to_element(area.x2, area.y2)
            
            # Shrink the area size by one element on each side.
            # Skip pruning elements in the area if the area is too small.
            x1 += 1
            x2 -= 1
            if x1 > x2:
                continue
            y1 += 1
            y2 -= 1
            if y1 > y2:
                continue
            
            area.inside_x1 = x1
            area.inside_y1 = y1
            area.inside_x2 = x2
            area.inside_y2 = y2
            area.elements = filter(self.area_element_prune_filter, area.elements)
            
        self.nav_grid.remove_pruned_elements()
    
    
    def connect_areas(self):
        count = 0
               
        for area in self.areas:
            for element in area.elements:
                for direction in DIRECTION_RANGE:
                    if element.connection[direction] is not None:
                        continue
                
                    other_element = element.elements[direction]
                    if other_element is None or other_element.area == area or other_element.area is None:
                        continue
                    
                    # Find all elements that connect to the other area.
                    connecting = []
                    other_area = other_element.area
                    for c_element in area.elements:
                        if c_element.elements[direction] is not None and c_element.elements[direction].area == other_area:
                            connecting.append(c_element)
                            connecting.append(c_element.elements[direction])
                    
                    x1, y1, x2, y2 = self.get_elements_bounds(connecting)
                    
                    # See if a connection exists in the other area that is equal to the current one.
                    connection = None
                    for c_connection in other_area.connections:
                        if c_connection.area_b == area and c_connection.x1 == x1 and c_connection.y1 == y1 and c_connection.x2 == x2 and c_connection.y2 == y2:
                            connection = c_connection
                            connection.flags |= navconnection.CONNECTION_FLAG_BA
                            break

                    # Create new connection object if needed.
                    if connection is None:
                        count += 1
                        
                        connection = navconnection.NavConnection()
                        connection.flags = navconnection.CONNECTION_FLAG_AB
                        connection.area_a = area
                        connection.area_b = other_area
                        connection.x1, connection.y1 = x1, y1
                        connection.x2, connection.y2 = x2, y2
                    
                    area.connections.append(connection)
                    
                    # Assign connection to elements.
                    for c_element in connecting:
                        if c_element.area == area:
                            c_element.connection[direction] = connection
        
        return count
                    
    
    def get_elements_bounds(self, elements):
        x1 = 0x8000
        y1 = 0x8000
        x2 = -0x8000
        y2 = -0x8000
        
        for element in elements:
            x1 = min(element.x, x1)
            y1 = min(element.y, y1)
            x2 = max(element.x, x2)
            y2 = max(element.y, y2)
        
        x1, y1 = self.nav_grid.element_to_map(x1, y1)
        x2, y2 = self.nav_grid.element_to_map(x2, y2)
        
        x1 -= self.nav_grid.element_size / 2
        y1 -= self.nav_grid.element_size / 2
        x2 += self.nav_grid.element_size / 2
        y2 += self.nav_grid.element_size / 2
        
        return x1, y1, x2, y2
    
    
    def area_element_prune_filter(self, element):
        if element.x >= element.area.inside_x1 and element.y >= element.area.inside_y1 and element.x < element.area.inside_x2 and element.y < element.area.inside_y2:
            self.nav_grid.element_prune.add(element)
            return False
        
        return True
            
    
    def generate_iteration(self, left, top, right, bottom, size):
        find_largest_area = self.find_largest_area
        add_area = self.add_area
        areas = self.areas
        element_hash = self.nav_grid.element_hash
        grid_width = self.nav_grid.width

        x = left
        y = top
        while 1:
            elements = element_hash.get(x + (y * grid_width))
            if elements is not None:
                for element in elements.itervalues():
                    if element.area is not None:
                        continue
                    
                    if find_largest_area(element, size) == False:
                        continue
                    
                    area = add_area(element, size, size)
                    area.sector = element.special_sector
                    area.flags = element.flags
                    area.plane = element.plane
                    areas.append(area)
                    
                    if len(areas) % int(250 / size) == 0:
                        print '{} navigation areas.'.format(len(areas))
            
            x += 1
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
            merge_area = element.area
            if merge_area is None:
                continue
            
            # Ignore areas that do not have similar contents.
            element_a = area.elements[0]
            element_b = merge_area.elements[0]
            if not (element_a.is_similar(element_b)):
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
            if width > self.max_area_size_merged or height > self.max_area_size_merged:
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

        # Move to the bottom right element.
        # This also rejects the potential area early on.
        start_element = element
        cx = 1
        while cx < size:
            start_element = start_element.elements[DIRECTION_RIGHT]
            if start_element is None:
                return False
            
            start_element = start_element.elements[DIRECTION_DOWN]
            if start_element is None:
                return False
            
            cx += 1
        
        # Test if each element is similar to the first one.
        xelement = start_element
        cx = x + size
        while cx > x:
            
            yelement = xelement
            cy = y + size
            while cy > y:
                if yelement is None or yelement.area is not None or (not yelement.is_similar(element)):
                    return False
                
                cy -= 1
                yelement = yelement.elements[DIRECTION_UP]
                
            cx -= 1
            xelement = xelement.elements[DIRECTION_LEFT]

        return True