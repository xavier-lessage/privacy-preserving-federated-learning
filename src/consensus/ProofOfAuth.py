import copy
import logging
import threading
from random import randint
from time import time, sleep

from PROJH402.src import constants
from PROJH402.src.Block import Block, State
from PROJH402.src.utils import gen_enode

BLOCK_PERIOD = 30
DIFF_NOTURN = 1
DIFF_INTURN = 2
DELAY_NOTURN = 5

def generate_genesis(auth_signers_list, initial_balances):
    state_var = {"n": 0, "balances": initial_balances}
    return Block(0, 0000, [], auth_signers_list, 0, 0, 0, nonce=1, state_var=state_var)


auth_signers = [gen_enode(i) for i in range(1,9)]
initial_balances = {"1": 1000, "2": 0}
GENESIS_BLOCK = generate_genesis(auth_signers, initial_balances)


class ProofOfAuthority:
    """
    Consensus protocol based on https://eips.ethereum.org/EIPS/eip-225
    """

    def __init__(self, genesis=GENESIS_BLOCK):
        self.genesis = genesis
        self.block_generation = ProofOfAuth

        # List of authorized block producers
        self.auth_signers = GENESIS_BLOCK.miner_id
        self.signer_count = len(self.auth_signers)

        # Boolean to check or not the block states
        self.trust = True

    def verify_chain(self, chain, previous_state):
        last_block = chain[0]
        if not self.verify_block(last_block, previous_state):
            return False
        i = 1
        while i < len(chain):
            last_block_hash = last_block.compute_block_hash()

            # Check Timestamp difference
            if chain[i].timestamp - last_block.timestamp < BLOCK_PERIOD // 2:
                logging.error("Timestamp error in the blockchain")
                logging.error(len(chain))
                logging.error(f"Previous: {last_block.timestamp}, Current: {chain[i].timestamp}")
                logging.error(chain)
                return False

            # Check the block
            elif not self.verify_block(chain[i], last_block.state):
                logging.error("Block error")
                logging.error(chain[i].__repr__())
                return False

            # Check the parent hash
            elif chain[i].parent_hash != last_block_hash:
                logging.error("Error in the blockchain")
                logging.error(chain[i].parent_hash + "###" + last_block_hash)
                return False
            else:
                last_block = chain[i]
            i += 1
        return True

    def verify_block(self, block, previous_state):
        # Verify signer
        if block.miner_id in self.auth_signers:
            signer_index = self.auth_signers.index(block.miner_id)
        else:
            return False

        # Verify block state
        if not self.trust:
            s = copy.deepcopy(previous_state)
            for transaction in block.data:
                s.apply_transaction(transaction)
            if s.state_hash() != block.state.state_hash():
                logging.error(f"Invalid state {previous_state.state_variables}")
                logging.error(f"{s.state_variables}")
                logging.error(f"{block.state.state_variables}")
                logging.error(f"{block.data}")
                return False

        # Check Total Difficulty
        if block.height % self.signer_count == signer_index:
            expected_diff = DIFF_INTURN
        else:
            expected_diff = DIFF_NOTURN

        if block.difficulty != expected_diff:
            return False

        return True

class ProofOfAuth():
    """
    Generates a block every X seconds
    """

    def __init__(self, node, period=BLOCK_PERIOD):
        self.node = node
        self.period = period
        self.flag = False

        self.timer = self.node.custom_timer
        self.sleep = 0

        self.consensus = self.node.consensus

        self.auth_signers = self.consensus.auth_signers
        self.signer_count = len(self.auth_signers)

        if self.node.enode in self.auth_signers:
            self.index = self.auth_signers.index(self.node.enode)
        else:
            print(f"Node {self.node.id} not allowed to produce blocks")
            self.stop()

    def run(self):
        timestamp = self.timer.time()
        last_block = copy.deepcopy(self.node.get_block('last'))
        last_signed_block = self.node.get_last_signed_block()
        next_block_number = last_block.height+1

        # No signing if already signed in last N/2+1 blocks
        if last_signed_block == 0:
            pass
        elif next_block_number - last_signed_block < (self.signer_count + 1) // 2 + (self.signer_count + 1) % 2:  
            return

        # If it is my turn to sign (diff = DIFF_INTURN)
        if next_block_number % self.signer_count == self.index:
            difficulty = DIFF_INTURN

        # If it is not my turn, wait (t = DELAY_NOTURN)
        elif timestamp-last_block.timestamp-self.period < DELAY_NOTURN:
            return
        
        # After wait, do out of turn signature (diff = DIFF_NOTURN)
        else:
            difficulty = DIFF_NOTURN

        previous_block = copy.deepcopy(self.node.get_block('last'))
        previous_state = previous_block.state
        
        if next_block_number > previous_block.height and timestamp > (previous_block.timestamp + self.period - 1):

            # Get transactions from mempool, but remove those already in previous blocks
            mempool = list((self.node.mempool.copy().values()))
            data = []
            for tx in mempool:
                if tx.id not in self.node.previous_transactions_id:
                    data.append(tx)
                else:
                    print('removed tx already in chain')

            previous_state_var = previous_block.state.state_variables
            block = Block(next_block_number, previous_block.hash, data,
                            self.node.enode,
                            timestamp, difficulty, previous_block.total_difficulty, state_var=previous_state_var)

            for transaction in block.data:
                block.state.apply_transaction(transaction)
                self.node.previous_transactions_id.add(transaction)

            self.node.chain.append(block)
            self.node.mempool.clear()
            logging.info(f"Block produced by Node {self.node.id}: ")
            logging.info(f"{repr(block)}")
            # logging.info(f"last_signed_block: {last_signed_block}")
            logging.info(f"###{block.state.state_variables}### \n")

    def step(self):
        if self.flag:
            if self.sleep > 0:
                self.sleep -= 1
            else:
                self.run()

    def start(self):
        self.flag = True

    def stop(self):
        self.flag = False

class ProofOfAuthThread(threading.Thread):
    """
    Generates a block every X seconds
    """

    def __init__(self, node, period=BLOCK_PERIOD):
        super().__init__()
        self.node = node
        self.period = period
        self.flag = threading.Event()

        self.timer = self.node.custom_timer

        self.consensus = self.node.consensus

        self.auth_signers = self.consensus.auth_signers
        self.signer_count = len(self.auth_signers)

        if self.node.enode in self.auth_signers:
            self.index = self.auth_signers.index(self.node.enode)
        else:
            print(f"Node {self.node.id} not allowed to produce blocks")
            self.stop()

    def step(self):
        pass

    def run(self):
        while not self.flag.is_set():
            timestamp = self.timer.time()
            delay = 0
            block_number = len(self.node.chain)
            if block_number % self.signer_count == self.index:
                difficulty = DIFF_INTURN
            else:
                delay = randint(self.period//10, self.period//3)
                self.timer.sleep(delay)

                difficulty = DIFF_NOTURN

            previous_block = copy.deepcopy(self.node.get_block('last'))
            if block_number > previous_block.height and timestamp > (previous_block.timestamp + self.period - 1):
                data = list((self.node.mempool.copy().values()))
                previous_state_var = previous_block.state.state_variables
                block = Block(block_number, previous_block.hash, data,
                              self.node.enode,
                              timestamp, difficulty, previous_block.total_difficulty, state_var=previous_state_var)

                for transaction in block.data:
                    block.state.apply_transaction(transaction)

                self.node.chain.append(block)
                self.node.mempool.clear()
                logging.info(f"Block produced by Node {self.node.id}: ")
                logging.info(f"{repr(block)}")
                logging.info(f"###{block.state.state_variables}### \n")

            self.timer.sleep(self.period - delay)

    def stop(self):
        self.flag.set()
