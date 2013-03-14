from doom.mapenum import *
from vector import Vector3, vector_substract, vector_crossproduct, vector_dotproduct


class Plane(object):
    
    def __init__(self):
        self.a = 0
        self.b = 0
        self.c = 0
        self.d = 0
        self.invc = 0


    def invert(self):
        self.a = -self.a
        self.b = -self.b
        self.c = -self.c
        self.d = -self.d
        self.invc = -self.invc
        
        
    def get_z(self, x, y):       
        return -(self.invc * (self.a * x + self.b * y + self.d))


def plane_setup(map_data, refsector_index, refsector_lines, refline, floor):
    vertex1 = map_data.vertices[refline[LINEDEF_VERTEX_1]]
    vertex2 = map_data.vertices[refline[LINEDEF_VERTEX_2]]
    
    refv1x = vertex1[VERTEX_X]
    refv1y = vertex1[VERTEX_Y]
    refdx = vertex2[VERTEX_X] - refv1x
    refdy = vertex2[VERTEX_Y] - refv1y
    
    farthest_vertex_index = -1
    farthest_distance = 0.0

    # Find the vertex comprising the sector that is farthest from the
    # slope's reference line
    for line in refsector_lines:
        line_vertex1 = map_data.vertices[line[LINEDEF_VERTEX_1]]
        line_vertex2 = map_data.vertices[line[LINEDEF_VERTEX_2]]
        
        # Calculate distance from vertex 1 of this line
        dist = abs((refv1y - line_vertex1[VERTEX_Y]) * refdx - (refv1x - line_vertex1[VERTEX_X]) * refdy)
        if dist > farthest_distance:
            farthest_distance = dist
            farthest_vertex_index = line[LINEDEF_VERTEX_1]
    
        # Calculate distance from vertex 2 of this line
        dist = abs((refv1y - line_vertex2[VERTEX_Y]) * refdx - (refv1x - line_vertex2[VERTEX_X]) * refdy)
        if dist > farthest_distance:
            farthest_distance = dist
            farthest_vertex_index = line[LINEDEF_VERTEX_2]
    
    if farthest_distance <= 0.0:
        return None
    
    farthest_vertex = map_data.vertices[farthest_vertex_index]

    # Determine which sector to align.
    front = map_data.sidedefs[refline[map_data.LINEDEF_SIDEDEF_FRONT]][SIDEDEF_SECTOR]
    back = map_data.sidedefs[refline[map_data.LINEDEF_SIDEDEF_BACK]][SIDEDEF_SECTOR]
    if refsector_index == front:
        align_sector_index = back
    else:
        align_sector_index = front
        
    refsector = map_data.sectors[refsector_index]
    align_sector = map_data.sectors[align_sector_index]
    
    # Now we have three points, which can define a plane:
    # The two vertices making up refline and farthest_vertex
    if floor == True:
        z1 = align_sector[SECTOR_FLOORZ]
    else:
        z1 = align_sector[SECTOR_CEILZ]
    
    if floor == True:
        z2 = refsector[SECTOR_FLOORZ]
    else:
        z2 = refsector[SECTOR_CEILZ]
    
    # bail if the plane is perfectly level
    if z1 == z2:
        return None

    p1 = Vector3(vertex1[VERTEX_X], vertex1[VERTEX_Y], z1)
    p2 = Vector3(vertex2[VERTEX_X], vertex2[VERTEX_Y], z1)
    p3 = Vector3(farthest_vertex[VERTEX_X], farthest_vertex[VERTEX_Y], z2)

    # Define the plane by drawing two vectors originating from
    # point p2:  the vector from p2 to p1 and from p2 to p3
    # Then take the crossproduct of those vectors to get the normal vector
    # for the plane, which provides the planar equation's coefficients
    vector1 = Vector3(0, 0, 0)
    vector2 = Vector3(0, 0, 0)
    vector_substract(vector1, p1, p2)
    vector_substract(vector2, p3, p2)
    
    normal = Vector3(0, 0, 0)
    vector_crossproduct(normal, vector1, vector2)
    normal.normalize()
    
    plane = Plane()
    plane.a = normal.x;
    plane.b = normal.y;
    plane.c = normal.z;
    plane.invc = 1.0 / normal.z;
    plane.d = -vector_dotproduct(normal, p1)

    # Flip inverted normals
    if (floor == True and normal.z < 0.0) or (floor == False and normal.z > 0.0):
        plane.invert()
    
    return plane