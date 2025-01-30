import time

class Block:
    next_id = 0
    GENESIS = None  # Will be initialized once
    
    def __init__(self, prev_id, transactions, miner_id):
        self.id = Block.next_id
        Block.next_id += 1
        self.prev_id = prev_id
        self.transactions = transactions
        self.miner_id = miner_id
        self.timestamp = time.time()
        self.size = 1 + len(transactions)  # 1KB base + 1KB per transaction (KB)
        
    def is_valid_size(self):
        return self.size <= 1024  # 1MB = 1024KB

# Initialize Genesis block
Block.GENESIS = Block(prev_id=-1, transactions=[], miner_id=-1)
Block.GENESIS.size = 1