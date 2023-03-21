import copy
import logging
import threading
from random import randint
from time import time, sleep

from PROJH402.src import constants
from PROJH402.src.Block import Block, State

EPOCH_LENGTH = 3000
BLOCK_PERIOD = 15
NONCE_AUTH = 0xffffffffffffffff
NONCE_DROP = 0x0000000000000000
DIFF_NOTURN = 1
DIFF_INTURN = 2
SIGNER_LIMIT = 3
GENESIS_BLOCK = Block(0, {"enode://1@127.0.0.1:1234": 4}, [], 0, 0, 0, 0,
                      ["enode://1@127.0.0.1:1234", "enode://2@127.0.0.1:1235", "enode://3@127.0.0.1:1236"])


class ProofOfAuthority:
    def __init__(self):
        self.genesis = GENESIS_BLOCK
        initial_state = State(GENESIS_BLOCK.parent_hash)
        self.genesis.update_state(initial_state)
        self.block_generation = ProofOfAuthThread
        self.epoch_length = EPOCH_LENGTH

        self.auth_signers = GENESIS_BLOCK.nonce
        self.signer_count = len(self.auth_signers)

        # Boolean to check or not the block states
        self.trust = False

    def verify_chain(self, chain, previous_state):
        last_block = chain[0]
        if not self.verify_block(last_block, previous_state):
            return False
        i = 1
        while i < len(chain):
            last_block_hash = last_block.compute_block_hash()

            if chain[i].timestamp - last_block.timestamp < BLOCK_PERIOD // 2:
                logging.error("Timestamp error in the blockchain")
                logging.error(len(chain))
                logging.error(f"Previous: {last_block.timestamp}, Current: {chain[i].timestamp}")
                logging.error(chain)
                return False
            elif not self.verify_block(chain[i], last_block.state):
                logging.error("Block error")
                logging.error(chain[i].__repr__())
                return False

            elif chain[i].parent_hash != last_block_hash:
                logging.error("Error in the blockchain")
                logging.error(chain)
                return False
            else:
                last_block = chain[i]

            # if chain[i].miner_id == last_block.miner_id:
            #     stack += 1
            # else:
            #     stack = 0

            # if stack >= SIGNER_LIMIT:
            #     print("Signer limit reached")
            #     print(chain)
            #     return False
            i += 1
        return True

    def verify_block(self, block, previous_state):
        # for transaction in block.data:
        #   verify_transaction(transaction)

        # Verify block state
        if not self.trust:
            s = copy.copy(previous_state)
            for transaction in block.data:
                s.apply_transaction(transaction)
            if s.state_hash() != block.state.state_hash():
                logging.error(f"Invalid state {previous_state.balances}")
                logging.error(f"{s.balances}")
                logging.error(f"{block.data}")
                return False

        # Verify signer
        if block.miner_id in self.auth_signers:
            signer_index = self.auth_signers.index(block.miner_id)
        else:
            return False

        # Check Total Difficulty
        if block.height % self.signer_count == signer_index:
            expected_diff = DIFF_INTURN
        else:
            expected_diff = DIFF_NOTURN

        if block.difficulty != expected_diff:
            return False

        return True


class ProofOfAuthThread(threading.Thread):
    """
    Generates a block every X seconds
    """

    def __init__(self, node, period=BLOCK_PERIOD):
        super().__init__()
        self.node = node
        self.period = period
        self.flag = threading.Event()

        self.consensus = self.node.consensus

        self.auth_signers = self.consensus.auth_signers
        self.signer_count = len(self.auth_signers)

        if self.node.enode in self.auth_signers:
            self.index = self.auth_signers.index(self.node.enode)
        else:
            print(f"Node {self.node.id} not allowed to produce blocks")
            self.stop()

    def run(self):
        while not self.flag.is_set():
            timestamp = time()
            delay = 0
            current_diff = self.node.get_block('last').total_difficulty
            block_number = len(self.node.chain)
            if block_number % self.signer_count == self.index:
                difficulty = DIFF_INTURN
            else:
                delay = randint(self.period//10, self.period//3)
                sleep(delay)
                difficulty = DIFF_NOTURN

            if block_number % self.node.consensus.epoch_length == 0:
                # Checkpoint
                pass

            # IMPORTANT: For the moment extraData stored in nonce and signature stored in Miner_id, to be changed

            if block_number > self.node.get_block('last').height and timestamp > (self.node.get_block('last').timestamp + self.period - 1):
                block = Block(block_number, self.node.get_block('last').hash, self.node.mempool.copy(),
                              self.node.enode,
                              timestamp, difficulty, self.node.get_block('last').total_difficulty, None)

                block.update_state(copy.copy(self.node.get_block('last').state))

                self.node.chain.append(block)
                self.node.broadcast_last_block()
                self.node.mempool.clear()
                logging.info(f"Block produced by Node {self.node.id}: " + str(block.compute_block_hash()))
                logging.info(repr(block) + str(time()) + "\n")

            sleep(self.period - delay)

    def stop(self):
        self.flag.set()
