import urllib.parse

from toychain.src.Block import Block
from toychain.src.Transaction import Transaction
from toychain.src.NodeServerThread import NodeServerThread
from toychain.src.Pingers import ChainPinger, MemPoolPinger
from toychain.src.constants import ENCODING, CHAIN_SYNC_INTERVAL, MEMPOOL_SYNC_INTERVAL, DEBUG
from toychain.src.utils import CustomTimer, create_block_from_list
import logging
logger = logging.getLogger('w3')

from multiprocessing import Process

import numpy as np

from collections import OrderedDict
import flwr as fl

import hashlib

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision.datasets import CIFAR10
from torchvision.transforms import Compose, Normalize, ToTensor
from tqdm import tqdm

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class Net(nn.Module):
    """Model (simple CNN adapted from 'PyTorch: A 60 Minute Blitz')"""

    def __init__(self) -> None:
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

 
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


def train(net, trainloader, epochs):
    """Train the model on the training set."""
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
    for _ in range(epochs):
        for images, labels in tqdm(trainloader):
            optimizer.zero_grad()
            criterion(net(images.to(DEVICE)), labels.to(DEVICE)).backward()
            optimizer.step()


def test(net, testloader):
    """Validate the model on the test set."""
    criterion = torch.nn.CrossEntropyLoss()
    correct, loss = 0, 0.0
    with torch.no_grad():
        for images, labels in tqdm(testloader):
            outputs = net(images.to(DEVICE))
            labels = labels.to(DEVICE)
            loss += criterion(outputs, labels).item()
            correct += (torch.max(outputs.data, 1)[1] == labels).sum().item()
    accuracy = correct / len(testloader.dataset)
    return loss, accuracy


def load_data():
    """Load CIFAR-10 (training and test set)."""
    trf = Compose([ToTensor(), Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    trainset = CIFAR10("./data", train=True, download=True, transform=trf)
    trainset.data = trainset.data[:32]
    trainset.targets = trainset.targets[:32]
    testset = CIFAR10("./data", train=False, download=True, transform=trf)
    testset.data = testset.data[:32]
    testset.targets = testset.targets[:32]
    return DataLoader(trainset, batch_size=32, shuffle=True), DataLoader(testset)

net = Net().to(DEVICE)
trainloader, testloader = load_data()


class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in net.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(net.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        net.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        train(net, trainloader, epochs=1)
        return self.get_parameters(config={}), len(trainloader.dataset), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = test(net, testloader)
        return float(loss), len(testloader.dataset), {'accuracy': accuracy}


class Node:
    """
    Class representing a 'user' that has his id, his blockchain and his mem-pool
    """

    def __init__(self, id, host, port, consensus):
        self.id = id
        self.chain = []
        self.mempool = {}

        # Transactions contained in the chain
        self.my_transaction_nonce = 0
        self.previous_transactions_id = set()

        self.host = host
        self.port = port

        self.enode = f"enode://{self.id}@{self.host}:{self.port}"

        self.consensus = consensus
        # Initialize the genesis Block
        self.chain.append(self.consensus.genesis)

        # {enode: node_info}
        self.peers = {}

        self.custom_timer = CustomTimer()

        self.node_server_thread = NodeServerThread(self, host, port, id)
        self.message_handler = self.node_server_thread.message_handler

        # Sync Threads
        self.mempool_sync_thread = MemPoolPinger(self)
        self.chain_sync_thread = ChainPinger(self)

        self.syncing = False
        self.mining = False
        self.mining_thread = consensus.block_generation(self)

        # Flower (federated learning)
        self.flower_client = FlowerClient()

        self.h = hashlib.new('sha256')
        self.hashing = True


    

    @property
    def sc(self):
        return self.get_block('latest').state
    
    def step(self):
        """
        Executes a time step for this node
        """
        self.custom_timer.step()
        self.mempool_sync_thread.step()
        self.chain_sync_thread.step()
        self.mining_thread.step()
    
    def start_mining(self):
        print(f"Node {self.id} started mining")
        self.mining_thread.start()
        # x = threading.Thread(target=self.mining_thread.start())
        # x.start()
        self.mining = True

    def stop_mining(self):
        self.mining_thread.stop()
        self.mining = False
        print("Node " + str(self.id) + " stopped mining")

    def start_tcp(self):
        """
        starts the NodeServerThread that handles the TCP connection with other nodes
        """
        self.syncing = True
        self.node_server_thread.start()
        self.chain_sync_thread.start()
        self.mempool_sync_thread.start()

    def stop_tcp(self):
        peers = list(self.peers.keys())
        for peer in peers:
            self.remove_peer(peer)

        self.node_server_thread.stop()
        self.chain_sync_thread.stop()
        self.mempool_sync_thread.stop()
        self.syncing = False

    def destroy_node(self):
        logger.info("Destroyed")
        self.stop_tcp()
        self.stop_mining()

    def get_block(self, height):
        """
        returns the block at the referred height in the blockchain
        """
        if height == 'last' or height == 'latest':
            return self.chain[-1]
        elif height == 'first':
            return self.chain[0]
        else:
            try:
                return self.chain[height]
            except IndexError:
                return None

    def sync_mempool(self, transactions):
        """
        Synchronises the mempool with a list of transaction objects
        """
        for transaction in transactions:
            if transaction.id not in self.previous_transactions_id:
                self.add_to_mempool(transaction)

    def sync_chain(self, chain_repr, height):
        """
        Adds the partial chain received to the blockchain

        Args:
            chain_repr(list[str]): list of block representation from a partial chain received
            height: the height at which the partial chain is supposed to be inserted
        """
        logger.info("Merging chains")
        chain = []
        # Reconstruct the partial chain
        for block_repr in chain_repr:
            block_vars = create_block_from_list(block_repr)
            chain.append(Block(*block_vars))

        # if chain[-1].total_difficulty < self.get_block('last').total_difficulty:
        #     return

        if not self.verify_chain(chain):
            return

        if chain[0].parent_hash == self.get_block(height).hash:
            # update mempool
            for block in chain:
                for transaction in block.data:
                    self.mempool.pop(transaction.id, None)
                    self.previous_transactions_id.add(transaction.id)

            # retrieving possible missed transactions
            for block in self.chain[height+1:]:
                for transaction in block.data:
                    if transaction.id not in self.previous_transactions_id:
                        self.add_to_mempool(transaction)

            # Replace self chain with the other chain
            del self.chain[height+1:]
            self.chain.extend(chain)
            logger.info(f"Node {self.id} has updated its chain, total difficulty : {self.get_block('last').total_difficulty}, n = {chain[-1].state.state_variables.get('n')}")
            for block in self.chain[-5:]:
                logger.info(f"{block.__repr__()}   ##{len(block.data)}##  {block.state.state_variables}")
        else:
            logger.info("Chain does not fit here")

    def add_peer(self, enode):
        if enode not in self.peers:
            logger.debug(f"Node {self.id} adding peer at {enode}")
            parsed_enode = urllib.parse.urlparse(enode)
            node_info = {"id": parsed_enode.username, "host": parsed_enode.hostname, "port": parsed_enode.port, "enode": enode}
            self.peers[enode] = node_info
            return True

    def remove_peer(self, enode):
        if self.peers.pop(enode, None):
            logger.debug(f"Node {self.id} removing peer at {enode}")

    def node_info(self):
        info = {"enode": self.enode, "id": self.id, "ip": self.host, "port": self.port}
        return info

    def verify_chain(self, chain):
        return self.consensus.verify_chain(chain, self.get_block('last').state)

    def send_transaction(self, transaction):
        self.add_to_mempool(transaction)
        return transaction.id

    def get_transaction(self, transaction_id):
        """
        Returns the transaction with the indicated id
        if it is not in the chain or in the mempool : returns None
        """
        transaction = self.mempool.get(transaction_id, None)
        if not transaction:
            for block in self.chain:
                for t in block.data:
                    if t.id == transaction_id:
                        return t
        return transaction

    def get_transaction_receipt(self, transaction_id):
        """
        returns whether the specified transaction is in the chain
        """
        if transaction_id in self.previous_transactions_id:
            return True
        return False

    def get_all_transactions(self):
        """
        Returns a list with all transaction objects
        """
        all_txs = []
        for block in self.chain:
            all_txs.extend(block.data)
        return all_txs

    def get_last_signed_block(self):
        for block in reversed(self.chain):
            if block.miner_id == self.enode:
                return block.height
        return 0

    def add_to_mempool(self, transaction):
        self.mempool[transaction.id] = transaction

    def display_chain(self):
        for block in self.chain:
            print(block)

    @property  
    def key(self):
        return self.id
    
    def gen_enode(self, id, host = '127.0.0.1', port = 0):
        if port == 0:
            port = 1233 + id
        return f"enode://{id}@{host}:{port}"

    def flower_fit_helper(self, timestamp):
        old_params = self.flower_client.get_parameters({})
        new_params = self.flower_client.fit(old_params, {})


        self.save_params(new_params)

        txdata = {'function': 'storeParameters', 'inputs': [new_params]}
        if self.hashing:
            #b = new_params.view(numpy.uint8)
            new_params = hashlib.sha1(str(new_params).encode('utf-8')).hexdigest()
            txdata = {'function': 'storeParameters', 'inputs': [new_params]}

        # TODO: update timestamp
        nonce = 1
        print("Sending transaction")
        tx = Transaction(sender = self.enode, receiver = 2, value = 0, data = txdata, nonce = nonce, timestamp = 1000)
        self.send_transaction(tx)

        #print(new_params)
        return new_params

    def flower_fit(self, timestamp):
        txdata = {'function': 'storeParameters', 'inputs': [1]}
        nonce = 1
        print("Sending transaction")
        tx = Transaction(sender = self.enode, receiver = 2, value = 0, data = txdata, nonce = nonce, timestamp = 1000)
        self.send_transaction(tx)

    def flower_fit(self, timestamp):
        client_process = Process(target=self.flower_fit_helper, args=(timestamp,))
        client_process.start()

    def start_flower_client_helper(self):
        print("Starting Flower client")
        fl.client.start_numpy_client(
            server_address="0.0.0.0:8000",
            client=self.flower_client)

    def start_flower_client(self):
        client_process = Process(target=self.start_flower_client_helper)
        client_process.start()

    def get_flower_parameters(self):
        return self.flower_client.get_parameters(config={})

    def retrieve_unhashed_params(self):
        pass

        
    def save_params(self, params):
        with open('params.npy', 'wb') as f:
            np.save(f, np.array([1, 2]))

    def read_params(self):
        """
        Read parameters of a model from a NumPy file and return them
        """

        with open('params.npy', 'rb') as f:
            params = np.load(f)
        return params


    def aggregate_model(self):
        """
        Aggregate model parameters based on a Numpy file
        """
        pass
