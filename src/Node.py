from time import time

from PROJH402.src.Block import Block
from PROJH402.src.MiningThreads import MiningThread
from PROJH402.src.NodeThread import NodeThread
from PROJH402.src.Pingers import ChainPinger, MemPoolPinger
from PROJH402.src.constants import ENCODING, CHAIN_SYNC_INTERVAL, MEMPOOL_SYNC_INTERVAL


class Node:
    """
    Class representing a 'user' that has his id, his blockchain and his mem-pool
    """

    def __init__(self, id, host, port, difficulty):
        self.id = id
        self.chain = []
        self.mem_pool = set()
        self.difficulty = difficulty

        # Initialize the first Block
        first_block = Block(0, 0000000, [], self.id, time(), self.difficulty, 0, 0)
        self.chain.append(first_block)

        self.peers = {}

        self.node_thread = NodeThread(self, host, port, id)

        self.data_handler = self.node_thread.data_handler

        self.mining_thread = MiningThread(self)

    def start_mining(self):
        print("Starting the mining \n")
        self.mining_thread.start()
        # self.poa_thread.start()

    def stop_mining(self):
        self.mining_thread.stop()
        print("Node " + str(self.id) + " stopped mining")

    def start_tcp(self):
        """
        starts the NodeThread that handles the TCP connection with other nodes
        """
        self.node_thread.start()

    def stop_tcp(self):
        self.node_thread.stop()
        self.data_handler.stop()

        peers = list(self.peers.keys())
        for peer in peers:
            self.remove_peer(peer)
        print(f"Node {self.id} stopped")

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

    def sync_mempool(self, mempool):
        for elem in mempool:
            self.mem_pool.add(elem)
            # print(elem)

    def sync_chain(self, chain_repr):
        """
        To be enhanced
        :param chain_repr:
        :return:
        """
        if int(chain_repr[-1][-1]) > self.get_block('last').total_difficulty:
            for block in chain_repr:
                for elem in block[2]:
                    self.mem_pool.discard(elem)
            for i in reversed(range(int(chain_repr[-1][0]) - self.get_block('last').height)):
                block = Block(chain_repr[0], chain_repr[1], chain_repr[2], chain_repr[3], chain_repr[4],
                              chain_repr[5], chain_repr[6], chain_repr[7])
                self.chain.append(block)
            return True
        else:
            return False

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

    def add_peer(self, addr):
        if addr not in self.peers:
            print(f"Node {self.id} adding peer at {addr}")
            if addr not in self.node_thread.connection_threads:
                connection = self.node_thread.connect_to(addr)
                connection.start()
            chain_sync_thread = ChainPinger(self, addr, CHAIN_SYNC_INTERVAL)
            mempool_sync_thread = MemPoolPinger(self, addr, MEMPOOL_SYNC_INTERVAL)
            self.peers[addr] = [chain_sync_thread, mempool_sync_thread]
            chain_sync_thread.start()
            mempool_sync_thread.start()

    def remove_peer(self, addr):
        sync_threads = self.peers.get(addr)
        if sync_threads:
            for thread in sync_threads:
                thread.stop()
            self.peers.pop(addr)
        self.node_thread.disconnect_from(addr)
