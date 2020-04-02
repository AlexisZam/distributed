from collections import defaultdict
from copy import deepcopy
from time import time

import metrics
import state
from block import Block, GenesisBlock


class Blockchain:
    def __init__(self):
        self.blocks = [GenesisBlock()]

        # side effects
        with state.blockchain_lock:
            state.blockchain = self

        print("Blockchain created")

    def add(self, block):
        self.blocks.append(block)

        # metrics
        metrics.average_block_time.add(time() - block.timestamp)

    def validate(self):
        for block in self.blocks:
            if block.previous_hash != self.blocks[block.index - 1].current_hash:
                raise Exception

        utxos = defaultdict(dict)
        for block in self.blocks:
            block.validate(utxos, validate_blockchain=True)

        # side effects
        with state.blockchain_lock:
            state.blockchain = self
        with state.utxos_lock:
            state.utxos = deepcopy(utxos)
        with state.committed_utxos_lock:
            state.committed_utxos = utxos
        with state.block_lock:
            state.block = Block()
        # FIXME maybe nested locking

        print("Blockchain validated")

    def top(self):
        return self.blocks[-1]

    def length(self):
        return len(self.blocks)
