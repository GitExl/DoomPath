from doom.map.objects import Linedef
from nav import navconnection
from nav.navenum import DIRECTION_RANGE, DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT
from util import rectangle
import pygame


COLOR_LINEDEF_IMPASSIBLE = pygame.Color(223, 223, 223, 255)
COLOR_LINEDEF_2SIDED = pygame.Color(95, 95, 95, 255)
COLOR_LINEDEF_HIGHLIGHT = pygame.Color(255, 100, 0, 255)
COLOR_BLOCKMAP = pygame.Color(0, 45, 89, 255)
COLOR_BLOCKMAP_HIGHLIGHT = pygame.Color(0, 96, 191, 255)
COLOR_THING = pygame.Color(0, 255, 0, 255)

grid_colors = None
grid_colors_special = None


def render_connections(nav_mesh, surface, camera, mouse_pos):
    COLOR_RECTANGLE = pygame.Color(7, 23, 31, 255)
    COLOR_TELEPORT = pygame.Color(31, 191, 95, 255)
    COLOR_ACTIVE = pygame.Color(255, 47, 63, 255)
    TELEPORT_SIZE = 6    
    
    connections = set()
    c_rect = rectangle.Rectangle()
    
    for area in nav_mesh.areas:
        for connection in area.connections:
            if (connection.flags & navconnection.CONNECTION_FLAG_TELEPORTER) != 0:
                c_rect.copy_from(connection.rect)
                c_rect.flip_if_reversed()
                
                x1, y1 = camera.map_to_screen(c_rect.left, c_rect.top)
                x2, y2 = camera.map_to_screen(c_rect.right, c_rect.bottom)
                
                if mouse_pos.x >= c_rect.left - TELEPORT_SIZE and mouse_pos.y >= c_rect.top - TELEPORT_SIZE and \
                  mouse_pos.x <= c_rect.right + TELEPORT_SIZE and mouse_pos.y <= c_rect.bottom + TELEPORT_SIZE:
                    color = COLOR_ACTIVE
                    connections.add(connection)
                    active = True
                else:
                    color = COLOR_TELEPORT
                    active = False
                    
                size = int(TELEPORT_SIZE * camera.zoom)
                pygame.draw.line(surface, color, (x1, y1), (x2, y2), size)
                
                if active == True:
                    sx, sy = camera.map_to_screen(connection.rect.left + connection.rect.get_width() / 2, connection.rect.top + connection.rect.get_height() / 2)
                    dx, dy = camera.map_to_screen(connection.area_b.rect.left + connection.area_b.rect.get_width() / 2, connection.area_b.rect.top + connection.area_b.rect.get_height() / 2)
                    pygame.draw.line(surface, COLOR_ACTIVE, (sx, sy), (dx, dy), 1)
                
            else:
                rx, ry = camera.map_to_screen(connection.rect.left, connection.rect.top)
                width, height = connection.rect.get_width() * camera.zoom, connection.rect.get_height() * camera.zoom
                
                rx += 1
                ry += 1
                width -= 1
                height -= 1
                
                if rx < 0:
                    width -= abs(rx)
                    rx = 0
                if ry < 0:
                    height -= abs(ry)
                    ry = 0
                if rx + width >= surface.get_width():
                    width = surface.get_width() - rx
                if ry + height >= surface.get_height():
                    height = surface.get_height() - ry
                    
                if width < 1 or height < 1:
                    continue
    
                if connection.rect.is_point_inside(mouse_pos) == True:
                    color = COLOR_ACTIVE
                    connections.add(connection)
                else:
                    color = COLOR_RECTANGLE
                    
                rect = pygame.Rect(rx, ry, width, height)
                surface.fill(color, rect, special_flags=pygame.BLEND_ADD)
            
    return connections


def render_blockmap(map_data, surface, camera, mouse_pos):
    box_top = mouse_pos.y + map_data.config.player_radius
    box_bottom = mouse_pos.y - map_data.config.player_radius
    box_right = mouse_pos.x + map_data.config.player_radius
    box_left = mouse_pos.x - map_data.config.player_radius
    
    x1 = int((box_left - map_data.blockmap.origin.x) / map_data.blockmap.blocksize)
    y1 = int((box_bottom - map_data.blockmap.origin.y) / map_data.blockmap.blocksize)
    x2 = int((box_right - map_data.blockmap.origin.x) / map_data.blockmap.blocksize) + 1
    y2 = int((box_top - map_data.blockmap.origin.y) / map_data.blockmap.blocksize) + 1
    
    # Draw blockmap.
    for cx in range(0, map_data.blockmap.size.x):
        for cy in range(0, map_data.blockmap.size.y):
            
            bx = int(cx * map_data.blockmap.blocksize + map_data.blockmap.origin.x)
            by = int(cy * map_data.blockmap.blocksize + map_data.blockmap.origin.y)
            pos1 = camera.map_to_screen(bx, by)
            pos2 = (int(map_data.blockmap.blocksize * camera.zoom), int(map_data.blockmap.blocksize * camera.zoom))
            rect = pygame.Rect(pos1, pos2)

            if cx >= x1 and cx < x2 and cy >= y1 and cy < y2:
                color = COLOR_BLOCKMAP_HIGHLIGHT
            else:
                color = COLOR_BLOCKMAP
                
            pygame.draw.rect(surface, color, rect, 1)


def render_things(map_data, config, surface, camera):
    color = COLOR_THING
    for thing in map_data.things:
        thing_def = config.thing_dimensions.get(thing.doomid)
        if thing_def is None:
            continue

        x, y = camera.map_to_screen(thing.x, thing.y)
        pos = (int(x), int(y))
        radius = int((thing_def.radius / 3) * camera.zoom)
        if radius >= 1:
            pygame.draw.circle(surface, color, pos, radius)
            
        rect = pygame.Rect(
            camera.map_to_screen(thing.x - thing_def.radius, thing.y - thing_def.radius),
            ((thing_def.radius * 2) * camera.zoom, (thing_def.radius * 2) * camera.zoom)
        )
        pygame.draw.rect(surface, color, rect, 1)


def render_linedefs(map_data, surface, camera, sector_mark):
    color = None
    for linedef in map_data.linedefs:
        front = linedef.sidedef_front
        back = linedef.sidedef_back
        
        sector = -1
        if front != Linedef.SIDEDEF_NONE:
            sector = map_data.sidedefs[front].sector
        if sector != sector_mark and back != Linedef.SIDEDEF_NONE:
            sector = map_data.sidedefs[back].sector
        
        if sector == sector_mark:
            color = COLOR_LINEDEF_HIGHLIGHT
        elif (linedef.flags & Linedef.FLAG_TWOSIDED) == 0 or (linedef.flags & Linedef.FLAG_IMPASSIBLE) != 0:
            color = COLOR_LINEDEF_IMPASSIBLE
        else:
            color = COLOR_LINEDEF_2SIDED
            
        pos1 = camera.map_to_screen(linedef.vertex1.x, linedef.vertex1.y)
        pos2 = camera.map_to_screen(linedef.vertex2.x, linedef.vertex2.y)
        
        pygame.draw.line(surface, color, pos1, pos2, 1)
    
    if sector_mark >= 0:
        center_pos = map_data.get_sector_center(sector_mark)
        center_pos.x, center_pos.y = camera.map_to_screen(center_pos.x, center_pos.y)
        
        pygame.draw.circle(surface, COLOR_LINEDEF_HIGHLIGHT, (int(center_pos.x), int(center_pos.y)), int(5 * camera.zoom))
        

def render_navmesh(nav_mesh, surface, camera, mouse_pos):
    COLOR_FILL = pygame.Color(15, 15, 15, 255)
    COLOR_HIGHLIGHT = pygame.Color(63, 63, 63, 255)
    COLOR_BORDER = pygame.Color(191, 95, 0, 255)

    areas = []

    for area in nav_mesh.areas:
        if area.rect.is_point_inside(mouse_pos) == True:
            color = COLOR_HIGHLIGHT
            areas.append(area)
        else:
            color = COLOR_FILL
        
        x, y = camera.map_to_screen(area.rect.left, area.rect.top)
        width, height = area.rect.get_width() * camera.zoom, area.rect.get_height() * camera.zoom
        
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
        
        surface.fill(color, rect, special_flags=pygame.BLEND_SUB)
        pygame.draw.rect(surface, COLOR_BORDER, rect, 1)
    
    return areas


def render_navgrid_init(nav_grid):
    COLOR_ELEMENT_SPECIAL = pygame.Color(255, 0, 255, 255)
    COLOR_ELEMENT = pygame.Color(255, 255, 255, 255)
    
    nav_grid.grid_colors = [None] * 256
    for index in range(0, 256):
        v = index / 255.0
        nav_grid.grid_colors[index] = pygame.Color(int(COLOR_ELEMENT.r * v), int(COLOR_ELEMENT.g * v), int(COLOR_ELEMENT.b * v), 255)
    
    nav_grid.grid_colors_special = [None] * 256
    for index in range(0, 256):
        v = index / 255.0
        nav_grid.grid_colors_special[index] = pygame.Color(int(COLOR_ELEMENT_SPECIAL.r * v), int(COLOR_ELEMENT_SPECIAL.g * v), int(COLOR_ELEMENT_SPECIAL.b * v), 255)


def render_navgrid(nav_grid, surface, camera, mouse_pos):
    COLOR_ELEMENT_HIGHLIGHT = pygame.Color(0, 255, 255, 255)
    
    mouse_pos = nav_grid.map_to_element(mouse_pos)
    rect = pygame.Rect((0, 0), (nav_grid.element_size * camera.zoom, nav_grid.element_size * camera.zoom))
    z_mod = 255.0 / nav_grid.map_data.size.z
    
    elements = []
    for element in nav_grid.elements:
        if element.pos.x == mouse_pos.x and element.pos.y == mouse_pos.y:
            elements.append(element)
        
        pos = nav_grid.element_to_map(element.pos)
        x, y = camera.map_to_screen(pos.x, pos.y)
        rect.top = y - (nav_grid.element_size / 2) * camera.zoom
        rect.left = x - (nav_grid.element_size / 2) * camera.zoom
        
        v = int((element.pos.z - nav_grid.map_data.min_z) * z_mod)
        if element.special_sector is not None:
            color = nav_grid.grid_colors_special[v]
        else:
            color = nav_grid.grid_colors[v]
        
        pygame.draw.rect(surface, color, rect, 1)
    
    rect = pygame.Rect((0, 0), (nav_grid.element_size * camera.zoom, nav_grid.element_size * camera.zoom))
    element_hash = mouse_pos.x + (mouse_pos.y * (nav_grid.map_data.size.x / nav_grid.element_size))
    element = nav_grid.element_hash.get(element_hash)
    if element is not None:
        element = element[element.keys()[0]]

        color = COLOR_ELEMENT_HIGHLIGHT
        x, y = nav_grid.element_to_map(element.x, element.y)
        x, y = camera.map_to_screen(x, y)
        rect.top = y - (nav_grid.element_size / 2) * camera.zoom
        rect.left = x - (nav_grid.element_size / 2) * camera.zoom

        pygame.draw.rect(surface, color, rect, 1)
        
        for direction in DIRECTION_RANGE:
            if element.elements[direction] is not None:
                start = (rect.left + (nav_grid.element_size * camera.zoom) / 2, rect.top + (nav_grid.element_size * camera.zoom) / 2)
                
                if direction == DIRECTION_UP:
                    end = (start[0], start[1] - (nav_grid.element_size * camera.zoom))
                elif direction == DIRECTION_RIGHT:
                    end = (start[0] + (nav_grid.element_size * camera.zoom), start[1])
                elif direction == DIRECTION_DOWN:
                    end = (start[0], start[1] + (nav_grid.element_size * camera.zoom))
                elif direction == DIRECTION_LEFT:
                    end = (start[0] - (nav_grid.element_size * camera.zoom), start[1])
                    
                pygame.draw.line(surface, color, start, end, 1)
    
    return elements