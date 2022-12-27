import uuid
from hashlib import sha256
from random import randint
from time import time

from PROJH402.src.utils import compute_hash, verify_transaction


class Block:
    def __init__(self, height, parent_hash, data, miner_id, timestamp, difficulty, total_diff, nonce=None):
        self.height = height
        self.parent_hash = parent_hash
        self.data = data
        self.miner_id = miner_id
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.total_difficulty = total_diff + difficulty

        if not nonce:
            nonce = randint(0, 1000)

        self.nonce = nonce

        self.transactions_root = self.transactions_hash()
        self.hash = self.compute_block_hash()

    def compute_block_hash(self):
        """
        computes the hash of the block header
        :return: hash of the block
        """
        list = [self.height, self.parent_hash, self.transactions_root, self.miner_id, self.timestamp, self.difficulty,
                self.total_difficulty, self.nonce]

        self.hash = compute_hash(list)

        return self.hash

    def transactions_hash(self):
        """
        computes the hash of the block transactions
        :return: the hash of the transactions
        """
        self.transactions_root = compute_hash([self.data])
        return self.transactions_root

    def verify(self):

        for transaction in self.data:
            verify_transaction(transaction)

        target_string = '1' * (256 - self.difficulty)
        target_string = target_string.zfill(256)

        hash_int = int(self.hash, 16)
        binary_hash = bin(hash_int)
        binary_hash = binary_hash[3:]

        if target_string > binary_hash:
            return True
        return False

    def print_header(self):
        """
        Prints the block information
        """
        print("Index: ", self.height)
        print("Hash", self.compute_block_hash())
        print("Nonce: ", self.nonce)
        print("Previous: ", self.parent_hash)
        print("data: ", self.data)

    def get_header_hash(self):
        header = [self.parent_hash, self.transactions_root, self.timestamp, self.difficulty, self.nonce]
        return compute_hash(header)

    def increase_nonce(self):
        self.nonce += 1

    def update_data(self, data):
        """
        Updates the data of a block
        """
        self.data = data.copy()
        self.transactions_root = self.transactions_hash()

    def __repr__(self):
        """
        Translate the block object in a string object
        :return: The constructor as a string
        """
        # TODO
        return f'["{self.height}", "{self.parent_hash}", "{self.data}", "{self.miner_id}"' \
               f', "{self.timestamp}", "{self.difficulty}", "{self.total_difficulty}", "{self.nonce}", {self.hash}]'

    def update(self, height, parent_hash, data, difficulty, total_difficulty):
        self.timestamp = time()
        self.height = height
        self.parent_hash = parent_hash
        self.update_data(data)
        self.difficulty = difficulty
        self.total_difficulty = total_difficulty


def block_to_list(block):
    return [block.height, block.parent_hash, block.data, block.miner_id, block.timestamp, block.difficulty,
            block.total_difficulty, block.nonce]


def create_block_from_list(list):
    height = list[0]
    parent_hash = list[1]
    data = list[2]
    miner_id = list[3]
    timestamp = list[4]
    difficulty = list[5]
    total_difficulty = list[6] - difficulty
    nonce = list[7]

    return Block(height, parent_hash, data, miner_id, timestamp, difficulty, total_difficulty, nonce)
