import pickle
import threading
from queue import Queue

from PROJH402.src import constants
from PROJH402.src.Block import block_to_list


class DataHandler:
    def __init__(self, node, node_thread):
        self.node = node
        self.node_thread = node_thread
        self.host = node_thread.host
        self.port = node_thread.port
        self.id = node.id

        self.flag = threading.Event()

        # {addr : height}
        self.pending_block_request = {}
        self.message_queue = Queue()
        threading.Thread(target=self.handle_messages).start()

    def stop(self):
        self.flag.set()

    def handle_messages(self):
        """
        Handle message that are put in a queue to avoid data inconsistency
        """
        while not self.flag.is_set():
            try:
                while not self.message_queue.empty():
                    msg, connection = self.message_queue.get()
                    if msg:
                        self.handle_data(msg, connection)

            except Exception as e:
                self.node.stop_tcp()
                raise e

    def handle_data(self, msg, connection):
        """
        Choose action to do from the message information
        """
        if constants.DEBUG:
            print("Node " + str(self.id) + " received : " + str(msg))

        if not self.check_message_validity(msg):
            "not valid"
            return

        msg_type = msg["type"]

        if msg_type == "mempool_sync":
            self.node.mempool.update(msg["data"])
        if msg_type == "chain_sync":
            self.handle_chain_sync(msg, connection)
        if msg_type == "block":
            self.handle_block(msg)
        if msg_type == "chain":
            self.handle_partial_chain(msg)

    def check_message_validity(self, message):
        mandatory_keys = ["data", "type", "receiver", "sender"]
        if isinstance(message, dict):
            for key in mandatory_keys:
                if key not in message:
                    return False

            if message["receiver"][0] != self.host or message["receiver"][1] != self.port:
                # wrong address
                print("wrong addr")
                return False
            return True
        return False

    def send_message_to(self, addr, content, msg_type, msg_id=None):
        receiver = addr
        message = self.construct_message(content, msg_type, addr)

        dumped_message = pickle.dumps(message)
        if receiver not in self.node_thread.connection_threads:
            return
        else:
            connection = self.node_thread.connection_threads[receiver]
        connection.send(dumped_message)

    def construct_message(self, data, msg_type, receiver=None):
        message = {"type": msg_type, "receiver": receiver, "sender": (self.host, self.port), "data": data}
        return message

    def handle_chain_sync(self, message, connection):
        last_block = self.node.get_block('last')
        if message["data"] == (last_block.get_header_hash(), last_block.total_difficulty):
            # Chains are synchronised
            print(f"Node {self.node.id} is chain sync")
            return

        if last_block.total_difficulty < message["data"][1]:
            # If the chains have equal sizes, node keeps his
            # If the chain of the node is longer than the received one, let him do the work

            self.request_block(len(self.node.chain) - 1, message["sender"])

    def request_block(self, height, addr):
        if addr in self.pending_block_request:
            if self.pending_block_request[addr] < height:
                # Currently in a process to find the common block
                return
        block = self.node.get_block(height)
        content = (block.get_header_hash(), block.total_difficulty, height)
        self.send_message_to(addr, content, "block")
        self.pending_block_request[addr] = height

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
            print(self.node.chain)
            while i < len(self.node.chain):
                partial_chain.append(block_to_list(self.node.get_block(i)))
                i += 1
            content = partial_chain
        else:
            content = None
        self.send_message_to(message["sender"], content, "chain")

    def handle_partial_chain(self, message):
        height = self.pending_block_request.get(message["sender"])
        if message["data"] is None:
            # Try again with chain[height-1]
            self.request_block(height-1, message["sender"])
            return
        self.pending_block_request.pop(message["sender"])
        self.node.sync_chain(message["data"], height)






