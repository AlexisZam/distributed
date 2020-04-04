from pickle import dumps, loads
from threading import Lock

from Cryptodome.PublicKey import RSA
from requests import post

from config import BOOTSTRAP_ADDRESS, HOST, PORT

address = f"{HOST}:{PORT}"

private_key = RSA.generate(2048)
public_key = private_key.publickey().exportKey()

if address == BOOTSTRAP_ADDRESS:
    index = 0
    lock = Lock()
    addresses = [address]
    public_keys = [public_key]
else:
    index, addresses, public_keys = loads(
        post(
            f"http://{BOOTSTRAP_ADDRESS}/login", data=dumps((address, public_key)),
        ).content
    )
