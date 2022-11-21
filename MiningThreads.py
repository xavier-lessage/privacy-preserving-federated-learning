from Node import *
import threading
from time import sleep
from Block import *


class MiningThread(threading.Thread):
    """
    Thread class that tries to create a block that answer the consensus
    This block generation is done according to the proof of work
    """

    def __init__(self, node, difficulty=3):
        super().__init__()
        self.node = node
        self.difficulty = difficulty

    def run(self):
        """
        Increase the nonce until the hash of the block has the expected number of zeros at the front of the hash
        """
        print("Starting the mining \n")
        i = 1
        block = Block(len(self.node.chain), self.node.get_last_block().compute_hash(), self.node.mempool.copy())
        while True:
            block.update_data(self.node.mempool)
            if block.compute_hash()[:self.difficulty] != "0" * self.difficulty:
                block.increase_nonce()
                # print(i)
                i += 1
            else:
                print(str(block.compute_hash()))
                self.node.chain.append(block)
                self.node.mempool.clear()
                print("Block added: " + str(block.compute_hash()))
                print("Attempts: " + str(i))
                print(repr(block))
                break


class ProofOfAuthThread(threading.Thread):
    """
    Generates a block every X seconds
    """

    def __init__(self, node, time=10):
        super().__init__()
        self.node = node
        self.time = time

    def run(self):
        for i in range(3):
            sleep(self.time)
            block = Block(len(self.node.chain), self.node.get_last_block().compute_hash(), self.node.mempool)
            self.node.chain.append(block)


class AddMempoolThread(threading.Thread):
    """
    Thread that adds data to the mempool of a node.
    Useful to test the block generation
    """

    def __init__(self, node, data):
        super().__init__()
        self.data = data
        self.node = node

    def run(self):
        self.node.add_to_mempool(self.data)
        print("data added")
