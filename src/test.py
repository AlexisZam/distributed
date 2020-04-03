#!/usr/bin/env python3.8

from argparse import ArgumentParser
from pickle import dumps, loads
from time import sleep

from requests import get, post

parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
parser.add_argument("-p", "--port", default=5000, type=int)
parser.add_argument("-n", "--n_nodes", default=1, type=int)
args = parser.parse_args()
address = f"{args.host}:{args.port}"
n_nodes = args.n_nodes

public_keys = loads(get(f"http://{address}/public_keys").content)
index = loads(get(f"http://{address}/index").content)

with open(
    f"/home/user/distributed/transactions/{n_nodes}nodes/transactions{index}.txt"
) as f:
    for line in f:
        index, amount = map(int, line[2:].split())
        post(f"http://{address}/transaction", data=dumps((public_keys[index], amount)))

sleep(5)

average_block_time = loads(get(f"http://{address}/metrics/average_block_time").content)
print(average_block_time)

average_throughput = loads(get(f"http://{address}/metrics/average_throughput").content)
print(average_throughput)

balance = loads(get(f"http://{address}/balance").content)
print(balance)

post(f"http://{address}/quit")
