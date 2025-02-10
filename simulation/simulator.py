# from .event import EventQueue
# from .event import Event
# import os

# class Simulator:
#     def __init__(self, network, Ttx,I, max_time):
#         self.network = network
#         self.Ttx = Ttx
#         self.I = I
#         self.max_time = max_time
#         self.event_queue = EventQueue()
    
#     def initialize_events(self):
#         for peer in self.network.peers:
#             peer.schedule_transactions(self.event_queue,self.Ttx)
#             peer.schedule_mining(0,self.event_queue)
    
#     def run(self):
#         while (event := self.event_queue.next_event()) is not None:
#             if event.timestamp > self.max_time:
#                 break
#             event.callback(event.timestamp, self.event_queue,event)
        
#         self.save_blockchain_trees()
            
        
#     def save_blockchain_trees(self):
#         os.makedirs("blockchain", exist_ok=True)
#         for peer in self.network.peers:
#             with open(f'blockchain/peer_{peer.peer_id}.txt', 'w') as f:
#                 for blk_id, data in peer.block_tree.items():
#                     f.write(f"{blk_id}|{data['parent']}|{data['arrival_time']}\n")


from .event import EventQueue
from .event import Event
import os
import pandas as pd
from collections import defaultdict


class Simulator:
    def __init__(self, network, Ttx, I, max_time):
        self.network = network
        self.Ttx = Ttx
        self.I = I
        self.max_time = max_time
        self.event_queue = EventQueue()
    
    def initialize_events(self):
        for peer in self.network.peers:
            peer.schedule_transactions(self.event_queue, self.Ttx)
            peer.schedule_mining(0, self.event_queue)
    
    def run(self):
        while (event := self.event_queue.next_event()) is not None:
            if event.timestamp > self.max_time:
                break
            event.callback(event.timestamp, self.event_queue, event)
        
        self.save_blockchain_trees()
        self.generate_statistics_table()
        
    def save_blockchain_trees(self):
        os.makedirs("blockchain", exist_ok=True)
        for peer in self.network.peers:
            with open(f'blockchain/peer_{peer.peer_id}.txt', 'w') as f:
                for blk_id, data in peer.block_tree.items():
                    f.write(f"{blk_id}|{data['parent']}|{data['arrival_time']}\n")
    

    def generate_statistics_table(self):
        data = []
        blocks_in_longest_chain = self.get_longest_chain_blocks()  # Get blocks mined in longest chain per peer

        for peer in self.network.peers:
            node_id = peer.peer_id
            hashing_power = peer.hashing_power
            speed = "low cpu" if peer.is_low_cpu else "high cpu"
            total_blocks_mined = peer.total_blocks_mined
            total_blocks_in_longest_chain = blocks_in_longest_chain.get(node_id, 0)  # Handle missing peers safely
            ratio = total_blocks_in_longest_chain / total_blocks_mined if total_blocks_mined > 0 else 0

            data.append([node_id, hashing_power, speed, total_blocks_mined, total_blocks_in_longest_chain, ratio])

        df = pd.DataFrame(data, columns=[
            "Node No", "Hashing Power", "Speed", "Blocks Mined", "Blocks in Longest Chain", "Ratio"])

        print("\nSimulation Results:")
        print(df.to_string(index=False))
        df.to_csv("simulation_results.csv", index=False)

    def get_longest_chain_blocks(self):
        blocks_created_by_peer = defaultdict(int)
        current_block = self.network.peers[0]._longest_chain_tip  # Start from longest chain tip

        while current_block and current_block.miner_id != "GENESIS":
            miner_id = current_block.miner_id  # Get the miner ID
            blocks_created_by_peer[miner_id] += 1  # Increment count for miner

            parent_id = self.network.peers[0].block_tree[current_block.id]['parent']  # Get parent block ID
            if parent_id:
                current_block = self.network.peers[0].block_tree[parent_id]['block']  # Get parent block object
            else:
                break  # Reached genesis
            
        return dict(blocks_created_by_peer)  # Convert to normal dict


