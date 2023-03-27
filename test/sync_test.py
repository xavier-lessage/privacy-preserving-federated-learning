import logging
import multiprocessing
import os
import sys
import threading
from time import sleep, time

from PROJH402.src.Block import State, Block, block_to_list, create_block_from_list

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
logging.basicConfig(level=logging.INFO)


def f():
    # logging.basicConfig(level=logging.INFO)
    trans = Transaction("enode://1@127.0.0.1:1234", "enode://2@127.0.0.1:1235", {"action": "add_k", "input": 1}, 0)
    node1.mempool[trans.id] = trans
    node3.start_tcp()
    node1.start_tcp()
    node2.start_tcp()

    node3.start_mining()
    node1.start_mining()
    node2.start_mining()

    node3.add_peer(node1.enode)
    node3.add_peer(node2.enode)

    # sleep(35)
    # print(node1.get_block('last').state.balances)
    # print(node2.get_block('last').state.balances)
    # print(node3.get_block('last').state.balances)

def g():
    s = State({"enode://1@127.0.0.1:1234": 4, "n": 3})
    trans = Transaction("enode://1@127.0.0.1:1234", "enode://2@127.0.0.1:1235", {"action": "add_k", "input": 1}, 0)
    b = Block(1, 0000, [trans], 3, 0, 0, 0, state_var=s.balances)
    b.update_state(s)
    l = block_to_list(b)
    b = create_block_from_list(l)
    print(b.state.balances)


if __name__ == '__main__':
    f()
