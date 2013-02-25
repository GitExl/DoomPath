from ctypes import cdll, c_void_p, c_uint, c_char_p


doompathlib = cdll.doompath

mapdata_create = doompathlib.mapdata_create
mapdata_create.argtypes = None
mapdata_create.restype = c_void_p

mapdata_free = doompathlib.mapdata_free
mapdata_free.argtypes = [c_void_p]
mapdata_free.restype = None

mapdata_put_vertices = doompathlib.mapdata_put_vertices
mapdata_put_vertices.argtypes = [c_void_p, c_uint, c_char_p]
mapdata_put_vertices.restype = None

mapdata_put_nodes = doompathlib.mapdata_put_nodes
mapdata_put_nodes.argtypes = [c_void_p, c_uint, c_char_p]
mapdata_put_nodes.restype = None