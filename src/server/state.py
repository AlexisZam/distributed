from collections import defaultdict
from pickle import dumps, loads
from threading import Event, Lock, Thread

from requests import get, post

import node
import state
from block import Block
from blockchain import Blockchain
from config import BOOTSTRAP_ADDRESS

lock = Lock()

block = Block()
utxos = defaultdict(dict)
committed_utxos = defaultdict(dict)

busy = Event()

validating_block = Event()

if node.address == BOOTSTRAP_ADDRESS:
    blockchain = Blockchain()
else:
    blockchain = None
