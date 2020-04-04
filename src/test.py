#!/usr/bin/env python3.8

from argparse import ArgumentParser
from pickle import dumps, loads
from pprint import pprint
from time import sleep
from math import ceil

from requests import get, post

parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
parser.add_argument("-p", "--port", default=5000, type=int)
parser.add_argument("-n", "--n_nodes", default=1, type=int)
args = parser.parse_args()
address = f"{args.host}:{args.port}"
n_nodes = args.n_nodes

sleep(5)

public_keys = loads(get(f"http://{address}/public_keys").content)
index = loads(get(f"http://{address}/index").content)

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
while True:
    sleep(5)
    curr_balances = loads(get(f"http://{address}/balances").content)
    if curr_balances == prev_balances:
        sleep(60)
        if curr_balances == loads(get(f"http://{address}/balances").content):
            break
    prev_balances = curr_balances

average_block_time = loads(get(f"http://{address}/metrics/average_block_time").content)
pprint("Average block time")
pprint(average_block_time)

average_throughput = loads(get(f"http://{address}/metrics/average_throughput").content)
pprint("Average throughput")
pprint(average_throughput)

statistics = loads(get(f"http://{address}/metrics/statistics").content)
pprint("Statistics")
pprint(statistics)

balance = loads(get(f"http://{address}/balance").content)
pprint("Balance")
pprint(balance)

balances = loads(get(f"http://{address}/balances").content)
pprint("Balances")
pprint(balances)

post(f"http://{address}/quit")
