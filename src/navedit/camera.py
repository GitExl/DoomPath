class Camera(object):
    
    def __init__(self, x, y, width, height, zoom):
        self.x = x
        self.y = y
        
        self.zoom = zoom
        
        self.screen_width = width
        self.screen_height = height
        
        self.map_width = width / zoom
        self.map_height = height / zoom
        
        
    def move_relative(self, x, y):
        self.x -= x
        self.y -= y
    
    
    def set_center(self, x, y):
        self.x = x - self.map_width / 2
        self.y = y - self.map_height / 2
        
        
    def set_zoom(self, zoom):
        if zoom < 0.1:
            zoom = 0.1
        if zoom > 4:
            zoom = 4
            
        self.zoom = zoom
        
        self.map_width = self.screen_width / self.zoom
        self.map_height = self.screen_height / self.zoom
        
        
    def screen_to_map(self, x, y):
        return int((x / self.zoom) + self.x), int((y / self.zoom) + self.y)
    
    
    def map_to_screen(self, x, y):
        return int((x - self.x) * self.zoom), int((y - self.y) * self.zoom)