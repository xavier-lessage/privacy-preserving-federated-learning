from Node import *
import threading
from time import sleep


def mine_thread(node, difficulty=3):
    print("Starting the mining \n")
    i = 1
    block = Block(len(node.chain), node.get_last_block().compute_hash(), node.mempool)
    while True:
        block.update_data(node.mempool)
        if block.compute_hash()[:difficulty] != "0" * difficulty:
            block.increase_nonce()
            # print(i)
            i += 1
        else:
            print("Block added: " + str(block.compute_hash()))
            print("Attempts: " + str(i))
            print(repr(block))
            node.chain.append(block)
            node.mempool.clear()
            break


def proof_of_auth(node, time=10):
    for i in range(3):
        sleep(time)
        block = Block(len(node.chain), node.get_last_block().compute_hash(), node.mempool)
        node.chain.append(block)
