from collections import defaultdict
from pickle import dumps, loads
from threading import RLock, Thread  # FIXME

from requests import get, post

import node
from block import Block
from blockchain import Blockchain
from config import BOOTSTRAP_ADDRESS

block_lock = RLock()
block = Block()  # FIXME

utxos_lock = RLock()
utxos = defaultdict(dict)
committed_utxos_lock = RLock()
committed_utxos = defaultdict(dict)

blockchain_lock = RLock()
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
