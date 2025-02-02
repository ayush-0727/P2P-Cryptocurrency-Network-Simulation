class Transaction:
    next_id = 0
    
    def __init__(self, sender_id, recipient_id, amount,is_coinbase):
        self.txn_id = Transaction.next_id
        Transaction.next_id += 1
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount
        self.size = 1
        self.is_coinbase = is_coinbase
    def __repr__(self):
        return f"TxnID:{self.txn_id}: {self.sender_id} pays {self.recipient_id} {self.amount} coins"