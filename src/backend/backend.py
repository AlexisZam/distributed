#!/usr/bin/env python3.8

from collections import defaultdict
from copy import deepcopy
from flask import Flask, request
from multiprocessing import Value
from pickle import dumps, loads
from requests import get, post
from threading import Thread
from time import sleep

from block import Block, GenesisBlock
from blockchain import Blockchain
from config import bootstrap_address, n_nodes
import node
import state
from transaction import GenesisTransaction, Transaction


# TODO diff after failed mining


def broadpost(path, data):
    # TODO async io
    for address in state.addresses:
        if address != node.address:
            post(f"http://{address}{path}", data=dumps(data))


def broadget(path):
    return [
        loads(get(f"http://{address}{path}").content, address)
        for address in state.addresses
        if address != node.address
    ]


def generate_transaction(receiver_public_key, amount):
    sleep(1)  # FIXME
    transaction = Transaction(
        node.public_key, node.private_key, receiver_public_key, amount, state.utxos
    )
    broadpost("/validate_transaction", transaction)
    handle_transaction(transaction)


def handle_transaction(transaction):
    with state.utxos_lock:
        transaction.update_utxos(state.utxos)
    with state.block_lock:
        state.block.add(transaction)
        if state.block.full():
            mine()


# TODO check with block headers, resolve conflict from check failure onwards
def validate_blockchain(blockchain):
    if blockchain.validate(defaultdict(dict)):
        with state.committed_utxos_lock:
            state.committed_utxos = defaultdict(dict)
            blockchain.update_utxos(state.committed_utxos)
        with state.blockchain_lock:
            state.blockchain = blockchain
        with state.utxos_lock:
            state.utxos = deepcopy(state.committed_utxos)
        with state.block_lock:
            state.block = Block()
        print("blockchain validating succeeded")
    else:
        print("blockchain validating failed")


def mine():
    if state.block.mine(state.blockchain):
        broadpost("/validate_block", state.block)
        with state.blockchain_lock:
            state.blockchain.add(state.block)
        with state.committed_utxos_lock:
            state.block.update_utxos(state.committed_utxos)
        with state.utxos_lock:
            state.utxos = deepcopy(state.committed_utxos)
        # TODO with state.block_lock:
        state.block = Block()
        print("mining succeeded")
    else:
        print("mining failed")


app = Flask(__name__)


@app.route("/view")
def view():
    return dumps(
        [transaction.__dict__ for transaction in state.blockchain.top().transactions]
    )


@app.route("/balance")
def balance():
    return dumps(sum(amount for amount in state.utxos[node.public_key].values()))


@app.route("/addresses")
def addresses():
    return dumps(state.addresses)


@app.route("/index")
def index():
    return dumps(node.index)


@app.route("/public_keys")
def public_keys():
    return dumps(state.public_keys)


@app.route("/blockchain")
def blockchain():
    return dumps(state.blockchain)


@app.route("/blockchain/length")
def blockchain_length():
    return dumps(len(state.blockchain))


@app.route("/login")  # FIXME
def login():
    if node.address != bootstrap_address:
        return ""

    with counter.get_lock():
        index = counter.value
        counter.value += 1

    return dumps(index)


@app.route("/address", methods=["POST"])
def address():
    address = loads(request.get_data())
    with state.addresses_lock:
        state.addresses.append(address)
    return ""


@app.route("/transaction", methods=["POST"])
def transaction():
    data = loads(request.get_data())
    generate_transaction(data["receiver_public_key"], data["amount"])
    return ""


@app.route("/public_key", methods=["POST"])
def public_key():
    index, public_key = loads(request.get_data())
    with state.public_keys_lock:
        state.public_keys[index] = public_key

    if node.address == bootstrap_address:  # FIXME
        Thread(target=generate_transaction, args=(public_key, 100)).start()

    return ""


@app.route("/validate_transaction", methods=["POST"])
def validate_transaction():
    transaction = loads(request.get_data())
    if transaction.validate(state.utxos):
        handle_transaction(transaction)
        print("transaction validating succeeded")
    else:
        print("transaction validating failed")
    return ""


@app.route("/validate_block", methods=["POST"])
def validate_block():
    block = loads(request.get_data())
    try:
        if block.validate(state.committed_utxos, state.blockchain):
            with state.blockchain_lock:
                state.blockchain.add(block)
            with state.committed_utxos_lock:
                block.update_utxos(state.committed_utxos)
            with state.utxos_lock:
                state.utxos = deepcopy(state.committed_utxos)
            with state.block_lock:
                state.block = Block()
            print("block validating succeeded")
        else:
            print("block validating failed")
    except ValueError:
        while True:
            length, address = max(broadget("/blockchain/length"))
            blockchain = loads(get(f"http://{address}/blockchain").content)
            if length == blockchain.length():
                break
        if length > state.blockchain.length():
            validate_blockchain(blockchain)
    return ""


if node.address == bootstrap_address:
    counter = Value("i", 0)
    with counter.get_lock():
        node.index = counter.value
        counter.value += 1
    state.public_keys[node.index] = node.public_key

    state.addresses = [node.address]

    state.blockchain = Blockchain()
    state.block = GenesisBlock()
    genesis_transaction = GenesisTransaction(node.public_key)
    handle_transaction(genesis_transaction)
else:
    sleep(3)
    addresses = loads(
        get(f"http://{bootstrap_address}/addresses", timeout=None).content
    )  # FIXME
    addresses.append(node.address)
    with state.addresses_lock:
        state.addresses = addresses
    broadpost("/address", node.address)

    blockchain = loads(get(f"http://{bootstrap_address}/blockchain").content)
    validate_blockchain(blockchain)

    node.index = loads(get(f"http://{bootstrap_address}/login").content)

    public_keys = loads(get(f"http://{bootstrap_address}/public_keys").content)
    public_keys[node.index] = node.public_key
    with state.public_keys_lock:
        state.public_keys = public_keys
    broadpost("/public_key", (node.index, node.public_key))


app.run(host=node.host, port=node.port)
