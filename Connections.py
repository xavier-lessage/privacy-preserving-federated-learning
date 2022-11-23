from Node import *
import socket

PORT = 65432


class ConnectionThread(threading.Thread):
    def __init__(self, node, sock, id, host, port):
        super().__init__()

        self.node = node
        self.id = id
        self.host = host
        self.sock = sock
        self.port = port

        self.terminate_flag = threading.Event()

    def send(self, data):
        self.sock.sendall(data.encode("utf-8"))

    def stop(self):
        self.terminate_flag.set()

    def run(self):
        self.sock.settimeout(10.0)

        while not self.terminate_flag.is_set():
            data = self.sock.recv(4096)
            msg = data.decode()
            print(msg)
            self.node.add_to_mempool(msg)
            sleep(0.01)
        self.sock.settimeout(None)
        self.sock.close()
        sleep(1)


class NodeThread(threading.Thread):
    """
    Thread used by the node to communicate to other nodes
    """

    def __init__(self, node, host="", port=652, id=0):
        super().__init__()
        self.terminate_flag = threading.Event()

        self.id = id
        self.node = node

        self.host = host
        self.ip = host
        self.port = port

        self.nodes_connected = []
        self.msgs = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Initialisation of the Node on port: " + str(self.port))
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(10.0)
        self.sock.listen(1)

    def network_send(self, message):
        for i in self.nodes_connected:
            i.send(message)

    def connect_to(self, host, port):
        # for node in self.nodes_connected:
        #         # if node.host == host:
        #     #     print("[connect_to]: Already connected with this node.")
        #     #     return True

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        sock.send(str(self.id).encode("utf-8"))
        connected_node_id = sock.recv(1024).decode("utf-8")
        print("connected_node_id: ", connected_node_id)

        thread_client = self.create_connection(
            sock, connected_node_id, host, port
        )
        self.nodes_connected.append(thread_client)

    def stop(self):
        self.terminate_flag.set()

    def run(self):
        while not self.terminate_flag.is_set():
            try:
                connection, client_address = self.sock.accept()
                connected_node_id = connection.recv(2048).decode("utf-8")
                connection.send(str(self.id).encode("utf-8"))

                if self.id != connected_node_id:
                    thread_client = self.create_connection(
                        connection,
                        connected_node_id,
                        client_address[0],
                        client_address[1],
                    )
                    thread_client.start()

                    self.nodes_connected.append(thread_client)
                else:
                    connection.close()

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            sleep(0.01)

        for t in self.nodes_connected:
            t.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def create_connection(self, sock, id, host, port):
        return ConnectionThread(self.node, sock, id, host, port)
