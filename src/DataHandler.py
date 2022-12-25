import pickle
import threading
import time
import uuid
from queue import Queue

from PROJH402.src import constants


class DataHandler:
    def __init__(self, node, node_thread):
        self.node = node
        self.node_thread = node_thread
        self.host = node_thread.host
        self.port = node_thread.port
        self.id = node.id

        self.flag = threading.Event()

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
        if constants.DEBUG:
            print("Node " + str(self.id) + " received : " + str(msg))

        if not self.check_message_validity(msg):
            return

        msg_type = msg["type"]
        sender = msg["sender"]
        self.node_thread.connection_threads[sender] = connection  # Register the connection thread with the actual sender
        connection.client_address = sender
        self.node.add_peer(sender)
        # print(self.node.peers)

        if msg_type == "mempool":
            self.node.mem_pool.update(msg["data"])
        if msg_type == "chain":
            # TODO
            # self.node.sync_chain(msg["data"])
            pass

    def check_message_validity(self, message):
        mandatory_keys = ["data", "type", "receiver", "msg_id", "sender"]
        if isinstance(message, dict):
            for key in mandatory_keys:
                if key not in message:
                    return False

            if message["receiver"][0] != self.host or message["receiver"][1] != self.port:
                # wrong address
                print("wrong add")
                return False
            return True
        return False

    def send_message_to(self, addr, content, msg_type, msg_id=None):
        receiver = addr
        message = self.construct_message(content, msg_type, addr, msg_id)

        dumped_message = pickle.dumps(message)
        if receiver not in self.node_thread.connection_threads:
            connection = self.node_thread.connect_to(receiver)
            # connection.start()
        else:
            connection = self.node_thread.connection_threads[receiver]
        try:
            connection.send(dumped_message)

        except Exception as e:
            print(self.node_thread.id)
            raise e

    def construct_message(self, data, msg_type, receiver=None, msg_id=None):
        message = {"type": msg_type, "time": str(time.time()), "receiver": receiver}

        if msg_id is not None:
            message["msg_id"] = msg_id
        else:
            message["msg_id"] = uuid.uuid4()
        message["sender"] = (self.host, self.port)
        message["data"] = data
        return message

