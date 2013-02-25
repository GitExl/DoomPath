import math


def vector_crossproduct(vector_out, vector1, vector2):
    vector_out.x = (vector1.y * vector2.z) - (vector1.z * vector2.y)
    vector_out.y = (vector1.z * vector2.x) - (vector1.x * vector2.z)
    vector_out.z = (vector1.x * vector2.y) - (vector1.y * vector2.x)
    

def vector_substract(vector_out, vector1, vector2):
    vector_out.x = vector1.x - vector2.x
    vector_out.y = vector1.y - vector2.y
    vector_out.z = vector1.z - vector2.z


def vector_dotproduct(vector1, vector2):
    return (vector1.x * vector2.x) + (vector1.y * vector2.y) + (vector1.z * vector2.z);


class Vector3(object):
    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        
    def normalize(self):
        length = self.length()
        if length > 0.0:
            self.scale(1.0 / length)
    
    
    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z);
    
    
    def scale(self, scale):
        self.x *= scale
        self.y *= scale
        self.z *= scale