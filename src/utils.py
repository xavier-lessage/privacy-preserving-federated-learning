import urllib.parse
from hashlib import sha256


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

    hash = sha256(hash_string.encode()).hexdigest()
    return hash


def verify_transaction(transaction):
    pass


