import pickle
from uuid import uuid4


class Transaction:
    def __init__(self, source, dest, data, value, nonce=None):
        self.source = source
        self.destination = dest
        self.data = data
        self.value = value

        self.nonce = nonce
        if not nonce:
            self.nonce = str(uuid4())


