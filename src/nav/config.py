import json


DEF_FLAG_HANGING = 0x01


class ThingDef(object):
    
    def __init__(self, radius, height, flags):
        self.radius = radius
        self.height = height
        self.flags = flags


class Config(object):
    
    def __init__(self, filename, dataset):
        json_data = open(filename).read()
        data = json.loads(json_data)
        
        if not dataset in data:
            print 'Unknown dataset {}'.format(dataset)
            return
         
        data = data[dataset]
        
        self.player_radius = data['player_radius']
        self.player_height = data['player_height']
        self.step_height = data['step_height']
        self.jump_height = data['jump_height']
        
        # Convert thing dimension keys to integers.
        self.thing_dimensions = {}
        for key, value in data['thing_dimensions'].iteritems():
            thing_def = ThingDef(value[0], value[1], value[2])
            self.thing_dimensions[int(key)] = thing_def
            
        # Convert sector type keys to integers.
        self.sector_types = {}
        for key, value in data['sector_types'].iteritems():
            self.sector_types[int(key)] = value
            
        # Convert sector generalized type keys to integers.
        self.sector_generalized_types = {}
        for key, value in data['sector_generalized_types'].iteritems():
            self.sector_generalized_types[int(key)] = value
        
        # Mandatory settings.
        self.start_thing_types = data['start_thing_types']
        self.linedef_specials = data['linedef_specials']
        
        # Optional settings.
        self.slope_special = data.get('slope_special')
        self.slope_steep = data.get('slope_steep')
        self.bridge_custom_type = data.get('bridge_custom_type')
        self.threedfloor_special = data.get('threedfloor_special')
        self.teleport_thing_type = data.get('teleport_thing_type') 
        self.line_identification_specials = data.get('line_identification_specials')