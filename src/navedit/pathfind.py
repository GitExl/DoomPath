from nav.connection import Connection
from nav.element import Element
from util.priorityqueue import PriorityQueue
import math


def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))


class PathNode(object):

    __slots__ = (
        'parent',
        'parent_connection',
        'area',
        
        'move_cost',
        'heuristic_cost',
        'total_cost'
    )
    
    
    def __init__(self, area):
        self.area = area
        self.parent = None
        self.parent_connection = None
        
        self.move_cost = 0
        self.heuristic_cost = 0
        self.total_cost = 0
        
    
    def __cmp__(self, other):
        if other.total_cost < self.total_cost:
            return -1
        elif other.total_cost > self.total_cost:
            return 1
        
        return 0
        

class Pathfinder(object):
    
    def __init__(self, nav_mesh):
        self.nav_mesh = nav_mesh
        
        self.nodes = {}
        
        self.nodes_visited = 0
        self.distance = 0
        
        self.start = None
        self.end = None
        
        for area in nav_mesh.areas:
            self.nodes[area] = PathNode(area)
        
        
    def find(self, start, end):
        self.nodes_visited = 0
        self.distance = 0
        self.start = start
        self.end = end
        
        for area in self.nav_mesh.areas:
            area.path = False
            area.visited = False
        
        open_list = PriorityQueue()
        closed_list = set()
        
        area_start = self.nav_mesh.get_area_at(start, start.z)
        if area_start is None:
            return None
        
        area_end = self.nav_mesh.get_area_at(end, end.z)
        if area_end is None:
            return None

        open_list.add(self.nodes[area_start])
        while len(open_list) > 0:
            node_current = open_list.lowest()
            
            if node_current.area == area_end:
                self.distance = node_current.move_cost
                return self.build_path(node_current, area_start)
            
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
                
                move_cost = self.get_move_cost(node_current.parent_connection, connection, node_to)
                cost = node_current.move_cost + int(move_cost)
                
                best_score = False
                if node_to not in open_list:
                    best_score = True
                    cx1, cy1 = connection.rect.get_center()
                    node_to.heuristic_cost = distance(cx1, cy1, end.x, end.y)
                    open_list.add(node_to)
                    
                elif cost < node_to.move_cost:
                    best_score = True
                    
                if best_score == True:
                    node_to.parent = node_current
                    node_to.parent_connection = connection
                    node_to.move_cost = cost
                    node_to.total_cost = node_to.move_cost + node_to.heuristic_cost
                    
                    node_to.area.visited = True
                    self.nodes_visited += 1

        return None
    
    
    def get_move_cost(self, connection_from, connection_to, node_to):
        if (connection_to.flags & Connection.FLAG_TELEPORTER) != 0:
            move_cost = 0
        else:
            if connection_from is None:
                cx1, cy1 = self.start.x, self.start.y
            else:
                cx1, cy1 = connection_from.rect.get_center()
            cx2, cy2 = connection_to.rect.get_center()
            move_cost = distance(cx1, cy1, cx2, cy2)
            
        if (node_to.area.flags & Element.FLAG_DAMAGE_LOW) != 0:
            move_cost *= 2
        elif (node_to.area.flags & Element.FLAG_DAMAGE_MEDIUM) != 0:
            move_cost *= 4
        elif (node_to.area.flags & Element.FLAG_DAMAGE_HIGH) != 0:
            move_cost *= 8
            
        return move_cost
    
        
    def build_path(self, end_node, area_start):
        node_path = []
        
        while end_node.area != area_start:
            end_node.area.path = True
            
            node_path.append(end_node)
            end_node = end_node.parent
        
        end_node.area.path = True
        node_path.reverse()
        
        connection_path = []
        for node in node_path:
            connection_path.append(node.parent_connection)
        
        return connection_path