from doom import wad, mapdata, maprender
from nav import navgrid
from nav.navmesh import NavMesh
import cProfile
import camera
import config
import pygame


COLOR_BACKGROUND = pygame.Color(0, 31, 63, 255)
COLOR_COLLISION_BOX = pygame.Color(127, 127, 127, 255)
COLOR_COLLISION_BOX_COLLIDE = pygame.Color(255, 255, 0, 255)
COLOR_TEXT = pygame.Color(255, 255, 255, 255)

MODE_INSPECT = 0
MODE_RENDER = 1


class Mouse(object):
    
    def __init__(self):
        self.buttons = [False] * 6
        
        self.x = 0
        self.y = 0
        
        self.map_x = 0
        self.map_y = 0


class Loop(object):
    
    def __init__(self):
        self.screen = None
        self.camera = None
        self.map_data = None
        self.config = None
        self.nav_grid = None
        self.nav_mesh = None
        
        pygame.font.init()
        self.font = pygame.font.Font('04b_03__.ttf', 8)
        
        self.iteration = 0
        self.mode = MODE_INSPECT
        self.generate_grid = True
        
        self.mouse = Mouse()
        self.keys = [False] * 512
                
        
    def loop_init(self):
        print 'Loading map...'
        wad_file = wad.WADReader('test/doom1.wad')
        self.map_data = mapdata.MapData(wad_file, 'E1M2')
        
        # Load dataset for map.
        if self.map_data.is_hexen:
            dataset = 'zdoom'
        else:
            dataset = 'doom'
        print 'Loading {} configuration...'.format(dataset)
        self.config = config.Config('doompath.json', dataset)
        
        # Build map structures.
        print 'Map setup...'
        self.map_data.setup(self.config)
        
        # Create empty nav grid.
        print 'Creating navigation grid...'
        self.nav_grid = navgrid.NavGrid(self.map_data, self.config)
        
        # Create a list of things that players spawn at.
        print 'Finding starting elements...'
        start_things = []
        for thing_type in self.config.start_thing_types:
            start_things.extend(self.map_data.get_thing_list(thing_type))
        
        # Add the spawn things as initial elements to the nav grid.
        for thing in start_things:
            x = thing[self.map_data.THING_X]
            y = thing[self.map_data.THING_Y]
            z = self.map_data.get_floor_z(x, y)
            
            collision, _ = self.nav_grid.walker.check_position(x, y, z, self.config.player_radius, self.config.player_height)
            if collision == True:
                print 'Thing at {},{} has no room to spawn, ignoring.'.format(x, y)
                continue
            
            self.nav_grid.add_walkable_element(x, y, z)
        print 'Added {} starting elements.'.format(len(start_things))
                
        print 'Detecting walkable space...'
        if self.generate_grid == True:
            self.nav_grid.create_walkable_elements(self.config)
            self.nav_grid.write('test/nav.bin')
        else:
            self.nav_grid.read('test/nav.bin')
            
        print 'Generating navigation mesh...'
        self.nav_mesh = NavMesh()
        if self.mode == MODE_INSPECT:
            self.nav_mesh.create_from_grid(self.nav_grid)

        print 'Creating display...'
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        self.camera = camera.Camera(0, 0, 1280, 720, 1.0)
        self.center_map()
        
        
    def loop_start(self):
        update_display = True
        
        while True:
            if self.mode == MODE_RENDER: 
                #self.nav_grid.create_walkable_elements(self.config, 50)
                #if len(self.nav_grid.element_tasks) == 0:
                    #break
                    
                if self.nav_mesh.create_from_grid(self.nav_grid, 1) == True:
                    break
                self.update_display()
                
                #pygame.image.save(self.screen, 'images/screen_{:06d}.png'.format(self.iteration))
                self.iteration += 1
            
            elif self.mode == MODE_INSPECT:
                
                event = pygame.event.wait()
                
                if event.type == pygame.QUIT or self.keys[pygame.K_ESCAPE] == True:
                    break
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.mouse.buttons[event.button] = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse.buttons[event.button] = False
                    
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse.x = event.pos[0]
                    self.mouse.y = event.pos[1]
                    
                    self.mouse.map_x, self.mouse.map_y = self.camera.screen_to_map(event.pos[0], event.pos[1])
                    self.mouse.map_x = int(self.mouse.map_x)
                    self.mouse.map_y = int(self.mouse.map_y)
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


    def update_display(self):
        sector = self.map_data.get_sector(self.mouse.map_x, self.mouse.map_y)
        
        self.screen.fill(COLOR_BACKGROUND)
        
        #maprender.render_blockmap(self.map_data, self.screen, self.camera, self.mouse.map_x, self.mouse.map_y)
        #self.nav_grid.render_elements(self.screen, self.camera, self.mouse.map_x, self.mouse.map_y)
        maprender.render_linedefs(self.map_data, self.screen, self.camera, self.mouse.map_x, self.mouse.map_y, sector)
        maprender.render_things(self.map_data, self.screen, self.camera, self.mouse.map_x, self.mouse.map_y)
        self.nav_mesh.render(self.screen, self.camera)
        self.render_collision_box()
        
        pygame.display.flip()
    
    
    def render_collision_box(self):
        x = self.mouse.map_x
        y = self.mouse.map_y
        z = self.map_data.get_floor_z(self.mouse.map_x, self.mouse.map_y)
        radius = self.config.player_radius
        height = self.config.player_height
        collision, state = self.nav_grid.walker.check_position(x, y, z, radius, height)
        
        if collision == False:
            color = COLOR_COLLISION_BOX
        else:
            color = COLOR_COLLISION_BOX_COLLIDE

        x = self.mouse.map_x - self.config.player_radius
        y = self.mouse.map_y - self.config.player_radius
        x, y = self.camera.map_to_screen(x, y)
        size = (self.config.player_radius * 2) * self.camera.zoom
        
        rect = pygame.Rect((x, y), (size, size))
        pygame.draw.rect(self.screen, color, rect, 1)
        
        # Debug text.
        text = '{}, {}'.format(self.mouse.map_x, self.mouse.map_y)
        self.render_text(text, 4, 4)
        text = 'floor z: {}, ceil z: {}, block line: {}, block thing: {}, special sector {}'.format(round(state.floorz, 2), round(state.ceilz, 2), state.blockline, state.blockthing, state.special_sector)
        self.render_text(text, 4, 20)
        
        x, y = self.nav_grid.map_to_element(self.mouse.map_x, self.mouse.map_y)
        elements = self.nav_grid.get_element_list(x, y)
        if elements is not None:
            x = 4
            y = 46
            for element in elements.itervalues():
                self.render_text(str(element), x, y)
                y += 18
        
        
    def render_text(self, text, x, y):
        surf = self.font.render(text, 0, COLOR_TEXT)
        surf = pygame.transform.scale(surf, (surf.get_width() * 2, surf.get_height() * 2))
        self.screen.blit(surf, (x, y))
        
        
    def center_map(self):
        map_size = max(self.map_data.width, self.map_data.height)
        display_size = min(1280, 720)
        zoom = float(display_size) / float(map_size) - 0.005

        x = self.map_data.min_x + self.map_data.width / 2
        y = self.map_data.min_y + self.map_data.height / 2
 
        self.camera.set_zoom(zoom)
        self.camera.set_center(x, y)


if __name__ == '__main__':   
    loop = Loop()
    cProfile.run('loop.loop_init()', sort=1)
    #loop.loop_init()
    loop.loop_start()