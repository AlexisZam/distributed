#!/usr/bin/env python3.8

from pickle import dumps, loads
from threading import Lock, Thread
from time import sleep

from requests import get, post

import node
import state
from app import app
from blockchain import Blockchain
from config import BOOTSTRAP_ADDRESS, HOST, PORT

Thread(target=app.run, kwargs={"host": HOST, "port": PORT}).start()

if node.address != BOOTSTRAP_ADDRESS:
    node.index, node.addresses, node.public_keys = post(
        f"http://{BOOTSTRAP_ADDRESS}/login",
        json={"address": node.address, "public_key": node.public_key},
    ).json()

    with state.lock:
        state.blockchain = loads(get(f"http://{BOOTSTRAP_ADDRESS}/blockchain").content)
        state.blockchain.validate()

    post(
        f"http://{BOOTSTRAP_ADDRESS}/transaction",
        json={"receiver_public_key": node.public_key, "amount": 100},
    )
