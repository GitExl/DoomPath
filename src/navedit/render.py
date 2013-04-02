from doom.map.objects import Linedef
from nav.connection import Connection
from nav.element import Element
from util import rectangle
from util.rectangle import Rectangle
from util.vector import Vector2
import pygame


COLOR_LINEDEF_IMPASSIBLE = pygame.Color(223, 223, 223, 255)
COLOR_LINEDEF_2SIDED = pygame.Color(95, 95, 95, 255)
COLOR_LINEDEF_HIGHLIGHT = pygame.Color(255, 100, 0, 255)

COLOR_THING = pygame.Color(0, 255, 0, 255)

COLOR_AREA_FILL = pygame.Color(31, 31, 31, 255)
COLOR_AREA_HIGHLIGHT = pygame.Color(91, 91, 91, 255)
COLOR_AREA_PATH = pygame.Color(255, 255, 63, 255)
COLOR_AREA_VISITED = pygame.Color(127, 127, 31, 255)
COLOR_AREA_BORDER = pygame.Color(191, 95, 0, 255)

COLOR_CONNECTION_RECTANGLE = pygame.Color(15, 47, 63, 255)
COLOR_CONNECTION_TELEPORT = pygame.Color(31, 191, 95, 255)
COLOR_CONNECTION_ACTIVE = pygame.Color(255, 47, 63, 255)
CONNECTION_TELEPORT_SIZE = 6

COLOR_POINT = pygame.Color(255, 31, 0, 255)

COLOR_PATH = pygame.Color(191, 15, 15, 255)
PATH_LINE_SIZE = 12

grid_colors = None
grid_colors_special = None


def draw_connection_path(surface, camera, start, end, path):
    if start is None or end is None or path is None:
        return
    
    x1, y1 = start.x, start.y
    
    for connection in path:
        x2, y2 = connection.rect.get_center()        
        p1 = camera.map_to_screen(x1, y1)
        p2 = camera.map_to_screen(x2, y2)
        pygame.draw.line(surface, COLOR_PATH, p1, p2, int(PATH_LINE_SIZE * camera.zoom))
        
        x1, y1 = x2, y2
    
    x2, y2 = end.x, end.y
    p1 = camera.map_to_screen(x1, y1)
    p2 = camera.map_to_screen(x2, y2)
    pygame.draw.line(surface, COLOR_PATH, p1, p2, int(PATH_LINE_SIZE * camera.zoom))


def draw_point(surface, camera, pos2):
    if pos2 is None:
        return
    
    x, y = camera.map_to_screen(pos2.x, pos2.y)
    pygame.draw.circle(surface, COLOR_POINT, (int(x), int(y)), int(10 * camera.zoom))


def render_map(map_data, surface, camera, config, sector_mark):
    p1 = Vector2(camera.x, camera.y)
    p2 = Vector2(camera.x + camera.map_width, camera.y + camera.map_height)
    
    bx1, by1 = map_data.blockmap.map_to_blockmap(p1)
    bx2, by2 = map_data.blockmap.map_to_blockmap(p2)
    rect = Rectangle(bx1, by1, bx2, by2)
    
    linedefs, things = map_data.blockmap.get_region(rect)
    linedefs = set(linedefs)
    things = set(things)
    
    cx = camera.x
    cy = camera.y
    cz = camera.zoom
    linefunc = pygame.draw.line
    FLAG_IMPASSABLE = Linedef.FLAG_IMPASSIBLE
    
    color = None
    for linedef_index in linedefs:
        linedef = map_data.linedefs[linedef_index]
        
        if (linedef.flags & FLAG_IMPASSABLE) != 0:
            color = COLOR_LINEDEF_IMPASSIBLE
        else:
            color = COLOR_LINEDEF_2SIDED
            
        x1 = int((linedef.vertex1.x - cx) * cz)
        y1 = int((linedef.vertex1.y - cy) * cz)
        x2 = int((linedef.vertex2.x - cx) * cz)
        y2 = int((linedef.vertex2.y - cy) * cz)
        
        linefunc(surface, color, (x1, y1), (x2, y2), 1)
    
    if sector_mark >= 0:
        sector = map_data.sectors[sector_mark]
        color = COLOR_LINEDEF_HIGHLIGHT
        
        for linedef in sector.linedefs:
            pos1 = camera.map_to_screen(linedef.vertex1.x, linedef.vertex1.y)
            pos2 = camera.map_to_screen(linedef.vertex2.x, linedef.vertex2.y)
        
            pygame.draw.line(surface, color, pos1, pos2, 1)
                
        center_pos = map_data.get_sector_center(sector_mark)
        center_pos.x, center_pos.y = camera.map_to_screen(center_pos.x, center_pos.y)
        
        pygame.draw.circle(surface, COLOR_LINEDEF_HIGHLIGHT, (center_pos.x, center_pos.y), int(5 * camera.zoom))
        
    color = COLOR_THING
    for thing_index in things:
        thing = map_data.things[thing_index]
        thing_def = config.thing_dimensions.get(thing.doomid)
        if thing_def is None:
            continue

        pos = camera.map_to_screen(thing.x, thing.y)
        radius = int((thing_def.radius / 3) * camera.zoom)
        if radius >= 1:
            pygame.draw.circle(surface, color, pos, radius)
            
        rect = pygame.Rect(
            camera.map_to_screen(thing.x - thing_def.radius, thing.y - thing_def.radius),
            ((thing_def.radius * 2) * camera.zoom, (thing_def.radius * 2) * camera.zoom)
        )
        pygame.draw.rect(surface, color, rect, 1)
        

def render_mesh(nav_mesh, map_data, surface, camera, mouse_pos):
    selected_areas = []
    
    p1 = Vector2(camera.x, camera.y)
    p2 = Vector2(camera.x + camera.map_width, camera.y + camera.map_height)
    
    bx1, by1 = map_data.blockmap.map_to_blockmap(p1)
    bx2, by2 = map_data.blockmap.map_to_blockmap(p2)
    rect = Rectangle(bx1, by1, bx2, by2)
    
    render_areas = []
    render_connections = []
    blockmap = map_data.blockmap
    blocks_len = len(blockmap.blocks)
    
    cy = rect.top
    while cy <= rect.bottom:
        cx = rect.left
        while cx <= rect.right:
            index = cx + cy * blockmap.size.x
            if index >= 0 and index < blocks_len:
                block = blockmap.blocks[index]
                if block is not None:
                    render_areas.extend(block.areas)
            
            cx += 1
        cy += 1
    render_areas = set(render_areas)
    
    for area_index in render_areas:
        area = nav_mesh.areas[area_index]
        
        if area.path == True:
            color = COLOR_AREA_PATH
        elif area.visited == True:
            color = COLOR_AREA_VISITED
        elif area.rect.is_point_inside(mouse_pos) == True:
            color = COLOR_AREA_HIGHLIGHT
            selected_areas.append(area)
        else:
            color = COLOR_AREA_FILL
  
        x = (area.rect.left - camera.x) * camera.zoom
        y = (area.rect.top - camera.y) * camera.zoom
        width = (area.rect.right - area.rect.left) * camera.zoom
        height = (area.rect.bottom - area.rect.top) * camera.zoom
        
        x += 1
        y += 1
        width -= 2
        height -= 2
        
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
        #pygame.draw.rect(surface, COLOR_AREA_BORDER, rect, 1)
        
        render_connections.extend(area.connections)

    c_rect = rectangle.Rectangle()
    selected_connections = []
    render_connections = set(render_connections)
    
    for connection in render_connections:
        if (connection.flags & Connection.FLAG_TELEPORTER) != 0:
            c_rect.copy_from(connection.rect)
            c_rect.flip_if_reversed()
            
            x1, y1 = camera.map_to_screen(c_rect.left, c_rect.top)
            x2, y2 = camera.map_to_screen(c_rect.right, c_rect.bottom)
            
            if mouse_pos.x >= c_rect.left - CONNECTION_TELEPORT_SIZE and mouse_pos.y >= c_rect.top - CONNECTION_TELEPORT_SIZE and \
              mouse_pos.x <= c_rect.right + CONNECTION_TELEPORT_SIZE and mouse_pos.y <= c_rect.bottom + CONNECTION_TELEPORT_SIZE:
                color = COLOR_CONNECTION_ACTIVE
                selected_connections.append(connection)
                active = True
            else:
                color = COLOR_CONNECTION_TELEPORT
                active = False
                
            size = int(CONNECTION_TELEPORT_SIZE * camera.zoom)
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), size)
            
            if active == True:
                sx, sy = camera.map_to_screen(connection.rect.left + connection.rect.get_width() / 2, connection.rect.top + connection.rect.get_height() / 2)
                dx, dy = camera.map_to_screen(connection.area_b.rect.left + connection.area_b.rect.get_width() / 2, connection.area_b.rect.top + connection.area_b.rect.get_height() / 2)
                pygame.draw.line(surface, COLOR_CONNECTION_ACTIVE, (sx, sy), (dx, dy), 1)
            
        else:
            rx, ry = camera.map_to_screen(connection.rect.left, connection.rect.top)
            width, height = connection.rect.get_width() * camera.zoom, connection.rect.get_height() * camera.zoom
            
            rx += 1
            ry += 1
            width -= 2
            height -= 2
            
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
                color = COLOR_CONNECTION_ACTIVE
                selected_connections.append(connection)
            else:
                color = COLOR_CONNECTION_RECTANGLE
                
            rect = pygame.Rect(rx, ry, width, height)
            surface.fill(color, rect, special_flags=pygame.BLEND_ADD)

    return selected_areas, selected_connections


def render_grid_init(nav_grid):
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


def render_grid(nav_grid, surface, camera, mouse_pos):
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
        
        for direction in Element.DIR_RANGE:
            if element.elements[direction] is not None:
                start = (rect.left + (nav_grid.element_size * camera.zoom) / 2, rect.top + (nav_grid.element_size * camera.zoom) / 2)
                
                if direction == Element.DIR_UP:
                    end = (start[0], start[1] - (nav_grid.element_size * camera.zoom))
                elif direction == Element.DIR_RIGHT:
                    end = (start[0] + (nav_grid.element_size * camera.zoom), start[1])
                elif direction == Element.DIR_DOWN:
                    end = (start[0], start[1] + (nav_grid.element_size * camera.zoom))
                elif direction == Element.DIR_LEFT:
                    end = (start[0] - (nav_grid.element_size * camera.zoom), start[1])
                    
                pygame.draw.line(surface, color, start, end, 1)
    
    return elements