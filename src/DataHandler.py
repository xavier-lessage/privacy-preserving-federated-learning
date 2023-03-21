import pickle
import threading
from queue import Queue

from PROJH402.src import constants
from PROJH402.src.Block import block_to_list
from PROJH402.src.utils import dict_to_transaction


class DataHandler:
    def __init__(self, node, node_thread):
        self.node = node
        self.node_thread = node_thread
        self.enode = self.node.enode
        self.id = node.id

        self.flag = threading.Event()

        # {enode : height}
        self.pending_block_request = {}
        self.message_queue = Queue()
        # threading.Thread(target=self.handle_messages).start()

    def stop(self):
        self.flag.set()

    def handle_data(self, msg):
        """
        Choose action to do from the message information
        """
        if constants.DEBUG:
            print("Node " + str(self.id) + " received : " + str(msg))

        if not self.check_message_validity(msg):
            print("invalid message")
            return

        msg_type = msg["type"]

        if msg_type == "mempool_sync":
            self.update_mempool(msg["data"])
        if msg_type == "chain_sync":
            self.handle_chain_sync(msg)
            # print("Node " + str(self.id) + " received : " + str(msg))
        if msg_type == "block":
            self.handle_block(msg)
        if msg_type == "chain":
            self.handle_partial_chain(msg)
            # print("Node " + str(self.id) + " received : " + str(msg))

    def check_message_validity(self, message):
        mandatory_keys = ["data", "type", "receiver", "sender"]
        if isinstance(message, dict):
            for key in mandatory_keys:
                if key not in message:
                    return False

            if message["receiver"] != self.enode:
                # wrong address
                print("wrong addr")
                return False
            return True
        return False

    def send_message_to(self, enode, content, msg_type):
        message = self.construct_message(content, msg_type, enode)

        dumped_message = pickle.dumps(message)
        if enode not in self.node_thread.connection_threads:
            return
        else:
            connection = self.node_thread.connection_threads[enode]
        connection.send(dumped_message)

    def construct_message(self, data, msg_type, receiver):
        message = {"type": msg_type, "receiver": receiver, "sender": self.enode, "data": data}
        return message

    def handle_chain_sync(self, message):
        last_block = self.node.get_block('last')
        if message["data"] == (last_block.get_header_hash(), last_block.total_difficulty):
            # Chains are synchronised
            if constants.DEBUG:
                print(f"Node {self.node.id} is chain sync")
            return

        if last_block.total_difficulty < message["data"][1]:
            # If the chains have equal sizes, node keeps his
            # If the chain of the node is longer than the received one, let him do the work
            self.request_block(len(self.node.chain) - 1, message["sender"])
        else:
            if constants.DEBUG:
                print(f"Node {self.node.id} has a current diff of {last_block.total_difficulty}")

    def request_block(self, height, enode):
        if enode in self.pending_block_request:
            if self.pending_block_request[enode] < height:
                # Currently in a process to find the common block
                print("Currently in a process to find the common block")
                return
        block = self.node.get_block(height)
        content = (block.get_header_hash(), block.total_difficulty, height)
        self.send_message_to(enode, content, "block")
        # print(f"{self.node.id} Sending request")
        self.pending_block_request[enode] = height

    def handle_block(self, message):
        """
        Tries to find the block in its blockChain
        """
        block_header = message["data"][0]
        total_difficulty = message["data"][1]
        height = message["data"][2]
        potential_common_block = self.node.get_block(height)
        if potential_common_block.get_header_hash() == block_header \
                and potential_common_block.total_difficulty == total_difficulty:
            # Common block found
            print(f"common block found in node {self.node.id}")
            partial_chain = []
            i = height + 1
            # print(self.node.chain)
            while i < len(self.node.chain):
                partial_chain.append(block_to_list(self.node.get_block(i)))
                i += 1
            content = partial_chain
        else:
            content = None
        self.send_message_to(message["sender"], content, "chain")

    def handle_partial_chain(self, message):
        """
        Handle the result of the block request
        """
        height = self.pending_block_request.get(message["sender"])
        if message["data"] is None:
            # Try again with chain[height-1]
            self.request_block(height-1, message["sender"])
            return
        self.pending_block_request.pop(message["sender"], None)
        self.node.sync_chain(message["data"], height)

    def update_mempool(self, transactions):
        _list = []
        for d in transactions:
            _list.append(dict_to_transaction(d))
        self.node.sync_mempool(_list)



