from simulation.transaction import Transaction
from simulation.event import Event
from simulation.block import Block
from collections import defaultdict
import copy
import random

class Peer:
    def __init__(self, peer_id, is_slow, is_low_cpu, link_params):
        self.peer_id = peer_id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        
        self.known_peer_ids = []
        self.neighbors = []
        
        self.received_txns = set()
        self.mempool = set()
        self.sent_transactions = defaultdict(set)

        self.balances = defaultdict(int)

        genesis_blk = Block(
            prev_id=None,
            prev_hash=None,
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
        self.orphaned_blks=[]
        self.longest_chain_tip = genesis_blk

        self.current_mining_event = None
        self.total_blocks_mined = 0

        self.hashing_power = 0
        
        self.link_params = link_params
        self.peers = []
    
    def schedule_transactions(self,event_queue,Ttx):
        event = Event(timestamp=0,
                    callback=self.generate_transaction_handler(Ttx))
        event_queue.add_event(event)


    # Periodically generate random transactions
    def generate_transaction_handler(self, Ttx):
        """
        Called by the simulator to generate a new transaction from this peer, 
        at random intervals with mean Ttx.
        """
        def handler(current_time, event_queue, event):
            # We check how many coins this peer (the sender) has according 
            # to the chain it knows. So re-calculate based on the longest chain:
            balances = self.calculate_balances_for_chain(self.longest_chain_tip)
            sender_balance = balances.get(self.peer_id, self.initial_coins)

            if sender_balance > 0:
                amount = random.randint(1, sender_balance)
                recipient = random.choice([
                    pid for pid in self.known_peer_ids if pid != self.peer_id
                ])
                transaction = Transaction(self.peer_id, recipient, amount)
                
                # Immediately treat it as if we "received" our own new txn:
                self.receive_transaction(transaction, self.peer_id, current_time, event_queue)
                
                print(f"Time {current_time:.2f}: Peer {self.peer_id} generated {transaction}")
            
            # Schedule the next transaction-generation event:
            delay = random.expovariate(1.0 / Ttx)
            event_queue.add_event(Event(
                current_time + delay,
                self.generate_transaction_handler(Ttx)
            ))
        return handler
    
    def calculate_latency(self, peer_id, msg_bits):
        link = (self.peer_id, peer_id)
        rho, c = self.link_params[link]
        
        mean_d = 96000 / c
        d = random.expovariate(1 / mean_d)
        
        return rho + (msg_bits / c) + d
    
    # Receive Transactions by adding the transaction into your own pool and propogating it to the neighbours
    def receive_transaction(self, transaction, sender_id, current_time, event_queue):
        if transaction.txn_id not in self.received_txns:
            self.received_txns.add(transaction.txn_id)
            # Add to local mempool (pending) if not already in chain
            # (Here we do not check in-chain duplicates in detail, but you could do so.)
            self.pending_transactions.add(transaction)

            # Forward to all connected peers except the one who sent it:
            for neighbor in self.neighbors:
                if neighbor != sender_id and neighbor not in self.sent_transactions[transaction.txn_id]:
                    # Calculate latency
                    msg_bits = transaction.size * 8000  # 1KB = 8000 bits
                    latency = self.calculate_latency(neighbor, msg_bits)
                    
                    event_queue.add_event(Event(
                        timestamp=current_time + latency,
                        callback=lambda t, q, e: self.peers[neighbor]
                            .receive_transaction(transaction, self.peer_id, t, q),
                        msg=transaction
                    ))
                    self.sent_transactions[transaction.txn_id].add(neighbor)
    
    # --------------------------------------------------------
    # Mining logic
    # --------------------------------------------------------
    def schedule_mining(self, current_time, event_queue, I=600):
        if self.current_mining_event:
            return
        
        # Create the block
        new_block = Block(
        prev_id=self.longest_chain_tip.id,
        prev_hash=None,
        transactions=[],
        miner_id=self.peer_id
        )
        # Create coinbase
        coinbase_tx = Transaction(
            sender_id=self.peer_id,
            recipient_id=self.peer_id,
            amount=50
        )

        new_block.transactions.append(coinbase_tx)

        # Choose the maximum possible transactions from mempool that can fit in the block
        for txn in self.mempool:
            new_block.transactions.append(txn)
            if not new_block.is_valid_size():
                while not new_block.is_valid_size():
                    new_block.transactions.pop()
                break
        

        # Calculate Tk
        mean_time = I / self.hashing_power
        Tk = random.expovariate(1.0 / mean_time)
        
        self.current_mining_event = Event(
            timestamp=current_time+Tk,
            callback=self.mine_block_callback,
            msg=new_block
        )
        # Schedule the event of mine_block_callback at current_time + Tk
        event_queue.add_event(self.current_mining_event)

    
        
    def mine_block_callback(self, current_time, event_queue, event):
        mined_block = event.msg
        self.current_mining_event = None

        if self.longest_chain_tip.id != mined_block.prev_id:
            self.schedule_mining(current_time,event_queue)
            return
        
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
        
        # Update the longest tip
        self.longest_chain_tip = mined_block
        
        # Remove those transactions from the mempool that have been included
        for tx in mined_block.transactions[1:]:
            if tx in self.mempool:
                self.mempool.remove(tx)

        # Update Balance
        self.balances = self.calculate_balances_for_chain(self.longest_chain_tip.id)
        
        self.total_blocks_mined += 1

        self.broadcast_block(mined_block, current_time, event_queue)

        self.schedule_mining(current_time, event_queue)

    
    def broadcast_block(self, new_block, current_time, event_queue):
        for neighbor in self.neighbors:
            if neighbor == self.peer_id:
                continue
            msg_bits = new_block.size * 8
            latency = self.calculate_latency(neighbor, msg_bits)
            event_queue.add_event(Event(
                timestamp=current_time + latency,
                callback=self.peers[neighbor].receive_block,
                msg=copy.deepcopy(new_block)
            ))
    
    def receive_block(self,current_time, event_queue,event):
        block = event.msg
        if block.id in self.block_tree:
            return

        if not self.validate_block(block):
            return
        
        parent_id = block.prev_id

        if parent_id not in self.block_tree:
            self.orphaned_blks.append(block)
            return
        
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
            self.longest_chain_tip = block
            self.balances = self.calculate_balances_for_chain(self.longest_chain_tip.id)
            for tx in block.transactions[1:]:
                if tx in self.mempool:
                    self.mempool.remove(tx)
            self.schedule_mining(current_time, event_queue)
        

        self.broadcast_block(block,current_time,event_queue)

        
    
    def validate_block(self, block):
        # Validate the transactions of the block by executing them and checking if locally stored balances are not getting negative for some sender
        if not block.is_valid_size():
            return False
        
        parent_id = block.prev_id
        if parent_id not in self.block_tree and block.id != "GENESIS":
            return False

        balances = self.calculate_balances_for_chain(parent_id)
        
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
        # Alternatively, we  can cache the balances at a particular block id
        balances = defaultdict(int)
        
        # Walk backwards from tip to genesis:
        current_block_id = tip_id
        while current_block_id and current_block_id != "GENESIS":
            bobj = self.block_tree[current_block_id]['block']
            for tx in bobj.transactions:
                if tx.sender_id == tx.recipient_id:
                    balances[tx.sender_id] += tx.amount
                else:
                    balances[tx.sender_id] -= tx.amount
                    balances[tx.recipient_id] += tx.amount
            current_block_id = bobj.prev_id

        return balances
    



    # Think about efficienly keeping track of the balance of the longest chain


    # Write a function to rollback the transactions of a chain in case the longest chain changes

    # Write a function to validate a transaction
        # Should not be included if it is already part of some block in the current longest chain
        # Should not include transaction that is not valid according to current balance
    
    # Think of replacing id with hashes to make the block chain tamper proof

    # It can happen that a child block is received before its parent block so keep track of such blocks as well

    # What if the chain changes and the transaction gets removed from the block chain? The creator of the transaction should again broadcast that transaction as the miners might have deleted it from their mempool


