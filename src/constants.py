from PROJH402.src.Block import Block

LOCALHOST = "127.0.0.1"
ENCODING = "utf-8"
MINING_DIFFICULTY = 18  # Approx One block every 7 seconds
MEMPOOL_SYNC_INTERVAL = 3.0
CHAIN_SYNC_INTERVAL = 3.0
DEBUG = True
GENESIS_BLOCK = Block(0, 0000000, [], 0, 0, MINING_DIFFICULTY, 0, 0)
