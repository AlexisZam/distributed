from collections import defaultdict
from threading import Lock
from time import time

from config import N_NODES


class AverageBlockTime:
    def __init__(self):
        self.__lock = Lock()
        self.__sum = 0
        self.__counter = 0

    def add(self, block_time):
        with self.__lock:
            self.__sum += block_time
            self.__counter += 1

    def get(self):
        with self.__lock:
            return None if self.__counter == 0 else self.__sum / self.__counter


class AverageThroughput:
    def __init__(self):
        self.__lock = Lock()
        self.__counter = 0

    def increment(self):
        with self.__lock:
            self.__counter += 1
            if self.__counter == N_NODES:
                self.__start = time()

    def time(self):
        with self.__lock:
            self.__finish = time()

    def get(self):
        with self.__lock:
            return (
                None
                if self.__counter == 0
                else self.__counter / (self.__finish - self.__start)
            )


average_block_time = AverageBlockTime()
average_throughput = AverageThroughput()
statistics = defaultdict(int)
