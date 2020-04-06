from pickle import dumps, loads
from threading import Lock

from flask import Flask, jsonify, request

import metrics
import node
import state
from config import BOOTSTRAP_ADDRESS, N_NODES
from transaction import Transaction

app = Flask(__name__)

# Login

if node.address == BOOTSTRAP_ADDRESS:

    lock = Lock()

    @app.route("/login", methods=["POST"])
    def login():
        json = request.get_json()
        with lock:
            index = len(node.public_keys)
            node.addresses.append(json["address"])
            node.public_keys.append(json["public_key"])

        while True:
            with lock:
                if len(node.public_keys) == N_NODES:
                    return jsonify(index, node.addresses, node.public_keys)


# Get node


@app.route("/index")
def index():
    return jsonify(node.index)


@app.route("/nodes/<index>/public_key")
def public_key(index):
    return jsonify(node.public_keys[int(index)])


@app.route("/public_keys")
def public_keys():
    return jsonify(node.public_keys)


@app.route("/addresses")
def addresses():
    return jsonify(node.addresses)


# Get state


@app.route("/balance")
def balance():
    return jsonify(sum(state.utxos[node.public_key].values()))


@app.route("/committed_balance")
def committed_balance():
    return jsonify(sum(state.committed_utxos[node.public_key].values()))


@app.route("/balances")
def balances():
    return jsonify(
        [sum(state.utxos[public_key].values()) for public_key in node.public_keys]
    )


@app.route("/committed_balances")
def committed_balances():
    return jsonify(
        [
            sum(state.committed_utxos[public_key].values())
            for public_key in node.public_keys
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
    return jsonify(
        [
            transaction.__dict__
            for transaction in state.blockchain.blocks[-1].transactions
        ]
    )


@app.route("/busy")
def busy():
    return jsonify(state.lock.locked())


# Get metrics


@app.route("/metrics/average_throughput")
def average_throughput():
    return jsonify(metrics.average_throughput.get())


@app.route("/metrics/average_block_time")
def average_block_time():
    return jsonify(metrics.average_block_time.get())


@app.route("/metrics/statistics")
def statistics():
    return jsonify(metrics.statistics)


# Post

# TODO authorize this view
@app.route("/transaction", methods=["POST"])
def transaction():
    json = request.get_json()

    # metrics
    metrics.average_throughput.increment()

    with state.lock:
        Transaction(json["receiver_public_key"], json["amount"])
    metrics.statistics["transactions_created"] += 1
    return ""


@app.route("/transaction/validate", methods=["POST"])
def transaction_validate():
    transaction = loads(request.get_data())

    # metrics
    metrics.average_throughput.increment()

    with state.lock:
        transaction.validate(state.utxos)
    metrics.statistics["transactions_validated"] += 1
    return ""


# TODO should mining be more parallel?
@app.route("/block/validate", methods=["POST"])
def block_validate():
    block = loads(request.get_data())
    state.validating_block.set()
    with state.lock:
        try:
            block.validate()
        except:
            state.validating_block.clear()
            state.block.mine()
    state.validating_block.clear()
    metrics.statistics["blocks_validated"] += 1
    return ""


# Quit


@app.route("/quit", methods=["POST"])
def quit():
    request.environ.get("werkzeug.server.shutdown")()
    return ""
