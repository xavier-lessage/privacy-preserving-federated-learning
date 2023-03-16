import pickle
from uuid import uuid4


class Transaction:
    def __init__(self, source, dest, data, value):
        self.source = source
        self.destination = dest
        self.data = data
        self.value = value
        self.nonce = uuid4()

    def __repr__(self):
        return f"Source : {self.source}, Dest: {self.destination}, data: {self.data} value:{self.value}, nonce: {self.nonce}"
