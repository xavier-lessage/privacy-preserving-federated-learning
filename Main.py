from Node import *

node0 = Node(0, "", 1234)
node1 = Node(1, "", 1235)
node2 = Node(2, "", 1236)


def mining_test():
    node0.start_mining()
    sleep(5)
    node0.stop_mining()
    node0.verify_chain(node0.chain)


def tcp_test():
    node0.start_tcp()
    node1.start_tcp()
    node2.start_tcp()
    node1.tcp_thread.connect_to("127.0.0.1", 1236)
    node0.tcp_thread.connect_to("127.0.0.1", 1235)
    # node0.tcp_thread.connect_to("127.0.0.1", 1236)
    node0.tcp_thread.network_send("Hello")
    sleep(5)
    node0.stop_tcp()
    node0.tcp_thread.connect_to("127.0.0.1", 1236)
    # node0.stop_tcp()


def comp_test():
    node0.start_mining()
    node1.start_mining()
    sleep(1)
    thread = AddMempoolThread(node0, "Hello")
    thread.start()
    thread.join()
    sleep(10)
    node0.stop_mining()
    node1.stop_mining()


if __name__ == '__main__':
    tcp_test()
    # mining_test()
    # comp_test()
