from collections import defaultdict
from threading import Lock
from time import time

from config import N_NODES


class AverageBlockTime:
    def __init__(self):
        self.lock = Lock()
        self.sum = 0
        self.counter = 0

    def add(self, block_time):
        with self.lock:
            self.sum += block_time
            self.counter += 1

    def get(self):
        with self.lock:
            return None if self.counter == 0 else self.sum / self.counter


class AverageThroughput:
    def __init__(self):
        self.lock = Lock()
        self.counter = 0

    def increment(self):
        with self.lock:
            if self.counter == N_NODES - 1:
                self.start = time()
            self.counter += 1

    def time(self):
        with self.lock:
            self.finish = time()

    def get(self):
        with self.lock:
            return (
                None
                if self.counter == 0
                else (self.counter - (N_NODES - 1)) / (self.finish - self.start)
            )


average_block_time = AverageBlockTime()
average_throughput = AverageThroughput()
statistics = defaultdict(int)
