from collections import defaultdict
from copy import deepcopy
from time import time

import metrics
import state
from block import Block, GenesisBlock
from config import DIFFICULTY


class Blockchain:
    def __init__(self):
        print("Creating blockchain")

        self.blocks = [GenesisBlock()]

        # side effects
        state.blockchain = self

        metrics.statistics["blockchains_created"] += 1
        print("Blockchain created")

    def add(self, block):
        self.blocks.append(block)

        # metrics
        metrics.average_throughput.time()

    def validate(self):
        print("Validating blockchain")

        previous = self.blocks[0]
        for block in self.blocks[1:]:
            if block.previous_hash != previous.current_hash:
                raise Exception("invalid blockchain")
            previous = block

        for block in self.blocks[1:]:
            if int(block.hash().hexdigest()[:DIFFICULTY], base=16) != 0:
                raise Exception("invalid proof of work")

        utxos = defaultdict(dict)
        for block in self.blocks:
            for transaction in block.transactions:
                transaction.validate(utxos, validate_block=True)

        # side effects
        transactions = state.block.transactions + [
            transaction
            for block in state.blockchain.blocks
            for transaction in block.transactions
        ]

        state.blockchain = self
        state.utxos = deepcopy(utxos)
        state.committed_utxos = utxos

        state.block = Block()
        for transaction in transactions:
            if transaction not in [
                transaction
                for block in self.blocks
                for transaction in block.transactions
            ]:
                transaction.validate(state.utxos)

        metrics.statistics["blockchains_validated"] += 1
        print("Blockchain validated")
