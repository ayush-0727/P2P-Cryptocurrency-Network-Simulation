import hashlib
import uuid
import json

class Block:
    GENESIS = None 

    def __init__(self, prev_id, prev_hash, transactions, miner_id):
        self.id = str(uuid.uuid4())
        self.prev_hash = prev_hash
        self.prev_id = prev_id
        self.transactions = transactions
        self.miner_id = miner_id

    @property
    def size(self):
        num_txs = len(self.transactions)
        return max(1, num_txs) * 1024  # at least 1 KB

    def is_valid_size(self):
        return self.size <= 1024 * 1024  # <= 1MB

    def get_hash(self):
        block_contents = {
            "id": self.id,
            "prev_id": self.prev_id,
            "prev_hash": self.prev_hash,
            "transactions": self.transactions,
            "miner_id": self.miner_id
        }
        block_string = json.dumps(block_contents, sort_keys=True)

        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()


