from doom.mapdata import Teleporter
from doom.plane import Plane
from nav import navconnection
from nav.navarea import NavArea
from nav.navconnection import NavConnection
from nav.navenum import *
from util.rectangle import Rectangle
from util.vector import Vector2
import struct


MESH_FILE_ID = 'DPMESH'
MESH_FILE_VERSION = 1
MESH_FILE_HEADER = struct.Struct('<6sH')
MESH_FILE_AREAS_HEADER = struct.Struct('<I')
MESH_FILE_AREA = struct.Struct('<ihhhhhihIH')
MESH_FILE_AREA_CONNECTION = struct.Struct('<i')
MESH_FILE_PLANES_HEADER = struct.Struct('<I')
MESH_FILE_PLANE = struct.Struct('<ifffff')
MESH_FILE_CONNECTIONS_HEADER = struct.Struct('<I')
MESH_FILE_CONNECTION = struct.Struct('<ihhhhiiiI')


class NavMesh(object):
    
    def __init__(self, map_data, config, nav_grid):
        self.areas = []
        
        self.map_data = map_data
        self.nav_grid = nav_grid
        self.config = config


    def create_from_grid(self, max_area_size, max_area_size_merged):
        self.max_area_size = max_area_size
        self.max_area_size_merged = max_area_size_merged
        
        self.max_size_elements = self.max_area_size / self.nav_grid.element_size
        
        # Determine the locations where to test for elements.
        grid_area = Rectangle()
        grid_area.left = self.nav_grid.map_data.min_x / self.nav_grid.element_size
        grid_area.top = self.nav_grid.map_data.min_y / self.nav_grid.element_size
        grid_area.right = grid_area.left + self.nav_grid.width
        grid_area.bottom = grid_area.top + self.nav_grid.height
        
        min_side = self.max_size_elements
        while min_side > 0:
            print 'Size iteration {}...'.format(min_side)
            self.generate_iteration(grid_area, min_side)            
            min_side -= 1
        
        print 'Merging...'
        while 1:
            old_len = len(self.areas)
            self.areas = filter(self.area_merge_filter, self.areas)
            new_len = len(self.areas)
            
            if new_len == old_len:
                break
            
            print 'Merged to {} navigation areas.'.format(new_len)
            
        print 'Adding areas to blockmap...'
        self.map_data.blockmap.generate_areas(self)

        print 'Pruning elements...'
        self.prune_elements()
        
        print 'Connecting areas...'
        count = self.connect_areas()
        print 'Generated {} connections.'.format(count)
        
        print 'Connecting teleporters...'
        self.connect_teleporters()
        
        return True


    def get_area_at(self, pos):
        x, y = self.map_data.blockmap.map_to_blockmap(pos)
        block = self.map_data.blockmap.get_xy(x, y)
        if block is None:
            return None

        for index in block.areas:
            area = self.areas[index]
            if area.rect.is_point_inside(pos) == True:
                return area
        
        return None
    
    
    def get_areas_intersecting(self, rect):
        x1, y1 = self.map_data.blockmap.map_to_blockmap(rect.p1)
        x2, y2 = self.map_data.blockmap.map_to_blockmap(rect.p2)

        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        area_indices = set()
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                block = self.map_data.blockmap.get_xy(x, y)
                area_indices.update(block.areas)
        
        areas = []
        for index in area_indices:
            area = self.areas[index]
            if area.rect.intersects_with_line(rect.left, rect.top, rect.right, rect.bottom) == True:
                areas.append(area)

        return areas


    def connect_teleporters(self):
        """
        Creates area connections for teleporter line types.
        """
        
        count = 0
        rect = Rectangle()
        
        for teleporter in self.map_data.teleporters:
            target_area = None
            
            # Get the area that the teleporter target is in.
            if teleporter.kind == Teleporter.TELEPORTER_THING:
                target_area = self.get_area_at(teleporter.dest)
            if teleporter.kind == Teleporter.TELEPORTER_LINE:
                dest = self.map_data.get_line_center(teleporter.dest_line)
                target_area = self.get_area_at(dest)

            # Ignore missing teleport targets.
            if target_area is None:
                print 'Teleporter linedef {} does not point to a place on the map with navigation areas.'.format(teleporter.source_line)
                continue
            
            # Create the teleport connection line from the linedef vertices.
            linedef = self.map_data.linedefs[teleporter.source_line]           
            rect.set(
                linedef.vertex1.x,
                linedef.vertex1.y,
                linedef.vertex2.x,
                linedef.vertex2.y
            )

            # Place a teleporter connection in all intersecting source areas.
            areas = self.get_areas_intersecting(rect)
            for area in areas:
                connection = NavConnection()
                connection.rect.copy_from(rect)
                connection.area_a = area
                connection.area_b = target_area
                connection.linedef = teleporter.source_line
                connection.flags = navconnection.CONNECTION_FLAG_AB | navconnection.CONNECTION_FLAG_TELEPORTER
                
                area.connections.append(connection)
            
            count += 1
        
        print 'Connected {} teleporters.'.format(count)
                

    def prune_elements(self):
        """
        Prunes elements that make up the inside of all navigation areas.
        """
        
        for area in self.areas:
            x1, y1 = self.nav_grid.map_to_element(area.rect.p1)
            x2, y2 = self.nav_grid.map_to_element(area.rect.p2)
            
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
            
            area.inside_rect.set(x1, y1, x2, y2)
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
                    
                    rect = self.get_elements_bounds(connecting)
                    
                    # See if a connection exists in the other area that is equal to the current one.
                    connection = None
                    for c_connection in other_area.connections:
                        if c_connection.area_b == area and c_connection.rect == rect:
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
                        connection.rect.copy_from(rect)
                        
                    area.connections.append(connection)
                    
                    # Assign connection to elements.
                    for c_element in connecting:
                        if c_element.area == area:
                            c_element.connection[direction] = connection
        
        return count
                    
    
    def get_elements_bounds(self, elements):
        p1 = Vector2(0x8000, 0x8000)
        p2 = Vector2(-0x8000, -0x8000)
        
        for element in elements:
            p1.x = min(element.pos.x, p1.x)
            p1.y = min(element.pos.y, p1.y)
            p2.x = max(element.pos.x, p2.x)
            p2.y = max(element.pos.y, p2.y)
        
        x1, y1 = self.nav_grid.element_to_map(p1)
        x2, y2 = self.nav_grid.element_to_map(p2)
        
        x1 -= self.nav_grid.element_size / 2
        y1 -= self.nav_grid.element_size / 2
        x2 += self.nav_grid.element_size / 2
        y2 += self.nav_grid.element_size / 2
        
        return Rectangle(x1, y1, x2, y2)
    
    
    def area_element_prune_filter(self, element):
        if element.pos.x >= element.area.inside_rect.left and element.pos.y >= element.area.inside_rect.top \
         and element.pos.x < element.area.inside_rect.right and element.pos.y < element.area.inside_rect.bottom:
            self.nav_grid.element_prune.add(element)
            return False
        
        return True
            
    
    def generate_iteration(self, grid_area, size):
        find_largest_area = self.find_largest_area
        add_area = self.add_area
        areas = self.areas
        element_hash = self.nav_grid.element_hash
        grid_width = self.nav_grid.width

        x = grid_area.left
        y = grid_area.top
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
                    
                    if len(areas) % int(1000 / size) == 0:
                        print '{} navigation areas.'.format(len(areas))
            
            x += 1
            if x >= grid_area.right:
                x = grid_area.left
                y += 1
                if y >= grid_area.bottom:
                    break

    
    def area_merge_filter(self, area):
        pos = Vector2()
        
        for side in SIDE_RANGE:
            x1, y1, x2, y2 = area.get_side(side)
            
            # Select a grid element on the current side.
            if side == SIDE_TOP:
                pos.set(x1 + 1, y1 + 1)
                direction = DIRECTION_UP
            elif side == SIDE_RIGHT:
                pos.set(x2 - 1, y2 - 1)
                direction = DIRECTION_RIGHT
            elif side == SIDE_BOTTOM:
                pos.set(x2 - 1, y2 - 1)
                direction = DIRECTION_DOWN
            elif side == SIDE_LEFT:
                pos.set(x1 + 1, y1 + 1)
                direction = DIRECTION_LEFT
            ex, ey = self.nav_grid.map_to_element(pos)
            
            # Find the element in this area.
            for element in area.elements:
                if element.pos.x == ex and element.pos.y == ey:
                    break
            else:
                continue
            
            # Select the connected element on the current side.
            element = element.elements[direction]
            if element is None:
                continue
            
            # Select the navigation area that the selected element is a part of.
            merge_area = element.area
            if merge_area is None:
                continue
            
            # Ignore areas that do not have similar contents.
            if not (area.elements[0].is_similar(merge_area.elements[0])):
                continue
            
            # See if the two areas have matching opposite sides.
            merge_x1, merge_y1, merge_x2, merge_y2 = merge_area.get_side(SIDE_RANGE_OPPOSITE[side])
            if x1 != merge_x1 or y1 != merge_y1 or x2 != merge_x2 or y2 != merge_y2:
                continue
            
            rect = area.rect
            merge_rect = merge_area.rect
            
            # Get the size of the new merged area.
            if side == SIDE_TOP:
                width = rect.get_width()
                height = rect.bottom - merge_rect.top 
            elif side == SIDE_RIGHT:
                width = merge_rect.right - rect.left
                height = rect.get_height()
            elif side == SIDE_BOTTOM:
                width = rect.get_width()
                height = merge_rect.bottom - rect.top
            elif side == SIDE_LEFT:
                width = rect.right - merge_rect.left
                height = rect.get_height()
                
            # Abort merging if the area dimensions are not good.
            if width > self.max_area_size_merged or height > self.max_area_size_merged:
                continue
            
            # Merge the area rectangle.
            if side == SIDE_TOP:
                merge_rect.set(merge_rect.left, merge_rect.top, merge_rect.right, rect.bottom)
            elif side == SIDE_RIGHT:
                merge_rect.set(rect.left, merge_rect.top, merge_rect.right, merge_rect.bottom)
            elif side == SIDE_BOTTOM:
                merge_rect.set(merge_rect.left, rect.top, merge_rect.right, merge_rect.bottom)
            elif side == SIDE_LEFT:
                merge_rect.set(merge_rect.left, merge_rect.top, rect.right, merge_rect.bottom)
                
            # Merge the area element lists.
            merge_area.elements.extend(area.elements)
            for element in area.elements:
                element.area = merge_area
                
            return False
        
        return True

    
    def add_area(self, element, width, height):
        area_rect = Rectangle()
        area_rect.set_size(element.pos.x, element.pos.y, width, height)
        
        # Create a new nav area of the found width and height.
        x1, y1 = self.nav_grid.element_to_map(area_rect.p1)
        x2, y2 = self.nav_grid.element_to_map(area_rect.p2)
        p1 = Vector2(x1, y1)
        p2 = Vector2(x2, y2)
        
        # Offset to grid element center.
        p1.x -= (self.nav_grid.element_size / 2)
        p1.y -= (self.nav_grid.element_size / 2)
        p2.x -= (self.nav_grid.element_size / 2)
        p2.y -= (self.nav_grid.element_size / 2)

        area = NavArea(p1.x, p1.y, p2.x, p2.y, element.pos.z)
        
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
        x = element.pos.x
        y = element.pos.y

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
    
    
    def write(self, filename):
        with open(filename, 'wb') as f:
            header_data = MESH_FILE_HEADER.pack(MESH_FILE_ID, MESH_FILE_VERSION)
            f.write(header_data)
            
            # Generate a list of area subdata.
            area_hashes = []
            plane_hashes = {}
            connection_hashes = {}
            for area in self.areas:
                area_hashes.append(hash(area))
                
                if area.plane is not None:
                    plane_hashes[hash(area.plane)] = area.plane
                
                for connection in area.connections:
                    connection_hashes[hash(connection)] = connection
            
            # Write plane data.
            planes_header = MESH_FILE_PLANES_HEADER.pack(len(plane_hashes))
            f.write(planes_header)
            for plane_hash, plane in plane_hashes.iteritems():
                plane_data = MESH_FILE_PLANE.pack(plane_hash, plane.a, plane.b, plane.c, plane.d, plane.invc)
                f.write(plane_data)
            
            # Write connection data.
            connections_header = MESH_FILE_CONNECTIONS_HEADER.pack(len(connection_hashes))
            f.write(connections_header)
            for connection_hash, connection in connection_hashes.iteritems():
                if connection.area_a is not None:
                    area_a_hash = hash(connection.area_a)
                else:
                    area_a_hash = 0
                if connection.area_b is not None:
                    area_b_hash = hash(connection.area_b)
                else:
                    area_a_hash = 0
                if connection.linedef is not None:
                    linedef = connection.linedef
                else:
                    linedef = -1
                    
                connection_data = MESH_FILE_CONNECTION.pack(connection_hash, connection.rect.left, connection.rect.top, connection.rect.right, connection.rect.bottom, area_a_hash, area_b_hash, linedef, connection.flags)
                f.write(connection_data)
            
            # Write area data.
            areas_header = MESH_FILE_AREAS_HEADER.pack(len(area_hashes))
            f.write(areas_header)
            for index, area in enumerate(self.areas):
                if area.sector is None:
                    sector_index = -1
                else:
                    sector_index = area.sector
                    
                if area.plane is not None:
                    plane_hash = hash(area.plane)
                else:
                    plane_hash = 0
                    
                area_data = MESH_FILE_AREA.pack(area_hashes[index], area.rect.left, area.rect.top, area.rect.right, area.rect.bottom, area.z, plane_hash, sector_index, area.flags, len(area.connections))
                f.write(area_data)
                
                for connection in area.connections:
                    connection_data = MESH_FILE_AREA_CONNECTION.pack(hash(connection))
                    f.write(connection_data)
                
    
    def read(self, filename):
        with open(filename, 'rb') as f:
            file_id, file_version = MESH_FILE_HEADER.unpack(f.read(MESH_FILE_HEADER.size))
            if file_id != MESH_FILE_ID:
                print 'Invalid mesh file.'
                return
            if file_version > MESH_FILE_VERSION:
                print 'Unsupported mesh version {}.'.format(file_version)
                return
            
            area_hashes = {}
            plane_hashes = {}
            connection_hashes = {}
            self.areas = []
            
            # Read planes.
            planes_count = MESH_FILE_PLANES_HEADER.unpack(f.read(MESH_FILE_PLANES_HEADER.size))[0]
            for _ in range(planes_count):
                plane = Plane()
                plane_hash, plane.a, plane.b, plane.c, plane.d, plane.invc = MESH_FILE_PLANE.unpack(f.read(MESH_FILE_PLANE.size))
                plane_hashes[plane_hash] = plane
            
            # Read area connections.
            connections_count = MESH_FILE_CONNECTIONS_HEADER.unpack(f.read(MESH_FILE_CONNECTIONS_HEADER.size))[0]
            for _ in range(connections_count):
                connection = NavConnection()
                connection_hash, left, top, right, bottom, area_a_hash, area_b_hash, linedef, flags = MESH_FILE_CONNECTION.unpack(f.read(MESH_FILE_CONNECTION.size))
                
                if linedef == -1:
                    linedef = None
                
                connection.rect.set(left, top, right, bottom)
                connection.area_a = area_a_hash
                connection.area_b = area_b_hash
                connection.linedef = linedef
                connection.flags = flags
                connection_hashes[connection_hash] = connection
            
            # Read mesh areas.
            area_count = MESH_FILE_AREAS_HEADER.unpack(f.read(MESH_FILE_AREAS_HEADER.size))[0]
            for _ in range(area_count):
                area_hash, left, top, right, bottom, z, plane_hash, sector_index, flags, connection_count = MESH_FILE_AREA.unpack(f.read(MESH_FILE_AREA.size))
                
                area = NavArea(left, top, right, bottom, z)
                if sector_index == -1:
                    sector_index = None
                area.sector = sector_index
                area.flags = flags
                if plane_hash != 0:
                    area.plane = plane_hashes[plane_hash]
                
                for _ in range(connection_count):
                    connection_hash = MESH_FILE_AREA_CONNECTION.unpack(f.read(MESH_FILE_AREA_CONNECTION.size))[0]
                    area.connections.append(connection_hashes[connection_hash])
                
                self.areas.append(area)
                area_hashes[area_hash] = area
            
            # Set connection objects. 
            for connection in connection_hashes.itervalues():
                if connection.area_a != 0:
                    connection.area_a = area_hashes[connection.area_a]
                else:
                    connection.area_a = None
                if connection.area_b != 0:
                    connection.area_b = area_hashes[connection.area_b]
                else:
                    connection.area_b = None