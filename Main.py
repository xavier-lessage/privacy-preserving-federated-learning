from Node import *


def main():
    node0 = Node(0)
    node1 = Node(1)

    node0.add_to_mempool("Oui")
    node1.add_to_mempool("Oui")

    node1.add_block()
    # node1.print_chain()



if __name__ == '__main__':
    main()
