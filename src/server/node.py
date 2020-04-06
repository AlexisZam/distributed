from threading import Lock

from Cryptodome.PublicKey import RSA
from requests import post

from config import BOOTSTRAP_ADDRESS, HOST, PORT

address = f"{HOST}:{PORT}"

private_key = RSA.generate(2048)
public_key = private_key.publickey().exportKey().decode()

if address == BOOTSTRAP_ADDRESS:
    index = 0
    addresses = [address]
    public_keys = [public_key]
else:
    index = None
    addresses = []
    public_keys = []
