from argparse import ArgumentParser
from Cryptodome.PublicKey import RSA

private_key = RSA.generate(2048)
public_key = private_key.publickey().exportKey()

_parser = ArgumentParser(add_help=False)
_parser.add_argument("-h", "--host", default="127.0.0.1", type=str)
_parser.add_argument("-p", "--port", default=5000, type=int)
_args = _parser.parse_args()
host = _args.host
port = _args.port
address = f"{host}:{port}"
