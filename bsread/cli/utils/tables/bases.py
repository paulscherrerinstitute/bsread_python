from abc import ABC, abstractmethod

from .data import TableData


class BaseDataTable(ABC):

    def __init__(self, receive_func, channel_filter, max_rows):
        self.data = TableData(receive_func, channel_filter, max_rows)

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

    def __init__(self, receive_func, channel_filter, clear):
        self.receive_func = receive_func
        self.channel_filter = channel_filter
        self.clear = clear

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

    def clear_screen(self):
        print(chr(27) + "[2J")



