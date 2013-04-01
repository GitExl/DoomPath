from nav.area import Area
from nav.connection import Connection
from nav.element import Element
import heapq
import math


def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))


class PathNode(object):

    __slots__ = (
        'parent',
        'area',
        
        'move_cost',
        'heuristic_cost',
        'total_cost'
    )
    
    
    def __init__(self, area):
        self.area = area
        self.parent = None
        
        self.move_cost = 0
        self.heuristic_cost = 0
        self.total_cost = 0
        
        

class Pathfinder(object):
    
    def __init__(self, nav_mesh):
        self.nav_mesh = nav_mesh
        
        self.nodes = {}
        
        for area in nav_mesh.areas:
            self.nodes[area] = PathNode(area)
        
        
    def find(self, start, end):
        visited = 0
        
        for area in self.nav_mesh.areas:
            area.path = False
            area.visited = False
        
        open_list = set()
        closed_list = set()
        
        area_start = self.nav_mesh.get_area_at(start, start.z)
        if area_start is None:
            print 'Invalid start.'
            return
        
        area_end = self.nav_mesh.get_area_at(end, end.z)
        if area_end is None:
            print 'Invalid end.'
            return

        open_list.add(self.nodes[area_start])
        while len(open_list) > 0:
            lowest_cost = 0xffffffff
            for node in open_list:
                if node.total_cost < lowest_cost:
                    node_current = node
                    lowest_cost = node.total_cost
            
            if node_current.area == area_end:
                path_list = self.build_path(node_current, area_start)
                
                efficiency = round(len(path_list) / float(visited), 2)
                
                print 'Visited {} areas, path is {} areas. {}% efficiency.'.format(visited, len(path_list), efficiency) 
                return path_list
            
            open_list.remove(node_current)
            closed_list.add(node_current)
            
            for connection in node_current.area.connections:
                area_from = node_current.area
                
                if area_from == connection.area_a and (connection.flags & Connection.FLAG_AB):
                    area_to = connection.area_b
                elif area_from == connection.area_b and (connection.flags & Connection.FLAG_BA):
                    area_to = connection.area_a
                else:
                    continue
                node_to = self.nodes[area_to]
                
                if node_to in closed_list:
                    continue
                
                if (connection.flags & Connection.FLAG_TELEPORTER) != 0:
                    move_cost = 0
                else:
                    if (node_to.area.flags & Element.FLAG_DAMAGE_LOW) != 0:
                        move_cost = 2
                    elif (node_to.area.flags & Element.FLAG_DAMAGE_MEDIUM) != 0:
                        move_cost = 4
                    elif (node_to.area.flags & Element.FLAG_DAMAGE_HIGH) != 0:
                        move_cost = 8
                    else:
                        move_cost = 1
                cost = node_current.move_cost + move_cost
                
                best_score = False
                if node_to not in open_list:
                    best_score = True
                    cx1, cy1 = area_to.rect.get_center()
                    node_to.heuristic_cost = distance(cx1, cy1, end.x, end.y)
                    open_list.add(node_to)
                    
                elif cost < node_to.move_cost:
                    best_score = True
                    
                if best_score == True:
                    node_to.parent = node_current
                    node_to.move_cost = cost
                    node_to.total_cost = node_to.move_cost + node_to.heuristic_cost
                    
                    node_to.area.visited = True
                    visited += 1
    
        print 'No path could be found.'
        
        return None
            
        
    def build_path(self, end_node, area_start):
        node_path = []
        
        while end_node.area != area_start:
            end_node.area.path = True
            
            node_path.append(end_node)
            end_node = end_node.parent
        
        end_node.area.path = True
        
        node_path.reverse()
        return node_path