from doom.actions import boom
from doom.actions.action import Action


type_mapping = {
    'door': Action.TYPE_DOOR,
    'floor': Action.TYPE_FLOOR,
    'ceiling': Action.TYPE_CEILING,
    'crusher': Action.TYPE_CRUSHER,
    'teleporter': Action.TYPE_TELEPORTER,
    'donut': Action.TYPE_DONUT,
    'stairs': Action.TYPE_STAIRS,
    'lift': Action.TYPE_LIFT,
    'elevator': Action.TYPE_ELEVATOR,
    'exit': Action.TYPE_EXIT,
    'lockeddoor': Action.TYPE_DOOR_LOCKED,
    'light': Action.TYPE_LIGHT
}

activate_mapping = {
    'push': Action.ACTIVATE_PUSH,
    'switch': Action.ACTIVATE_SWITCH,
    'walk': Action.ACTIVATE_WALK,
    'shoot': Action.ACTIVATE_SHOOT,
    'bump': Action.ACTIVATE_BUMP,
    'passthrough': Action.ACTIVATE_PASSTHROUGH,
}
    
movement_mapping = {
    'up': Action.MOVE_UP,
    'down': Action.MOVE_DOWN
}
        
door_mapping = {
    'openwaitclose': Action.DOOR_OPEN_WAIT_CLOSE,
    'openstay': Action.DOOR_OPEN_STAY,
    'closestay': Action.DOOR_CLOSE_STAY,
    'closewaitopen': Action.DOOR_CLOSE_WAIT_OPEN,
}
    
key_flags_mapping = {
    'cardblue': Action.KEY_CARD_BLUE,
    'cardred': Action.KEY_CARD_RED,
    'cardyellow': Action.KEY_CARD_YELLOW,
    'skullblue': Action.KEY_SKULL_BLUE,
    'skullred': Action.KEY_SKULL_RED,
    'skullyellow': Action.KEY_SKULL_YELLOW,
    'all': Action.KEY_ALL,
    'any': Action.KEY_ANY,
    'skulliscard': Action.KEY_SKULLS_ARE_CARDS
}

target_mapping = {
    'lowestneighbourceiling': Action.TARGET_LOWEST_NEIGHBOUR_CEILING,
    'lowestneighbourceiling8': Action.TARGET_LOWEST_NEIGHBOUR_CEILING8,
    'lowestneighbourfloor': Action.TARGET_LOWEST_NEIGHBOUR_FLOOR,
    'lowestneighbourfloor8': Action.TARGET_LOWEST_NEIGHBOUR_FLOOR8,
    'nextneighbourceiling': Action.TARGET_NEXT_NEIGHBOUR_CEILING,
    'nextneighbourfloor': Action.TARGET_NEXT_NEIGHBOUR_FLOOR,
    'highestneighbourceiling': Action.TARGET_HIGHEST_NEIGHBOUR_CEILING,
    'highestneighbourceiling8': Action.TARGET_HIGHEST_NEIGHBOUR_CEILING8,
    'highestneighbourfloor': Action.TARGET_HIGHEST_NEIGHBOUR_FLOOR,
    'highestneighbourfloor8': Action.TARGET_HIGHEST_NEIGHBOUR_FLOOR8,
    'shortestlower': Action.TARGET_SHORTEST_LOWER_TEXTURE,
    'targetceiling': Action.TARGET_CEILING,
    'targetceiling8': Action.TARGET_CEILING8,
    'targetfloor': Action.TARGET_FLOOR,
    'targetfloor8': Action.TARGET_FLOOR8,
    'currentfloor': Action.TARGET_CURRENT_FLOOR,
    'nextlowestfloor': Action.TARGET_NEXT_LOWEST_FLOOR,
    'nexthighestfloor': Action.TARGET_NEXT_HIGHEST_FLOOR,
    'nextfloor': Action.TARGET_NEXT_FLOOR,
    'lowestandhighest': Action.TARGET_LOWEST_AND_HIGHEST,
    'shortestupper': Action.TARGET_SHORTEST_UPPER_TEXTURE
}

change_flags_mapping = {
    'changetexture': Action.CHANGE_TEXTURE,
    'changetype': Action.CHANGE_TYPE,
    'removetype': Action.CHANGE_REMOVE_TYPE
}
    
model_mapping = {
    'numeric': Action.MODEL_NUMERIC,
    'trigger': Action.MODEL_TRIGGER
}
        
teleport_mapping = {
    'thing': Action.TELEPORT_THING,
    'line': Action.TELEPORT_LINE,
    'linereversed': Action.TELEPORT_LINE_REVERSED
}

light_mapping = {
    'light35': Action.LIGHT_35,
    'light255': Action.LIGHT_255,
    'blink': Action.LIGHT_BLINK,
    'minneighbour': Action.LIGHT_MIN_NEIGHBOUR,
    'maxneighbour': Action.LIGHT_MAX_NEIGHBOUR,
    'lowestneighbour': Action.LIGHT_LOWEST_NEIGHBOUR
}

# Movement speed units\tic mapping.
speed_mapping = {
    'slow': 2,
    'normal': 4,
    'fast': 8,
    'turbo': 16,
    'instant': 0
}

# Waiting time tic mapping.
wait_mapping = {
    'wait1': 35,
    'wait3': 105,
    'wait4': 140,
    'wait5': 175,
    'wait9': 315,
    'wait10': 350,
    'wait30': 1050
}

# Movement distance mapping.
distance_mapping = {
    'move4': 4,
    'move8': 8,
    'move16': 16,
    'move24': 24,
    'move32': 32,
    'move512': 512
}

flags_mapping = {
    'once': Action.FLAG_ONCE,
    'noplayer': Action.FLAG_NO_PLAYER,
    'monster': Action.FLAG_MONSTER,
    'crush': Action.FLAG_CRUSHES,
    'start': Action.FLAG_STARTS,
    'stop': Action.FLAG_STOPS,
    'silent': Action.FLAG_SILENT,
    'secret': Action.FLAG_SECRET_EXIT,
    'ignorefloor': Action.FLAG_IGNORE_FLOOR,
    'preserveangle': Action.FLAG_PRESERVE_ANGLE,
    'player': Action.FLAG_PLAYER,
    'projectile': Action.FLAG_PROJECTILE
}


class ActionList(object):
    
    def __init__(self):
        self.actions = {}
    
    
    def add(self, index, keywords):
        action = Action()
        action.index = index
        action.flag = Action.FLAG_PLAYER | Action.FLAG_PROJECTILE
        
        for keyword in keywords.split(','):
            if keyword in type_mapping:
                action.type = type_mapping[keyword]
            elif keyword in activate_mapping:
                action.activation = activate_mapping[keyword]
            elif keyword in movement_mapping:
                action.direction = movement_mapping[keyword]
            elif keyword in door_mapping:
                action.door_type = door_mapping[keyword]
            elif keyword in key_flags_mapping:
                action.key_flags |= key_flags_mapping[keyword]
            elif keyword in target_mapping:
                action.target = target_mapping[keyword]
            elif keyword in change_flags_mapping:
                action.change_flags |= change_flags_mapping[keyword]
            elif keyword in model_mapping:
                action.model = model_mapping[keyword]
            elif keyword in teleport_mapping:
                action.teleport_type = teleport_mapping[keyword]
            elif keyword in flags_mapping:
                action.flags |= flags_mapping[keyword]
            elif keyword in speed_mapping:
                action.speed = speed_mapping[keyword]
            elif keyword in wait_mapping:
                action.wait_time = wait_mapping[keyword]
            elif keyword in distance_mapping:
                action.move_amount = distance_mapping[keyword]
            elif keyword in light_mapping:
                action.light_change = light_mapping[keyword]
            else:
                print 'Unknown action keyword "{}".'.format(keyword)
        
        self.actions[index] = action
    
    
    def get(self, action_index):
        if action_index == 0:
            return None
        
        # Return an action from the known list.
        if action_index in self.actions:
            return self.actions[action_index]
        
        # Ignore non-generalized types.
        if boom.is_boom_action(action_index) == True:
            action = boom.parse_boom_action(action_index)
        else:
            return None
                
        # Remember new generalized action.
        self.actions[action_index] = action
        
        return action