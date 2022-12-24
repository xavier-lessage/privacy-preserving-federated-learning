from Node import *

DIFF = 5
node0 = Node(0, "", 1234, DIFF)
node1 = Node(1, "", 1235, DIFF+1)
node2 = Node(2, "", 1236, DIFF)


def mining_test():
    node0.start_mining()
    node0.add_to_mempool("HEJEK")
    sleep(5)
    node0.stop_mining()
    if node0.verify_chain(node0.chain):
        print("The blockchain is correct")


def tcp_test():
    node0.start_tcp()
    node1.start_tcp()
    node2.start_tcp()

    node1.tcp_thread.connect_to("127.0.0.1", 1236)
    node0.tcp_thread.connect_to("127.0.0.1", 1235)
    node0.tcp_thread.network_send("Hello")
    node0.tcp_thread.connect_to("127.0.0.1", 1236)
    node0.tcp_thread.connect_to("127.0.0.1", 1236)

    node0.stop_tcp()
    node1.stop_tcp()
    node2.stop_tcp()
    print(node1.mem_pool)
    print(node0.mem_pool)


def mem_test():
    node0.start_mining()
    node1.start_mining()
    sleep(10)
    # node0.start_mem()
    # node1.start_mem()
    # node0.mem_thread.connect_to("127.0.0.1", 1235)
    # node1.mem_thread.connect_to("127.0.0.1", 1234)
    #
    node0.start_chain_sync()
    node1.start_chain_sync()
    node0.chain_thread.connect_to("127.0.0.1", 1235)
    node1.chain_thread.connect_to("127.0.0.1", 1234)
    # node0.stop_mining()
    # node1.stop_mining()


def poa_test():
    node0.start_mem()
    node1.start_mem()
    node0.mem_thread.connect_to("127.0.0.1", 1235)
    node1.mem_thread.connect_to("127.0.0.1", 1234)
    sleep(5)
    node1.add_to_mempool("Hello")
    node1.add_to_mempool("World")

    node0.start_mining()
    node1.start_mining()
    sleep(19)
    # node0.poa_thread.stop()
    # node1.stop_mining()
    # node0.stop_mem()
    # node1.stop_mem()
    # node0.mem_thread.join()
    print("No" + str(node0.mem_pool))

if __name__ == '__main__':
    # tcp_test()
    mem_test()
    # mining_test()
    # poa_test()

