from pickle import dumps
from threading import Thread

from requests import post

import node


def broadcast(path, data):
    for address in node.addresses:
        if address != node.address:
            Thread(
                target=post,
                args=[f"http://{address}{path}"],
                kwargs={"data": dumps(data)},
            ).start()
