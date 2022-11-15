from hashlib import sha256


class Block:
    def __init__(self, index, previous_hash, data):
        self.index = index
        self.nonce = 0
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
