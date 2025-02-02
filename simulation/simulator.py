from .event import EventQueue
import os

class Simulator:
    def __init__(self, network, Ttx):
        self.network = network
        self.Ttx = Ttx
        self.event_queue = EventQueue()
    
    def initialize_events(self):
        for peer in self.network.peers:
            peer.generate_transaction_handler(self.Ttx)(0, self.event_queue)
            peer.schedule_mining(0,self.event_queue)
    
    def run(self, max_time=100):
        while (event := self.event_queue.next_event()) is not None:
            if event.timestamp > max_time:
                break
            event.callback(event.timestamp, self.event_queue,event)
            self.save_blockchain_trees()
            
        
    def save_blockchain_trees(self):
        os.makedirs("blockchain", exist_ok=True)
        for peer in self.network.peers:
            with open(f'blockchain/peer_{peer.peer_id}.txt', 'w') as f:
                for blk_id, data in peer.block_tree.items():
                    f.write(f"{blk_id}|{data['parent']}|{data['arrival_time']}\n")