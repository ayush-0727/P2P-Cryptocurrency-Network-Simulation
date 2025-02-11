import uuid

class Transaction:
    def __init__(self, sender_id, recipient_id, amount, coinbase=False):
        self.txn_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount
        self.coinbase = coinbase
        self.size = 1024  # 1 KB

    def __str__(self):
        return f"TxnID:{self.txn_id[:8]} => {self.sender_id} pays {self.recipient_id} {self.amount} coins"
    