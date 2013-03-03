import pygame


AREA_SIZE_MAX = 20


class NavArea(object):

    def __init__(self, x1, y1, x2, y2, z):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.z = z
        self.sector = -1
        self.elements = []
    
    
    def __repr__(self):
        return 'x1 {}, y1 {}, x2 {}, y2 {}, z {}, sector {}, width {}, height {}'.format(self.x1, self.y1, self.x2, self.y2, self.z, self.sector, self.x2 - self.x1, self.y2 - self.y1) 
    

class NavMesh(object):
    
    def __init__(self):
        self.areas = []


    def create_from_grid(self, nav_grid, iterations=-1):
        x = nav_grid.map_data.min_x / nav_grid.element_size
        y = nav_grid.map_data.min_y / nav_grid.element_size
        iteration = 0
        
        while 1:
            elements = nav_grid.get_element_list(x, y)
            if elements is not None:
                for element in elements.itervalues():
                    if element.area is None:
                        area = self.find_largest_area(nav_grid, element)
                        self.areas.append(area)
                        
                        iteration += 1
                        if iterations > 0 and iteration >= iterations:
                            return False
            
            x += 1
            if x >= nav_grid.width:
                x = 0
                y += 1
                if y >= nav_grid.height:
                    break
        
        print 'Created {} navigation areas.'.format(len(self.areas))
        
        return True
                
    
    def find_largest_area(self, nav_grid, element):
        x = element.x
        y = element.y
        z = element.z
        
        width = 1
        height = 1
        area_amount = 1
        max_height = AREA_SIZE_MAX
        
        # Find the largest area size.
        for cx in range(x, x + AREA_SIZE_MAX):
            for cy in range(y, y + max_height):
                add_element = nav_grid.get_element(cx, cy, z)
                if add_element is None or add_element.area is not None or add_element != element:
                    max_height = cy - y
                    break
                
                new_area_amount = ((cx - x) + 1) * ((cy - y) + 1)
                if new_area_amount > area_amount:
                    width = cx - x + 1
                    height = cy - y + 1
                    area_amount = new_area_amount

        # Create a new nav area of the found width and height.
        ex1, ey1, _ = nav_grid.element_to_map(x, y, z)
        ex2, ey2, _ = nav_grid.element_to_map(x + width, y + height, z)
        ex1 -= (nav_grid.element_size / 2)
        ey1 -= (nav_grid.element_size / 2)
        ex2 -= (nav_grid.element_size / 2)
        ey2 -= (nav_grid.element_size / 2)

        area = NavArea(ex1, ey1, ex2, ey2, z)
        area.sector = element.special_sector
        
        # Assign this area to all the elements in it.
        for cx in range(x, x + width):
            for cy in range(y, y + height):
                add_element = nav_grid.get_element(cx, cy, z)
                if add_element is None:
                    continue
                add_element.area = area
        
        return area
    
    
    def render(self, surface, camera):
        color = pygame.Color(79, 31, 0, 255)
        
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
            
            surface.fill(color, rect, special_flags=pygame.BLEND_ADD)