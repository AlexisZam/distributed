#!/usr/bin/env python3.8

from argparse import ArgumentParser
from math import ceil
from pickle import dumps, loads
from pprint import pprint
from time import sleep

from requests import get, post

parser = ArgumentParser(add_help=False)
parser.add_argument("-a", "--address", default="127.0.0.1:5000", type=str)
parser.add_argument("-n", "--n_nodes", default=1, type=int)
args = parser.parse_args()

public_keys = loads(get(f"http://{args.address}/public_keys").content)
while len(public_keys) != args.n_nodes:
    sleep(1)

addresses = loads(get(f"http://{args.address}/addresses").content)
while any(loads(get(f"http://{address}/busy").content) for address in addresses):
    sleep(1)

balances = loads(get(f"http://{args.address}/balances").content)
assert all(balance == 100 for balance in balances)

index = loads(get(f"http://{args.address}/index").content)
with open(
    f"/home/user/distributed/transactions/{ceil(args.n_nodes / 5) * 5}nodes/transactions{index}.txt"
) as f:
    for line in f:
        index, amount = map(int, line[2:].split())
        if index < args.n_nodes:
            post(
                f"http://{args.address}/transaction",
                data=dumps((public_keys[index], amount)),
            )

while any(loads(get(f"http://{address}/busy").content) for address in addresses):
    sleep(1)

average_block_time = loads(
    get(f"http://{args.address}/metrics/average_block_time").content
)
print("Average block time:", average_block_time)

average_throughput = loads(
    get(f"http://{args.address}/metrics/average_throughput").content
)
print("Average throughput:", average_throughput)

statistics = loads(get(f"http://{args.address}/metrics/statistics").content)
print("Statistics:", statistics)

balances = loads(get(f"http://{args.address}/balances").content)
print("Balances:", balances)
assert sum(balances) == args.n_nodes * 100

committed_balances = loads(get(f"http://{args.address}/committed_balances").content)
print("Committed balances:", committed_balances)
assert sum(committed_balances) == args.n_nodes * 100

post(f"http://{args.address}/quit")
