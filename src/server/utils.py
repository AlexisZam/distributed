from pickle import dumps
from threading import Thread

from requests import post

import node


def broadcast(path, data):
    for address in node.addresses:
        if address != node.address:
            post(f"http://{address}{path}", data=dumps(data))
