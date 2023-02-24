import threading
from random import randint
from time import time, sleep

from PROJH402.src import constants
from PROJH402.src.Block import Block

EPOCH_LENGTH = 3000
BLOCK_PERIOD = 15
NONCE_AUTH = 0xffffffffffffffff
NONCE_DROP = 0x0000000000000000
DIFF_NOTURN = 1
DIFF_INTURN = 2
SIGNER_LIMIT = 3
GENESIS_BLOCK = Block(0, 0000000, [], 0, 0, 0, 0,
                      ["enode://0@127.0.0.1:1234", "enode://1@127.0.0.1:1235", "enode://2@127.0.0.1:1236"])


class ProofOfAuthority:
    def __init__(self):
        self.genesis = GENESIS_BLOCK
        self.block_generation = ProofOfAuthThread
        self.epoch_length = EPOCH_LENGTH

        self.auth_signers = GENESIS_BLOCK.nonce
        self.signer_count = len(self.auth_signers)

    def verify_chain(self, chain):
        last_block = chain[0]
        i = 1
        stack = 0
        while i < len(chain):
            if chain[i].timestamp - last_block >= BLOCK_PERIOD and self.verify_block(chain[i]):
                last_block = chain[i]
                i += 1
            else:
                print("Error in the blockchain")
                print(chain)
                return False

            if chain[i].miner_id == last_block.miner_id:
                stack += 1
            else:
                stack = 0

            if stack >= SIGNER_LIMIT:
                print("Error in the blockchain")
                print(chain)
                return False

        return True

    def verify_block(self, block):
        # for transaction in block.data:
        #   verify_transaction(transaction)

        if block.miner_id in self.auth_signers:
            signer_index = self.auth_signers.index(block.miner_id)
        else:
            return False

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
            sleep(self.period)
            timestamp = time()

            block_number = len(self.node.chain)
            if block_number % self.signer_count == self.index:
                difficulty = DIFF_INTURN
            else:
                sleep(randint(0, int(self.signer_count * 0.5)))
                difficulty = DIFF_NOTURN

            if block_number % self.node.consensus.epoch_length == 0:
                # Checkpoint
                pass

            # IMPORTANT: For the moment extraData stored in nonce and signature stored in Miner_id, to be changed

            block = Block(block_number, self.node.get_block('last').hash, self.node.mempool.copy(),
                          self.node.enode,
                          timestamp, difficulty, self.node.get_block('last').total_difficulty, None)

            self.node.chain.append(block)
            self.node.mempool.clear()

            if constants.DEBUG:
                print("Block added: " + str(block.compute_block_hash()))
                print(repr(block) + "\n")

    def stop(self):
        self.flag.set()
