class Action(object):
    
    __slots__ = (
        'index',
        'type',
        'activation',
        'flags'
    )
    
    
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
    
    # Activation types.
    ACTIVATE_PUSH = 0
    ACTIVATE_SWITCH = 1
    ACTIVATE_WALK = 2
    ACTIVATE_SHOOT = 3
    
    
    # Can be activated only once.
    FLAG_ONCE = 0x1
    
    # Movement direction.
    FLAG_UP = 0x2
    FLAG_DOWN = 0x4

    # Keys.
    FLAG_KEY_BLUE = 0x8
    FLAG_KEY_RED = 0x10
    FLAG_KEY_YELLOW = 0x20
    FLAG_SKULL_BLUE = 0x40
    FLAG_SKULL_RED = 0x80
    FLAG_SKULL_YELLOW = 0x100
    
    # Need all key colors or need any key color.
    FLAG_ALL = 0x200
    FLAG_ANY = 0x400
    
    # Skullcards function as keycards.
    FLAG_SKULL_IS_KEY = 0x800
    
    # Will crush things.
    FLAG_CRUSHES = 0x1000
    
    # Teleports to a line.
    FLAG_TELEPORT_LINE = 0x2000
    
    # Starts or stops a crusher.
    FLAG_STARTS = 0x4000
    FLAG_STOPS = 0x8000
    
    # Crushes silently.
    FLAG_SILENT = 0x10000
    
    # Is a secret exit.
    FLAG_SECRET = 0x20000
    
    # Ignore floor texture changes.
    FLAG_IGNORE_FLOOR = 0x40000
    
    
    def __init__(self):
        self.index = 1
        self.type = Action.TYPE_DOOR
        self.activation = Action.ACTIVATE_PUSH
        self.flags = 0
    
    
    def __repr__(self):
        return 'Action {}: type {}, activation {}, flags {}'.format(self.index, self.type, self.activation, self.flags)
    

class ActionTypes(object):
    
    type_mapping = {
        'door': Action.TYPE_DOOR,
        'floor': Action.TYPE_FLOOR,
        'ceiling': Action.TYPE_CEILING,
        'crusher': Action.TYPE_CRUSHER,
        'teleporter': Action.TYPE_TELEPORTER,
        'donut': Action.TYPE_DONUT,
        'stairs': Action.TYPE_STAIRS,
        'platform': Action.TYPE_PLATFORM,
        'elevator': Action.TYPE_ELEVATOR,
        'exit': Action.TYPE_EXIT,
        'lockeddoor': Action.TYPE_DOOR_LOCKED
    }
    
    activate_mapping = {
        'push': Action.ACTIVATE_PUSH,
        'switch': Action.ACTIVATE_SWITCH,
        'walk': Action.ACTIVATE_WALK,
        'shoot': Action.ACTIVATE_SHOOT
    }
    
    flag_mapping = {
        'once': Action.FLAG_ONCE,
        'up': Action.FLAG_UP,
        'down': Action.FLAG_DOWN,
        'keyblue': Action.FLAG_KEY_BLUE,
        'keyred': Action.FLAG_KEY_RED,
        'keyyellow': Action.FLAG_KEY_YELLOW,
        'crush': Action.FLAG_CRUSHES,
        'line': Action.FLAG_TELEPORT_LINE,
        'start': Action.FLAG_STARTS,
        'stop': Action.FLAG_STOPS,
        'secret': Action.FLAG_SECRET,
        'skulliskey': Action.FLAG_SKULL_IS_KEY,
        'silent': Action.FLAG_SILENT,
        'all': Action.FLAG_ALL,
        'any': Action.FLAG_ANY,
        'blueskull': Action.FLAG_SKULL_BLUE,
        'redskull': Action.FLAG_SKULL_RED,
        'yellowskull': Action.FLAG_SKULL_YELLOW,
        'ignorefloor': Action.FLAG_IGNORE_FLOOR
    }
    
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
            if keyword in self.type_mapping:
                action.type = self.type_mapping[keyword]
            
            elif keyword in self.activate_mapping:
                action.activation = self.activate_mapping[keyword]
                
            elif keyword in self.flag_mapping:
                action.flags |= self.flag_mapping[keyword]
            
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