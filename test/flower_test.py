import logging
import sys
from multiprocessing import Process

sys.path.append("/home/volker/software/")

from toychain.src.Node import Node
from toychain.src.consensus.ProofOfAuth import ProofOfAuthority
from toychain.src.Block import Block, State
from toychain.src.Transaction import Transaction
from toychain.src.constants import LOCALHOST
from toychain.src.utils import gen_enode


# Flower-related
from typing import List, Tuple
import flwr as fl
from flwr.common import Metrics


LOGGER_NAME = "flwr"
FLOWER_LOGGER = logging.getLogger(LOGGER_NAME)
FLOWER_LOGGER.setLevel(logging.ERROR)

auth_signers = [gen_enode(i) for i in range(1,4)]
initial_state = State()

GENESIS_BLOCK = Block(0, 0000, [], auth_signers, 0, 0, 0, nonce = 1, state = initial_state)
CONSENSUS = ProofOfAuthority(genesis = GENESIS_BLOCK)

# Create the nodes with (id, host, port, consensus_protocol)
node1 = Node(1, LOCALHOST, 1234, CONSENSUS)
node2 = Node(2, LOCALHOST, 1235, CONSENSUS)
node3 = Node(3, LOCALHOST, 1236, CONSENSUS)

#allnodes = [node1, node2, node3]
allnodes = [node1, node2]

logging.basicConfig(level=logging.INFO)

def init_flower_server():

    fl.server.start_server(
        server_address="0.0.0.0:8000",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=fl.server.strategy.FedAvg())


def init_flower_client(node):

    node.start_flower_client()

def init_network():

    # Add the peers of each node
    node1.add_peer(node2.enode)
    #node1.add_peer(node3.enode)
    node2.add_peer(node1.enode)
    #node2.add_peer(node3.enode)
    node3.add_peer(node1.enode)
    node3.add_peer(node2.enode)
    

import time
if __name__ == '__main__':

    # FlowerServer (will be removed later)
    flower_server_thread = Process(target=init_flower_server, name="FlowerServerThread", args=())
    flower_server_thread.start()


    # Flower clients
    for node in allnodes:
        node.start_tcp()
        node.start_mining()
        #node.start_flower_client() # Start Flower client


    # Initialize the blockchain framework (connect all nodes to each other)
    init_network()

    # Setup simulation steps
    max_steps = 10000
    curr_step = 0
    step = 1


    node.flower_fit(curr_step)


    while True:

        for node in allnodes:
            node.step()

        time.sleep(0.05)
        curr_step += step

        if (curr_step % 100) == 0:
            print(curr_step)

            #txdata = {'function': 'storeParameters', 'inputs': [1]}
            #nonce = 1
            #tx = Transaction(sender = node1.enode, receiver = 2, value = 0, data = txdata, nonce = nonce, timestamp = curr_step)
            node1.flower_fit_helper(1000)

            # Display the final blockchains at the end of the simulation
            # print('Node 1')
            # print(node1.display_chain())
            # print('Node 2')
            # print(node2.display_chain())
            # print('Node 3')
            # print(node3.display_chain())

            #print(node.get_flower_parameters()[:5])


        if curr_step > max_steps:
            break
    
