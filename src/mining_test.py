from Node import *
import MiningThreads

def f():
    thread1 = MiningThread(node, 4)
    thread2 = AddMempoolThread(node, "Hi")
    thread1.start()
    thread2.start()
    thread2.join()
    thread1.join()
    node.print_chain()

def g():
    node = Node(2)
    # node.add_block()
    # node.print_chain()

if __name__ == '__main__':
    f()