from random import randint

from PROJH402.src.utils import compute_hash, transaction_to_dict, dict_to_transaction


class Block:
    """
    Class representing a block of a blockchain containing transactions
    """

    def __init__(self, height, parent_hash, data, miner_id, timestamp, difficulty, total_diff, nonce=None,
                 state_var=None):
        self.height = height
        self.number = height
        self.parent_hash = parent_hash
        self.data = data
        self.miner_id = miner_id
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.total_difficulty = total_diff + difficulty

        self.state = State(state_var)

        self.nonce = nonce
        if nonce is None:
            self.nonce = randint(0, 1000)

        self.transactions_root = self.transactions_hash()
        self.hash = self.compute_block_hash()

    def compute_block_hash(self):
        """
        computes the hash of the block header
        :return: hash of the block
        """
        _list = [self.height, self.parent_hash, self.transactions_hash(), self.miner_id, self.timestamp,
                 self.difficulty,
                 self.total_difficulty, self.nonce]

        self.hash = compute_hash(_list)

        return self.hash

    def transactions_hash(self):
        """
        computes the hash of the block transactions
        :return: the hash of the transaction list
        """
        transaction_list = [transaction_to_dict(t) for t in self.data]
        self.transactions_root = compute_hash(transaction_list)
        return self.transactions_root

    def get_header_hash(self):
        header = [self.parent_hash, self.transactions_hash(), self.timestamp, self.difficulty, self.nonce]
        return compute_hash(header)

    def increase_nonce(self):  ###### POW
        self.nonce += 1

    def __repr__(self):
        """
        Translate the block object in a string object
        """
        return f"## H: {self.height}, D: {self.difficulty}, TD: {self.total_difficulty}, P: {self.miner_id}, BH: {self.hash[0:5]}, TS:{self.timestamp}, #T:{len(self.data)}, SH:{self.state.state_hash()[0:5]}##"


class State:
    def __init__(self, state_variables=None):
        self.state_variables = state_variables
        self.balances = {}
        
        if not state_variables:
            self.state_variables = {"n": 0, "balances": {}}

    def apply_transaction(self, tx):

        self.state_variables["balances"].setdefault(tx.sender, 0)
        self.state_variables["balances"].setdefault(tx.receiver, 0)

        # Apply the transaction value
        if self.state_variables["balances"][tx.sender] - tx.value >= 0:
            self.state_variables["balances"][tx.sender] -= tx.value
            self.state_variables["balances"][tx.receiver] += tx.value
            self.state_variables["n"] += 1
        else:
            return

        # Apply the other functions contained in data
        if tx.data.get("function"):
            function = getattr(self, tx.data.get("function"))
            _inputs = tx.data.get("inputs")
            self.sc.function(_inputs)

    def state_hash(self):
        return compute_hash(self.state_variables.values())

def block_to_list(block):
    """
    Translates a block in a list
    """
    data = []
    for t in block.data:
        data.append(transaction_to_dict(t))
    return [block.height, block.parent_hash, data, block.miner_id, block.timestamp, block.difficulty,
            block.total_difficulty, block.nonce, block.state.state_variables]


def create_block_from_list(_list):
    height = _list[0]
    parent_hash = _list[1]
    data = []
    for d in _list[2]:
        data.append(dict_to_transaction(d))
    miner_id = _list[3]
    timestamp = _list[4]
    difficulty = _list[5]
    total_difficulty = _list[6] - difficulty
    nonce = _list[7]
    state_variables = _list[8]

    b = Block(height, parent_hash, data, miner_id, timestamp, difficulty, total_difficulty, nonce, state_variables)
    return b
