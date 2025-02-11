from simulation.transaction import Transaction
from simulation.event import Event
from simulation.block import Block
from collections import defaultdict
import copy
import random

class Peer:
    def __init__(self,is_low_cpu,is_slow,I,peer_id, link_params):
        self.peer_id = peer_id
        self.is_low_cpu = is_low_cpu
        self.is_slow = is_slow  
        self.I = I
        
        self.known_peer_ids = []
        self.neighbors = []
        
        self.received_txns = set()
        self.mempool = set()
        self.sent_transactions = defaultdict(set)

        self.balances = defaultdict(int)
        self.balance_cache = {}  # Cache computed balances for blocks

        genesis_blk = Block(
            prev_id=None,
            transactions=[],
            miner_id="GENESIS"
        )
        genesis_blk.id = "GENESIS"

        self.block_tree = {
            genesis_blk.id: {
                'block': genesis_blk,
                'parent': None,
                'children': [],
                'depth': 0,
                'arrival_time': 0
            }
        }
        self.orphaned_blks={}
        self.longest_chain_tip = genesis_blk

        self.current_mining_event = None
        self.total_blocks_mined = 0

        self.sent_blocks = defaultdict(set)
        
        self.hashing_power = 0
        
        self.longest_chain_txns = set()  # Stores transaction IDs in the longest chain
        
        self.link_params = link_params
        self.peers = []

    def calculate_latency(self, peer_id, msg_bits):
        link = (self.peer_id, peer_id)
        rho, c = self.link_params[link]
        
        mean_d = 96000 / c
        d = random.expovariate(1 / mean_d)
        
        return rho + (msg_bits / c) + d
    
    # --------------------------------------------------------
    # Transaction logic
    # --------------------------------------------------------

    def schedule_transactions(self,event_queue,Ttx):
        event = Event(timestamp=0,
                    callback=self.generate_transaction_handler(Ttx))
        event_queue.add_event(event)

    # Periodically generate random transactions
    def generate_transaction_handler(self, Ttx):
        def handler(current_time, event_queue, event):
            sender_balance = self.balances.get(self.peer_id,0)

            if sender_balance > 0:
                amount = random.randint(1, sender_balance)
                recipient = random.choice([
                    pid for pid in self.known_peer_ids if pid != self.peer_id
                ])
                transaction = Transaction(self.peer_id, recipient, amount)
                
                event.msg = transaction
                self.receive_transaction(current_time, event_queue, event)
                
                print(f"Time {current_time:.2f}: Peer {self.peer_id} generated {transaction}")
            
            # Schedule the next transaction after a delay
            delay = random.expovariate(1.0 / Ttx)
            event_queue.add_event(Event(
                current_time + delay,
                self.generate_transaction_handler(Ttx)
            ))
        return handler
    
    def receive_transaction(self, current_time, event_queue, event):
        transaction = event.msg
        sender_id = transaction.sender_id

        if not transaction or not sender_id:
            return
        
        if self.transaction_in_longest_chain(transaction):
            return
        
        if transaction.txn_id not in self.received_txns:
            self.received_txns.add(transaction.txn_id)
            self.mempool.add(transaction)

            # Forward to all connected peers except the one who sent it:
            for neighbor in self.neighbors:
                if neighbor != sender_id and neighbor not in self.sent_transactions[transaction.txn_id]:
                    # Calculate latency
                    msg_bits = transaction.size * 8
                    latency = self.calculate_latency(neighbor, msg_bits)
                    
                    event_queue.add_event(Event(
                        timestamp=current_time + latency,
                        callback=self.peers[neighbor].receive_transaction,
                        msg=transaction
                    ))
                    self.sent_transactions[transaction.txn_id].add(neighbor)
    
    # --------------------------------------------------------
    # Mining logic
    # --------------------------------------------------------
    def schedule_mining(self, current_time, event_queue):
        if self.current_mining_event:
            return
        
        # Create the block
        new_block = Block(
        prev_id=self.longest_chain_tip.id,
        transactions=[],
        miner_id=self.peer_id
        )
        # Create coinbase
        coinbase_tx = Transaction(
            sender_id=self.peer_id,
            recipient_id=self.peer_id,
            coinbase=True,
            amount=50
        )

        new_block.transactions.append(coinbase_tx)

        temp_balances = self.balances.copy()
        temp_balances[self.peer_id] += 50

        for txn in list(self.mempool):
            if self.transaction_in_longest_chain(txn):
                continue

            if txn.coinbase:
                temp_balances[txn.sender_id] += txn.amount
            else:
                if temp_balances[txn.sender_id] < txn.amount:
                    continue
                temp_balances[txn.sender_id] -= txn.amount
                temp_balances[txn.recipient_id] += txn.amount

            new_block.transactions.append(txn)

            if not new_block.is_valid_size():
                new_block.transactions.pop()
                break
        

        # Calculate Tk
        mean_time = self.I / self.hashing_power
        Tk = random.expovariate(1.0 / mean_time)
        
        self.current_mining_event = Event(
            timestamp=current_time+Tk,
            callback=self.mine_block_callback,
            msg=new_block
        )
        # Schedule the event of mine_block_callback at current_time + Tk
        event_queue.add_event(self.current_mining_event)
    
        
    def mine_block_callback(self, current_time, event_queue, event):
        if event != self.current_mining_event:
            return
        
        mined_block = event.msg
        self.current_mining_event = None
        
        # Add the node to the block tree
        parent_block = self.block_tree[mined_block.prev_id]
        new_depth = parent_block['depth'] + 1
        self.block_tree[mined_block.id] = {
            'block': mined_block,
            'parent': mined_block.prev_id,
            'children': [],
            'depth': new_depth,
            'arrival_time': current_time
        }

        print(f"Block mined by peer {self.peer_id} at time {current_time}s")
        parent_block['children'].append(mined_block.id)
        
        if mined_block.prev_id == self.longest_chain_tip.id:
            self.extend_longest_chain(mined_block)
        else:
            self.update_longest_chain(mined_block.id)
            
        # Update the longest tip
        self.update_canonical_chain(mined_block.id)
        
        # Remove those transactions from the mempool that have been included
        for tx in mined_block.transactions[1:]:
            if tx in self.mempool:
                self.mempool.remove(tx)
        
        self.total_blocks_mined += 1

        self.broadcast_block(mined_block, current_time, event_queue)

        self.schedule_mining(current_time, event_queue)

    
    def broadcast_block(self, new_block, current_time, event_queue):
        for neighbor in self.neighbors:
            if new_block.id in self.sent_blocks[neighbor]:
                continue  # Already sent, skip
            
            msg_bits = new_block.size * 8
            latency = self.calculate_latency(neighbor, msg_bits)
            event_queue.add_event(Event(
                timestamp=current_time + latency,
                callback=self.peers[neighbor].receive_block,
                msg=new_block
            ))
            self.sent_blocks[neighbor].add(new_block.id)
    
    
    def transaction_in_longest_chain(self, txn):
        return txn.txn_id in self.longest_chain_txns # O(1) lookup

    def extend_longest_chain(self, new_block):
         for tx in new_block.transactions:
             self.longest_chain_txns.add(tx.txn_id)

    def update_longest_chain(self, new_tip_id):
        self.longest_chain_txns.clear()  
        current_block_id = new_tip_id

        while current_block_id and current_block_id != "GENESIS":
            block = self.block_tree[current_block_id]['block']
            for tx in block.transactions:
                self.longest_chain_txns.add(tx.txn_id)  
            current_block_id = block.prev_id

    
    def receive_block(self,current_time, event_queue,event):
        block = event.msg
        if block.id in self.block_tree:
            return

        parent_id = block.prev_id
        if parent_id not in self.block_tree:
            self.orphaned_blks[block.id] = block  # Store in dict
            return
        
        if not self.validate_block(block):
            return
        
        if self.current_mining_event and block.prev_id == self.longest_chain_tip.id:
            self.current_mining_event = None
        

        # Insert the block to block tree
        parent_node = self.block_tree[parent_id]
        new_depth = parent_node['depth'] + 1
        
        self.block_tree[block.id] = {
            'block': block,
            'parent': parent_id,
            'children': [],
            'depth': new_depth,
            'arrival_time': current_time
        }
        parent_node['children'].append(block.id)

        if new_depth > self.block_tree[self.longest_chain_tip.id]['depth']:
            if parent_id == self.longest_chain_tip.id:
                self.extend_longest_chain(block)
            else:
                self.update_longest_chain(block.id)
                
            self.update_canonical_chain(block.id)
            for tx in block.transactions[1:]:
                if tx in self.mempool:
                    self.mempool.remove(tx)
            
            self.schedule_mining(current_time, event_queue)
        else:
            self.balance_cache[block.id] = self.calculate_balances_for_chain(block.id)
        
        self.process_orphan_blocks(current_time,event_queue)

        self.broadcast_block(block,current_time,event_queue)
    
    def find_common_ancestor(self, old_tip_id, new_tip_id):
        old_chain = set()
        current = old_tip_id
        while current:
            old_chain.add(current)
            current = self.block_tree[current]['parent']
        
        current = new_tip_id
        while current:
            if current in old_chain:
                return current
            current = self.block_tree[current]['parent']
        return None 

    def calculate_balances_for_chain_from(self, fork_point_id, tip_id):
        if fork_point_id in self.balance_cache:
            balances = self.balance_cache[fork_point_id].copy()
        else:
            balances = defaultdict(int)
        
        chain_segment = []
        current = tip_id
        while current and current != fork_point_id:
            chain_segment.append(current)
            current = self.block_tree[current]['parent']
        chain_segment.reverse() 
        
        for block_id in chain_segment:
            block = self.block_tree[block_id]['block']
            for tx in block.transactions:
                if tx.coinbase:
                    balances[tx.recipient_id] += tx.amount
                else:
                    balances[tx.sender_id] -= tx.amount
                    balances[tx.recipient_id] += tx.amount

            self.balance_cache[block_id] = balances.copy()
        
        return balances
    
    def update_canonical_chain(self, new_tip_id):
        old_tip_id = self.longest_chain_tip.id

        fork_point = self.find_common_ancestor(old_tip_id, new_tip_id)
        
        new_balances = self.calculate_balances_for_chain_from(fork_point, new_tip_id)
        
        self.balances = new_balances
        self.longest_chain_tip = self.block_tree[new_tip_id]['block']

    
    def process_orphan_blocks(self, current_time, event_queue):
        orphaned_block_ids = list(self.orphaned_blks.keys())

        for orphan_id in orphaned_block_ids:
            orphan_block = self.orphaned_blks[orphan_id]
            parent_id = orphan_block.prev_id

            if parent_id in self.block_tree:
                del self.orphaned_blks[orphan_id] 

                event = type('', (), {})()
                event.msg = orphan_block
                self.receive_block(current_time, event_queue, event)

        
    
    def validate_block(self, block):
        if not block.is_valid_size():
            return False

        if block.prev_id == "GENESIS":
            balances = defaultdict(int)
        else:
            balances = self.balance_cache[block.prev_id].copy()
        
        for tx in block.transactions:
            sender_bal = balances[tx.sender_id]
            if tx.sender_id != tx.recipient_id:
                if sender_bal < tx.amount:
                    return False
                balances[tx.sender_id] -= tx.amount
                balances[tx.recipient_id] += tx.amount
            else:
                balances[tx.sender_id] += tx.amount
        
        return True
        
    
    def calculate_balances_for_chain(self, tip_id):
        if tip_id in self.balance_cache:
            return self.balance_cache[tip_id]

        balances = defaultdict(int)
        current_block_id = tip_id
        chain_segment = []

        while current_block_id and current_block_id != "GENESIS":
            if current_block_id in self.balance_cache:
                balances = self.balance_cache[current_block_id].copy()
                break
            chain_segment.append(current_block_id)
            current_block_id = self.block_tree[current_block_id]['parent']

        for block_id in reversed(chain_segment):
            bobj = self.block_tree[block_id]['block']
            for tx in bobj.transactions:
                balances[tx.recipient_id] += tx.amount
                if tx.sender_id != tx.recipient_id:
                    balances[tx.sender_id] -= tx.amount

            self.balance_cache[block_id] = balances.copy()

        
        return balances
    

    def export_included_transactions(self,file_name):
        chain_blocks = []
        current_block_id = self.longest_chain_tip.id
        
        # Traverse backwards until we reach the genesis block
        while current_block_id and current_block_id != "GENESIS":
            block = self.block_tree[current_block_id]['block']
            chain_blocks.append(block)
            current_block_id = self.block_tree[current_block_id]['parent']
        
        # Reverse the list to have blocks in chronological order
        chain_blocks.reverse()
        
        # Write the transactions from each block to the file.
        with open(file_name, "w") as outfile:
            for block in chain_blocks:
                outfile.write(f"Block ID: {block.id}, Miner: {block.miner_id}\n")
                outfile.write("Transactions:\n")
                for txn in block.transactions:
                    outfile.write(f"    {str(txn)}\n")
                outfile.write("\n")
    



