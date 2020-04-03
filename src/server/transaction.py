from contextlib import nullcontext
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
        print("Creating transaction")

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

            broadcast("/transaction/validate", self)

            # side effects
            for tx_id in self.input:
                del state.utxos[self.sender_public_key][tx_id]
            state.utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]
            if "sender" in self.outputs:
                state.utxos[self.sender_public_key][self.id] = self.outputs["sender"]

            print("Transaction created")

        with state.block_lock:
            state.block.add(self)

    def __eq__(self, other):
        return self.id == other.id

    def validate(self, utxos, utxos_lock=nullcontext(), validate_block=False):
        if not validate_block:
            print("Validating transaction")

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
            for tx_id in self.input:
                del utxos[self.sender_public_key][tx_id]
            utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]
            if "sender" in self.outputs:
                utxos[self.sender_public_key][self.id] = self.outputs["sender"]

        if not validate_block:
            print("Transaction validated")

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
        print("Creating transaction")

        self.receiver_public_key = node.public_key
        self.id = self.__hash().hexdigest()
        self.outputs = {"receiver": 100 * N_NODES}

        # side effects
        with state.utxos_lock:
            state.utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]

        print("Transaction created")

    def __hash(self):
        data = self.receiver_public_key
        return SHA512.new(data=dumps(data))

    def validate(self, utxos, utxos_lock=nullcontext(), validate_block=False):
        if not validate_block:
            print("Validating transaction")

        # side effects
        with utxos_lock:
            utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]

        if not validate_block:
            print("Transaction validated")