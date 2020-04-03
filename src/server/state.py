from collections import defaultdict
from pickle import dumps, loads
from threading import RLock, Thread  # FIXME

from requests import get, post

import node
from block import Block
from blockchain import Blockchain
from config import BOOTSTRAP_ADDRESS

lock = RLock()

block = Block()  # FIXME

utxos = defaultdict(dict)
committed_utxos = defaultdict(dict)

if node.address == BOOTSTRAP_ADDRESS:
    blockchain = Blockchain()
else:
    blockchain = loads(get(f"http://{BOOTSTRAP_ADDRESS}/blockchain").content)
    blockchain.validate()
    Thread(
        target=post,
        args=[f"http://{BOOTSTRAP_ADDRESS}/transaction"],
        kwargs={"data": dumps((node.public_key, 100))},
    ).start()  # FIXME
