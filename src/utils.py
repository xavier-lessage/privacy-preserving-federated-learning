import urllib.parse
from hashlib import sha256

from PROJH402.src.Transaction import Transaction


def verify_chain(chain):
    """
    Checks every block of the chain to see if the previous_hash matches the hash of the previous block
    """
    last_block = chain[0]
    i = 1
    while i < len(chain):
        if chain[i].parent_hash == last_block.compute_block_hash() and chain[i].verify:
            last_block = chain[i]
            i += 1
        else:
            print("Error in the blockchain")
            print(chain)
            return False
    return True


def compute_hash(list):
    if len(list) < 1:
        return
    hash_string = ""
    for elem in list:
        hash_string += str(elem)

    return sha256(hash_string.encode()).hexdigest()


def transaction_to_dict(transaction):
    return {"source": transaction.source, "destination": transaction.destination, "data": transaction.data,
            "value": transaction.value, "timestamp": transaction.timestamp, "nonce": transaction.nonce,
            "id": transaction.id}


def dict_to_transaction(_dict):
    return Transaction(_dict["source"], _dict["destination"], _dict["data"], _dict["value"], _dict["timestamp"],
                       _dict["nonce"], _dict["id"])

