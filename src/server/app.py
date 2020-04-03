#!/usr/bin/env python3.8

from collections import defaultdict
from multiprocessing import Value
from pickle import dumps, loads
from threading import Thread

from flask import Flask, request
from requests import get, post

import metrics
import node
import state
from config import BOOTSTRAP_ADDRESS, HOST, N_NODES, PORT
from transaction import Transaction

app = Flask(__name__)

# Login

if node.address == BOOTSTRAP_ADDRESS:

    @app.route("/login", methods=["POST"])
    def login():
        address, public_key = loads(request.get_data())
        with node.addresses_lock:
            node.addresses.append(address)
        with node.public_keys_lock:
            index = len(node.public_keys)
            node.public_keys.append(public_key)

        while True:
            with node.public_keys_lock:
                if len(node.public_keys) == N_NODES:
                    return dumps((index, node.addresses, node.public_keys))


# Get node


@app.route("/index")
def index():
    return dumps(node.index)


@app.route("/nodes/<index>/public_key")
def public_key(index):
    return dumps(node.public_keys[int(index)])


@app.route("/public_keys")
def public_keys():
    return dumps(node.public_keys)


# Get state


@app.route("/balance")
def balance():
    with state.utxos_lock:
        return dumps(sum(state.utxos[node.public_key].values()))


@app.route("/blockchain")
def blockchain():
    with state.blockchain_lock:
        return dumps(state.blockchain)


@app.route("/blockchain/length")
def blockchain_length():
    with state.blockchain_lock:
        return dumps(state.blockchain.length())


@app.route("/blockchain/top/transactions")
def view():
    with state.blockchain_lock:
        return dumps(
            [
                transaction.__dict__  # FIXME
                for transaction in state.blockchain.blocks[-1].transactions
            ]
        )


# Get metrics


@app.route("/metrics/average_throughput")
def average_throughput():
    return dumps(metrics.average_throughout.get())


@app.route("/metrics/average_block_time")
def average_block_time():
    return dumps(metrics.average_block_time.get())


# Post


@app.route("/transaction", methods=["POST"])
def transaction():
    receiver_public_key, amount = loads(request.get_data())
    Transaction(receiver_public_key, amount)
    return ""


@app.route("/transaction/validate", methods=["POST"])
def transaction_validate():
    transaction = loads(request.get_data())
    transaction.validate(state.utxos, state.utxos_lock)
    return ""


@app.route("/block/validate", methods=["POST"])
def block_validate():
    block = loads(request.get_data())
    block.validate()
    return ""


# Quit


@app.route("/quit", methods=["POST"])
def quit():
    request.environ.get("werkzeug.server.shutdown")()
    return ""


app.run(host=HOST, port=PORT)
