import pickle
import time
from uuid import uuid4


class Transaction:
    def __init__(self, source, dest, data, value, timestamp, nonce=None, id=None):
        self.source = source
        self.destination = dest
        self.data = data
        self.value = value
        self.timestamp = timestamp
        self.nonce = nonce
        self.id = id

        if not id:
            self.id = str(uuid4())


