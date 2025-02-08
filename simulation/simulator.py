from .event import EventQueue
from .event import Event
import os

class Simulator:
    def __init__(self, network, Ttx,I, max_time):
        self.network = network
        self.Ttx = Ttx
        self.I = I
        self.max_time = max_time
        self.event_queue = EventQueue()
    
    def initialize_events(self):
        for peer in self.network.peers:
            # peer.schedule_transactions(self.event_queue,self.Ttx)
            peer.schedule_mining(0,self.event_queue)
    
    def run(self):
        while (event := self.event_queue.next_event()) is not None:
            if event.timestamp > self.max_time:
                break
            event.callback(event.timestamp, self.event_queue,event)
        
        self.save_blockchain_trees()
            
        
    def save_blockchain_trees(self):
        os.makedirs("blockchain", exist_ok=True)
        for peer in self.network.peers:
            with open(f'blockchain/peer_{peer.peer_id}.txt', 'w') as f:
                for blk_id, data in peer.block_tree.items():
                    f.write(f"{blk_id}|{data['parent']}|{data['arrival_time']}\n")