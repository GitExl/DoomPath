from nav.connection import Connection
from nav.element import Element
from util.priorityqueue import PriorityQueue


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
        if self.total_cost < other.total_cost:
            return -1
        elif self.total_cost > other.total_cost:
            return 1
        
        return 0
        

class Pathfinder(object):
    
    def __init__(self, nav_mesh):
        self.nav_mesh = nav_mesh
        
        # Statistics.
        self.nodes_visited = 0
        self.distance = 0
        
        # 3d start and end point coordinates.
        self.start = None
        self.end = None
        
        # A list of nodes that map directly to mesh areas.
        self.nodes = []
        for area in nav_mesh.areas:
            self.nodes.append(PathNode(area))
        
        
    def find(self, start, end):
        self.nodes_visited = 0
        self.distance = 0
        self.start = start
        self.end = end
        
        open_list = PriorityQueue()
        closed_list = set()
        
        area_start = self.nav_mesh.get_area_at(start, start.z)
        if area_start is None:
            return None
        
        area_end = self.nav_mesh.get_area_at(end, end.z)
        if area_end is None:
            return None

        # Process nodes on the open list until it is empty.
        open_list.push(self.nodes[area_start.index])
        while len(open_list) > 0:
            # Retrieve the item with the lowest value from the open list.
            node_current = open_list.pop_lowest()
            
            # Test if we have reached the end area.
            if node_current.area == area_end:
                self.distance = int(node_current.move_cost)
                return self.build_path(node_current, area_start)
            
            closed_list.add(node_current)
            
            # Test every connection to other areas from the current node's area.
            for connection in node_current.area.connections:
                
                # Select which area in the connection to use, ignoring one-way connections.
                if node_current.area == connection.area_a and (connection.flags & Connection.FLAG_AB):
                    node_to = self.nodes[connection.area_b.index]
                elif node_current.area == connection.area_b and (connection.flags & Connection.FLAG_BA):
                    node_to = self.nodes[connection.area_a.index]
                else:
                    continue

                # Ignore nodes that were already examined.
                if node_to in closed_list:
                    continue
                
                # Test if we can move from this area to the other.
                if node_current.area.sector is not None or node_to.area.sector is not None:
                    if self.can_traverse(node_current.area, node_to.area) == False:
                        continue
                
                # Determine the cost to move to this node.
                cost = node_current.move_cost + self.get_move_cost(node_current.parent_connection, connection, node_current, node_to)
                best_score = False
                
                # Add the new node to the open list.
                if node_to not in open_list:
                    best_score = True
                    cx1, cy1 = connection.center
                    node_to.heuristic_cost = (abs(end.x - cx1) + abs(end.y - cy1))
                    open_list.push(node_to)
                    
                # Found a cheaper node.
                elif cost < node_to.move_cost:
                    best_score = True
                    
                # Set this node as a new part of the path.
                if best_score == True:
                    node_to.parent = node_current
                    node_to.parent_connection = connection
                    node_to.move_cost = cost
                    node_to.total_cost = node_to.move_cost + node_to.heuristic_cost
                    
                    node_to.area.visited = True
                    self.nodes_visited += 1

        return None
    
    
    def can_traverse(self, area_from, area_to):
        # Into special area.
        if area_from.sector is None and area_to.sector is not None:
            pass
        
        # Out of special area.
        elif area_from.sector is not None and area_to.sector is None:
            pass
        
        # Passing through the same special area.
        elif area_from.sector == area_to.sector:
            return True
        
        # Passing through different special areas.
        else:
            pass
    
    
    def get_move_cost(self, connection_from, connection_to, node_from, node_to):
        # Teleporters connect at no cost.
        if (connection_to.flags & Connection.FLAG_TELEPORTER) != 0:
            move_cost = 0
        
        # Use distance between two connections as the cost.
        else:
            if connection_from is None:
                cx1, cy1 = self.start.x, self.start.y
            else:
                cx1, cy1 = connection_from.center
            cx2, cy2 = connection_to.center
            move_cost = abs(cx2 - cx1) + abs(cy2 - cy1)
        
        # Multiply cost for damaging areas.
        if (node_to.area.flags & Element.FLAG_DAMAGE_LOW) != 0:
            move_cost *= 2
        elif (node_to.area.flags & Element.FLAG_DAMAGE_MEDIUM) != 0:
            move_cost *= 4
        elif (node_to.area.flags & Element.FLAG_DAMAGE_HIGH) != 0:
            move_cost *= 8
        
        # Avoid drop offs.
        if node_from.area.z > node_to.area.z + 24:
            move_cost *= 10
            
        return move_cost
    
        
    def build_path(self, end_node, area_start):
        node_path = []
        connection_path = []
        
        # Start at the end node and follow parent nodes back to the start area.
        while end_node.area != area_start:
            end_node.area.path = True
            
            node_path.append(end_node)
            end_node = end_node.parent
        
        end_node.area.path = True
        
        # Reverse the path so that it starts at the starting point and not the end.
        node_path.reverse()
        
        # Create a path out of area connections instead of nodes.
        for node in node_path:
            connection_path.append(node.parent_connection)
        
        return connection_path