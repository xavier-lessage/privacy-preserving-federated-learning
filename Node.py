from MiningThreads import *
from Block import *
from Connections import *


# from PROJH402.Connections import NodeThread


class Node:
    """
    Class representing a 'user' that has his id, his blockchain and his mempool
    """

    def __init__(self, id, host, port, difficulty):
        self.id = id
        self.chain = []
        self.mempool = []
        self.difficulty = difficulty

        # Initialize the first Block
        first_block = Block(0, 0000000, [], self.id, time(), self.difficulty, 0)
        self.chain.append(first_block)

        self.tcp_thread = NodeThread(self, host, port, id)

        self.mining_thread = MiningThread(self)

    def start_mining(self):
        """
        Starts the mining thread
        """
        print("Starting the mining \n")
        self.mining_thread.start()

    def stop_mining(self):
        self.mining_thread.stop()

    def start_tcp(self):
        """
        starts the NodeThread that handles the TCP connection with other nodes
        :return:
        """
        self.tcp_thread.start()

    def stop_tcp(self):
        self.tcp_thread.stop()

    def verify_chain(self, chain):
        """
        Checks every block of the chain to see if the previous_hash matches the hash of the previous block
        TODO: check the block height
        """
        last_block = chain[0]
        i = 1
        while i < len(chain):
            if chain[i].parent_hash == last_block.compute_hash() and chain[i].verify:
                last_block = chain[i]
                i += 1
            else:
                print("Error in the blockchain")
                return False
        return True

    def compare_chains(self, chain):
        """
        Compares two chains to determine the one to keep
        :param chain: Chain to compare with the actual chain of the node
        :return: True if the input chain is "better" than the actual chain
                False if the chain is not valid or if the actual chain is better than the input one
        """
        if not self.verify_chain(chain):
            return False
        if chain[-1].total_difficulty > self.get_block('last').total_difficulty:
            return True
        else:
            return False

    def get_block(self, height):
        if height == 'last':
            return self.chain[-1]
        elif height == 'first':
            return self.chain[0]
        else:
            return self.chain[height]

    def add_to_mempool(self, data):
        """
        Adds an element to the mempool list
        """
        self.mempool.append(data)

    def print_chain(self):
        """
        Prints the complete chain information, block by block
        """
        print("Node: ", self.id)
        for block in self.chain:
            block.print_header()

    def compact_print(self):
        """
        Prints a compact version of the blockchain
        """
        print("Node: ", self.id)
        for block in self.chain:
            print(block.__repr__())
        print("\n")
