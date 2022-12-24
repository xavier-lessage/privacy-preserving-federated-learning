import pickle

from Node import *
import socket

PORT = 65432


class ConnectionThread(threading.Thread):
    def __init__(self, sock, main_node_thread, addr, timeout=20.0):
        super().__init__()

        self.node_thread = main_node_thread
        self.addr = addr
        self.sock = sock

        self.terminate_flag = threading.Event()

        self.sock.settimeout(timeout)

    def send(self, data):
        # self.sock.sendall(data.encode("utf-8"))
        self.sock.sendall(data)

    def stop(self):
        self.terminate_flag.set()

    def run(self):
        self.sock.settimeout(10.0)

        while not self.terminate_flag.is_set():
            try:
                data = self.sock.recv(4096)
                # msg = data.decode()
                msg = pickle.loads(data)
                self.node_thread.handle_data(msg, self)

            except socket.timeout:
                self.terminate_flag.set()

            except EOFError:
                pass

            except ConnectionResetError:
                print("A Connection ended abruptly")
                self.terminate_flag.set()

            except Exception as e:
                self.terminate_flag.set()
                raise e

            sleep(0.01)
        self.sock.settimeout(None)
        self.sock.close()
        sleep(1)
