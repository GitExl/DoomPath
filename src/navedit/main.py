from doom import wad
from doom.map.data import MapData
from nav.config import Config
from nav.mesh import Mesh
from navedit import pathfind
from util.vector import Vector2, Vector3
import cProfile
import camera
import pygame
import random
import render
import sys


COLOR_BACKGROUND = pygame.Color(0, 31, 63, 255)
COLOR_COLLISION_BOX = pygame.Color(127, 127, 127, 255)
COLOR_COLLISION_BOX_COLLIDE = pygame.Color(255, 255, 0, 255)
COLOR_TEXT = pygame.Color(255, 255, 255, 255)

MODE_INSPECT = 0
MODE_RENDER = 1


class Mouse(object):
    
    def __init__(self):
        self.buttons = [False] * 6
        
        self.pos = Vector2()
        self.map_pos = Vector2()


class Loop(object):
    
    def __init__(self):
        self.screen = None
        self.camera = None
        self.map_data = None
        self.config = None
        self.nav_grid = None
        self.nav_mesh = None
        
        self.pathfinder = None
        self.path = None
        self.point_start = None
        self.point_end = None
        
        pygame.font.init()
        self.font = pygame.font.Font('04b_03__.ttf', 8)
        
        self.mouse = Mouse()
        self.keys = [False] * 512
                
        
    def loop_init(self):
        wad_file = 'test/doom.wad'
        map_lump = 'E1M3'
        mesh_file = 'test/doom_e1m3.dpm'
        configuration = None
        
        print 'Loading map...'
        wad_file = wad.WADReader(wad_file)            
        self.map_data = MapData(wad_file, map_lump)
        
        # Load dataset for map.
        if configuration == None:
            if self.map_data.is_hexen:
                configuration = 'zdoom'
            else:
                configuration = 'doom'
        print 'Loading {} configuration...'.format(configuration)
        self.config = Config('doompath.json', configuration)
        
        print 'Map setup...'
        self.map_data.setup(self.config)
        
        #print 'Creating navigation grid...'
        #self.nav_grid = Grid()
        
        print 'Reading navigation mesh...'
        self.nav_mesh = Mesh()
        self.nav_mesh.read(mesh_file, self.map_data)
        
        self.map_data.blockmap.generate_areas(self.nav_mesh)
        self.map_data.blockmap.prune_empty()

        print 'Creating display...'
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        self.camera = camera.Camera(0, 0, 1280, 720, 1.0)
        self.center_map()
        
        #render.render_grid_init(self.nav_grid)
        
        self.pathfinder = pathfind.Pathfinder(self.nav_mesh)
        
        return True
    
    
    def benchmark_pathfinder(self):
        random.seed(1751987)
        start = Vector3()
        end = Vector3()
        for _ in range(5000):
            start.x = random.randint(self.map_data.min.x, self.map_data.max.x)
            start.y = random.randint(self.map_data.min.y, self.map_data.max.y)
            start.z = self.map_data.get_floor_z(start.x, start.y)
            
            end.x = random.randint(self.map_data.min.x, self.map_data.max.x)
            end.y = random.randint(self.map_data.min.y, self.map_data.max.y)
            end.z = self.map_data.get_floor_z(end.x, end.y)
            
            path = self.pathfinder.find(start, end)
            if path is not None and self.pathfinder.nodes_visited > 0:
                efficiency = round((len(path) / float(self.pathfinder.nodes_visited)) * 100, 1)
                print 'Visited {} areas, path is {} areas. {} distance. {}% efficiency.'.format(self.pathfinder.nodes_visited, len(path), self.pathfinder.distance, efficiency)
        
        
    def loop_start(self):
        update_display = True
        
        while True:
            event = pygame.event.wait()
            
            if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE] == True:
                break
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse.buttons[event.button] = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse.buttons[event.button] = False
                
                if event.button == 1:
                    self.place_path_point(self.mouse.map_pos.x, self.mouse.map_pos.y)
                    update_display = True
                
            elif event.type == pygame.MOUSEMOTION:
                self.mouse.pos.x = event.pos[0]
                self.mouse.pos.y = event.pos[1]
                
                self.mouse.map_pos.x, self.mouse.map_pos.y = self.camera.screen_to_map(event.pos[0], event.pos[1])
                self.mouse.map_pos.x = int(self.mouse.map_pos.x)
                self.mouse.map_pos.y = int(self.mouse.map_pos.y)
                update_display = True
                
                if self.mouse.buttons[3] == True:
                    self.camera.move_relative(event.rel[0] / self.camera.zoom, event.rel[1] / self.camera.zoom)
                    update_display = True
                
            elif event.type == pygame.KEYDOWN:
                self.keys[event.key] = True
            elif event.type == pygame.KEYUP:
                self.keys[event.key] = False
                
            if self.mouse.buttons[4] == True:
                self.camera.set_zoom(self.camera.zoom / 0.92)
                #self.camera.set_center(self.mouse.map_x, self.mouse.map_y)
                update_display = True
            elif self.mouse.buttons[5] == True:
                self.camera.set_zoom(self.camera.zoom * 0.92)
                #self.camera.set_center(self.mouse.map_x, self.mouse.map_y)
                update_display = True
            
            if update_display == True:
                self.update_display()
                update_display = False


    def place_path_point(self, x, y):
        z = self.map_data.get_floor_z(x, y)
        
        if self.point_start is None or self.point_end is not None:
            self.point_start = Vector3(x, y, z)
            self.point_end = None
            
        elif self.point_end is None:
            self.point_end = Vector3(x, y, z)
            
            for area in self.nav_mesh.areas:
                area.path = False
                area.visited = False
            
            self.path = self.pathfinder.find(self.point_start, self.point_end)            
            if self.path is None:
                print 'No path could be found.'
            else:
                efficiency = round((len(self.path) / float(self.pathfinder.nodes_visited)) * 100, 1)
                print 'Visited {} areas, path is {} areas. {} distance. {}% efficiency.'.format(self.pathfinder.nodes_visited, len(self.path), self.pathfinder.distance, efficiency)
                    

    def update_display(self):
        sector = -1
        state = None
        areas = None
        connections = None
        elements = None
        
        #sector = self.map_data.get_sector(self.mouse.map_pos.x, self.mouse.map_pos.y)
        
        self.screen.fill(COLOR_BACKGROUND)
        
        #elements = render.render_nav(self.nav_grid, self.screen, self.camera, self.mouse.map_pos)
        render.render_map(self.map_data, self.screen, self.camera, self.config, sector)
        areas, connections = render.render_mesh(self.nav_mesh, self.map_data, self.screen, self.camera, self.mouse.map_pos)
        #state = self.render_collision_box()
        self.render_debug_text(connections, state, elements, areas)
        
        render.draw_connection_path(self.screen, self.camera, self.point_start, self.point_end, self.path)
        render.draw_point(self.screen, self.camera, self.point_start)
        render.draw_point(self.screen, self.camera, self.point_end)
        
        pygame.display.flip()       
    
    
    def render_collision_box(self):
        x = self.mouse.map_pos.x
        y = self.mouse.map_pos.y
        z = self.map_data.get_floor_z(self.mouse.map_pos.x, self.mouse.map_pos.y)
        pos = Vector3(x, y, z)
        
        radius = self.config.player_radius
        height = self.config.player_height
        collision, state = self.nav_grid.collider.check_position(pos, radius, height)
        
        if collision == False:
            color = COLOR_COLLISION_BOX
        else:
            color = COLOR_COLLISION_BOX_COLLIDE

        x = self.mouse.map_pos.x - self.config.player_radius
        y = self.mouse.map_pos.y - self.config.player_radius
        x, y = self.camera.map_to_screen(x, y)
        size = (self.config.player_radius * 2) * self.camera.zoom
        
        rect = pygame.Rect((x, y), (size, size))
        pygame.draw.rect(self.screen, color, rect, 1)
        
        return state
        

    def render_debug_text(self, connections, state, elements, areas):
        text = '{}, {}'.format(self.mouse.map_pos.x, self.mouse.map_pos.y)
        self.render_text(text, 4, 4)
        
        x = 4
        y = 46
        
        if state is not None:
            text = 'floor z: {}, ceil z: {}, block line: {}, block thing: {}, special sector {}'.format(round(state.floorz, 2), round(state.ceilz, 2), state.blockline, state.blockthing, state.special_sector)
            self.render_text(text, 4, 20)
            y += 18
        
        if elements is not None:
            for element in elements:
                self.render_text(str(element), x, y)
                y += 18
        
        if connections is not None:
            for connection in connections:
                self.render_text(str(connection), x, y)
                y += 18
                
        if areas is not None:
            for area in areas:
                self.render_text(str(area), x, y)
                y += 18
        
        
    def render_text(self, text, x, y):
        surf = self.font.render(text, 0, COLOR_TEXT)
        surf = pygame.transform.scale(surf, (surf.get_width() * 2, surf.get_height() * 2))
        self.screen.blit(surf, (x, y))
        
        
    def center_map(self):
        map_size = max(self.map_data.size.x, self.map_data.size.y)
        display_size = min(1280, 720)
        zoom = float(display_size) / float(map_size) - 0.005

        x = self.map_data.min.x + self.map_data.size.x / 2
        y = self.map_data.min.y + self.map_data.size.y / 2
 
        self.camera.set_zoom(zoom)
        self.camera.set_center(x, y)


if __name__ == '__main__':   
    loop = Loop()
    if loop.loop_init() == False:
        sys.exit()
    #cProfile.run('loop.benchmark_pathfinder()', sort=1)
    loop.loop_start()