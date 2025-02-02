from .transaction import Transaction
from .event import Event
from .block import Block
from collections import defaultdict
import random

class Peer:
    def __init__(self, peer_id, is_slow, is_low_cpu):
        self.peer_id = peer_id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.coins = 0  # Initial coin balance (assumed)
        self.known_peer_ids = []
        self.neighbors = []
        self.sent_transactions = defaultdict(set)  # {txn_id: set(peer_ids)}
        self.block_tree = {
            Block.GENESIS.id: {
                'block': Block.GENESIS,
                'parent': None,
                'children': [],
                'depth': 0,
                'arrival_time': 0
            }
        }
        self.longest_chain_tip = Block.GENESIS.id
        self.pending_transactions = set()
        self.current_mining_event = None
        self.total_blocks_mined = 0
        self.hashing_power = 0
    
    def generate_transaction_handler(self, Ttx):
        def handler(current_time, event_queue):
            if self.coins > 0:
                amount = random.randint(1, self.coins)
                recipient = random.choice(self.known_peer_ids)
                transaction = Transaction(self.id, recipient, amount)
                # Schedule receive of the current transaction
                self.receive_transaction(transaction,self.peer_id,current_time,event_queue)
                print(f"Time {current_time:.2f}: Peer {self.id} generated {transaction}")
            # Schedule next transaction
            delay = random.expovariate(1.0 / Ttx)
            event_queue.add_event(Event(
                current_time + delay,
                self.generate_transaction_handler(Ttx)
            ))
            

        return handler
    
    def calculate_latency(self, peer_id, msg_bits):
        link = (self.peer_id, peer_id)
        rho, c = self.network.link_params[link]
        
        # Queuing delay calculation
        mean_d = (96_000)/c  # 96kbits/c bits-per-second = seconds
        d = random.expovariate(1/mean_d)
        
        return rho + (msg_bits/c) + d
    
    def receive_transaction(self, transaction, sender_id, current_time, event_queue):
        if transaction.txn_id not in self.received_txns:
            self.received_txns.add(transaction.txn_id)
            
            # Forward to all connected peers except sender
            neighbors = self.neighbors
            for neighbor in neighbors:
                if neighbor != sender_id and \
                   neighbor not in self.sent_transactions[transaction.txn_id]:
                    
                    # Calculate latency
                    msg_bits = transaction.size * 8_000  # 1KB = 8000 bits
                    latency = self.calculate_latency(neighbor, msg_bits)
                    
                    # Schedule receive event
                    event_queue.add_event(Event(
                        timestamp=current_time + latency,
                        callback=lambda t, q: self.network.peers[neighbor]
                            .receive_transaction(transaction, self.peer_id, t, q),
                        msg=transaction
                    ))
                    self.sent_transactions[transaction.txn_id].add(neighbor)
    
    # Mining logic


    def schedule_mining(self, current_time, event_queue, I=600):
        if self.current_mining_event:
            return  # Already mining
        
        hk = self.hashing_power
        Tk = random.expovariate(hk/I)

        # Select transactions from pending pool
        max_txns = min(1023, len(self.pending_transactions))  # Max 1023 txns + coinbase
        selected_txns = random.sample(self.pending_transactions, max_txns)
        
        # Create coinbase transaction
        coinbase = Transaction(self.id, self.id, 50)
        
        # Create block
        new_block = Block(
            prev_id=self.longest_chain_tip,
            transactions=selected_txns + [coinbase],
            miner_id=self.id
        )
        
        self.current_mining_event = Event(
            current_time + Tk,
            self.mine_block_callback,
            msg={
                "block":new_block,
                "longest_chain_tip":self.longest_chain_tip
            }
        )
        event_queue.add_event(self.current_mining_event)
        
    def mine_block_callback(self, current_time, event_queue,event):
        new_block,longest_chain_tip = event.msg.values()
        if new_block.is_valid_size() and self.longest_chain_tip==longest_chain_tip:
            self.block_tree[new_block.id] = {
            'block': new_block,
            'parent': new_block.prev_id,
            'children': [],
            'arrival_time': current_time,
            'depth': self.block_tree[new_block.prev_id]['depth'] + 1
            }
            self.block_tree[new_block.prev_id]['children'].append(new_block.id)
            self.broadcast_block(new_block, current_time, event_queue)
            self.schedule_mining(current_time,event_queue)
            self.total_blocks_mined += 1
        
        self.current_mining_event = None
    
    def broadcast_block(self,new_block,current_time,event_queue):
        neighbors = self.neighbors
        for neighbor in neighbors:
            if neighbor != self.peer_id:
                
                # Calculate latency
                msg_bits = new_block.size * 8_000  # 1KB = 8000 bits
                latency = self.calculate_latency(neighbor, msg_bits)
                
                # Schedule receive event
                event_queue.add_event(Event(
                    timestamp=current_time + latency,
                    callback=lambda t, q: self.network.peers[neighbor]
                        .receive_block(new_block, self.peer_id, t, q),
                    msg=new_block
                ))
        
    

        
    # Block validation and propagation
    def receive_block(self, block, sender_id, current_time, event_queue):
        if block.id in self.block_tree:
            return
        
        # Store block in tree
        self.block_tree[block.id] = {
            'block': block,
            'parent': block.prev_id,
            'children': [],
            'arrival_time': current_time,
            'depth': self.block_tree[block.prev_id]['depth'] + 1
        }
        self.block_tree[block.prev_id]['children'].append(block.id)
        
        # Validate transactions
        if self.validate_block(block):
            if self.block_tree[block.id]['depth'] > self.block_tree[self.longest_chain_tip]['depth']:
                self.longest_chain_tip = block.id
                self.schedule_mining(current_time, event_queue)
        
        # Propagate block
        self.broadcast_block(block, current_time, event_queue)
        
    def validate_block(self, block):
        # Check transaction balances using longest chain
        balances = self.calculate_balances()
        for txn in block.transactions:
            if txn.sender_id not in balances or balances[txn.sender_id] < txn.amount:
                return False
            balances[txn.sender_id] -= txn.amount
        return True
    
    def calculate_balances(self):
        # Traverse longest chain to calculate current balances
        balances = defaultdict(int)
        current_block_id = self.longest_chain_tip
        
        while current_block_id != Block.GENESIS.id:
            block = self.block_tree[current_block_id]['block']
            for txn in block.transactions:
                if txn.sender_id == txn.recipient_id:  # Coinbase
                    balances[txn.sender_id] += txn.amount
                else:
                    balances[txn.sender_id] -= txn.amount
                    balances[txn.recipient_id] += txn.amount
            current_block_id = block.prev_id
        
        return balances