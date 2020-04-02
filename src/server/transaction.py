from contextlib import nullcontext
from copy import deepcopy
from pickle import dumps

from Cryptodome.Hash import SHA512
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5

import node
import state
from config import N_NODES
from utils import broadcast


class Transaction:
    def __init__(self, receiver_public_key, amount):
        if receiver_public_key == node.public_key:
            raise ValueError("invalid receiver_public_key")
        if amount <= 0:
            raise ValueError("invalid amount")

        self.sender_public_key = node.public_key
        self.receiver_public_key = receiver_public_key

        with state.utxos_lock:
            utxo_amount = 0
            self.input = []
            for tx_id, tx_amount in state.utxos[self.sender_public_key].items():
                if utxo_amount >= amount:
                    break
                utxo_amount += tx_amount
                self.input.append(tx_id)
            if utxo_amount < amount:
                raise ValueError("insufficient amount")

            h = self.__hash()
            self.id = h.hexdigest()
            self.signature = PKCS1_v1_5.new(node.private_key).sign(h)  # TODO pio kato

            self.outputs = {"receiver": amount}
            if utxo_amount != amount:
                self.outputs["sender"] = utxo_amount - amount

            # side effects
            self.__modify_state(state.utxos, state.utxos_lock)

        broadcast("/transaction/validate", self)

        print("Transaction created")

    def __eq__(self, other):
        return self.id == other.id

    def validate(self, utxos, utxos_lock=nullcontext(), validate_block=False):
        if self.sender_public_key == self.receiver_public_key:
            raise Exception("sender == receiver")

        if not PKCS1_v1_5.new(RSA.importKey(self.sender_public_key)).verify(
            self.__hash(), self.signature
        ):
            raise Exception("invalid signature")

        with utxos_lock:
            if sum(utxos[self.sender_public_key][tx_id] for tx_id in self.input) != sum(
                self.outputs.values()
            ):
                raise Exception("amount != sum of outputs")

            # side effects
            self.__modify_state(utxos, utxos_lock, validate_block)

            print("Transaction validated")

    def __modify_state(self, utxos, utxos_lock, validate_block=False):
        for tx_id in self.input:
            del utxos[self.sender_public_key][tx_id]
        utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]
        if "sender" in self.outputs:
            utxos[self.sender_public_key][self.id] = self.outputs["sender"]
        if not validate_block:
            with state.block_lock:
                state.block.add(self)

    def __hash(self):
        data = (
            self.sender_public_key,
            self.receiver_public_key,
            self.input,
        )
        return SHA512.new(data=dumps(data))


class GenesisTransaction(Transaction):
    def __init__(self):
        self.receiver_public_key = node.public_key
        self.id = self.__hash().hexdigest()
        self.outputs = {"receiver": 100 * N_NODES}

        # side effects
        self.__modify_state(state.utxos, state.utxos_lock)

        print("Transaction created")

    def __hash(self):
        data = self.receiver_public_key
        return SHA512.new(data=dumps(data))

    def validate(self, utxos, utxos_lock=nullcontext(), validate_block=False):
        # side effects
        self.__modify_state(utxos, utxos_lock)

        print("Transaction validated")

    def __modify_state(self, utxos, utxos_lock):
        with utxos_lock:
            utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]
