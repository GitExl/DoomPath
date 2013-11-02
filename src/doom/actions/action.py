class Action(object):
    
    # Effect types.
    TYPE_DOOR = 0
    TYPE_FLOOR = 1
    TYPE_CEILING = 2
    TYPE_CRUSHER = 3
    TYPE_TELEPORTER = 4
    TYPE_DONUT = 5
    TYPE_STAIRS = 6
    TYPE_LIFT = 7
    TYPE_ELEVATOR = 8
    TYPE_EXIT = 9
    TYPE_DOOR_LOCKED = 10
    TYPE_LIGHT = 11
    
    # Activation flags.
    ACTIVATE_PUSH = 0x1
    ACTIVATE_SWITCH = 0x2
    ACTIVATE_WALK = 0x4
    ACTIVATE_SHOOT = 0x8
    ACTIVATE_BUMP = 0x10
    ACTIVATE_PASSTHROUGH = 0x20
       
    # Movement types.
    MOVE_UP = 0
    MOVE_DOWN = 1

    # Door types.
    DOOR_OPEN_WAIT_CLOSE = 0
    DOOR_OPEN_STAY = 1
    DOOR_CLOSE_STAY = 2
    DOOR_CLOSE_WAIT_OPEN = 3
    
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

    # Sector move targets.
    TARGET_NONE = 0
    TARGET_LOWEST_NEIGHBOUR_CEILING = 1
    TARGET_LOWEST_NEIGHBOUR_CEILING8 = 2
    TARGET_LOWEST_NEIGHBOUR_FLOOR = 3
    TARGET_LOWEST_NEIGHBOUR_FLOOR8 = 4
    TARGET_NEXT_NEIGHBOUR_CEILING = 5
    TARGET_NEXT_NEIGHBOUR_FLOOR = 6
    TARGET_HIGHEST_NEIGHBOUR_CEILING = 7
    TARGET_HIGHEST_NEIGHBOUR_CEILING8 = 8
    TARGET_HIGHEST_NEIGHBOUR_FLOOR = 9
    TARGET_HIGHEST_NEIGHBOUR_FLOOR8 = 10
    TARGET_SHORTEST_LOWER_TEXTURE = 11
    TARGET_CEILING = 12
    TARGET_CEILING8 = 13
    TARGET_FLOOR = 14
    TARGET_FLOOR8 = 15
    TARGET_NEXT_LOWEST = 16
    TARGET_NEXT_HIGHEST = 17
    TARGET_CURRENT_FLOOR = 18
    TARGET_NEXT_LOWEST_FLOOR = 19
    TARGET_NEXT_HIGHEST_FLOOR = 20
    TARGET_NEXT_FLOOR = 21
    TARGET_LOWEST_AND_HIGHEST = 22
    TARGET_SHORTEST_UPPER_TEXTURE = 11
    
    # Mover properties changes.
    CHANGE_TEXTURE = 0x1
    CHANGE_TYPE = 0x2
    CHANGE_REMOVE_TYPE = 0x4
    
    # Mover model sector selection.
    MODEL_NUMERIC = 0
    MODEL_TRIGGER = 1
    
    # Teleporter types.
    TELEPORT_THING = 0
    TELEPORT_LINE = 1
    TELEPORT_LINE_REVERSED = 2
    
    # Light type mapping.
    LIGHT_35 = 0
    LIGHT_255 = 1
    LIGHT_BLINK = 2
    LIGHT_MIN_NEIGHBOUR = 3
    LIGHT_MAX_NEIGHBOUR = 4
    LIGHT_LOWEST_NEIGHBOUR = 5

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
    
    # Can be activated by players.
    FLAG_PLAYER = 0x400
    
    # Can be activated by projectiles.
    FLAG_PROJECTILE = 0x800
    
    
    def __init__(self):
        self.index = 1
        self.type = Action.TYPE_DOOR
        self.activation = Action.ACTIVATE_PUSH
        
        self.key_flags = 0
        self.change_flags = 0
        self.flags = 0
        
        self.speed = 8
        self.wait_time = 105
        self.move_amount = 0

        self.door_type = Action.DOOR_OPEN_WAIT_CLOSE
        self.teleport_type = Action.TELEPORT_THING
        self.direction = Action.MOVE_UP
        self.target = Action.TARGET_HIGHEST_NEIGHBOUR_CEILING
        self.model = Action.MODEL_TRIGGER
        self.light_change = Action.LIGHT_255