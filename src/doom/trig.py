#!/usr/bin/env python
#coding=utf8

"""
Utility trigonometric functions.
"""

from ctypes import cdll, c_int, c_void_p, c_short, c_byte


class Rectangle(object):
    
    __slots__ = ('left', 'top', 'right', 'bottom')
    
    
    def __init__(self, left=0, top=0, right=0, bottom=0):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        
    
    def get_width(self):
        return self.right - self.left
    
    
    def get_height(self):
        return self.bottom - self.top
    
    
    def intersects(self, rect):
        return (self.left > rect.right or rect.right < self.left or rect.top > self.bottom or rect.bottom < self.top)

    
    def is_point_inside(self, x, y):
        return (x >= self.left and x <= self.right and y >= self.top and y <= self.bottom)
    
    
    def __repr__(self):
        return '{} x {}, {} x {}'.format(self.left, self.top, self.right, self.bottom)
    


doompathlib = cdll.doompath

point_in_subsector = doompathlib.point_in_subsector
point_in_subsector.argtypes = [c_void_p, c_short, c_short]
point_in_subsector.restype = c_short
                                                                                                  
box_on_line_side = doompathlib.box_on_line_side
box_on_line_side.argtypes = [c_short, c_short, c_short, c_short, c_short, c_short, c_short, c_short]
box_on_line_side.restype = c_byte


CLIP_RIGHT = 1
CLIP_LEFT = 2
CLIP_TOP = 4
CLIP_BOTTOM = 8

def box_intersects_line(rect, x1, y1, x2, y2):
    """
    Cohen-Sutherland based line-AABB clipping algorithm.

    """
    
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
        
    if rect.left > rect.right:
        rect.left, rect.right = rect.right, rect.left
    if rect.top > rect.bottom:
        rect.top, rect.bottom = rect.bottom, rect.top
        
    outcode1 = 0
    if x1 > rect.right:
        outcode1 = CLIP_RIGHT
    elif x1 < rect.left:
        outcode1 = CLIP_LEFT
    if y1 > rect.bottom:
        outcode1 |= CLIP_TOP
    elif y1 < rect.top:
        outcode1 |= CLIP_BOTTOM
    if outcode1 == 0:
        return True

    outcode2 = 0
    if x2 > rect.right:
        outcode2 = CLIP_RIGHT
    elif x2 < rect.left:
        outcode2 = CLIP_LEFT
    if y2 > rect.bottom:
        outcode2 |= CLIP_TOP
    elif y2 < rect.top:
        outcode2 |= CLIP_BOTTOM

    if outcode2 == 0:
        return True

    if (outcode1 & outcode2) > 0:
        return False

    if (outcode1 & (CLIP_RIGHT | CLIP_LEFT)):
        if (outcode1 & CLIP_RIGHT):
            interceptx = rect.right
        else:
            interceptx = rect.left
        
        ax1 = x2 - x1
        ax2 = interceptx - x1
        intercepty = y1 + ax2 * (y2 - y1) / ax1
        if intercepty <= rect.bottom and intercepty >= rect.top:
            return True

    if (outcode1 & (CLIP_TOP | CLIP_BOTTOM)):
        if (outcode1 & CLIP_TOP):
            intercepty = rect.bottom
        else:
            intercepty = rect.top
        
        ay1 = y2 - y1
        ay2 = intercepty - y1
        interceptx = x1 + ay2 * (x2 - x1) / ay1
        if interceptx <= rect.right and interceptx >= rect.left:
            return True

    return False
