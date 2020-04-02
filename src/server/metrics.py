from threading import Lock


class AverageBlockTime:
    def __init__(self):
        self.lock = Lock()
        self.__sum = 0
        self.__counter = 0

    def add(self, block_time):
        with self.lock:
            self.__sum += block_time
            self.__counter += 1

    def get(self):
        with self.lock:
            return self.__sum / self.__counter


class AverageThroughput:  # FIXME
    def __init__(self):
        self.__lock = Lock()
        self.__counter = 0

    def add(self):
        self.__counter += 1

    def get(self):
        with self.__lock:
            return self.__counter


average_block_time = AverageBlockTime()
average_throughout = AverageThroughput()
