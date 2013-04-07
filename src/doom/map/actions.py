class Action(object):
    
    # Effect types.
    TYPE_DOOR = 0
    TYPE_FLOOR = 1
    TYPE_CEILING = 2
    TYPE_CRUSHER = 3
    TYPE_TELEPORTER = 4
    TYPE_DONUT = 5
    TYPE_STAIRS = 6
    TYPE_PLATFORM = 7
    TYPE_ELEVATOR = 8
    TYPE_EXIT = 9
    TYPE_DOOR_LOCKED = 10
    TYPE_LIGHT = 11
    
    type_mapping = {
        'door': TYPE_DOOR,
        'floor': TYPE_FLOOR,
        'ceiling': TYPE_CEILING,
        'crusher': TYPE_CRUSHER,
        'teleporter': TYPE_TELEPORTER,
        'donut': TYPE_DONUT,
        'stairs': TYPE_STAIRS,
        'platform': TYPE_PLATFORM,
        'elevator': TYPE_ELEVATOR,
        'exit': TYPE_EXIT,
        'lockeddoor': TYPE_DOOR_LOCKED,
        'light': TYPE_LIGHT
    }
    
    # Activation types.
    ACTIVATE_PUSH = 0
    ACTIVATE_SWITCH = 1
    ACTIVATE_WALK = 2
    ACTIVATE_SHOOT = 3
    
    activate_mapping = {
        'push': ACTIVATE_PUSH,
        'switch': ACTIVATE_SWITCH,
        'walk': ACTIVATE_WALK,
        'shoot': ACTIVATE_SHOOT
    }
    
    # Movement types.
    MOVE_UP = 0
    MOVE_DOWN = 1
    
    movement_mapping = {
        'up': MOVE_UP,
        'down': MOVE_DOWN
    }

    # Door types.
    DOOR_OPEN_WAIT_CLOSE = 0
    DOOR_OPEN_STAY = 1
    DOOR_CLOSE_STAY = 2
    DOOR_CLOSE_WAIT_OPEN = 3
    
    door_mapping = {
        'openwaitclose': DOOR_OPEN_WAIT_CLOSE,
        'openstay': DOOR_OPEN_STAY,
        'closestay': DOOR_CLOSE_STAY,
        'closewaitopen': DOOR_CLOSE_WAIT_OPEN,
    }
    
    # Key flags.
    KEY_CARD_BLUE = 0x1
    KEY_CARD_RED = 0x2
    KEY_CARD_YELLOW = 0x4
    KEY_SKULL_BLUE = 0x8
    KEY_SKULL_RED = 0x10
    KEY_SKULL_YELLOW = 0x20
    KEY_ALL = 0x40
    KEY_ANY = 0x80
    KEY_SKULLS_ARE_CARDS = 0x100
    
    key_flags_mapping = {
        'cardblue': KEY_CARD_BLUE,
        'cardred': KEY_CARD_RED,
        'cardyellow': KEY_CARD_YELLOW,
        'skullblue': KEY_SKULL_BLUE,
        'skullred': KEY_SKULL_RED,
        'skullyellow': KEY_SKULL_YELLOW,
        'all': KEY_ALL,
        'any': KEY_ANY,
        'skulliscard': KEY_SKULLS_ARE_CARDS
    }

    # Sector move targets.
    TARGET_LOWEST_NEIGHBOUR_CEILING = 0
    TARGET_LOWEST_NEIGHBOUR_CEILING8 = 1
    TARGET_LOWEST_NEIGHBOUR_FLOOR = 2
    TARGET_LOWEST_NEIGHBOUR_FLOOR8 = 3
    TARGET_NEXT_NEIGHBOUR_CEILING = 4
    TARGET_NEXT_NEIGHBOUR_FLOOR = 5
    TARGET_HIGHEST_NEIGHBOUR_CEILING = 6
    TARGET_HIGHEST_NEIGHBOUR_CEILING8 = 7
    TARGET_HIGHEST_NEIGHBOUR_FLOOR = 8
    TARGET_HIGHEST_NEIGHBOUR_FLOOR8 = 9
    TARGET_SHORTEST_LOWER_TEXTURE = 10
    TARGET_CEILING = 11
    TARGET_CEILING8 = 12
    TARGET_FLOOR = 13
    TARGET_FLOOR8 = 14
    TARGET_NEXT_LOWEST = 15
    TARGET_NEXT_HIGHEST = 16
    TARGET_CURRENT_FLOOR = 17
    TARGET_NEXT_LOWEST_FLOOR = 18
    TARGET_NEXT_HIGHEST_FLOOR = 19
    TARGET_NEXT_FLOOR = 20
    TARGET_LOWEST_AND_HIGHEST = 21
    
    target_mapping = {
        'lowestneighbourceiling': TARGET_LOWEST_NEIGHBOUR_CEILING,
        'lowestneighbourceiling8': TARGET_LOWEST_NEIGHBOUR_CEILING8,
        'lowestneighbourfloor': TARGET_LOWEST_NEIGHBOUR_FLOOR,
        'lowestneighbourfloor8': TARGET_LOWEST_NEIGHBOUR_FLOOR8,
        'nextneighbourceiling': TARGET_NEXT_NEIGHBOUR_CEILING,
        'nextneighbourfloor': TARGET_NEXT_NEIGHBOUR_FLOOR,
        'highestneighbourceiling': TARGET_HIGHEST_NEIGHBOUR_CEILING,
        'highestneighbourceiling8': TARGET_HIGHEST_NEIGHBOUR_CEILING8,
        'highestneighbourfloor': TARGET_HIGHEST_NEIGHBOUR_FLOOR,
        'highestneighbourfloor8': TARGET_HIGHEST_NEIGHBOUR_FLOOR8,
        'shortestlower': TARGET_SHORTEST_LOWER_TEXTURE,
        'targetceiling': TARGET_CEILING,
        'targetceiling8': TARGET_CEILING8,
        'targetfloor': TARGET_FLOOR,
        'targetfloor8': TARGET_FLOOR8,
        'currentfloor': TARGET_CURRENT_FLOOR,
        'nextlowestfloor': TARGET_NEXT_LOWEST_FLOOR,
        'nexthighestfloor': TARGET_NEXT_HIGHEST_FLOOR,
        'nextfloor': TARGET_NEXT_FLOOR,
        'lowestandhighest': TARGET_LOWEST_AND_HIGHEST
    }
    
    # Mover properties changes.
    CHANGE_TEXTURE = 0x1
    CHANGE_TYPE = 0x2
    CHANGE_REMOVE_TYPE = 0x4
    
    change_flags_mapping = {
        'changetexture': CHANGE_TEXTURE,
        'changetype': CHANGE_TYPE,
        'removetype': CHANGE_REMOVE_TYPE
    }
    
    # Mover model sector selection.
    MODEL_NUMERIC = 0
    MODEL_TRIGGER = 1
    
    model_mapping = {
        'numeric': MODEL_NUMERIC,
        'trigger': MODEL_TRIGGER
    }
    
    # Teleporter types.
    TELEPORT_THING = 0
    TELEPORT_LINE = 1
    TELEPORT_LINE_REVERSED = 2
    
    teleport_mapping = {
        'thing': TELEPORT_THING,
        'line': TELEPORT_LINE,
        'linereversed': TELEPORT_LINE_REVERSED
    }
    
    # Light type mapping.
    LIGHT_35 = 0
    LIGHT_255 = 1
    LIGHT_BLINK = 2
    LIGHT_MIN_NEIGHBOUR = 3
    LIGHT_MAX_NEIGHBOUR = 4
    LIGHT_LOWEST_NEIGHBOUR = 5
    
    light_mapping = {
        'light35': LIGHT_35,
        'light255': LIGHT_255,
        'blink': LIGHT_BLINK,
        'minneighbour': LIGHT_MIN_NEIGHBOUR,
        'maxneighbour': LIGHT_MAX_NEIGHBOUR,
        'lowestneighbour': LIGHT_LOWEST_NEIGHBOUR
    }
    
    # Movement speed tic mapping.
    # TODO: Find the right values from code.
    speed_mapping = {
        'slow': 16,
        'fast': 32,
        'instant': 0
    }
    
    # Waiting time tic mapping.
    wait_mapping = {
        'wait3': 105,
        'wait4': 140,
        'wait30': 1050
    }
    
    # Movement distance mapping.
    distance_mapping = {
        'move8': 8,
        'move16': 16,
        'move24': 24,
        'move32': 32,
        'move512': 512
    }
    
    # Can be activated only once.
    FLAG_ONCE = 0x1
    
    # Cannot be activated by players.
    FLAG_NO_PLAYER = 0x2
    
    # Can be activated by monsters.
    FLAG_MONSTER = 0x4
    
    # Will crush things.
    FLAG_CRUSHES = 0x8
    
    # Starts or stops movement.
    FLAG_STARTS = 0x10
    FLAG_STOPS = 0x20
    
    # Moves silently.
    FLAG_SILENT = 0x40
    
    # Is a secret exit.
    FLAG_SECRET_EXIT = 0x80
    
    # Ignores floor texture changes.
    FLAG_IGNORE_FLOOR = 0x100
    
    # Preserve angle when teleporting.
    FLAG_PRESERVE_ANGLE = 0x200
    
    flags_mapping = {
        'once': FLAG_ONCE,
        'noplayer': FLAG_NO_PLAYER,
        'monster': FLAG_MONSTER,
        'crush': FLAG_CRUSHES,
        'start': FLAG_STARTS,
        'stop': FLAG_STOPS,
        'silent': FLAG_SILENT,
        'secret': FLAG_SECRET_EXIT,
        'ignorefloor': FLAG_IGNORE_FLOOR,
        'preserveangle': FLAG_PRESERVE_ANGLE
    }
    
    
    def __init__(self):
        self.index = 1
        self.type = Action.TYPE_DOOR
        self.activation = Action.ACTIVATE_PUSH
        
        self.door_type = Action.DOOR_OPEN_WAIT_CLOSE
        self.teleport_type = Action.TELEPORT_THING
        
        self.key_flags = 0
        self.change_flags = 0
        self.flags = 0
        
        self.speed = 8
        self.wait_time = 105
        self.direction = Action.MOVE_UP
        self.target = Action.TARGET_HIGHEST_NEIGHBOUR_CEILING
        self.move_amount = 0
        self.model = Action.MODEL_TRIGGER
        self.light_change = Action.LIGHT_255
    
    
    def __repr__(self):
        return 'Action {}: type {}'.format(self.index, self.type)
    

class ActionTypes(object):
    
    BOOM_TRIGGER = 0x7
    BOOM_SPEED = 0x18
    
    BOOM_FLOOR_MODEL = 0x20
    BOOM_FLOOR_DIRECTION = 0x40
    BOOM_FLOOR_TARGET = 0x380
    BOOM_FLOOR_CHANGE = 0xc00
    BOOM_FLOOR_CRUSH = 0x1000
    
    BOOM_CEILING_MODEL = 0x20
    BOOM_CEILING_DIRECTION = 0x40
    BOOM_CEILING_TARGET = 0x380
    BOOM_CEILING_CHANGE = 0xc00
    BOOM_CEILING_CRUSH = 0x1000
    
    BOOM_DOOR_KIND = 0x60
    BOOM_DOOR_MONSTER = 0x80
    BOOM_DOOR_DELAY = 0x300
    
    BOOM_DOOR_LOCK_KIND = 0x60
    BOOM_DOOR_LOCK_TYPE = 0x20
    BOOM_DOOR_LOCK_SKULL_IS_KEY = 0x200
    
    BOOM_LIFT_MONSTER = 0x20
    BOOM_LIFT_DELAY = 0xc0
    BOOM_LIFT_TARGET = 0x300
    
    BOOM_STAIRS_MONSTER = 0x20
    BOOM_STAIRS_STEP = 0xc0
    BOOM_STAIRS_DIRECTION = 0x100
    BOOM_STAIRS_IGNORE_FLOOR = 0x200
    
    BOOM_CRUSHER_MONSTER = 0x20
    BOOM_CRUSHER_SILENT = 0x40
    
    
    def __init__(self):
        self.actions = {}
    
    
    def add(self, index, keywords):
        action = Action()
        action.index = index
        
        for keyword in keywords.split(','):
            if keyword in Action.type_mapping:
                action.type = Action.type_mapping[keyword]
            elif keyword in Action.activate_mapping:
                action.activation = Action.activate_mapping[keyword]
            elif keyword in Action.movement_mapping:
                action.direction = Action.movement_mapping[keyword]
            elif keyword in Action.door_mapping:
                action.door_type = Action.door_mapping[keyword]
            elif keyword in Action.key_flags_mapping:
                action.key_flags |= Action.key_flags_mapping[keyword]
            elif keyword in Action.target_mapping:
                action.target = Action.target_mapping[keyword]
            elif keyword in Action.change_flags_mapping:
                action.change_flags |= Action.change_flags_mapping[keyword]
            elif keyword in Action.model_mapping:
                action.model = Action.model_mapping[keyword]
            elif keyword in Action.teleport_mapping:
                action.teleport_type = Action.teleport_mapping[keyword]
            elif keyword in Action.flags_mapping:
                action.flags |= Action.flags_mapping[keyword]
            elif keyword in Action.speed_mapping:
                action.speed = Action.speed_mapping[keyword]
            elif keyword in Action.wait_mapping:
                action.wait_time = Action.wait_mapping[keyword]
            elif keyword in Action.distance_mapping:
                action.move_amount = Action.distance_mapping[keyword]
            elif keyword in Action.light_mapping:
                action.light_change = Action.light_mapping[keyword]
            else:
                print 'Unknown action keyword "{}".'.format(keyword)
        
        self.actions[index] = action
    
    
    def get(self, action_index):
        if action_index == 0:
            return None
        
        if action_index in self.actions:
            return self.actions[action_index]
        
        if action_index < 0x2f80 or action_index > 0x8000:
            return None
        
        action = Action()
        
        index = action_index
        if index >= 0x6000 and index < 0x8000:
            action.type = Action.TYPE_FLOOR
            
            index -= 0x6000
            action.activation, action.flags = self.get_boom_activation(index)
            
            if ((index >> 6) & ActionTypes.BOOM_FLOOR_DIRECTION) != 0:
                action.flags |= Action.FLAG_UP
            else:
                action.flags |= Action.FLAG_DOWN
            
            if ((index >> 12) & ActionTypes.BOOM_FLOOR_CRUSH) != 0:
                action.flags |= Action.FLAG_CRUSHES
                        
        elif index >= 0x4000 and index < 0x6000:
            action.type = Action.TYPE_CEILING
            
            index -= 0x4000
            action.activation, action.flags = self.get_boom_activation(index)
            
            if ((index >> 6) & ActionTypes.BOOM_CEILING_DIRECTION) != 0:
                action.flags |= Action.FLAG_UP
            else:
                action.flags |= Action.FLAG_DOWN
                
            if ((index >> 12) & ActionTypes.BOOM_FLOOR_CRUSH) != 0:
                action.flags |= Action.FLAG_CRUSHES
            
        elif index >= 0x3c00 and index < 0x4000:
            action.type = Action.TYPE_DOOR
            
            index -= 0x3c00
            action.activation, action.flags = self.get_boom_activation(index)
            
        elif index >= 0x3800 and index < 0x3c00:
            action.type = Action.TYPE_DOOR_LOCKED
            
            index -= 0x3800
            action.activation, action.flags = self.get_boom_activation(index)
            
            lock = ((index >> 6) & ActionTypes.BOOM_DOOR_LOCK_TYPE)
            if lock == 0:
                action.flags |= Action.FLAG_ANY
            elif lock == 1:
                action.flags |= Action.FLAG_KEY_RED
            elif lock == 2:
                action.flags |= Action.FLAG_KEY_BLUE
            elif lock == 3:
                action.flags |= Action.FLAG_KEY_YELLOW
            elif lock == 4:
                action.flags |= Action.FLAG_SKULL_RED
            elif lock == 5:
                action.flags |= Action.FLAG_SKULL_BLUE
            elif lock == 6:
                action.flags |= Action.FLAG_SKULL_YELLOW
            elif lock == 7:
                action.flags |= Action.FLAG_ALL
            
            if ((index >> 9) & ActionTypes.BOOM_DOOR_LOCK_SKULL_IS_KEY) != 0:
                action.flags |= Action.FLAG_SKULL_IS_KEY
            
        elif index >= 0x3400 and index < 0x3800:
            action.type = Action.TYPE_LIFT
            
            index -= 0x3400
            action.activation, action.flags = self.get_boom_activation(index)
            
        elif index >= 0x3000 and index < 0x3400:
            action.type = Action.TYPE_STAIRS
            
            index -= 0x3000
            action.activation, action.flags = self.get_boom_activation(index)
            
            if ((index >> 9) & ActionTypes.BOOM_STAIRS_IGNORE_FLOOR) != 0:
                action.flags |= Action.FLAG_IGNORE_FLOOR
            
        elif index >= 0x2f80 and index < 0x3000:
            action.type = Action.TYPE_CRUSHER
            
            index -= 0x2f80
            action.activation, action.flags = self.get_boom_activation(index)
            
        else:
            return None
        
        self.actions[action_index] = action
        return action
    
    
    def get_boom_activation(self, boom_index):
        boom_index = (boom_index & ActionTypes.BOOM_TRIGGER)
        if boom_index == 0:
            return Action.ACTIVATE_WALK, Action.FLAG_ONCE
        elif boom_index == 1:
            return Action.ACTIVATE_WALK, 0
        elif boom_index == 2:
            return Action.ACTIVATE_SWITCH, Action.FLAG_ONCE
        elif boom_index == 3:
            return Action.ACTIVATE_SWITCH, 0
        elif boom_index == 4:
            return Action.ACTIVATE_SHOOT, Action.FLAG_ONCE
        elif boom_index == 5:
            return Action.ACTIVATE_SHOOT, 0
        elif boom_index == 6:
            return Action.ACTIVATE_PUSH, Action.FLAG_ONCE
        elif boom_index == 7:
            return Action.ACTIVATE_PUSH, 0