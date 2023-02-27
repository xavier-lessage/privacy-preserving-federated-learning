import pickle
from uuid import uuid4


class Transaction:
    def __init__(self, source, dest, data):
        self.source = source
        self.dest = dest
        self.data = data
        self.nonce = uuid4()

