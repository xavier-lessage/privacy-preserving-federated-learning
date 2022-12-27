import threading
from time import time, sleep

# from PROJH402.src.Block import Block
from PROJH402.src.Block import Block, create_block_from_list
from PROJH402.src.MiningThreads import MiningThread
from PROJH402.src.NodeThread import NodeThread
from PROJH402.src.Pingers import ChainPinger, MemPoolPinger
from PROJH402.src.constants import ENCODING, CHAIN_SYNC_INTERVAL, MEMPOOL_SYNC_INTERVAL, GENESIS_BLOCK
from PROJH402.src.utils import compute_hash, verify_chain


class Node:
    """
    Class representing a 'user' that has his id, his blockchain and his mem-pool
    """

    def __init__(self, id, host, port, difficulty):
        self.id = id
        self.chain = []
        self.mempool = set()
        self.difficulty = difficulty

        self.host = host
        self.port = port

        self.enode = f"enode://{self.id}@{self.host}:{self.port}"

        # Initialize the genesis Block
        genesis_block = GENESIS_BLOCK
        self.chain.append(genesis_block)

        # {addr: node_info}
        self.peers = {}
        # {addr : [sync_threads]}
        self.sync_threads = {}

        self.node_thread = NodeThread(self, host, port, id)

        self.syncing = False
        self.data_handler = self.node_thread.data_handler

        self.mining = False
        self.mining_thread = MiningThread(self)

    def start_mining(self):
        print("Starting the mining \n")
        self.mining_thread.start()
        self.mining = True

    def stop_mining(self):
        self.mining_thread.stop()
        self.mining = False
        print("Node " + str(self.id) + " stopped mining")

    def start_tcp(self):
        """
        starts the NodeThread that handles the TCP connection with other nodes
        """
        self.syncing = True
        self.node_thread.start()

    def stop_tcp(self):
        peers = list(self.sync_threads.keys())
        for peer in peers:
            self.remove_peer(peer)

        self.node_thread.stop()
        self.data_handler.stop()
        self.syncing = False

    def get_block(self, height):
        if height == 'last':
            return self.chain[-1]
        elif height == 'first':
            return self.chain[0]
        else:
            return self.chain[height]

    def sync_mempool(self, mempool):
        for elem in mempool:
            self.mempool.add(elem)

    def sync_chain(self, chain_repr, height):
        print("Merging chains")
        chain = []
        # Reconstruct the partial chain
        for block_repr in chain_repr:
            block = create_block_from_list(block_repr)
            chain.append(block)

        if not verify_chain(chain):
            return

        for block in chain:
            for transaction in block.data:
                self.mempool.discard(transaction)

        if chain[0].parent_hash == self.get_block(height).hash:
            # Replace self chain with the other chain
            del self.chain[height+1:]
            self.chain.extend(chain)
            print(f"Node {self.id} has updated its chain")
            print(self.chain)
        else:
            print("Error here")

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

    def add_peer(self, addr, node_info=None):
        if addr not in self.peers:
            print(f"Node {self.id} adding peer at {addr}")
            if addr not in self.node_thread.connection_threads:
                # Connection
                connection, node_info = self.node_thread.connect_to(addr)
                connection.start()
            self.peers[addr] = node_info
            chain_sync_thread = ChainPinger(self, addr, CHAIN_SYNC_INTERVAL)
            mempool_sync_thread = MemPoolPinger(self, addr, MEMPOOL_SYNC_INTERVAL)
            self.sync_threads[addr] = [chain_sync_thread, mempool_sync_thread]
            chain_sync_thread.start()
            mempool_sync_thread.start()

    def remove_peer(self, addr):
        sync_threads = self.sync_threads.get(addr)
        if sync_threads:
            for thread in sync_threads:
                thread.stop()
            self.sync_threads.pop(addr)
        self.node_thread.disconnect_from(addr)
        self.peers.pop(addr, None)

    def node_info(self):
        protocol = {"difficulty": self.difficulty}
        info = {"enode": self.enode, "id": self.id, "ip": self.host, "port": self.port, "protocol": protocol}
        return info
