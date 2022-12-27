import pickle

import socket
import threading
from time import sleep, time

from PROJH402.src.Pingers import ChainPinger, MemPoolPinger
from PROJH402.src.constants import MEMPOOL_SYNC_INTERVAL, CHAIN_SYNC_INTERVAL

PORT = 65432


class ConnectionThread(threading.Thread):
    def __init__(self, sock, main_node_thread, addr, message_queue, disconnection_queue, timeout=8.0):
        super().__init__()

        self.node_thread = main_node_thread
        self.addr = addr
        self.sock = sock
        self.message_queue = message_queue
        self.disconnection_queue = disconnection_queue

        self.terminate_flag = threading.Event()
        self.sock.settimeout(timeout)

        self.timer = time()

    def send(self, data):
        # self.sock.sendall(data.encode("utf-8"))
        self.sock.sendall(data)

    def stop(self):
        self.terminate_flag.set()

    def run(self):
        while not self.terminate_flag.is_set():
            try:
                data = self.sock.recv(4096)
                msg = pickle.loads(data)
                self.message_queue.put((msg, self))

            except socket.timeout:
                self.terminate_flag.set()

            except EOFError:
                pass

            except ConnectionResetError or ConnectionAbortedError:
                print("A Connection ended abruptly")
                self.terminate_flag.set()

            except Exception as e:
                self.terminate_flag.set()
                raise e

        self.disconnection_queue.put(self.addr)
        self.sock.settimeout(None)
        self.sock.close()
        sleep(1)
