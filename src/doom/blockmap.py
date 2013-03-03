from doom.mapenum import *
import struct


BLOCKMAP_HEADER = struct.Struct('<hhHH')
BLOCKMAP_LINEDEF = struct.Struct('<H')


class Block(object):
    __slots__ = ('linedefs', 'things')
    
    def __init__(self):
        self.linedefs = []
        self.things = []


class BlockMap(object):
    
    def __init__(self):
        self.origin_x = 0
        self.origin_y = 0
        
        self.width = 0
        self.height = 0
        
        self.blocksize = 64
        self.blocks = None
    
    
    def get(self, x, y):
        if x < 0 or x >= self.width:
            return None
        if y < 0 or y >= self.height:
            return None
        
        return self.blocks[x + y * self.width]
    
    
    def get_region(self, x1, y1, x2, y2):
        linedefs = []
        things = []
        blocks_len = len(self.blocks)
        index = x1 + y1 * self.width
        
        cy = y1
        while cy <= y2:
            cx = x1
            while cx <= x2:
                index = cx + cy * self.width
                if index >= 0 and index < blocks_len:
                    block = self.blocks[index]
                    linedefs.extend(block.linedefs)
                    things.extend(block.things)
                
                cx += 1

            cy += 1
        
        return linedefs, things
    
    
    def blockmap_to_map(self, x, y):
        return x * self.blocksize + self.origin_x, y * self.blocksize + self.origin_y
    
    
    def map_to_blockmap(self, x, y):
        return int((x - self.origin_x) / self.blocksize), int((y - self.origin_y) / self.blocksize)
    
    
    def scale(self, a, b, c):
        return a * b / c;
    

    def generate_linedefs(self, map_data):
        for index, line in enumerate(map_data.linedefs):
            x1 = map_data.vertices[line[LINEDEF_VERTEX_1]][VERTEX_X]
            y1 = map_data.vertices[line[LINEDEF_VERTEX_1]][VERTEX_Y]
            x2 = map_data.vertices[line[LINEDEF_VERTEX_2]][VERTEX_X]
            y2 = map_data.vertices[line[LINEDEF_VERTEX_2]][VERTEX_Y]
            
            dx = x2 - x1
            dy = y2 - y1
            
            bx = (x1 - map_data.min_x) / self.blocksize
            by = (y1 - map_data.min_y) / self.blocksize
            bx2 = (x2 - map_data.min_x) / self.blocksize
            by2 = (y2 - map_data.min_y) / self.blocksize
    
            block = self.blocks[bx + by * self.width]
            endblock = self.blocks[bx2 + by2 * self.width]
            
            if block == endblock:
                block.linedefs.append(index)
                
            elif by == by2:
                if bx > bx2:
                    temp = bx
                    bx = bx2
                    bx2 = temp
                    
                block = self.blocks[bx + by * self.width]
                while (bx < bx2):
                    block.linedefs.append(index)
                    bx += 1
                    block = self.blocks[bx + by * self.width]
                block.linedefs.append(index)
            
            elif bx == bx2:
                if by > by2:
                    temp = by
                    by = by2
                    by2 = temp
                    
                block = self.blocks[bx + by * self.width]
                while (by < by2):
                    block.linedefs.append(index)
                    by += 1
                    block = self.blocks[bx + by * self.width]
                block.linedefs.append(index)

            else:
                if dx < 0:
                    xchange = -1
                else:
                    xchange = 1
                if dy < 0:
                    ychange = -1
                else:
                    ychange = 1
                    
                adx = abs(dx)
                ady = abs(dy)
    
                if adx == ady:
                    xb = (x1 - map_data.min_x) & (self.blocksize - 1)
                    yb = (y1 - map_data.min_y) & (self.blocksize - 1)
                    if dx < 0:
                        xb = self.blocksize - xb
                    if dy < 0:
                        yb = self.blocksize - yb
                    if xb < yb:
                        adx -= 1

                if adx >= ady:
                    if dy < 0:
                        yadd = -1
                    else:
                        yadd = self.blocksize

                    while (by != by2):
                        stop = (self.scale((by * self.blocksize) + yadd - (y1 - map_data.min_y), dx, dy) + (x1 - map_data.min_x)) / self.blocksize
                        block = self.blocks[bx + by * self.width]
                        while (bx != stop):
                            block.linedefs.append(index)
                            bx += xchange
                            block = self.blocks[bx + by * self.width]
                        
                        block.linedefs.append(index)
                        by += ychange
                        block = self.blocks[bx + by * self.width]
                    
                    while (block != endblock):
                        block.linedefs.append(index)
                        bx += xchange
                        block = self.blocks[bx + by * self.width]

                    block.linedefs.append(index)
                
                else:
                    if dx < 0:
                        xadd = -1
                    else:
                        xadd = self.blocksize

                    while(bx != bx2):
                        stop = (self.scale((bx * self.blocksize) + xadd - (x1 - map_data.min_x), dy, dx) + (y1 - map_data.min_y)) / self.blocksize
                        block = self.blocks[bx + by * self.width]
                        while (by != stop):
                            block.linedefs.append(index)
                            by += ychange
                            block = self.blocks[bx + by * self.width]

                        block.linedefs.append(index)
                        bx += xchange;
                        block = self.blocks[bx + by * self.width]
                        
                    while (block != endblock):
                        block.linedefs.append(index)
                        by += ychange
                        block = self.blocks[bx + by * self.width]
                        
                    block.linedefs.append(index)
                    
                    
    def generate_things(self, map_data):
        for index, thing in enumerate(map_data.things):
            thing_type = thing[map_data.THING_TYPE]
            thing_def = map_data.config.thing_dimensions.get(thing_type)
            
            if map_data.config.bridge_custom_type is not None and thing_type == map_data.config.bridge_custom_type:
                radius = thing[THING_HEXEN_ARG0]
            else:
                if thing_def is None:
                    continue                
                radius = thing_def.radius 

            left = thing[map_data.THING_X] - radius
            top = thing[map_data.THING_Y] - radius
            right = thing[map_data.THING_X] + radius
            bottom = thing[map_data.THING_Y] + radius
            
            left, top = self.map_to_blockmap(left, top)
            right, bottom = self.map_to_blockmap(right, bottom)
            
            left = max(0, left)
            top = max(0, top)
            right = min(self.width, right)
            bottom = min(self.height, bottom)
            
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    block = self.blocks[x + y * self.width]
                    block.things.append(index)
        
    
    def generate(self, map_data):
        self.origin_x = map_data.min_x
        self.origin_y = map_data.min_y
        
        self.width = int(map_data.width / self.blocksize) + 1
        self.height = int(map_data.height / self.blocksize) + 1
        
        self.blocks = [None] * (self.width * self.height)
        for y in range(0, self.height):
            for x in range(0, self.width):
                self.blocks[x + y * self.width] = Block()

        self.generate_linedefs(map_data)
        self.generate_things(map_data)
    
        
    def read(self, data):
        header = BLOCKMAP_HEADER.unpack_from(data)
        self.origin_x = header[0]
        self.origin_y = header[1]
        self.width = header[2]
        self.height = header[3]
        self.blocksize = 128
        
        block_count = self.width * self.height
        offset_struct = struct.Struct('<' + ('H' * block_count))
        offsets = offset_struct.unpack_from(data[8:])
        
        self.blocks = []
        linedef = 0
        for offset in offsets:
            block = Block()
            offset *= 2

            while True:
                offset += 2
                linedef = BLOCKMAP_LINEDEF.unpack_from(data[offset:])[0]
                if linedef == 0xffff:
                    break
                block.linedefs.append(linedef)
            
            self.blocks.append(block)