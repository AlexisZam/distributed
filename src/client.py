#!/usr/bin/env python3.8

import readline
from argparse import ArgumentParser
from cmd import Cmd
from pickle import dumps, loads
from pprint import pprint

from requests import get, post


class REPL(Cmd):
    intro = 'Noobcash 1.0\nType "help" for more information.'
    prompt = ">>> "

    def do_transaction(self, arg):
        parser = ArgumentParser(prog="transaction", add_help=False)
        parser.add_argument("index", type=int)
        parser.add_argument("amount", type=int)
        args = parser.parse_args(args=arg.split())

        receiver_public_key = loads(
            get(f"http://{address}/nodes/{args.index}/public_key").content
        )
        post(
            f"http://{address}/transaction",
            data=dumps((receiver_public_key, args.amount)),
        )

    def do_view(self, _):
        transactions = loads(
            get(f"http://{address}/blockchain/top/transactions").content
        )
        pprint(transactions)

    def do_balance(self, _):
        balance = loads(get(f"http://{address}/balance").content)
        pprint(balance)

    def do_help(self, _):
        print(
            "transaction receiver_public_key amount",
            "view",
            "balance",
            "help",
            sep="\n",
        )

    # FIXME delete hereafter

    def do_balances(self, _):
        balances = loads(get(f"http://{address}/balances").content)
        pprint(balances)

    def do_average_throughput(self, _):
        average_throughput = loads(
            get(f"http://{address}/metrics/average_throughput").content
        )
        pprint(average_throughput)

    def do_average_block_time(self, _):
        average_block_time = loads(
            get(f"http://{address}/metrics/average_block_time").content
        )
        pprint(average_block_time)

    def do_statistics(self, _):
        statistics = loads(get(f"http://{address}/metrics/statistics").content)
        pprint(statistics)


parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
parser.add_argument("-p", "--port", default=5000, type=int)
args = parser.parse_args()
address = f"{args.host}:{args.port}"

REPL().cmdloop()
