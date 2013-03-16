from doom.mapenum import *
from nav.navenum import DIRECTION_RANGE, DIRECTION_UP, DIRECTION_RIGHT, DIRECTION_DOWN, DIRECTION_LEFT
import pygame


COLOR_LINEDEF_IMPASSIBLE = pygame.Color(223, 223, 223, 255)
COLOR_LINEDEF_2SIDED = pygame.Color(95, 95, 95, 255)
COLOR_LINEDEF_HIGHLIGHT = pygame.Color(255, 100, 0, 255)
COLOR_BLOCKMAP = pygame.Color(0, 45, 89, 255)
COLOR_BLOCKMAP_HIGHLIGHT = pygame.Color(0, 96, 191, 255)
COLOR_THING = pygame.Color(0, 255, 0, 255)

grid_colors = None
grid_colors_special = None


def render_connections(nav_mesh, surface, camera, x, y):
    COLOR_FILL = pygame.Color(7, 23, 31, 255)
    COLOR_ACTIVE = pygame.Color(255, 47, 63, 255)
    
    connections = set()
    
    for area in nav_mesh.areas:
        for connection in area.connections:
            rx, ry = camera.map_to_screen(connection.x1, connection.y1)
            width, height = ((connection.x2 - connection.x1) * camera.zoom, (connection.y2 - connection.y1) * camera.zoom)
            
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

            if x >= connection.x1 and y >= connection.y1 and x < connection.x2 and y < connection.y2:
                color = COLOR_ACTIVE
                connections.add(connection)
            else:
                color = COLOR_FILL
                
            rect = pygame.Rect(rx, ry, width, height)
            surface.fill(color, rect, special_flags=pygame.BLEND_ADD)
            
    return connections


def render_blockmap(map_data, surface, camera, x, y):
    box_top = y + map_data.config.player_radius
    box_bottom = y - map_data.config.player_radius
    box_right = x + map_data.config.player_radius
    box_left = x - map_data.config.player_radius
    
    x1 = int((box_left - map_data.blockmap.origin_x) / map_data.blockmap.blocksize)
    y1 = int((box_bottom - map_data.blockmap.origin_y) / map_data.blockmap.blocksize)
    x2 = int((box_right - map_data.blockmap.origin_x) / map_data.blockmap.blocksize) + 1
    y2 = int((box_top - map_data.blockmap.origin_y) / map_data.blockmap.blocksize) + 1
    
    # Draw blockmap.
    for cx in range(0, map_data.blockmap.width):
        for cy in range(0, map_data.blockmap.height):
            bx = int(cx * map_data.blockmap.blocksize + map_data.blockmap.origin_x)
            by = int(cy * map_data.blockmap.blocksize + map_data.blockmap.origin_y)
            pos1 = camera.map_to_screen(bx, by)
            pos2 = (int(map_data.blockmap.blocksize * camera.zoom), int(map_data.blockmap.blocksize * camera.zoom))
            rect = pygame.Rect(pos1, pos2)
            
            if cx >= x1 and cx < x2 and cy >= y1 and cy < y2:
                color = COLOR_BLOCKMAP_HIGHLIGHT
            else:
                color = COLOR_BLOCKMAP
                
            pygame.draw.rect(surface, color, rect, 1)


def render_things(map_data, surface, camera, x, y):
    color = COLOR_THING
    for thing in map_data.things:
        thing_def = map_data.config.thing_dimensions.get(thing[map_data.THING_TYPE])
        if thing_def is None:
            continue

        x, y = camera.map_to_screen(thing[map_data.THING_X], thing[map_data.THING_Y])
        pos = (int(x), int(y))
        radius = int((thing_def.radius / 3) * camera.zoom)
        if radius >= 1:
            pygame.draw.circle(surface, color, pos, radius)
            
        rect = pygame.Rect(
            camera.map_to_screen(thing[map_data.THING_X] - thing_def.radius, thing[map_data.THING_Y] - thing_def.radius),
            ((thing_def.radius * 2) * camera.zoom, (thing_def.radius * 2) * camera.zoom)
        )
        pygame.draw.rect(surface, color, rect, 1)


def render_linedefs(map_data, surface, camera, x, y, sector_mark):
    color = None
    for linedef in map_data.linedefs:
        front = linedef[map_data.LINEDEF_SIDEDEF_FRONT]
        back = linedef[map_data.LINEDEF_SIDEDEF_BACK]
        
        sector = -1
        if front != SIDEDEF_NONE:
            sector = map_data.sidedefs[front][SIDEDEF_SECTOR]
        if sector != sector_mark and back != SIDEDEF_NONE:
            sector = map_data.sidedefs[back][SIDEDEF_SECTOR]
        
        if sector == sector_mark:
            color = COLOR_LINEDEF_HIGHLIGHT
        elif (linedef[LINEDEF_FLAGS] & LINEDEF_FLAG_TWOSIDED) == 0 or (linedef[LINEDEF_FLAGS] & LINEDEF_FLAG_IMPASSIBLE) != 0:
            color = COLOR_LINEDEF_IMPASSIBLE
        else:
            color = COLOR_LINEDEF_2SIDED
            
        vertex1 = map_data.vertices[linedef[LINEDEF_VERTEX_1]]
        vertex2 = map_data.vertices[linedef[LINEDEF_VERTEX_2]]
        
        pos1 = camera.map_to_screen(vertex1[VERTEX_X], vertex1[VERTEX_Y])
        pos2 = camera.map_to_screen(vertex2[VERTEX_X], vertex2[VERTEX_Y])
        
        pygame.draw.line(surface, color, pos1, pos2, 1)
    
    if sector_mark >= 0:
        center_x, center_y = map_data.get_sector_center(sector_mark)
        center_x, center_y = camera.map_to_screen(center_x, center_y)
        
        pygame.draw.circle(surface, COLOR_LINEDEF_HIGHLIGHT, (int(center_x), int(center_y)), int(5 * camera.zoom))
        

def render_navmesh(nav_mesh, surface, camera):
    COLOR_FILL = pygame.Color(15, 15, 15, 255)
    COLOR_BORDER = pygame.Color(191, 95, 0, 255)

    for area in nav_mesh.areas:
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


def render_navgrid(nav_grid, surface, camera, sx, sy):
    COLOR_ELEMENT_HIGHLIGHT = pygame.Color(0, 255, 255, 255)
    
    sx, sy = nav_grid.map_to_element(sx, sy)
    rect = pygame.Rect((0, 0), (nav_grid.element_size * camera.zoom, nav_grid.element_size * camera.zoom))
    z_mod = 255.0 / nav_grid.map_data.depth
    
    elements = []
    for element in nav_grid.elements:
        if element.x == sx and element.y == sy:
            elements.append(element)
        
        x, y = nav_grid.element_to_map(element.x, element.y)
        x, y = camera.map_to_screen(x, y)
        rect.top = y - (nav_grid.element_size / 2) * camera.zoom
        rect.left = x - (nav_grid.element_size / 2) * camera.zoom
        
        v = int((element.z - nav_grid.map_data.min_z) * z_mod)
        if element.special_sector is not None:
            color = nav_grid.grid_colors_special[v]
        else:
            color = nav_grid.grid_colors[v]
        
        pygame.draw.rect(surface, color, rect, 1)
    
    rect = pygame.Rect((0, 0), (nav_grid.element_size * camera.zoom, nav_grid.element_size * camera.zoom))
    element_hash = sx + (sy * (nav_grid.map_data.width / nav_grid.element_size))
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