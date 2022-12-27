from time import sleep

from PROJH402.src.Block import Block, create_block_from_list, block_to_list
from PROJH402.src.Node import Node
from PROJH402.src.constants import LOCALHOST, MINING_DIFFICULTY
from PROJH402.src.utils import compute_hash, verify_chain

node0 = Node(0, LOCALHOST, 1234, MINING_DIFFICULTY)
node1 = Node(1, LOCALHOST, 1235, MINING_DIFFICULTY)
node2 = Node(2, LOCALHOST, 1236, MINING_DIFFICULTY)


def f():
    node0.mempool.add("jj")
    node0.start_tcp()
    node1.start_tcp()
    node2.start_tcp()

    node0.start_mining()
    node1.start_mining()
    node2.start_mining()

    node0.add_peer((LOCALHOST, 1235))
    node0.add_peer((LOCALHOST, 1236))

    sleep(10)
    node0.remove_peer((LOCALHOST, 1235))
    sleep(12)
    node0.add_peer((LOCALHOST, 1235))


if __name__ == '__main__':
    f()
