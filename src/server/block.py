from contextlib import nullcontext
from copy import deepcopy
from pickle import dumps, loads
from random import random
from threading import Event
from time import time

from Cryptodome.Hash import SHA512
from requests import get

import metrics
import node
import state
from config import CAPACITY, DIFFICULTY
from transaction import GenesisTransaction
from utils import broadcast

block_validated = Event()
# mining = Event()


class Block:
    def __init__(self):
        self.transactions = []

    def add(self, transaction):
        self.transactions.append(transaction)
        if len(self.transactions) == CAPACITY:
            print("Creating block")

            with state.blockchain_lock:
                self.previous_hash = state.blockchain.blocks[-1].current_hash
                self.index = state.blockchain.length()

            self.timestamp = time()
            while True:
                if block_validated.is_set():
                    print("Block creation failed")
                    return
                self.nonce = random()
                self.current_hash = self.hash().hexdigest()
                if int(self.current_hash[:DIFFICULTY], base=16) == 0:
                    # metrics
                    metrics.average_block_time.add(time() - self.timestamp)
                    break

            broadcast("/block/validate", self)

            # side effects
            with state.blockchain_lock:
                state.blockchain.add(self)
            with state.utxos_lock:
                with state.committed_utxos_lock:
                    state.committed_utxos = deepcopy(state.utxos)
            with state.block_lock:
                state.block = Block()
            # FIXME maybe nested locking

            print("Block created")

    def validate(self):  # FIXME
        print("Validating block")

        if int(self.hash().hexdigest()[:DIFFICULTY], base=16) != 0:
            raise Exception("invalid hash")

        with state.blockchain_lock:
            if self.previous_hash != state.blockchain.blocks[-1].current_hash:
                if self.previous_hash in [
                    block.current_hash for block in state.blockchain.blocks[:-1]
                ]:
                    print("block from shorter (or equal) blockchain")
                    print("Block validation failed")
                    return
                Block.__resolve_conflict()  # FIXME this should be at validate blockchain
                print("Block validation failed")
                return

        with state.committed_utxos_lock:
            utxos = deepcopy(state.committed_utxos)  # FIXME should this be first?
            for transaction in self.transactions:
                transaction.validate(utxos, validate_block=True)
            assert utxos != state.committed_utxos

            block_validated.set()

            # side effects
            with state.blockchain_lock:
                state.blockchain.add(self)
            state.committed_utxos = utxos
            with state.utxos_lock:
                state.utxos = deepcopy(utxos)
                assert state.utxos == state.committed_utxos
            with state.block_lock:
                transactions = deepcopy(state.block.transactions)
                state.block = Block()
                # FIXME why is this (and the following lines) locked?
                for transaction in transactions:
                    if transaction not in self.transactions:
                        transaction.validate(state.utxos, state.utxos_lock)
            # FIXME maybe nested locking

            block_validated.clear()

        print("Block validated")

    def hash(self):
        data = (
            [tx.id for tx in self.transactions],
            self.index,
            self.timestamp,
            self.previous_hash,
            self.nonce,
        )
        return SHA512.new(data=dumps(data))

    # TODO check with block headers, resolve conflict from check failure onwards
    @staticmethod
    def __resolve_conflict():
        print("Resolving conflict")
        while True:
            blockchain_lengths_addresses = [
                (loads(get(f"http://{address}/blockchain/length").content), address)
                for address in node.addresses
                if address != node.address
            ]
            max_length, address = max(blockchain_lengths_addresses)
            blockchain = loads(get(f"http://{address}/blockchain").content)
            if max_length <= blockchain.length():
                with state.blockchain_lock:
                    if max_length < state.blockchain.length():
                        break  # FIXME might go on forever
                blockchain.validate()  # TODO try catch this
                break
        print("Conflict resolved")


class GenesisBlock(Block):
    def __init__(self):
        print("Creating block")

        self.transactions = [GenesisTransaction()]
        self.timestamp = time()
        self.current_hash = 0
        self.index = 0

        # side effects
        with state.block_lock:
            state.block = Block()

        print("Block created")

    def validate(self, utxos, utxos_lock=nullcontext()):
        print("Validating block")

        self.transactions[0].validate(utxos, utxos_lock)

        # side effects
        with state.block_lock:
            state.block = Block()

        print("Block validated")
