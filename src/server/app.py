#!/usr/bin/env python3.8

from pickle import dumps, loads  # TODO json

from flask import Flask, request
from threading import Thread
from requests import post

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
        with node.lock:
            index = len(node.public_keys)
            node.addresses.append(address)
            node.public_keys.append(public_key)

        while True:
            with node.lock:
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
    return dumps(sum(state.utxos[node.public_key].values()))


@app.route("/committed_balance")
def committed_balance():
    return dumps(sum(state.committed_utxos[node.public_key].values()))


@app.route("/balances")
def balances():
    return dumps([sum(utxos.values()) for utxos in state.utxos.values()])


@app.route("/committed_balances")
def committed_balances():
    return dumps(
        [
            sum(committed_utxos.values())
            for committed_utxos in state.committed_utxos.values()
        ]
    )


@app.route("/blockchain")
def blockchain():
    return dumps(state.blockchain)


@app.route("/blockchain/length")
def blockchain_length():
    return dumps(len(state.blockchain.blocks))


@app.route("/blockchain/top/transactions")
def view():
    return dumps(
        [
            transaction.__dict__
            for transaction in state.blockchain.blocks[-1].transactions
        ]
    )


# Get metrics


@app.route("/metrics/average_throughput")
def average_throughput():
    return dumps(metrics.average_throughput.get())


@app.route("/metrics/average_block_time")
def average_block_time():
    return dumps(metrics.average_block_time.get())


@app.route("/metrics/statistics")
def statistics():
    return dumps(metrics.statistics)


# Post

# TODO authorize this view
@app.route("/transaction", methods=["POST"])
def transaction():
    receiver_public_key, amount = loads(request.get_data())

    # metrics
    metrics.average_throughput.increment()

    with state.lock:
        Transaction(receiver_public_key, amount)
    return ""


@app.route("/transaction/validate", methods=["POST"])
def transaction_validate():
    transaction = loads(request.get_data())

    # metrics
    metrics.average_throughput.increment()

    with state.lock:
        transaction.validate(state.utxos)
    return ""


# TODO should mining be more parallel?
@app.route("/block/validate", methods=["POST"])
def block_validate():
    block = loads(request.get_data())
    state.validating.set()
    with state.lock:
        try:
            block.validate()
        except:
            state.validating.clear()
            state.block.mine()
    state.validating.clear()
    return ""


# Quit


@app.route("/quit", methods=["POST"])
def quit():
    request.environ.get("werkzeug.server.shutdown")()
    return ""


Thread(target=app.run, kwargs={"host": HOST, "port": PORT}).start()
if node.address != BOOTSTRAP_ADDRESS:
    post(f"http://{BOOTSTRAP_ADDRESS}/transaction", data=dumps((node.public_key, 100)))
