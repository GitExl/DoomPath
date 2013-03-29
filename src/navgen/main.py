from doom import wad
from doom.map.data import MapData
from nav.config import Config
from nav.grid import Grid
from nav.mesh import Mesh
from navgen import options
from os import path
import sys


APP_NAME = 'navgen'
APP_VERSION = '0.9 beta'

       
def generate_map(wad_file, map_lump, settings):

    print ''
    print '[{}]'.format(map_lump)
    map_data = MapData(wad_file, map_lump)
    
    if settings.config == None:
        if map_data.is_hexen:
            configuration = 'zdoom'
        else:
            configuration = 'doom'
    else:
        configuration = settings.config
            
    print 'Using "{}" configuration...'.format(configuration)
    config_data = Config('doompath.json', configuration)
    
    print 'Map setup...'
    map_data.setup(config_data)

    print 'Detecting walkable space...'
    nav_grid = Grid()
    nav_grid.create(config_data, map_data, settings.resolution)
    if settings.write_grid == True:
        dest_file = get_side_filename(settings.wad, map_lump, 'dpg')
        nav_grid.write(dest_file)
        
    print 'Generating navigation mesh...'
    nav_mesh = Mesh()
    nav_mesh.create(nav_grid, map_data, config_data, settings.max_area_size, settings.max_area_size_merged)
    
    print 'Writing navigation mesh...'
    dest_file = get_side_filename(settings.wad, map_lump, 'dpm')
    lump_index = wad_file.get_index(map_lump)
    nav_mesh.write(dest_file, wad_file, lump_index)
    
    return True


def get_side_filename(wad, map_name, extension):
    base_name = path.basename(wad)
    base_name = path.splitext(base_name)[0]
    
    base_path = path.split(wad)[0]
    
    return '{}/{}_{}.{}'.format(base_path, base_name, map_name.lower(), extension)
        
        
if __name__ == '__main__':
    print '{} version {}'.format(APP_NAME, APP_VERSION)
        
    parser = options.get_parser()
    settings = parser.parse_args()
    
    if settings.license == True:
        options.print_license()
        sys.exit(0)
    else:
        print 'This program is licensed under the FreeBSD license. Use the --license option to view this license text.'
        print ''
        
    print 'Loading {}...'.format(settings.wad)
    wad_file = wad.WADReader(settings.wad)
    
    if settings.map is None:
        maplist = wad_file.get_map_list() 
    else:
        maplist = [settings.map] 
        
    for map_lump in maplist:
        generate_map(wad_file, map_lump, settings)
    
    print ''
    print 'Finished.'