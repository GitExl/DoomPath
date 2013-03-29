import binascii
import hashlib


def hashfile(file_obj, hasher, blocksize=0xffff):
    data = file_obj.read(blocksize)
    
    while len(data) > 0:
        hasher.update(data)
        data = file_obj.read(blocksize)
    
    return hasher.digest()


def sha256_from_file(filename):
    with open(filename, 'rb') as file_obj:
        file_hash = hashfile(file_obj, hashlib.sha256())
    
    return file_hash


def md5_from_file(filename):
    with open(filename, 'rb') as file_obj:
        file_hash = hashfile(file_obj, hashlib.md5())
    
    return file_hash


def crc32_from_file(filename):
    with open(filename, 'rb') as file_obj:
        data = file_obj.read()
    
    file_hash = binascii.crc32(data)
    
    return file_hash