#!/usr/bin/env python
#coding=utf8

"""
Contains Doom WAD file reading classes.
"""

import struct


class WADError(Exception):
    """
    Base class for errors in WAD files.
    """
    
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg
    
class WADTypeError(WADError):
    """
    The WAD file has an invalid type.
    """
     

class Lump(object):
    """
    A lump that is part of a WAD file.
    
    It is recommended to access a lump's data through the get_data() method to prevent having to load an entire
    WAD's data in memory.
    """
    
    def __init__(self, name, size, offset, owner):
        self.name = name
        self.size = size
        self.offset = offset
        self.data = None
        self.owner = owner

        
    def get_data(self):
        """
        Returns this lump's data.
        
        If the data has not yet been read, it will open the WAD file and read it before returning it.
        """
        
        if self.data is None:
            with open(self.owner.filename, 'rb') as f:
                f.seek(self.offset)
                self.data = f.read(self.size)
        
        return self.data
     

class WADReader(object):
    """
    Reads Doom WAD files.
    """
    
    TYPE_IWAD = 'IWAD'
    TYPE_PWAD = 'PWAD'
    
    S_HEADER = struct.Struct("<4sII")
    S_LUMP = struct.Struct("<II8s")

    
    def __init__(self, filename):
        self.filename = None
        self.lumps = None
        self.type = None
        
        self.read(filename)
    
    
    def read(self, filename):
        """
        Reads a WAD file's header and lump directory.
        
        @raise WADTypeError: if the WAD file is not of a valid type (IWAD or PWAD). 
        """
        
        with open(filename, 'rb') as f:
            
            # Read and validate header. Should contain PWAD or IWAD magic bytes.
            wad_type, entry_count, dir_offset = self.S_HEADER.unpack(f.read(self.S_HEADER.size)) 
            wad_type = wad_type.decode('ascii')
            if wad_type != self.TYPE_IWAD and wad_type != self.TYPE_PWAD:
                raise WADTypeError('Invalid WAD type "{}"'.format(type))
            
            # Read lump directory.
            f.seek(dir_offset)
            self.lumps = []
            for _ in range(entry_count):
                offset, size, name = self.S_LUMP.unpack(f.read(self.S_LUMP.size))
                
                # Strip trailing NULL characters.
                name = name.split('\x00')[0].decode('ascii')
                
                self.lumps.append(Lump(name, size, offset, self))
            
        self.filename = filename
        self.type = wad_type
            
    
    def get_index(self, lump_name):
        index = len(self.lumps) - 1
        for lump in reversed(self.lumps):
            if lump.name == lump_name:
                return index
            index -= 1
        
        return -1
    
    
    def get_lump_index(self, lump_index):
        if lump_index >= 0 and lump_index < len(self.lumps):
            return self.lumps[lump_index]
        
        return None
    
    
    def get_lump(self, lump_name):
        """
        Searches this WAD's lump directory for a lump by name.
        
        @return: the first matching lump with the specified name, or None if no lump with that name could be found.
        """
        
        for lump in reversed(self.lumps):
            if lump.name == lump_name:
                return lump
        
        return None