#!/usr/bin/env python3.8

import readline
from argparse import ArgumentParser
from cmd import Cmd
from pickle import dumps, loads

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
        print(transactions)

    def do_balance(self, _):
        balance = loads(get(f"http://{address}/balance").content)
        print(balance)

    def do_help(self, _):
        print(
            "transaction receiver_public_key amount",
            "view",
            "balance",
            "help",
            sep="\n",
        )

    # FIXME remove from here onwards

    def do_index(self, _):
        index = loads(get(f"http://{address}/index").content)
        print(index)


parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
parser.add_argument("-p", "--port", default=5000, type=int)
args = parser.parse_args()
address = f"{args.host}:{args.port}"

REPL().cmdloop()
