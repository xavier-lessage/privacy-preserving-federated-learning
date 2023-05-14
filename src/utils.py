from hashlib import sha256
from time import sleep

from PROJH402.src.Transaction import Transaction


def compute_hash(list):
    """
    Computes the hash of all the elements contained in the list by putting them in a string
    """
    if len(list) < 1:
        return
    hash_string = ""
    for elem in list:
        hash_string += str(elem)

    return sha256(hash_string.encode()).hexdigest()


def transaction_to_dict(transaction):
    return {"source": transaction.source, "destination": transaction.destination, "data": transaction.data,
            "value": transaction.value, "timestamp": transaction.timestamp, "nonce": transaction.nonce,
            "id": transaction.id}


def dict_to_transaction(_dict):
    return Transaction(_dict["source"], _dict["destination"], _dict["data"], _dict["value"], _dict["timestamp"],
                       _dict["nonce"], _dict["id"])

class CustomTimer:
    def __init__(self):
        self.time_counter = 0

    def time(self):
        return self.time_counter

    def sleep(self, period):
        starting_time = self.time()

        while self.time_counter < starting_time + period:
            sleep(0.01)

    def increase_timer(self):
        self.time_counter += 1

