from copy import deepcopy
from hashlib import blake2b
from pickle import dumps, loads
from random import random
from time import time

from requests import get

import config
import metrics
import node
import state
from transaction import GenesisTransaction
from utils import broadcast


class Block:
    def __init__(self):
        self.transactions = []

    def add(self, transaction):
        self.transactions.append(transaction)
        self.mine()

    def mine(self):
        if len(self.transactions) == config.CAPACITY:
            self.previous_hash = state.blockchain.blocks[-1].current_hash

            self.timestamp = time()
            h = self.hash()
            while True:
                if state.validating_block.is_set():
                    return
                nonce = random()
                h_copy = h.copy()
                h_copy.update(dumps(nonce))
                current_hash = h.hexdigest()
                if int(current_hash[: config.DIFFICULTY], base=16) == 0:
                    self.nonce = nonce
                    self.current_hash = current_hash
                    metrics.average_block_time.add(time() - self.timestamp)
                    break
            broadcast("/block/validate", self)

            # side effects
            state.blockchain.add(self)
            state.committed_utxos = deepcopy(state.utxos)
            state.block = Block()

            metrics.statistics["blocks_created"] += 1

    def validate(self):
        if len(self.transactions) != config.CAPACITY:
            raise Exception("invalid capacity")

        current_hash = self.hash().hexdigest()
        if current_hash != self.current_hash:
            raise Exception("invalid block hash")
        if int(current_hash[: config.DIFFICULTY], base=16) != 0:
            raise Exception("invalid proof of work")

        if self.previous_hash != state.blockchain.blocks[-1].current_hash:
            if self.previous_hash in [
                block.current_hash for block in state.blockchain.blocks[:-1]
            ]:
                return
            Block.resolve_conflict()
            return

        utxos = deepcopy(state.committed_utxos)
        for transaction in self.transactions:
            transaction.validate(utxos, validate_block=True)

        # side effects
        state.blockchain.add(self)
        state.committed_utxos = utxos
        state.utxos = deepcopy(utxos)

        transactions = deepcopy(state.block.transactions)
        state.block = Block()
        for transaction in transactions:
            if transaction not in self.transactions:
                transaction.validate(state.utxos)

        metrics.statistics["blocks_validated"] += 1

    def hash(self):
        h = blake2b(
            dumps(
                [tx.id for tx in self.transactions], self.timestamp, self.previous_hash,
            )
        )
        if hasattr(self, "nonce"):
            h.update(dumps(self.nonce))
        return h

    # FIXME might go on forever
    # TODO check with block headers, resolve conflict from check failure onwards
    @staticmethod
    def resolve_conflict():
        while True:
            max_length, address = max(
                (get(f"http://{address}/blockchain/length").json(), address)
                for address in node.addresses
                if address != node.address
            )
            blockchain = loads(get(f"http://{address}/blockchain").content)
            if max_length <= len(blockchain.blocks):
                if max_length >= len(state.blockchain.blocks):
                    try:
                        blockchain.validate()
                    except:
                        continue
                break

        metrics.statistics["conflicts_resolved"] += 1


class GenesisBlock(Block):
    def __init__(self):
        self.transactions = [GenesisTransaction()]
        self.timestamp = time()
        self.current_hash = 0
        self.index = 0

        # side effects
        state.block = Block()
