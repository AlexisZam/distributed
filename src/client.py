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
        parser.add_argument("receiver_public_key", type=str)
        parser.add_argument("amount", type=int)
        args = parser.parse_args(args=arg.split())

        post(
            f"http://{address}/transaction",
            data=dumps((args.receiver_public_key, args.amount)),
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


parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", type=str)
parser.add_argument("-p", "--port", type=int)
args = parser.parse_args()
address = f"{args.host}:{args.port}"

REPL().cmdloop()
