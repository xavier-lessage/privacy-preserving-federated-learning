from hashlib import sha256
from random import randint
from time import time


class Block:
    def __init__(self, height, parent_hash, data, miner_id, timestamp, difficulty, total_diff):
        self.height = height
        self.parent_hash = parent_hash
        self.data = data
        self.miner_id = miner_id
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.total_difficulty = total_diff + difficulty

        self.nonce = randint(0, 10000)

        self.transactions_root = self.transactions_hash()
        self.hash = self.compute_hash()

    def compute_hash(self):
        """
        computes the hash of the block header
        :return:hash of the block header
        """
        hash_string = ""
        hash_string += str(self.height)
        hash_string += str(self.parent_hash)
        hash_string += str(self.transactions_root)
        hash_string += str(self.miner_id)
        hash_string += str(self.timestamp)
        hash_string += str(self.difficulty)
        hash_string += str(self.total_difficulty)
        hash_string += str(self.nonce)

        self.hash = sha256(hash_string.encode()).hexdigest()

        return self.hash

    def transactions_hash(self):
        """
        computes the hash of the block transactions
        :return: the hash of the transactions
        """
        hash_string = ""
        hash_string += str(self.data)

        return hash_string

    def verify(self):
        """
        :return:
        """
        pass

    def print_header(self):
        """
        Prints the block information
        """
        print("Index: ", self.height)
        print("Hash", self.compute_hash())
        print("Nonce: ", self.nonce)
        print("Previous: ", self.parent_hash)
        print("data: ", self.data)

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
        return f'Block("{self.height}", "{self.parent_hash}", "{self.data}", "{self.nonce}", "{self.miner_id}", ' \
               f'"{self.total_difficulty}") '

    def update_time(self):
        self.timestamp = time()

    def update_diff(self, diff):
        self.difficulty = diff
