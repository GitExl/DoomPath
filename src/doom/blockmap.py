#!/usr/bin/env python
#coding=utf8

from doom.mapenum import *
import struct


BLOCKMAP_HEADER = struct.Struct('<hhHH')
BLOCKMAP_LINEDEF = struct.Struct('<H')


class Block(object):
    """
    A block of map data used by the blockmap.
    """
    
    __slots__ = ('linedefs', 'things', 'areas')
    
    def __init__(self):
        self.linedefs = []
        self.things = []
        self.areas = []


class BlockMap(object):
    """
    Handles Doom map blockmap data.
    
    A blockmap that is read from a Doom lump always contains blocks 128 units in size.
    When generating a blockmap, a more optimal block size can be configured.
    """
    
    def __init__(self):
        # Origin point of the top left blockmap block.
        self.origin_x = 0
        self.origin_y = 0
        
        # Size of this blockmap, in blocks.
        self.width = 0
        self.height = 0
        
        # Size of a block, in map units.
        self.blocksize = 64
        
        # List of Block objects.
        self.blocks = None
    
    
    def get(self, x, y):
        """
        Returns a single Block object from this blockmap.
        
        @param x: the X coordinate of the block to return.
        @param y: the Y coordinate of the block to return.
        
        @return: a BLock object or None if the block falls outside the blockmap coordinate range.
        """
          
        if x < 0 or x >= self.width:
            return None
        if y < 0 or y >= self.height:
            return None
        
        return self.blocks[x + y * self.width]
    
    
    def get_region(self, x1, y1, x2, y2):
        """
        Returns a list of blocks that fall inside a blockmap region.
        
        @param x1: X coordinate of the region start.
        @param y1: Y coordinate of the region start.
        @param x2: X coordinate of the region end.
        @param y2: Y coordinate of the region end.
        
        @return: a list of Block objects from x1, y1 up to and including x2, y2.
        """
        
        linedefs = []
        things = []
        blocks_len = len(self.blocks)
        
        cy = y1
        while cy <= y2:
            cx = x1
            while cx <= x2:
                index = cx + cy * self.width
                if index >= 0 and index < blocks_len:
                    block = self.blocks[index]
                    if block is not None:
                        linedefs.extend(block.linedefs)
                        things.extend(block.things)
                
                cx += 1

            cy += 1
        
        return linedefs, things
    
    
    def blockmap_to_map(self, x, y):
        """
        Returns map unit coordinates for the blockmap block at coordinate x, y.
        """
        
        return x * self.blocksize + self.origin_x, y * self.blocksize + self.origin_y
    
    
    def map_to_blockmap(self, x, y):
        """
        Returns blockmap coordinates for the map units x, y.
        """
        
        return int((x - self.origin_x) / self.blocksize), int((y - self.origin_y) / self.blocksize)
    

    def generate_linedefs(self, map_data):
        """
        Places all linedefs in a map data object onto the blockmap.
        
        Adapted from ZDBSP's FBlockmapBuilder::BuildBlockmap.
        
        @param map_data: the map data object to use the linedefs from.
        """
        
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
            
            # The linedef is in only one block.
            if block == endblock:
                block.linedefs.append(index)
                
            # The linedef is horizontal, place it in all blocks it passes through.
            elif by == by2:
                if bx > bx2:
                    bx, bx2 = bx2, bx
                    
                block = self.blocks[bx + by * self.width]
                while (bx < bx2):
                    block.linedefs.append(index)
                    bx += 1
                    block = self.blocks[bx + by * self.width]
                block.linedefs.append(index)
            
            # The linedef is vertical, place it in all blocks it passes through.
            elif bx == bx2:
                if by > by2:
                    by, by2 = by2, by
                    
                block = self.blocks[bx + by * self.width]
                while (by < by2):
                    block.linedefs.append(index)
                    by += 1
                    block = self.blocks[bx + by * self.width]
                block.linedefs.append(index)

            # Draw a Bresenham style line through all the blocks that this line passes through.
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

                # Line is mostly horizontal.
                if adx >= ady:
                    if dy < 0:
                        yadd = -1
                    else:
                        yadd = self.blocksize

                    while (by != by2):
                        a, b, c = (by * self.blocksize) + yadd - (y1 - map_data.min_y), dx, dy
                        scaled = a * b / c
                        stop = (scaled + (x1 - map_data.min_x)) / self.blocksize
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
                
                # Line is mostly vertical.
                else:
                    if dx < 0:
                        xadd = -1
                    else:
                        xadd = self.blocksize

                    while(bx != bx2):
                        a, b, c = (bx * self.blocksize) + xadd - (x1 - map_data.min_x), dy, dx
                        scaled = a * b / c
                        stop = (scaled + (y1 - map_data.min_y)) / self.blocksize
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
        """
        Places all things in the blockmap blocks that they occupy.
        
        @param map_data: the map data object to use the things from.
        """ 
        
        for index, thing in enumerate(map_data.things):
            thing_type = thing[map_data.THING_TYPE]
            thing_def = map_data.config.thing_dimensions.get(thing_type)
            if thing_def is None:
                    continue                
                
            # Get bridge thing radius from Hexen parameters.
            if map_data.config.bridge_custom_type is not None and thing_type == map_data.config.bridge_custom_type:
                radius = thing[THING_HEXEN_ARG0]
            
            # Use configuration radius
            else:
                radius = thing_def.radius 

            # Determine thing bounding box.
            left = thing[map_data.THING_X] - radius
            top = thing[map_data.THING_Y] - radius
            right = thing[map_data.THING_X] + radius
            bottom = thing[map_data.THING_Y] + radius
            
            # Convert map bounding box to blockmap bounding box.
            left, top = self.map_to_blockmap(left, top)
            right, bottom = self.map_to_blockmap(right, bottom)
            
            # Clip bounding box to blockmap dimensions.
            left = max(0, left)
            top = max(0, top)
            right = min(self.width, right)
            bottom = min(self.height, bottom)
            
            # Fill a box over the blockmap blocks that this thing occupies.
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    block = self.blocks[x + y * self.width]
                    block.things.append(index)
                    
                    
    def generate_areas(self, nav_mesh):
        """
        Places all mesh areas in the blockmap blocks they occupy.
        
        @param nav_mesh: the mesh object to use the areas from.
        """
        
        for index, area in enumerate(nav_mesh.areas):
            # Convert map bounding box to blockmap bounding box.
            left, top = self.map_to_blockmap(area.x1, area.y1)
            right, bottom = self.map_to_blockmap(area.x2, area.y2)
            
            # Clip bounding box to blockmap dimensions.
            left = max(0, left)
            top = max(0, top)
            right = min(self.width, right)
            bottom = min(self.height, bottom)
            
            # Fill a box over the blockmap blocks that this thing occupies.
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    block = self.blocks[x + y * self.width]
                    block.areas.append(index)
        
    
    def generate(self, map_data):
        """
        Generate a new blockmap from amap data object.
        
        @param map_data: the map data object to generate the blockmap for.
        """
        
        self.origin_x = map_data.min_x
        self.origin_y = map_data.min_y
        
        self.width = int(map_data.width / self.blocksize) + 1
        self.height = int(map_data.height / self.blocksize) + 1
        
        # Create a new blockmap grid of Block objects.
        self.blocks = [None] * (self.width * self.height)
        for y in range(0, self.height):
            for x in range(0, self.width):
                self.blocks[x + y * self.width] = Block()

        # Generate Block contents.
        self.generate_linedefs(map_data)
        self.generate_things(map_data)
    
    
    def prune_empty(self):
        """
        Sets all blocks in this blockmap that do not have any entries to None.
        """
        
        for index, block in enumerate(self.blocks):
            if len(block.linedefs) == 0 and len(block.things) == 0 and len(block.areas) == 0:
                self.blocks[index] = None
    
        
    def read(self, data):
        """
        Reads a blockmap from Doom blockmap lump data.
        
        @param data: the data of the lump to read.
        """
        
        header = BLOCKMAP_HEADER.unpack_from(data)
        self.origin_x = header[0]
        self.origin_y = header[1]
        self.width = header[2]
        self.height = header[3]
        self.blocksize = 128
        
        # Read offsets.
        block_count = self.width * self.height
        offset_struct = struct.Struct('<' + ('H' * block_count))
        offsets = offset_struct.unpack_from(data[8:])
        
        self.blocks = []
        linedef = 0
        for offset in offsets:
            block = Block()
            offset *= 2

            # Unpack linedef indices from the current block.
            while 1:
                offset += 2
                linedef = BLOCKMAP_LINEDEF.unpack_from(data[offset:])[0]
                if linedef == 0xffff:
                    break
                block.linedefs.append(linedef)
            
            self.blocks.append(block)