from argparse import ArgumentParser
from pickle import dumps, loads
from threading import Lock

from Cryptodome.PublicKey import RSA
from requests import post

from config import BOOTSTRAP_ADDRESS

_parser = ArgumentParser(add_help=False)
_parser.add_argument("-h", "--host", type=str)
_parser.add_argument("-p", "--port", type=int)
_args = _parser.parse_args()
host = _args.host
port = _args.port
address = f"{host}:{port}"

private_key = RSA.generate(2048)
public_key = private_key.publickey().exportKey()

if address == BOOTSTRAP_ADDRESS:
    index = 0
    addresses_lock = Lock()
    addresses = [address]
    public_keys_lock = Lock()
    public_keys = [public_key]
else:
    index, addresses, public_keys = loads(
        post(
            f"http://{BOOTSTRAP_ADDRESS}/login", data=dumps((address, public_key))
        ).content
    )
