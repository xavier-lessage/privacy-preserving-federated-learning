import threading
from time import sleep


class ChainPinger(threading.Thread):
    def __init__(self, node, client_addr, timeout=2.0):
        super(ChainPinger, self).__init__()

        self.node = node
        self.data_handler = node.data_handler
        self.client_addr = client_addr
        self.timeout = timeout

        self.flag = threading.Event()

    def run(self):
        while not self.flag.is_set():
            # TODO
            last_block = self.node.get_block('last')
            content = (last_block.get_header_hash(), last_block.total_difficulty)
            self.data_handler.send_message_to(self.client_addr, content, "chain_sync")
            sleep(self.timeout)

    def stop(self):
        self.flag.set()


class MemPoolPinger(threading.Thread):
    def __init__(self, node, client_addr, timeout=2.0):
        super(MemPoolPinger, self).__init__()

        self.node = node
        self.data_handler = node.data_handler
        self.client_addr = client_addr
        self.timeout = timeout

        self.flag = threading.Event()

    def run(self):
        while not self.flag.is_set():
            content = self.node.mempool
            try:
                self.data_handler.send_message_to(self.client_addr, content, "mempool_sync")
                sleep(self.timeout)
            except Exception as e:
                print(self.client_addr)
                print(content)
                print(e)
                raise e

    def stop(self):
        self.flag.set()



