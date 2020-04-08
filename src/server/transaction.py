from Cryptodome.Hash import BLAKE2b
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5

import config
import metrics
import node
import state
from utils import broadcast


class Transaction:
    def __init__(self, receiver_public_key, amount):
        if receiver_public_key == node.public_key:
            raise ValueError("invalid receiver_public_key")
        if amount <= 0:
            raise ValueError("invalid amount")

        self.sender_public_key = node.public_key
        self.receiver_public_key = receiver_public_key

        utxo_amount = 0
        self.input = []
        for tx_id, tx_amount in state.utxos[self.sender_public_key].items():
            if utxo_amount >= amount:
                break
            utxo_amount += tx_amount
            self.input.append(tx_id)
        if utxo_amount < amount:
            raise ValueError("insufficient amount")

        h = self.hash()
        self.id = h.digest()
        self.signature = PKCS1_v1_5.new(node.private_key).sign(h)

        self.outputs = {"receiver": amount}
        if utxo_amount != amount:
            self.outputs["sender"] = utxo_amount - amount

        # side effects
        for tx_id in self.input:
            del state.utxos[self.sender_public_key][tx_id]
        state.utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]
        if "sender" in self.outputs:
            state.utxos[self.sender_public_key][self.id] = self.outputs["sender"]

        threaded = (
            node.index != 0
            or metrics.statistics["transactions_created"] > config.N_NODES - 1
        )
        broadcast("/transaction/validate", self, threaded=threaded)

        state.block.add(self)

    def __eq__(self, other):
        return self.id == other.id

    def validate(self, utxos, validate_block=False):
        if self.sender_public_key == self.receiver_public_key:
            raise Exception("sender == receiver")

        if not PKCS1_v1_5.new(RSA.importKey(self.sender_public_key.encode())).verify(
            self.hash(), self.signature
        ):
            raise Exception("invalid signature")

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
            state.block.add(self)

    def hash(self):
        h = BLAKE2b.new(data=self.sender_public_key.encode())
        h.update(self.receiver_public_key.encode())
        h.update(b"".join(self.input))
        return h


class GenesisTransaction(Transaction):
    def __init__(self):
        self.receiver_public_key = node.public_key
        self.id = self.hash().digest()
        self.outputs = {"receiver": 100 * config.N_NODES}

        # side effects
        state.utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]

    def hash(self):
        return BLAKE2b.new(data=self.receiver_public_key.encode())

    def validate(self, utxos, validate_block=False):
        # side effects
        utxos[self.receiver_public_key][self.id] = self.outputs["receiver"]
