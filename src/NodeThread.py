import threading

import socket
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
                self.handle_connection(client_sock, client_address)

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            sleep(0.01)

        for connection in self.connection_threads.values():
            connection.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def handle_connection(self, sock, address):
        connected_node_id = sock.recv(2048).decode(ENCODING)
        sock.send(str(self.id).encode(ENCODING))
        client_thread = self.create_connection(sock, address, self.data_handler.message_queue)
        client_thread.start()

    def connect_to(self, address):
        if address in self.connection_threads:
            return self.connection_threads.get(address)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)

        sock.send(str(self.id).encode(ENCODING))
        connected_node_id = sock.recv(1024).decode(ENCODING)
        print(f"Node {self.id} connected with node: {connected_node_id}")

        thread_client = self.create_connection(sock, address, self.data_handler.message_queue)
        self.connection_threads[address] = thread_client
        # TODO change it of place
        # thread_client.start()
        return thread_client

    def disconnect_from(self, address):
        connection = self.connection_threads.get(address)
        if connection:
            connection.stop()
        else:
            print(f"Not connected with this Node {address}")

    def stop(self):
        self.terminate_flag.set()

    def create_connection(self, sock, addr, message_queue):
        return ConnectionThread(sock, self, addr, message_queue)





