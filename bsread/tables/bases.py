from abc import ABC, abstractmethod

from .data import TableData


class BaseDataTable(ABC):

    def __init__(self, receive_func, max_rows, channel_filter):
        self.data = TableData(receive_func, max_rows, channel_filter)

    def start(self):
        try:
            self.data.start()
            self.run()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.data.stop()

    @abstractmethod
    def run(self):
        raise NotImplementedError



class BaseTable(ABC):

    def __init__(self, receive_func, channel_filter):
        self.receive_func = receive_func
        self.channel_filter = channel_filter

    def start(self):
        try:
            self.run()
        except KeyboardInterrupt:
            pass

    def stop(self):
        pass

    @abstractmethod
    def run(self):
        raise NotImplementedError



