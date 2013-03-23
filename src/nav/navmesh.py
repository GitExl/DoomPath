from doom.mapdata import Teleporter
from doom.mapenum import LINEDEF_VERTEX_1, LINEDEF_VERTEX_2, VERTEX_X, VERTEX_Y, LINEDEF_HEXEN_ARG0, LINEDEF_HEXEN_ARG1, \
    LINEDEF_DOOM_TAG
from doom.plane import Plane
from doom.trig import box_intersects_line, box_on_line_side
from nav import navconnection, navarea
from nav.navarea import NavArea
from nav.navconnection import NavConnection
from nav.navenum import *
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
MESH_FILE_CONNECTION = struct.Struct('<ihhhhiiI')


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
        left = self.nav_grid.map_data.min_x / self.nav_grid.element_size
        top = self.nav_grid.map_data.min_y / self.nav_grid.element_size
        right = left + self.nav_grid.width
        bottom = top + self.nav_grid.height
        
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


    def get_area(self, x, y):
        bx, by = self.map_data.blockmap.map_to_blockmap(x, y)
        block = self.map_data.blockmap.get(bx, by)
        if block is None:
            return None
        
        for index in block.areas:
            area = self.areas[index]
            if x >= area.x1 and x <= area.x2 and y >= area.y1 and y <= area.y2:
                return area
        
        return None
    
    
    def get_areas_intersecting(self, x1, y1, x2, y2):
        bx1, by1 = self.map_data.blockmap.map_to_blockmap(x1, y1)
        bx2, by2 = self.map_data.blockmap.map_to_blockmap(x2, y2)
        
        area_indices = []
        for y in range(by1, by2 + 1):
            for x in range(bx1, bx2 + 1):
                block = self.map_data.blockmap.get(x, y)
                area_indices.extend(block.areas)
        
        areas = []
        for index in area_indices:
            area = self.areas[index]
            if box_on_line_side(area.x1, area.y1, area.x2, area.y2, x1, y1, x2, y2) == -1:
                areas.append(area)
        
        return areas


    def connect_teleporters(self):
        """
        Creates area connections for teleporter line types.
        """
        
        for teleporter in self.map_data.teleporters:
            target_area = None
            
            if teleporter.kind == Teleporter.TELEPORTER_THING:
                target_area = self.get_area(teleporter.dest_x, teleporter.dest_y)
            if teleporter.kind == Teleporter.TELEPORTER_LINE:
                dest_x, dest_y = self.map_data.get_line_center(teleporter.dest_line)
                target_area = self.get_area(dest_x, dest_y)

            # Ignore missing teleport targets.
            if target_area is None:
                print 'Teleporter linedef {} does not point to a place on the map with navigation areas.'.format(teleporter.source_line)
                continue
            
            # Create the teleport connection line from the linedef vertices.
            linedef = self.map_data.linedefs[teleporter.source_line]
            vertex1 = self.map_data.vertices[linedef[LINEDEF_VERTEX_1]]
            vertex2 = self.map_data.vertices[linedef[LINEDEF_VERTEX_2]]
            x1 = vertex1[VERTEX_X]
            y1 = vertex1[VERTEX_Y]
            x2 = vertex2[VERTEX_X]
            y2 = vertex2[VERTEX_Y]
            
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1

            # Place a teleporter connection in all source areas.
            areas = self.get_areas_intersecting(x1, y1, x2, y2)
            for area in areas:
                connection = NavConnection()
                connection.x1 = x1
                connection.y1 = y1
                connection.x2 = x2
                connection.y2 = y2
                connection.area_a = area
                connection.area_b = target_area
                connection.linedef = teleporter.source_line
                connection.flags = navconnection.CONNECTION_FLAG_AB | navconnection.CONNECTION_FLAG_TELEPORTER
                
                area.connections.append(connection)
                

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
                ex, ey = x1 + 1, y1 + 1
                direction = DIRECTION_UP
            elif side == SIDE_RIGHT:
                ex, ey = x2 - 1, y2 - 1
                direction = DIRECTION_RIGHT
            elif side == SIDE_BOTTOM:
                ex, ey = x2 - 1, y2 - 1
                direction = DIRECTION_DOWN
            elif side == SIDE_LEFT:
                ex, ey = x1 + 1, y1 + 1
                direction = DIRECTION_LEFT
            ex, ey = self.nav_grid.map_to_element(ex, ey)
            
            # Find the element in this area.
            for element in area.elements:
                if element.x == ex and element.y == ey:
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
                
            # Merge the area element lists.
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
                    
                connection_data = MESH_FILE_CONNECTION.pack(connection_hash, connection.x1, connection.y1, connection.x2, connection.y2, area_a_hash, area_b_hash, connection.flags)
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
                    
                area_data = MESH_FILE_AREA.pack(area_hashes[index], area.x1, area.y1, area.x2, area.y2, area.z, plane_hash, sector_index, area.flags, len(area.connections))
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
                connection_hash, x1, y1, x2, y2, area_a_hash, area_b_hash, flags = MESH_FILE_CONNECTION.unpack(f.read(MESH_FILE_CONNECTION.size))
                connection.x1 = x1
                connection.y1 = y1
                connection.x2 = x2
                connection.y2 = y2
                connection.area_a = area_a_hash
                connection.area_b = area_b_hash
                connection.flags = flags
                connection_hashes[connection_hash] = connection
            
            # Read mesh areas.
            area_count = MESH_FILE_AREAS_HEADER.unpack(f.read(MESH_FILE_AREAS_HEADER.size))[0]
            for _ in range(area_count):
                area_hash, x1, y1, x2, y2, z, plane_hash, sector_index, flags, connection_count = MESH_FILE_AREA.unpack(f.read(MESH_FILE_AREA.size))
                
                area = NavArea(x1, y1, x2, y2, z)
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