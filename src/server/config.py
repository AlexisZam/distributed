from argparse import ArgumentParser

parser = ArgumentParser(add_help=False)
parser.add_argument("-h", "--host", default="192.168.1.1", type=str)
parser.add_argument("-p", "--port", default=5000, type=int)
parser.add_argument("-b", "--bootstrap_address", default="192.168.1.1:5000", type=str)
parser.add_argument("-c", "--capacity", default=2, type=int)
parser.add_argument("-d", "--difficulty", default=4, type=int)
parser.add_argument("-n", "--n_nodes", default=3, type=int)
args = parser.parse_args()

BOOTSTRAP_ADDRESS = args.bootstrap_address
HOST = args.host
PORT = args.port
CAPACITY = args.capacity
DIFFICULTY = args.difficulty
N_NODES = args.n_nodes
