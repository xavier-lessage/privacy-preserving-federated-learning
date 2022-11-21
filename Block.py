from hashlib import sha256


class Block:
    def __init__(self, index, previous_hash, data, nonce=0):
        self.index = index
        self.nonce = nonce
        self.previous_hash = previous_hash
        self.data = data

    def compute_hash(self):
        """
        computes the hash of the block header
        :return:hash of the block header
        """
        hash_string = ""
        hash_string += str(self.index)
        hash_string += str(self.nonce)
        hash_string += str(self.previous_hash)
        hash_string += str(self.data)

        return sha256(hash_string.encode()).hexdigest()

    def verify(self):
        """
        TODO in the node class
        :return:
        """

    def print_header(self):
        """
        Prints the block information
        """
        print("Index: ", self.index)
        print("Nonce: ", self.nonce)
        print("Previous: ", self.previous_hash)
        print("data: ", self.data)

    def increase_nonce(self):
        self.nonce += 1

    def update_data(self, data):
        """
        Updates the data of a block
        :param data:
        :return:
        """
        self.data = data.copy()

    def __repr__(self):
        """
        Translate the block object in a string object
        :return: The constructor as a string
        """
        return f'Block("{self.index}", "{self.previous_hash}", "{self.data}", "{self.nonce}")'
