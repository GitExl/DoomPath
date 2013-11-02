from doom.actions.action import Action


BITS_TRIGGER = 0x7
BITS_TRIGGER_SHIFT = 0
BITS_SPEED = 0x18
BITS_SPEED_SHIFT = 3

BITS_FLOOR_MODEL = 0x20
BITS_FLOOR_MODEL_SHIFT = 5
BITS_FLOOR_DIRECTION = 0x40
BITS_FLOOR_DIRECTION_SHIFT = 6
BITS_FLOOR_TARGET = 0x380
BITS_FLOOR_TARGET_SHIFT = 7
BITS_FLOOR_CHANGE = 0xc00
BITS_FLOOR_CHANGE_SHIFT = 10
BITS_FLOOR_CRUSH = 0x1000
BITS_FLOOR_CRUSH_SHIFT = 12

BITS_CEILING_MODEL = 0x20
BITS_CEILING_MODEL_SHIFT = 5
BITS_CEILING_DIRECTION = 0x40
BITS_CEILING_DIRECTION_SHIFT = 6
BITS_CEILING_TARGET = 0x380
BITS_CEILING_TARGET_SHIFT = 7
BITS_CEILING_CHANGE = 0xc00
BITS_CEILING_CHANGE_SHIFT = 10
BITS_CEILING_CRUSH = 0x1000
BITS_CEILING_CRUSH_SHIFT = 12

BITS_DOOR_KIND = 0x60
BITS_DOOR_KIND_SHIFT = 5
BITS_DOOR_MONSTER = 0x80
BITS_DOOR_MONSTER_SHIFT = 7
BITS_DOOR_DELAY = 0x300
BITS_DOOR_DELAY_SHIFT = 8

BITS_DOOR_LOCK_KIND = 0x60
BITS_DOOR_LOCK_KIND_SHIFT = 5
BITS_DOOR_LOCK_TYPE = 0x20
BITS_DOOR_LOCK_TYPE_SHIFT = 6
BITS_DOOR_LOCK_SKULL_IS_CARD = 0x200
BITS_DOOR_LOCK_SKULL_IS_CARD_SHIFT = 9

BITS_LIFT_MONSTER = 0x20
BITS_LIFT_MONSTER_SHIFT = 05
BITS_LIFT_DELAY = 0xc0
BITS_LIFT_DELAY_SHIFT = 6
BITS_LIFT_TARGET = 0x300
BITS_LIFT_TARGET_SHIFT = 8

BITS_STAIRS_MONSTER = 0x20
BITS_STAIRS_MONSTER_SHIFT = 5
BITS_STAIRS_STEP = 0xc0
BITS_STAIRS_STEP_SHIFT = 6
BITS_STAIRS_DIRECTION = 0x100
BITS_STAIRS_DIRECTION_SHIFT = 8
BITS_STAIRS_IGNORE_FLOOR = 0x200
BITS_STAIRS_IGNORE_FLOOR_SHIFT = 9

BITS_CRUSHER_MONSTER = 0x20
BITS_CRUSHER_MONSTER_SHIFT = 5
BITS_CRUSHER_SILENT = 0x40
BITS_CRUSHER_SILENT_SHIFT = 6


def is_boom_action(index):
    return index >= 0x2f80 and index < 0x8000
    

def parse_boom_action(index):
    action = Action()
    
    # Floors.
    if index >= 0x6000 and index < 0x8000:
        action.type = Action.TYPE_FLOOR
        index -= 0x6000
        action.activation, action.flags = get_boom_activation(index)
        parse_boom_floor(index, action)
                    
    # Ceilings.
    elif index >= 0x4000 and index < 0x6000:
        action.type = Action.TYPE_CEILING
        index -= 0x4000
        action.activation, action.flags = get_boom_activation(index)
        parse_boom_ceiling(index, action)
        
    # Doors.
    elif index >= 0x3c00 and index < 0x4000:
        action.type = Action.TYPE_DOOR
        index -= 0x3c00
        action.activation, action.flags = get_boom_activation(index)
        parse_boom_door(index, action)
        
    # Locked doors.
    elif index >= 0x3800 and index < 0x3c00:
        action.type = Action.TYPE_DOOR_LOCKED
        index -= 0x3800
        action.activation, action.flags = get_boom_activation(index)
        parse_boom_locked_door(index, action)
        
    # Lifts.
    elif index >= 0x3400 and index < 0x3800:
        action.type = Action.TYPE_LIFT
        index -= 0x3400
        action.activation, action.flags = get_boom_activation(index)
        parse_boom_lift(index, action)
        
    # Stairs.
    elif index >= 0x3000 and index < 0x3400:
        action.type = Action.TYPE_STAIRS
        index -= 0x3000
        action.activation, action.flags = get_boom_activation(index)
        parse_boom_stairs(index, action)

    # Crushers.
    elif index >= 0x2f80 and index < 0x3000:
        action.type = Action.TYPE_CRUSHER
        index -= 0x2f80
        action.activation, action.flags = get_boom_activation(index)
        parse_boom_crusher(index, action)
        
    else:
        return None

    return action


def parse_boom_crusher(self, index, action):
        if ((index >> BITS_CRUSHER_MONSTER) & BITS_CRUSHER_MONSTER) != 0:
            action.flags |= Action.FLAG_MONSTER
            
        if ((index >> BITS_CRUSHER_SILENT) & BITS_CRUSHER_SILENT) != 0:
            action.flags |= Action.FLAG_SILENT
    
    
def parse_boom_stairs(self, index, action):
    if ((index >> BITS_STAIRS_IGNORE_FLOOR_SHIFT) & BITS_STAIRS_IGNORE_FLOOR) != 0:
        action.flags |= Action.FLAG_IGNORE_FLOOR
    
    if ((index >> BITS_STAIRS_DIRECTION_SHIFT) & BITS_STAIRS_DIRECTION) != 0:
        action.direction = Action.MOVE_UP
    else:
        action.direction = Action.MOVE_DOWN
    
    step = ((index >> BITS_STAIRS_STEP_SHIFT) & BITS_STAIRS_STEP)
    if step == 0:
        action.move_amount = 4
    elif step == 1:
        action.move_amount = 8
    elif step == 2:
        action.move_amount = 16
    elif step == 3:
        action.move_amount = 24
    
    if ((index >> BITS_STAIRS_MONSTER_SHIFT) & BITS_STAIRS_MONSTER) != 0:
        action.flags |= Action.FLAG_MONSTER
    
    if ((index >> BITS_STAIRS_IGNORE_FLOOR_SHIFT) & BITS_STAIRS_IGNORE_FLOOR) != 0:
        action.flags |= Action.FLAG_IGNORE_FLOOR


def parse_boom_lift(self, index, action):
    delay = ((index >> BITS_LIFT_DELAY_SHIFT) & BITS_LIFT_DELAY)
    if delay == 0:
        action.delay = 1
    elif delay == 1:
        action.delay = 3
    elif delay == 2:
        action.delay = 5
    elif delay == 3:
        action.delay = 10
    
    if ((index >> BITS_LIFT_MONSTER_SHIFT) & BITS_LIFT_MONSTER) != 0:
        action.flags |= Action.FLAG_MONSTER

    kind = ((index >> BITS_LIFT_TARGET_SHIFT) & BITS_LIFT_TARGET)
    if kind == 0:
        action.target = Action.TARGET_LOWEST_NEIGHBOUR_FLOOR
    elif kind == 1:
        action.target = Action.TARGET_NEXT_NEIGHBOUR_FLOOR
    elif kind == 2:
        action.target = Action.TARGET_LOWEST_NEIGHBOUR_CEILING
    elif kind == 3:
        action.target = Action.TARGET_LOWEST_AND_HIGHEST


def parse_boom_door(self, index, action):
    delay = ((index >> BITS_DOOR_DELAY_SHIFT) & BITS_DOOR_DELAY)
    if delay == 0:
        action.delay = 1
    elif delay == 1:
        action.delay = 4
    elif delay == 2:
        action.delay = 9
    elif delay == 3:
        action.delay = 30
        
    if ((index >> BITS_DOOR_MONSTER_SHIFT) & BITS_DOOR_MONSTER) != 0:
        action.flags |= Action.FLAG_MONSTER
        
    kind = ((index >> BITS_DOOR_KIND_SHIFT) & BITS_DOOR_KIND)
    if kind == 0:
        action.kind = Action.DOOR_OPEN_WAIT_CLOSE
    elif kind == 1:
        action.kind = Action.DOOR_OPEN_STAY
    elif kind == 2:
        action.kind = Action.DOOR_CLOSE_STAY
    elif kind == 3:
        action.kind = Action.DOOR_CLOSE_WAIT_OPEN


def parse_boom_locked_door(self, index, action):       
    kind = ((index >> BITS_DOOR_LOCK_KIND_SHIFT) & BITS_DOOR_LOCK_KIND)
    if kind == 0:
        action.kind = Action.DOOR_OPEN_WAIT_CLOSE
    elif kind == 1:
        action.kind = Action.DOOR_OPEN_STAY
    elif kind == 2:
        action.kind = Action.DOOR_CLOSE_STAY
    elif kind == 3:
        action.kind = Action.DOOR_CLOSE_WAIT_OPEN
    
    lock = ((index >> BITS_DOOR_LOCK_TYPE_SHIFT) & BITS_DOOR_LOCK_TYPE)
    if lock == 0:
        action.key_flags = Action.KEY_ANY
    elif lock == 1:
        action.key_flags = Action.KEY_CARD_RED
    elif lock == 2:
        action.key_flags = Action.KEY_CARD_BLUE
    elif lock == 3:
        action.key_flags = Action.KEY_CARD_YELLOW
    elif lock == 4:
        action.key_flags = Action.KEY_SKULL_RED
    elif lock == 5:
        action.key_flags = Action.KEY_SKULL_BLUE
    elif lock == 6:
        action.key_flags = Action.KEY_SKULL_YELLOW
    elif lock == 7:
        action.key_flags = Action.KEY_ALL
    
    if ((index >> BITS_DOOR_LOCK_SKULL_IS_CARD_SHIFT) & BITS_DOOR_LOCK_SKULL_IS_CARD) != 0:
        action.key_flags |= Action.KEY_SKULLS_ARE_CARDS


def parse_boom_ceiling(self, index, action):
    if ((index >> BITS_CEILING_DIRECTION_SHIFT) & BITS_CEILING_DIRECTION) != 0:
        action.direction = Action.MOVE_UP
    else:
        action.direction = Action.MOVE_DOWN
    
    change = ((index >> BITS_CEILING_CHANGE_SHIFT) & BITS_CEILING_CHANGE) 
    if change == 1:
        action.change_flags = Action.CHANGE_TEXTURE
    elif change == 2:
        action.change_flags = Action.CHANGE_TEXTURE | Action.CHANGE_REMOVE_TYPE
    elif change == 3:
        action.change_flags = Action.CHANGE_TEXTURE | Action.CHANGE_TYPE
    
    target = ((index >> BITS_CEILING_TARGET_SHIFT) & BITS_CEILING_TARGET) 
    if target == 0:
        action.target = Action.TARGET_LOWEST_NEIGHBOUR_CEILING
    elif target == 1:
        action.target = Action.TARGET_NEXT_NEIGHBOUR_CEILING
    elif target == 2:
        action.target = Action.TARGET_LOWEST_NEIGHBOUR_CEILING
    elif target == 3:
        action.target = Action.TARGET_HIGHEST_NEIGHBOUR_FLOOR
    elif target == 4:
        action.target = Action.TARGET_FLOOR
    elif target == 5:
        action.target = Action.TARGET_NONE
        action.move_amount = 24
    elif target == 6:
        action.target = Action.TARGET_NONE
        action.move_amount = 32
    elif target == 7:
        action.target = Action.TARGET_SHORTEST_UPPER_TEXTURE
    
    model = ((index >> BITS_CEILING_MODEL_SHIFT) & BITS_CEILING_MODEL)
    if model == 0:
        action.model = Action.MODEL_TRIGGER
    elif model == 1:
        action.model = Action.MODEL_NUMERIC
    
    if ((index >> BITS_CEILING_CRUSH_SHIFT) & BITS_CEILING_CRUSH) != 0:
        action.flags |= Action.FLAG_CRUSHES


def parse_boom_floor(self, index, action):
    if ((index >> BITS_FLOOR_DIRECTION_SHIFT) & BITS_FLOOR_DIRECTION) != 0:
        action.direction = Action.MOVE_UP
    else:
        action.direction = Action.MOVE_DOWN
        
    change = ((index >> BITS_FLOOR_CHANGE_SHIFT) & BITS_FLOOR_CHANGE) 
    if change == 1:
        action.change_flags = Action.CHANGE_TEXTURE
    elif change == 2:
        action.change_flags = Action.CHANGE_TEXTURE | Action.CHANGE_REMOVE_TYPE
    elif change == 3:
        action.change_flags = Action.CHANGE_TEXTURE | Action.CHANGE_TYPE
    
    target = ((index >> BITS_FLOOR_TARGET_SHIFT) & BITS_FLOOR_TARGET) 
    if target == 0:
        action.target = Action.TARGET_LOWEST_NEIGHBOUR_FLOOR
    elif target == 1:
        action.target = Action.TARGET_NEXT_NEIGHBOUR_FLOOR
    elif target == 2:
        action.target = Action.TARGET_LOWEST_NEIGHBOUR_CEILING
    elif target == 3:
        action.target = Action.TARGET_HIGHEST_NEIGHBOUR_FLOOR
    elif target == 4:
        action.target = Action.TARGET_CEILING
    elif target == 5:
        action.target = Action.TARGET_NONE
        action.move_amount = 24
    elif target == 6:
        action.target = Action.TARGET_NONE
        action.move_amount = 32
    elif target == 7:
        action.target = Action.TARGET_SHORTEST_LOWER_TEXTURE
    
    model = ((index >> BITS_FLOOR_MODEL_SHIFT) & BITS_FLOOR_MODEL)
    if model == 0:
        action.model = Action.MODEL_TRIGGER
    elif model == 1:
        action.model = Action.MODEL_NUMERIC
        
    if ((index >> BITS_FLOOR_CRUSH_SHIFT) & BITS_FLOOR_CRUSH) != 0:
        action.flags |= Action.FLAG_CRUSHES


def get_boom_activation(self, index):
    index = (index & BITS_TRIGGER)
    if index == 0:
        return Action.ACTIVATE_WALK, Action.FLAG_ONCE
    elif index == 1:
        return Action.ACTIVATE_WALK, 0
    elif index == 2:
        return Action.ACTIVATE_SWITCH, Action.FLAG_ONCE
    elif index == 3:
        return Action.ACTIVATE_SWITCH, 0
    elif index == 4:
        return Action.ACTIVATE_SHOOT, Action.FLAG_ONCE
    elif index == 5:
        return Action.ACTIVATE_SHOOT, 0
    elif index == 6:
        return Action.ACTIVATE_PUSH, Action.FLAG_ONCE
    elif index == 7:
        return Action.ACTIVATE_PUSH, 0