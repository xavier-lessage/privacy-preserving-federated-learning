from threading import Thread

from MiningThreads import *
from Block import *


class Node:

    def __init__(self, id):
        self.id = id
        self.chain = []
        self.mempool = []

        # Initialize the first Block
        first_block = Block(0, 0000000, [])
        self.chain.append(first_block)

    def add_block(self):
        """
        Add a block to the Chain with the actual mempool
        """
        block = Block(len(self.chain), self.get_last_block().compute_hash(), self.mempool.copy())
        self.mine()

    def mine(self):
        """
        Works to create a block that has the right level of difficulty
        :return:
        """
        mining_thread = Thread(target=mine_thread, args=(self, ))
        mining_thread.start()
        mining_thread.join()

    def verify_chain(self):
        """
        Checks every block of the chain to see if the previous_hash matches the hash of the previous block
        """
        last_block = self.chain[0]
        i = 1
        while i < len(self.chain):
            if self.chain[i].previous_hash == last_block.compute_hash():
                last_block = self.chain[i]
                i += 1
                print("Correct block")
            else:
                print("Error in the blockchain")
                return False

        return True

    def compare_chains(self, chain):
        """
        TODO: compare otherwise the blocks
        Compares two chains to determine the one to keep
        :param chain: Chain to compare with the actual chain of the node
        :return: True if the input chain is "better" than the actual chain
                False if the chain is not valid or if the actual chain is better than the input one
        """
        if not chain.verify():
            return False
        if len(chain) > len(self.chain):
            return True
        else:
            return False

    def get_last_block(self):
        return self.chain[-1]

    def add_to_mempool(self, data):
        self.mempool.append(data)

    def print_chain(self):
        print("Node: ", self.id)
        for block in self.chain:
            print("Block index: ", block.index)
            print("Block hash: ", block.compute_hash())
            print("Block parent", block.previous_hash)
            print("Block data", block.data)
