from ctypes import cdll, c_int, c_void_p, c_short, c_byte


doompathlib = cdll.doompath

box_intersects_line = doompathlib.box_intersects_line
box_intersects_line.argtypes = [c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int]
box_intersects_line.restype = c_int

point_in_subsector = doompathlib.point_in_subsector
point_in_subsector.argtypes = [c_void_p, c_short, c_short]
point_in_subsector.restype = c_short
                                                                                                  
box_on_line_side = doompathlib.box_on_line_side
box_on_line_side.argtypes = [c_short, c_short, c_short, c_short, c_short, c_short, c_short, c_short]
box_on_line_side.restype = c_byte


def box_intersects_line(left, top, right, bottom, x1, y1, x2, y2):
    if x1 < left and x2 >= left:
        iy = y1 + (y2 - y1) * (left - x1) / (x2 - x1)
        if iy >= bottom and iy <= top:
            return True
    elif x1 > right and x2 <= right:
        iy = y1 + (y2 - y1) * (right - x1) / (x2 - x1)
        if iy >= bottom and iy <= top:
            return True
    
    if y1 < bottom and y2 >= bottom:
        ix = x1 + (x2 - x1) * (bottom - y1) / (y2 - y1)
        if ix >= left and ix <= right:
            return True
    elif y1 > top and y2 <= top:
        ix = x1 + (x2 - x1) * (top - y1) / (y2 - y1)
        if ix >= left and ix <= right:
            return True
    
    return False


def box_intersects_box(left1, top1, right1, bottom1, left2, top2, right2, bottom2):
    return not (left2 > right1 or right2 < left1 or top2 > bottom1 or bottom2 < top1)