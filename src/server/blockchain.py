from collections import defaultdict
from copy import deepcopy
from time import time

import state
from block import Block, GenesisBlock
from config import DIFFICULTY


class Blockchain:
    def __init__(self):
        print("Creating blockchain")

        self.blocks = [GenesisBlock()]

        # side effects
        with state.blockchain_lock:
            state.blockchain = self

        print("Blockchain created")

    def add(self, block):
        self.blocks.append(block)

    def validate(self):
        print("Validating blockchain")

        for block in self.blocks[1:]:
            if block.previous_hash != self.blocks[block.index - 1].current_hash:
                raise Exception("invalid blockchain")

        for block in self.blocks[1:]:
            if int(block.hash().hexdigest()[:DIFFICULTY], base=16) != 0:
                raise Exception("invalid hash")

        utxos = defaultdict(dict)
        for block in self.blocks:
            for transaction in block.transactions:
                transaction.validate(utxos, validate_block=True)
        assert utxos != defaultdict(dict)

        # side effects
        with state.blockchain_lock:
            state.blockchain = self
            with state.utxos_lock:
                state.utxos = deepcopy(utxos)
                with state.committed_utxos_lock:
                    state.committed_utxos = utxos
        assert state.utxos == state.committed_utxos

        with state.block_lock:
            transactions = deepcopy(state.block.transactions)
            state.block = Block()
            # FIXME why is this (and the following lines) locked?
            for transaction in transactions:
                if transaction not in [
                    transaction
                    for block in self.blocks
                    for transaction in block.transactions
                ]:
                    transaction.validate(state.utxos, state.utxos_lock)
        # FIXME maybe nested locking

        print("Blockchain validated")

    def length(self):
        return len(self.blocks)
