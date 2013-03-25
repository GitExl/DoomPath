#!/usr/bin/env python
#coding=utf8

from util.vector import Vector2


class Rectangle(object):   
    __slots__ = ('p1', 'p2', 'left', 'top', 'right', 'bottom')
    
    def __init__(self, left=0, top=0, right=0, bottom=0):
        self.p1 = Vector2()
        self.p2 = Vector2()
        
        self.p1.set(left, top)
        self.p2.set(right, bottom)
        
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        
    
    def get_width(self):
        return self.right - self.left
    
    
    def get_height(self):
        return self.bottom - self.top
    
    
    def intersects_with(self, rect):
        return not (rect.left > self.right or rect.right < self.left or rect.top > self.bottom or rect.bottom < self.top)

    
    def is_point_inside(self, pos):
        return (pos.x >= self.left and pos.x <= self.right and pos.y >= self.top and pos.y <= self.bottom)


    def flip_if_reversed(self):
        if self.left > self.right:
            self.left, self.right = self.right, self.left
        
        if self.top > self.bottom:
            self.top, self.bottom = self.bottom, self.top
            
        self.p1.set(self.left, self.top)
        self.p2.set(self.right, self.bottom)

    
    def set(self, left, top, right, bottom):
        self.p1.set(left, top)
        self.p2.set(right, bottom)
        
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
    
    
    def set_size(self, left, top, width, height):
        self.set(left, top, left + width, top + height)
        
        
    def copy_from(self, other):
        self.p1.set(other.left, other.top)
        self.p2.set(other.right, other.bottom)
        
        self.left = other.left
        self.top = other.top
        self.right = other.right
        self.bottom = other.bottom
    

    def intersects_with_line(self, x1, y1, x2, y2):
        """
        Cohen-Sutherland based line-AABB clipping algorithm.
        """
        
        CLIP_RIGHT = 1
        CLIP_LEFT = 2
        CLIP_TOP = 4
        CLIP_BOTTOM = 8
    
        outcode1 = 0
        if x1 > self.right:
            outcode1 = CLIP_RIGHT
        elif x1 < self.left:
            outcode1 = CLIP_LEFT
        if y1 > self.bottom:
            outcode1 |= CLIP_TOP
        elif y1 < self.top:
            outcode1 |= CLIP_BOTTOM
        if outcode1 == 0:
            return True
    
        outcode2 = 0
        if x2 > self.right:
            outcode2 = CLIP_RIGHT
        elif x2 < self.left:
            outcode2 = CLIP_LEFT
        if y2 > self.bottom:
            outcode2 |= CLIP_TOP
        elif y2 < self.top:
            outcode2 |= CLIP_BOTTOM
    
        if outcode2 == 0:
            return True
    
        if (outcode1 & outcode2) > 0:
            return False
    
        if (outcode1 & (CLIP_RIGHT | CLIP_LEFT)):
            if (outcode1 & CLIP_RIGHT):
                interceptx = self.right
            else:
                interceptx = self.left
            
            ax1 = x2 - x1
            ax2 = interceptx - x1
            intercepty = y1 + ax2 * (y2 - y1) / ax1
            if intercepty <= self.bottom and intercepty >= self.top:
                return True
    
        if (outcode1 & (CLIP_TOP | CLIP_BOTTOM)):
            if (outcode1 & CLIP_TOP):
                intercepty = self.bottom
            else:
                intercepty = self.top
            
            ay1 = y2 - y1
            ay2 = intercepty - y1
            interceptx = x1 + ay2 * (x2 - x1) / ay1
            if interceptx <= self.right and interceptx >= self.left:
                return True
    
        return False
        
        
    def __eq__(self, other):
        return self.left == other.left and self.top == other.top and self.right == other.right and self.bottom == other.bottom
    
    
    def _ne__(self, other):
        return not self.__eq__(other)
    
    
    def __repr__(self):
        return '{}, {}'.format(self.p1, self.p2)