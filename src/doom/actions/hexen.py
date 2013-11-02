from doom.actions.action import Action
from doom.map.objects import Linedef


class HexenActionTypes(object):
    
    function_map = {
        10: act_door_close,
        11: act_door_open, 
    }
    
    def __init__(self, action_types):
        self.action_types = action_types
        
    
    def get(self, linedef):
        index = linedef.action
        args = linedef.args
        
        func = self.function_map.get(index)
        if func is None:
            return None
        
        action = Action()
        action.index = index
        
        if (linedef.flags & Linedef.FLAG_HEXEN_PLAYERUSE) != 0:
            action.activation |= Action.ACTIVATE_SWITCH
            action.flags |= Action.FLAG_PLAYER
        elif (linedef.flags & Linedef.FLAG_HEXEN_PLAYERBUMP) != 0:
            action.activation |= Action.ACTIVATE_BUMP
            action.flags |= Action.FLAG_PLAYER
        elif (linedef.flags & Linedef.FLAG_HEXEN_PROJECTILECROSS) != 0:
            action.activation |= Action.ACTIVATE_WALK
            action.flags |= Action.FLAG_PROJECTILE
        elif (linedef.flags & Linedef.FLAG_HEXEN_PLAYERSANDMONSTERS) != 0:
            action.flags |= Action.FLAG_MONSTER | Action.FLAG_PLAYER
        elif (linedef.flags & Linedef.FLAG_HEXEN_REPEATEDUSE) == 0:
            action.flags |= Action.FLAG_ONCE
        
        return func(self, action, args)
        
        
    def act_door_open(self, action, args):
        action.type = Action.TYPE_DOOR
        action.tag = args[0]
        action.speed = args[1]
        action.lighttag = args[2]
        
        return action
    
    
    def act_door_close(self, action, args):
        action.type = Action.TYPE_DOOR
        action.tag = 0