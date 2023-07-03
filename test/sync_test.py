import logging
import sys

sys.path.append("/home/eksander/toychain-argos/")

from PROJH402.src.Node import Node
from PROJH402.src.consensus.ProofOfAuth import ProofOfAuthority
from PROJH402.src.Transaction import Transaction
from PROJH402.src.constants import LOCALHOST


# consensus = ProofOfWork()
consensus = ProofOfAuthority()
node1 = Node(1, LOCALHOST, 1234, consensus)
node2 = Node(2, LOCALHOST, 1235, consensus)
node3 = Node(3, LOCALHOST, 1236, consensus)
logging.basicConfig(level=logging.INFO)


def f():
    # logging.basicConfig(level=logging.INFO)
    # trans = Transaction("enode://1@127.0.0.1:1234", "enode://2@127.0.0.1:1235", {"action": "add_k", "input": 1}, 0, 0)
    # node1.mempool[trans.id] = trans
    
    
    node1.start_tcp()
    node2.start_tcp()
    node3.start_tcp()
    
    node1.start_mining()
    node2.start_mining()
    node3.start_mining()

    node1.add_peer(node2.enode)
    node1.add_peer(node3.enode)
    node2.add_peer(node1.enode)
    node2.add_peer(node3.enode)
    node3.add_peer(node1.enode)
    node3.add_peer(node2.enode)

    # sleep(35)
    # print(node1.get_block('last').state.balances)
    # print(node2.get_block('last').state.balances)
    # print(node3.get_block('last').state.balances)

import time
if __name__ == '__main__':
    f()
    max_steps = 600
    curr_step = 0
    step = 1
    while True:
        print(curr_step)
        node1.step()
        node2.step()
        node3.step()
        # time.sleep(0.000001)
        curr_step+=step
        if curr_step>max_steps:
            break

    print('Node 1')
    print(node1.display_chain())
    print('Node 2')
    print(node2.display_chain())
    print('Node 3')
    print(node3.display_chain())
