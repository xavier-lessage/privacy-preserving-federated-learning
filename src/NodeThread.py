import pickle
import threading

import socket
from queue import Queue
from time import sleep

from PROJH402.src import constants
from PROJH402.src.ConnectionThread import ConnectionThread
from PROJH402.src.DataHandler import DataHandler
from PROJH402.src.constants import ENCODING


class NodeThread(threading.Thread):
    """
    Thread used by the node to communicate to other nodes
    """

    def __init__(self, node, host, port, id):
        super().__init__()

        self.id = id
        self.node = node
        self.host = host
        self.port = port

        self.data_handler = DataHandler(node, self)

        self.terminate_flag = threading.Event()

        self.connection_threads = {}
        self.disconnections = Queue()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Node " + str(self.id) + " starting on port " + str(self.port))
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1.0)
        self.sock.listen(1)

    def run(self):
        while not self.terminate_flag.is_set():
            try:
                client_sock, client_address = self.sock.accept()
                self.handle_connection(client_sock)

            except socket.timeout:
                pass

            except Exception as e:
                print("error")
                raise e

            sleep(0.01)

            while not self.disconnections.empty():
                address = self.disconnections.get()
                self.node.remove_peer(address)
                connection = self.connection_threads.pop(address, None)
                if connection:
                    connection.stop()

        for connection in self.connection_threads.values():
            connection.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def handle_connection(self, sock):
        connected_node_info = sock.recv(1024)
        connected_node_info = pickle.loads(connected_node_info)
        node_info = self.node.node_info()
        node_info = pickle.dumps(node_info)
        sock.send(node_info)

        host = connected_node_info.get("ip")
        port = connected_node_info.get("port")
        address = (host, port)
        client_thread = self.create_connection(sock, address, self.data_handler.message_queue)
        self.connection_threads[address] = client_thread
        client_thread.start()
        self.node.add_peer(address, connected_node_info)

    def connect_to(self, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)

        node_info = self.node.node_info()
        node_info = pickle.dumps(node_info)
        sock.send(node_info)
        connected_node_info = sock.recv(1024)
        connected_node_info = pickle.loads(connected_node_info)
        connected_node_id = connected_node_info.get("id")
        print(f"Node {self.id} connected with node: {connected_node_id}")

        thread_client = self.create_connection(sock, address, self.data_handler.message_queue)
        self.connection_threads[address] = thread_client
        return thread_client, connected_node_info

    def disconnect_from(self, address):
        connection = self.connection_threads.get(address)
        if connection:
            connection.stop()
            self.connection_threads.pop(address)
        else:
            print(f"Not connected with this Node {address}")

    def stop(self):
        self.terminate_flag.set()

    def create_connection(self, sock, addr, message_queue):
        return ConnectionThread(sock, self, addr, message_queue, self.disconnections)





