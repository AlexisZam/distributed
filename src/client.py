#!/usr/bin/env python3.8

import readline
from argparse import ArgumentParser
from cmd import Cmd

from requests import get, post


class REPL(Cmd):
    intro = 'Noobcash 1.0\nType "help" for more information.'
    prompt = ">>> "

    def do_transaction(self, arg):
        parser = ArgumentParser(prog="transaction", add_help=False)
        parser.add_argument("index", type=int)
        parser.add_argument("amount", type=int)
        args = parser.parse_args(args=arg.split())

        receiver_public_key = get(
            f"http://{address}/nodes/{args.index}/public_key"
        ).json()
        post(
            f"http://{address}/transaction",
            json={"receiver_public_key": receiver_public_key, "amount": args.amount},
        )

    def do_view(self, _):
        transactions = get(f"http://{address}/blockchain/blocks/last").json()
        print(transactions)

    def do_balance(self, _):
        balance = get(f"http://{address}/balance").json()
        print(balance)

    def do_help(self, _):
        print(
            "transaction receiver_public_key amount",
            "view",
            "balance",
            "help",
            sep="\n",
        )


parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
parser.add_argument("-p", "--port", default=5000, type=int)
args = parser.parse_args()
address = f"{args.host}:{args.port}"

REPL().cmdloop()
