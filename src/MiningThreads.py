
import threading
from random import randint
from time import sleep, time

from PROJH402.src import constants
from PROJH402.src.constants import *
from PROJH402.src.Block import Block


class MiningThread(threading.Thread):
    """
    Thread class that generate blocks that answer to the consensus rules
    This block generation is done according to the proof of work
    """

    def __init__(self, node):
        super().__init__()
        self.node = node
        self.difficulty = node.difficulty

        self.flag = threading.Event()

        self.timer = time()

    def run(self):
        """
        Increase the nonce until the hash of the block has the expected number of zeros at the front of the hash
        """
        timestamp = time()

        block = Block(len(self.node.chain), self.node.get_block('last').hash, self.node.mem_pool.copy(), self.node.id,
                      timestamp, self.difficulty, self.node.get_block('last').total_difficulty, randint(0, 1000))

        while not self.flag.is_set():
            last_block = self.node.get_block("last")
            block.update(last_block.height+1, last_block.hash, last_block.data, self.node.difficulty,
                         last_block.total_difficulty + self.node.difficulty)

            target_string = '1' * (256 - self.difficulty)
            target_string = target_string.zfill(256)

            hash_int = int(block.compute_hash(), 16)
            binary_hash = bin(hash_int)
            binary_hash = binary_hash[3:]

            if binary_hash > target_string:
                block.increase_nonce()

            else:
                self.node.chain.append(block)
                self.node.mem_pool.clear()
                if constants.DEBUG:
                    print("Block added: " + str(block.compute_hash()))
                    print(repr(block) + "\n")

                block = Block(len(self.node.chain), self.node.get_block('last').hash, self.node.mem_pool.copy(),
                              self.node.id, timestamp, self.difficulty, self.node.get_block('last').total_difficulty,
                              randint(0, 1000))
            if last_block.height>=20:
                print(time()-self.timer)
                break

    def stop(self):
        self.flag.set()


class ProofOfAuthThread(threading.Thread):
    """
    Generates a block every X seconds
    """

    def __init__(self, node, time=10):
        super().__init__()
        self.node = node
        self.time = time
        self.flag = threading.Event()

        self.difficulty = node.difficulty

    def run(self):
        while not self.flag.is_set():
            sleep(self.time)
            timestamp = time()
            block = Block(len(self.node.chain), self.node.get_block('last').hash, self.node.mem_pool.copy(),
                          self.node.id, timestamp, self.difficulty, self.node.get_block('last').total_difficulty)
            self.node.chain.append(block)
            self.node.mem_pool.clear()
            print("Block added: " + str(block.compute_hash()))
            print(repr(block) + "\n")
