#!/usr/bin/env python3.8

from argparse import ArgumentParser
from cmd import Cmd
import readline
from pickle import dumps, loads
from pprint import pprint
from requests import get, post


class REPL(Cmd):
    intro = 'Noobcash 1.0\nType "help" for more information.'
    prompt = ">>> "

    def do_transaction(self, arg):
        parser = ArgumentParser(prog="transaction", add_help=False)
        parser.add_argument("receiver_public_key", type=str)
        parser.add_argument("amount", type=int)
        args = parser.parse_args(args=arg.split())

        data = {"receiver_public_key": args.receiver_public_key, "amount": args.amount}
        post(f"http://{address}/create_transaction", data=dumps(data))

    def do_view(self, _):
        transactions = loads(get(f"http://{address}/view").content)
        pprint(transactions)

    def do_balance(self, _):
        balance = loads(get(f"http://{address}/balance").content)
        print(balance)

    def do_help(self, _):
        # TODO add explanations
        print(
            "transaction receiver_address amount", "view", "balance", "help", sep="\n"
        )


parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
parser.add_argument("-p", "--port", default=5000, type=int)
args = parser.parse_args()
address = f"{args.host}:{args.port}"

REPL().cmdloop()
