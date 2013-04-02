import heapq


class PriorityQueue(object):
    
    def __init__(self):
        self.item_list = []
        self.item_set = set()
    
        
    def add(self, item):
        heapq.heappush(self.item_list, item)
        self.item_set.add(item)
    
    
    def remove(self, item):
        self.item_list.remove(item)
        self.item_set.remove(item)
    
    
    def lowest(self):
        return self.item_list[0]
    
    
    def __len__(self):
        return len(self.item_list)
    
    
    def __contains__(self, item):
        return item in self.item_set