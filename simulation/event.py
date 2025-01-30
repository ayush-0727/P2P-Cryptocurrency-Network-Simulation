import heapq

class Event:
    def __init__(self, timestamp, callback, msg = None):
        self.timestamp = timestamp
        self.callback = callback  # Signature: callback(current_time, event_queue)
        self.msg = msg  # Store message details

class EventQueue:
    def __init__(self):
        self.events = []
        self.counter = 0  # For stable sorting
    
    def add_event(self, event):
        heapq.heappush(self.events, (event.timestamp, self.counter, event))
        self.counter += 1
    
    def next_event(self):
        if self.events:
            return heapq.heappop(self.events)[2]
        return None