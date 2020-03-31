#!/usr/bin/env python3.8

from argparse import ArgumentParser
from pickle import dumps, loads
from requests import get, post
from sys import stdin
from time import sleep

from config import n_nodes

_parser = ArgumentParser(add_help=False)
_parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
_parser.add_argument("-p", "--port", default=5000, type=int)
_args = _parser.parse_args()
host = _args.host
port = _args.port
address = f"{host}:{port}"

while True:
    public_keys = loads(get(f"http://{address}/public_keys").content)
    if len(public_keys) == n_nodes:
        break
    sleep(1)

index = loads(get(f"http://{address}/index").content)

with open(
    f"/home/user/distributed/transactions/{n_nodes}nodes/transactions{index}.txt"
) as f:
    for line in f:
        index, amount = line.split()
        index = int(index[2:])
        data = {"receiver_public_key": public_keys[index], "amount": int(amount)}
        post(f"http://{address}/transaction", data=dumps(data))

balance = loads(get(f"http://{address}/balance").content)
print(balance)
