from contextlib import nullcontext
from copy import deepcopy
from pickle import dumps, loads
from random import random
from threading import Event
from time import time

from Cryptodome.Hash import SHA512
from requests import get

import node
import state
from config import BLOCK_CAPACITY, DIFFICULTY
from transaction import GenesisTransaction
from utils import broadcast

block_validated = Event()
mining = Event()


class Block:
    def __init__(self):
        self.transactions = []
        self.timestamp = time()

    def add(self, transaction):
        self.transactions.append(transaction)
        if len(self.transactions) == BLOCK_CAPACITY:
            with state.blockchain_lock:
                self.previous_hash = state.blockchain.top().current_hash
                self.index = state.blockchain.length()

            mining.set()
            while True:
                if block_validated.is_set():
                    mining.clear()
                    block_validated.clear()
                    return
                self.nonce = random()
                self.current_hash = self.__hash().hexdigest()
                if int(self.current_hash[:DIFFICULTY], base=16) == 0:
                    mining.clear()
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

    def validate(
        self, utxos, utxos_lock=nullcontext(), validate_blockchain=False
    ):  # FIXME
        if int(self.__hash().hexdigest()[:DIFFICULTY], base=16) != 0:
            raise Exception("invalid hash")

        try:
            with state.blockchain_lock:
                if (
                    not validate_blockchain
                    and self.previous_hash != state.blockchain.top().current_hash
                ):
                    raise Exception("conflict")
        except:
            Block.__resolve_conflict()  # FIXME this should be at validate blockchain
            return

        temp_utxos = deepcopy(utxos)  # FIXME should this be first?
        for transaction in self.transactions:
            transaction.validate(temp_utxos, validate_block=True)

        if mining.is_set():
            block_validated.set()

        # side effects
        if not validate_blockchain:
            with state.blockchain_lock:
                state.blockchain.add(self)
            with state.utxos_lock:
                state.utxos = deepcopy(temp_utxos)
            with state.committed_utxos_lock:
                state.committed_utxos = temp_utxos
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

    def __hash(self):
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


class GenesisBlock(Block):
    def __init__(self):
        self.transactions = [GenesisTransaction()]
        self.timestamp = time()
        self.current_hash = 0
        self.previous_hash = 0
        self.index = 0

        # side effects
        with state.block_lock:
            state.block = Block()

        print("Block created")

    def validate(self, utxos, utxos_lock=nullcontext(), validate_blockchain=False):
        self.transactions[0].validate(utxos, utxos_lock)

        # side effects
        if not validate_blockchain:
            with state.block_lock:
                state.block = Block()

        print("Block validated")
