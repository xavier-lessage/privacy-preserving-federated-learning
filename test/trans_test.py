from PROJH402.src.Node import Node
from PROJH402.src.consensus.ProofOfAuth import ProofOfAuthority
from PROJH402.src.constants import LOCALHOST


def f():
    consensus = ProofOfAuthority()
    node1 = Node(1, LOCALHOST, 1234, consensus)


if __name__ == '__main__':
    f()
