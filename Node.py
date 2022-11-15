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
        block = Block(len(self.chain), self.get_last_block().compute_hash(), self.mempool)
        self.mine(block)
        self.mempool.clear()
        self.chain.append(block)
        print("Block added: " + block.compute_hash())

    def mine(self, block):
        """
        Works to create a block that has the right level of difficulty
        :return:
        """
        # sets the difficulty
        difficulty = 3
        attempts_number = 0

        while block.compute_hash()[:difficulty] != "0" * difficulty:
            # print("Retry"+block.compute_hash())
            block.nonce += 1
            attempts_number += 1

        # print("Good job"+block.compute_hash())
        print("Tried " + str(attempts_number))

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
