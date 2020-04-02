#!/usr/bin/env python3.8

from argparse import ArgumentParser
from pickle import dumps, loads

from requests import get, post

from config import N_NODES

_parser = ArgumentParser(add_help=False)
_parser.add_argument("-h", "--host", type=str)
_parser.add_argument("-p", "--port", type=int)
_args = _parser.parse_args()
host = _args.host
port = _args.port
address = f"{host}:{port}"

public_keys = loads(get(f"http://{address}/public_keys").content)
index = loads(get(f"http://{address}/index").content)

with open(
    f"/home/user/distributed/transactions/{N_NODES}nodes/transactions{index}.txt"
) as f:
    for line in f:
        index, amount = map(int, line[2:].split())
        post(f"http://{address}/transaction", data=dumps((public_keys[index], amount)))

balance = loads(get(f"http://{address}/balance").content)
print(balance)
