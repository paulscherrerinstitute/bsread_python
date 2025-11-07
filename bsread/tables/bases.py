from abc import ABC, abstractmethod

from .data import TableData


class BaseDataTable(ABC):

    def __init__(self, receive_func, max_rows):
        self.data = TableData(receive_func, max_rows)

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

    def __init__(self, receive_func):
        self.receive_func = receive_func

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



