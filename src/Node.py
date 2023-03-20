import logging
import threading
import urllib.parse
from time import time, sleep

# from PROJH402.src.Block import Block
from PROJH402.src.Block import Block, create_block_from_list
from PROJH402.src.NodeThread import NodeThread
from PROJH402.src.Pingers import ChainPinger, MemPoolPinger
from PROJH402.src.constants import ENCODING, CHAIN_SYNC_INTERVAL, MEMPOOL_SYNC_INTERVAL, DEBUG
from PROJH402.src.utils import compute_hash, verify_chain


class Node:
    """
    Class representing a 'user' that has his id, his blockchain and his mem-pool
    """

    def __init__(self, id, host, port, consensus):
        self.id = id
        self.chain = []
        self.mempool = {}

        self.previous_transactions_id = set()

        self.host = host
        self.port = port

        self.enode = f"enode://{self.id}@{self.host}:{self.port}"

        self.consensus = consensus
        # Initialize the genesis Block
        self.chain.append(self.consensus.genesis)

        # {enode: node_info}
        self.peers = {}
        # {enode : [sync_threads]}
        self.sync_threads = {}

        self.node_thread = NodeThread(self, host, port, id)

        self.syncing = False
        self.data_handler = self.node_thread.data_handler

        self.mining = False
        self.mining_thread = consensus.block_generation(self)

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

    def destroy_node(self):
        print("Destroyed")
        self.stop_tcp()
        self.stop_mining()

    def get_block(self, height):
        if height == 'last':
            return self.chain[-1]
        elif height == 'first':
            return self.chain[0]
        else:
            return self.chain[height]

    def sync_mempool(self, transactions):
        for elem in transactions:
            if elem.nonce not in self.previous_transactions_id:
                self.mempool[elem.nonce] = elem
                # print("?????????????????????")
                # print(f"###{self.mempool}###")
                # print(self.previous_transactions_id)

    def sync_chain(self, chain_repr, height):
        print("Merging chains")
        chain = []
        # Reconstruct the partial chain
        for block_repr in chain_repr:
            block = create_block_from_list(block_repr)
            chain.append(block)

        if not self.verify_chain(chain):
            return

        if chain[0].parent_hash == self.get_block(height).hash:
            # update mempool
            for block in chain:
                for transaction in block.data:
                    self.mempool.pop(transaction.nonce, None)
                    self.previous_transactions_id.add(transaction.nonce)
                    logging.info(transaction.nonce)

            # retrieving possible missed transactions
            for block in self.chain[height+1:]:
                for transaction in block.data:
                    if transaction.nonce not in self.previous_transactions_id:
                        self.mempool[transaction.nonce] = transaction


            # Replace self chain with the other chain
            del self.chain[height+1:]
            self.chain.extend(chain)
            print(f"Node {self.id} has updated its chain, total difficulty : {self.get_block('last').total_difficulty}")
            for block in self.chain[-5:]:
                print(block.__repr__())
        else:
            print("Chain does not fit here")

    def add_peer(self, enode, node_info=None):
        if enode not in self.peers:
            print(f"Node {self.id} adding peer at {enode}")
            if enode not in self.node_thread.connection_threads:
                # Connection
                connection, node_info = self.node_thread.connect_to(enode)
                connection.start()
            self.peers[enode] = node_info
            chain_sync_thread = ChainPinger(self, enode, CHAIN_SYNC_INTERVAL)
            mempool_sync_thread = MemPoolPinger(self, enode, MEMPOOL_SYNC_INTERVAL)
            self.sync_threads[enode] = [chain_sync_thread, mempool_sync_thread]
            chain_sync_thread.start()
            mempool_sync_thread.start()
            return True

    def remove_peer(self, enode):
        print(f"Node {self.id} removing peer at {enode}")
        self.peers.pop(enode, None)
        sync_threads = self.sync_threads.get(enode)
        if sync_threads:
            for thread in sync_threads:
                thread.stop()
            self.sync_threads.pop(enode)
        self.node_thread.disconnect_from(enode)


    def node_info(self):
        protocol = {"consensus": self.consensus}
        #info = {"enode": self.enode, "id": self.id, "ip": self.host, "port": self.port, "protocol": protocol}
        info = {"enode": self.enode, "id": self.id, "ip": self.host, "port": self.port}
        return info

    def verify_chain(self, chain):
        return self.consensus.verify_chain(chain, self.get_block('last').state)

    def broadcast_block(self, block):
        last_block = self.get_block('last')
        content = (last_block.get_header_hash(), last_block.total_difficulty)
        for p in self.peers:
            self.data_handler.send_message_to(p, content, "chain_sync")
