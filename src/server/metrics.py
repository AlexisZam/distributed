from threading import Lock
from time import time


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
            return self.__sum / self.__counter


class AverageThroughput:
    def __init__(self):
        self.__lock = Lock()
        self.__counter = 0

    def increment(self):
        with self.__lock:
            if self.__counter == 0:
                self.__start = time()
            self.__counter += 1

    def time(self):
        with self.__lock:
            self.__finish = time()

    def get(self):
        with self.__lock:
            return self.__counter / (self.__finish - self.__start)


average_block_time = AverageBlockTime()
average_throughput = AverageThroughput()
