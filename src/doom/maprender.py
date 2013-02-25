from doom.mapenum import *
import pygame


COLOR_LINEDEF_IMPASSIBLE = pygame.Color(223, 223, 223, 255)
COLOR_LINEDEF_2SIDED = pygame.Color(95, 95, 95, 255)
COLOR_LINEDEF_HIGHLIGHT = pygame.Color(255, 100, 0, 255)
COLOR_BLOCKMAP = pygame.Color(0, 45, 89, 255)
COLOR_BLOCKMAP_HIGHLIGHT = pygame.Color(0, 96, 191, 255)
COLOR_THING = pygame.Color(0, 255, 0, 255)


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
        
        pygame.draw.circle(surface, COLOR_LINEDEF_HIGHLIGHT, (int(center_x), int(center_y)), int(10 * camera.zoom))