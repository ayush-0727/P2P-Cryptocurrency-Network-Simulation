def parse_transaction(line):
    """
    Given a transaction line of the form:
       "TxnID:<txn_id> => <sender> pays <recipient> <amount> coins"
    returns a tuple (txn_id, sender, recipient, amount)
    """
    line = line.strip()
    # Remove any indentation
    if line.startswith("TxnID:"):
        # Split on " => " to separate ID from the rest.
        parts = line.split(" => ")
        txn_id = parts[0].replace("TxnID:", "").strip()
        # The right-hand side is expected to be like: "<sender> pays <recipient> <amount> coins"
        tokens = parts[1].split()
        sender = tokens[0]
        recipient = tokens[2]
        try:
            amount = int(tokens[3])
        except ValueError:
            raise ValueError(f"Could not parse amount in line: {line}")
        return txn_id, sender, recipient, amount
    else:
        return None

def verify_transactions(file_name):
    """
    Reads the blockchain transaction log from file_name and verifies that:
      - Each block has a valid coinbase transaction (first transaction equals 50 coins credited to the miner)
      - No transaction transfers more coins than the sender currently holds.
    Returns a tuple (errors, final_balances).
    """
    balances = {}
    errors = []
    current_block = None
    current_miner = None

    with open(file_name, 'r') as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("Block ID:"):
                # If we have a block in progress, process it now.
                if current_block is not None:
                    process_block(current_block, current_miner, balances, errors)
                # Start a new block.
                # Expect a line like: "Block ID: <block_id>, Miner: <miner_id>"
                parts = line.split(',')
                if len(parts) < 2:
                    errors.append(f"Invalid block header: {line}")
                    current_miner = None
                else:
                    current_miner = parts[1].split(":")[1].strip()
                current_block = []  # list to hold transactions for this block
            elif line.startswith("Transactions:"):
                # Header line; skip it.
                continue
            elif line.strip() == "":
                # Blank line signals end of block.
                if current_block is not None:
                    process_block(current_block, current_miner, balances, errors)
                    current_block = None
                    current_miner = None
            elif line.strip().startswith("TxnID:"):
                txn = parse_transaction(line)
                if txn is not None:
                    if current_block is None:
                        errors.append("Transaction found outside of a block: " + line)
                    else:
                        current_block.append(txn)
    # Process the final block if the file does not end with a blank line.
    if current_block is not None:
        process_block(current_block, current_miner, balances, errors)
    
    return errors, balances

def process_block(transactions, miner, balances, errors):
    """
    Process a single block of transactions.
    The first transaction must be the coinbase transaction:
      It must have sender == miner, recipient == miner, and amount == 50.
    Then, process the remaining transactions by checking that each sender has enough balance.
    Update the balances accordingly.
    """
    if not transactions:
        errors.append(f"Block by miner {miner} has no transactions.")
        return
    # Process coinbase transaction (first transaction)
    coinbase = transactions[0]
    txn_id, sender, recipient, amount = coinbase
    if sender != miner or recipient != miner or amount != 50:
        errors.append(f"Invalid coinbase transaction in block by miner {miner}: {coinbase}")
    else:
        balances[miner] = balances.get(miner, 0) + 50

    # Process the rest of the transactions in the block
    for txn in transactions[1:]:
        txn_id, sender, recipient, amount = txn
        sender_balance = balances.get(sender, 0)
        if sender_balance < amount:
            errors.append(f"Insufficient balance for transaction {txn_id}: sender {sender} has {sender_balance} coins, tries to send {amount} coins.")
        else:
            balances[sender] = sender_balance - amount
            balances[recipient] = balances.get(recipient, 0) + amount

if __name__ == '__main__':
    file_name = "peer0_transactions.txt"
    errors, final_balances = verify_transactions(file_name)
    if errors:
        print("Errors found during verification:")
        for err in errors:
            print("  -", err)
    else:
        print("All transactions are consistent.")
    print("\nFinal balances:")
    for account, balance in final_balances.items():
        print(f"  Account {account}: {balance} coins")
