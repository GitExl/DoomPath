#!/usr/bin/env python
#coding=utf8

from util.vector import Vector3, vector_substract, vector_crossproduct, vector_dotproduct


class Plane(object):
    """
    Describes an angled plane.
    """
    
    def __init__(self):
        self.a = 0
        self.b = 0
        self.c = 0
        self.d = 0
        self.invc = 0


    def invert(self):
        """
        Inverts this plane.
        """
        
        self.a = -self.a
        self.b = -self.b
        self.c = -self.c
        self.d = -self.d
        self.invc = -self.invc
        
        
    def get_z(self, x, y):
        """
        Returns the Z height at coordinates x,y on this plane.
        """
               
        return -(self.invc * (self.a * x + self.b * y + self.d))


def plane_setup(map_data, refsector_index, refsector_lines, refline, floor):
    """
    Creates a new Plane object for a sloped Doom sector.
    
    Adapted from ZDoom's p_slope.cpp::P_AlignPlane.
    
    @param map_data: the map data object to generate the plane for.
    @param refsector_index: the reference sector index.
    @param refsector_lines: a list of linedefs belonging to the reference sector.
    @param refline: the linedef on which the slope special is used.
    
    @return: a Plane object or None if no plane could be generated.
    """    

    refv1x = refline.vertex1.x
    refv1y = refline.vertex1.y
    refdx = refline.vertex2.x - refv1x
    refdy = refline.vertex2.y - refv1y
    
    farthest_vertex = None
    farthest_distance = 0.0

    # Find the vertex comprising the sector that is farthest from the
    # slope's reference line.
    for line in refsector_lines:
       
        # Calculate distance from vertex 1 of this line.
        dist = abs((refv1y - line.vertex1.y) * refdx - (refv1x - line.vertex1.x) * refdy)
        if dist > farthest_distance:
            farthest_distance = dist
            farthest_vertex = line.vertex1
    
        # Calculate distance from vertex 2 of this line.
        dist = abs((refv1y - line.vertex2.y) * refdx - (refv1x - line.vertex2.x) * refdy)
        if dist > farthest_distance:
            farthest_distance = dist
            farthest_vertex = line.vertex2
    
    if farthest_distance <= 0.0:
        return None

    # Determine which sector to align.
    front_side = map_data.sidedefs[refline.sidedef_front]
    back_side = map_data.sidedefs[refline.sidedef_back]
    if refsector_index == front_side.sector:
        align_sector = map_data.sectors[back_side.sector]
    else:
        align_sector = map_data.sectors[front_side.sector]
    refsector = map_data.sectors[refsector_index]
    
    # Now we have three points, which can define a plane.
    # The two vertices making up refline and farthest_vertex.
    if floor == True:
        z1 = align_sector.floorz
    else:
        z1 = align_sector.ceilingz
    
    if floor == True:
        z2 = refsector.floorz
    else:
        z2 = refsector.ceilingz
    
    # Bail if the plane is perfectly level.
    if z1 == z2:
        return None

    p1 = Vector3(refline.vertex1.x, refline.vertex1.y, z1)
    p2 = Vector3(refline.vertex2.x, refline.vertex2.y, z1)
    p3 = Vector3(farthest_vertex.x, farthest_vertex.y, z2)

    # Define the plane by drawing two vectors originating from
    # point p2: the vector from p2 to p1 and from p2 to p3.
    # Then take the crossproduct of those vectors to get the normal vector
    # for the plane, which provides the planar equation's coefficients.
    vector1 = Vector3()
    vector2 = Vector3()
    vector_substract(vector1, p1, p2)
    vector_substract(vector2, p3, p2)
    
    normal = Vector3()
    vector_crossproduct(normal, vector1, vector2)
    normal.normalize()
    
    # Create the new plane.
    plane = Plane()
    plane.a = normal.x;
    plane.b = normal.y;
    plane.c = normal.z;
    plane.invc = 1.0 / normal.z;
    plane.d = -vector_dotproduct(normal, p1)

    # Flip inverted normals.
    if (floor == True and normal.z < 0.0) or (floor == False and normal.z > 0.0):
        plane.invert()
    
    return plane