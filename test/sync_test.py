import multiprocessing
import os
import sys
from time import sleep, time


sys.path.append("/home/ubuntu/Documents/toychain-argos/PROJH402")

from PROJH402.src.Node import Node
from PROJH402.src.ProofOfAuth import ProofOfAuthority
from PROJH402.src.Transaction import Transaction
from PROJH402.src.constants import LOCALHOST


# consensus = ProofOfWork()
consensus = ProofOfAuthority()
node1 = Node(1, LOCALHOST, 1234, consensus)
node2 = Node(2, LOCALHOST, 1235, consensus)
node3 = Node(3, LOCALHOST, 1236, consensus)


def f():
    # trans = Transaction("U", "D", "Hello")
    # node3.mempool.add(trans)
    print(time())
    node3.start_tcp()
    node1.start_tcp()
    node2.start_tcp()
    print(time())

    node3.start_mining()
    node1.start_mining()
    node2.start_mining()

    print(time())
    node3.add_peer(node1.enode)
    node3.add_peer(node2.enode)
    print(f"Finished adding peers {time()}")
    sleep(35)
    print(node3.chain)

def g():
    print("Destroying now")
    node1.destroy()

if __name__ == '__main__':
    g()
