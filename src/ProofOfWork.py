
"""
Every consensus should have :
- a genesis block
- a block generation thread
- a block verification function
"""
import threading
from random import randint
from time import time

from PROJH402.src import constants
from PROJH402.src.Block import Block

MINING_DIFFICULTY = 18  # Approx One block every 7 seconds
GENESIS_BLOCK = Block(0, 0000000, [], 0, 0, MINING_DIFFICULTY, 0, 0)

class ProofOfWork:
    def __init__(self):
        self.genesis = GENESIS_BLOCK
        self.block_generation = MiningThread

    def verify_chain(self, chain):
        last_block = chain[0]
        i = 1
        while i < len(chain):
            if chain[i].parent_hash == last_block.compute_block_hash() and self.verify_block(chain[i]):
                last_block = chain[i]
                i += 1
            else:
                print("Error in the blockchain")
                print(chain)
                return False
        return True

    def verify_block(self, block):
        # for transaction in block.data:
            # verify_transaction(transaction)

        target_string = '1' * (256 - block.difficulty)
        target_string = target_string.zfill(256)

        hash_int = int(block.hash, 16)
        binary_hash = bin(hash_int)
        binary_hash = binary_hash[3:]

        if target_string > binary_hash:
            return True
        return False


class MiningThread(threading.Thread):
    """
    Thread class that generate blocks that answer to the consensus rules
    This block generation is done according to the proof of work
    """

    def __init__(self, node):
        super().__init__()
        self.node = node
        self.difficulty = MINING_DIFFICULTY

        self.flag = threading.Event()

        self.timer = time()

    def run(self):
        """
        Increase the nonce until the hash of the block has the expected number of zeros at the front of the hash
        """
        timestamp = time()

        block = Block(len(self.node.chain), self.node.get_block('last').hash, self.node.mempool.copy(), self.node.id,
                      timestamp, self.difficulty, self.node.get_block('last').total_difficulty, randint(0, 1000))

        while not self.flag.is_set():
            last_block = self.node.get_block("last")
            block.update(last_block.height+1, last_block.hash, last_block.data, self.difficulty,
                         last_block.total_difficulty + self.difficulty)

            target_string = '1' * (256 - self.difficulty)
            target_string = target_string.zfill(256)

            hash_int = int(block.compute_block_hash(), 16)
            binary_hash = bin(hash_int)
            binary_hash = binary_hash[3:]

            if binary_hash > target_string:
                block.increase_nonce()

            else:
                self.node.chain.append(block)
                self.node.mempool.clear()
                if constants.DEBUG:
                    print("Block added: " + str(block.compute_block_hash()))
                    print(repr(block) + "\n")

                block = Block(len(self.node.chain), self.node.get_block('last').hash, self.node.mempool.copy(),
                              self.node.id, timestamp, self.difficulty, self.node.get_block('last').total_difficulty,
                              randint(0, 1000))

    def stop(self):
        self.flag.set()



