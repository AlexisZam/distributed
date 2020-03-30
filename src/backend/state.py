from collections import defaultdict
from threading import Lock

addresses = []
addresses_lock = Lock()

public_keys = {}
public_keys_lock = Lock()

block = None
block_lock = Lock()

blockchain = None
blockchain_lock = Lock()

committed_utxos = defaultdict(dict)
committed_utxos_lock = Lock()

utxos = defaultdict(dict)
utxos_lock = Lock()
