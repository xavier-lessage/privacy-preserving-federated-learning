from random import randint

from PROJH402.src.utils import compute_hash, transaction_to_dict, dict_to_transaction


class Block:
    """
    Class representing a block of a blockchain containing transactions
    """

    def __init__(self, height, parent_hash, data, miner_id, timestamp, difficulty, total_diff, nonce=None,
                 state_var=None):
        self.height = height
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
                 self.total_difficulty, self.nonce, self.state.state_hash()]

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
        return f"## Height: {self.height}, Diff: {self.difficulty}, Total_diff: {self.total_difficulty}, Producer: {self.miner_id} ##"


class State:
    def __init__(self, state_variables=None):
        self.state_variables = state_variables
        self.balances = 0
        if not state_variables:
            self.state_variables = {"n": 0, "balances": {}}

    def add_k(self, k):
        """
        custom function that adds k to a state variable named n
        """
        self.state_variables["n"] += k

    def apply_transaction(self, t):
        # Initialise account
        if t.source not in self.state_variables["balances"]:
            self.state_variables["balances"][t.source] = 0

        # Check the balance
        if self.state_variables["balances"][t.source] - t.value >= 0:
            self.state_variables["balances"][t.source] -= t.value
        else:
            return

        # Make the payment
        if t.destination not in self.state_variables["balances"]:
            self.state_variables["balances"][t.destination] = 0

        self.state_variables["balances"][t.destination] += t.value

        # Apply the other actions (smart contract)
        if t.data.get("action"):
            action = getattr(self, t.data.get("action"))
            _input = t.data.get("input")
            action(_input)

    def state_hash(self):
        return compute_hash(self.state_variables)


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
