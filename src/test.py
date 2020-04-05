#!/usr/bin/env python3.8

from argparse import ArgumentParser
from math import ceil
from pickle import dumps, loads
from pprint import pprint
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

assert len(public_keys) == n_nodes

for _ in range(3):
    balances = loads(get(f"http://{address}/balances").content)
    if all(balance == 100 for balance in balances):
        break
    sleep(5)

print(balances)
assert all(balance == 100 for balance in balances)

sleep(20)

with open(
    f"/home/user/distributed/transactions/{ceil(n_nodes / 5) * 5}nodes/transactions{index}.txt"
) as f:
    for line in f:
        index, amount = map(int, line[2:].split())
        if index < n_nodes:
            post(
                f"http://{address}/transaction",
                data=dumps((public_keys[index], amount)),
            )

prev_balances = loads(get(f"http://{address}/balances").content)
prev_committed_balances = loads(get(f"http://{address}/balances").content)
n_equals = 0
while True:
    sleep(20)
    curr_balances = loads(get(f"http://{address}/balances").content)
    curr_committed_balances = loads(get(f"http://{address}/balances").content)
    if (
        curr_balances == prev_balances
        and curr_committed_balances == prev_committed_balances
    ):
        n_equals += 1
        if n_equals == 5:
            break
    else:
        n_equals = 0
    prev_balances = curr_balances
    prev_committed_balances = curr_committed_balances

average_block_time = loads(get(f"http://{address}/metrics/average_block_time").content)
pprint("Average block time")
pprint(average_block_time)

average_throughput = loads(get(f"http://{address}/metrics/average_throughput").content)
pprint("Average throughput")
pprint(average_throughput)

statistics = loads(get(f"http://{address}/metrics/statistics").content)
pprint("Statistics")
pprint(statistics)

balances = loads(get(f"http://{address}/balances").content)
pprint("Balances")
pprint(balances)
assert sum(balances) == n_nodes * 100

committed_balances = loads(get(f"http://{address}/committed_balances").content)
pprint("Committed balances")
pprint(committed_balances)
assert sum(committed_balances) == n_nodes * 100

post(f"http://{address}/quit")
