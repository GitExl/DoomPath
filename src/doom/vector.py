#!/usr/bin/env python
#coding=utf8

"""
3D vector functionality.
"""

import math


def vector_crossproduct(vector_out, vector1, vector2):
    """
    Calculates the cross product of a 3d vector.
    
    @param vector_out: the Vector3 to store the result in.
    @param vector1: the left hand vector to use in the cross product.
    @param vector2: the right hand vector to use in the cross product.  
    """
    
    vector_out.x = (vector1.y * vector2.z) - (vector1.z * vector2.y)
    vector_out.y = (vector1.z * vector2.x) - (vector1.x * vector2.z)
    vector_out.z = (vector1.x * vector2.y) - (vector1.y * vector2.x)
    

def vector_substract(vector_out, vector1, vector2):
    """
    Substracts one vector from another.
    
    @param vector_out: the Vector3 to store the result in.
    @param vector1: the left hand vector to use in the substraction.
    @param vector2: the right hand vector to use in the substraction.
    """
    
    vector_out.x = vector1.x - vector2.x
    vector_out.y = vector1.y - vector2.y
    vector_out.z = vector1.z - vector2.z


def vector_dotproduct(vector1, vector2):
    """
    Returns the dot product of two Vector3 objects.
    """
    
    return (vector1.x * vector2.x) + (vector1.y * vector2.y) + (vector1.z * vector2.z);


class Vector3(object):
    """
    A three dimensional vector.
    """
    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        
    def normalize(self):
        """
        Normalizes this vector.
        """
        
        length = self.length()
        if length > 0.0:
            self.scale(1.0 / length)
    
    
    def length(self):
        """
        Returns the length of this vector.
        """
        
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z);
    
    
    def scale(self, scale):
        """
        Scales this vector.
        """
        
        self.x *= scale
        self.y *= scale
        self.z *= scale