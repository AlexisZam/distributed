#!/usr/bin/env python3.8

from argparse import ArgumentParser
from math import ceil
from pprint import pprint
from time import sleep

from requests import get, post

parser = ArgumentParser(add_help=False)
parser.add_argument("-a", "--address", default="127.0.0.1:5000", type=str)
parser.add_argument("-n", "--n_nodes", default=1, type=int)
args = parser.parse_args()

while True:
    public_keys = get(f"http://{args.address}/public_keys").json()
    if len(public_keys) == args.n_nodes:
        break

addresses = get(f"http://{args.address}/addresses").json()
while True:
    if all(
        all(balance == 100 for balance in get(f"http://{address}/balances").json())
        for address in addresses
    ):
        break
    sleep(5)

sleep(5)
index = get(f"http://{args.address}/index").json()

with open(
    f"/home/user/distributed/transactions/{ceil(args.n_nodes / 5) * 5}nodes/transactions{index}.txt"
) as f:
    for line in f:
        index, amount = map(int, line[2:].split())
        if index < args.n_nodes:
            post(
                f"http://{args.address}/transaction",
                json={"receiver_public_key": public_keys[index], "amount": amount},
            )

# counter = 0
# while True:
#     if not any(get(f"http://{address}/busy").json() for address in addresses):
#         counter += 1
#         if counter == 5:
#             break
#     else:
#         counter = 0
#     sleep(1)

prev_balances = get(f"http://{args.address}/balances").json()
prev_committed_balances = get(f"http://{args.address}/balances").json()
n_equals = 0
while True:
    sleep(5)
    curr_balances = get(f"http://{args.address}/balances").json()
    curr_committed_balances = get(f"http://{args.address}/balances").json()
    if (
        curr_balances == prev_balances
        and curr_committed_balances == prev_committed_balances
    ):
        n_equals += 1
        if n_equals == 10:
            break
    else:
        n_equals = 0
    prev_balances = curr_balances
    prev_committed_balances = curr_committed_balances

average_block_time = get(f"http://{args.address}/metrics/average_block_time").json()
print("Average block time:", average_block_time)

average_throughput = get(f"http://{args.address}/metrics/average_throughput").json()
print("Average throughput:", average_throughput)

statistics = get(f"http://{args.address}/metrics/statistics").json()
print("Statistics:", statistics)

balances = get(f"http://{args.address}/balances").json()
print("Balances:", balances)
assert sum(balances) == args.n_nodes * 100

committed_balances = get(f"http://{args.address}/committed_balances").json()
print("Committed balances:", committed_balances)
assert sum(committed_balances) == args.n_nodes * 100

post(f"http://{args.address}/quit")
