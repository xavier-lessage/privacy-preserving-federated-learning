from time import sleep

from PROJH402.src.Block import Block, create_block_from_list, block_to_list
from PROJH402.src.ProofOfAuth import ProofOfAuthority
from PROJH402.src.ProofOfWork import ProofOfWork
from PROJH402.src.Node import Node
from PROJH402.src.constants import LOCALHOST
from PROJH402.src.utils import compute_hash, verify_chain

# consensus = ProofOfWork()
consensus = ProofOfAuthority()
node0 = Node(0, LOCALHOST, 1234, consensus)
node1 = Node(1, LOCALHOST, 1235, consensus)
node2 = Node(2, LOCALHOST, 1236, consensus)


def f():
    node0.mempool.add("jj")
    node0.start_tcp()
    node1.start_tcp()
    node2.start_tcp()

    node0.start_mining()
    node1.start_mining()
    node2.start_mining()

    node0.add_peer(node1.enode)
    node0.add_peer(node2.enode)

    sleep(35)
    print(node0.chain)


if __name__ == '__main__':
    f()