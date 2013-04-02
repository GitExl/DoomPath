import heapq


class PriorityQueue(object):
    
    def __init__(self):
        self.item_list = []
        self.item_set = set()
    
        
    def push(self, item):
        heapq.heappush(self.item_list, item)
        self.item_set.add(item)
    
    
    def pop_lowest(self):
        return heapq.heappop(self.item_list)


    def __len__(self):
        return len(self.item_list)
    
    
    def __contains__(self, item):
        return item in self.item_set