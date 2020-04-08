from threading import Lock

from Cryptodome.PublicKey import RSA
from requests import post

from config import BOOTSTRAP_ADDRESS, HOST, PORT

# user info

private_key = RSA.generate(2048)
public_key = private_key.publickey().exportKey().decode()

# miner info

address = f"{HOST}:{PORT}"

if address == BOOTSTRAP_ADDRESS:
    index = 0
    addresses = [address]
    public_keys = [public_key]
else:
    index, addresses, public_keys = post(
        f"http://{BOOTSTRAP_ADDRESS}/login",
        json={"address": address, "public_key": public_key},
    ).json()
