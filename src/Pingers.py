import threading
from time import sleep


class ChainPinger(threading.Thread):
    def __init__(self, node, enode, timeout=2.0):
        super(ChainPinger, self).__init__()

        self.node = node
        self.data_handler = node.data_handler
        self.dest_enode = enode
        self.timeout = timeout

        self.flag = threading.Event()

    def run(self):
        while not self.flag.is_set():
            last_block = self.node.get_block('last')
            content = (last_block.get_header_hash(), last_block.total_difficulty)
            try:
                self.data_handler.send_message_to(self.dest_enode, content, "chain_sync")
                sleep(self.timeout)

            except (ConnectionAbortedError, BrokenPipeError):
                self.flag.set()

            except Exception as e:
                self.flag.set()
                raise e

        # print(f"PINGER ENDING IN NODE {self.node.id}")

    def stop(self):
        self.flag.set()


class MemPoolPinger(threading.Thread):
    def __init__(self, node, dest_enode, interval=2.0):
        super(MemPoolPinger, self).__init__()

        self.node = node
        self.data_handler = node.data_handler
        self.dest_enode = dest_enode
        self.interval = interval

        self.flag = threading.Event()

    def run(self):
        while not self.flag.is_set():
            content = self.node.mempool
            try:
                self.data_handler.send_message_to(self.dest_enode, content, "mempool_sync")
                sleep(self.interval)

            except (ConnectionAbortedError, BrokenPipeError):
                # self.flag.set()
                pass
            except Exception as e:
                self.flag.set()
                raise e

    def stop(self):
        self.flag.set()



