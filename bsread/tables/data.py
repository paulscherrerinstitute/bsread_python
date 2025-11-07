from time import sleep
from collections import deque
from threading import Event, Lock, Thread


FIXED = [
    "pulse_id",
    "global_timestamp",
    "global_timestamp_offset"
]


class TableData:

    def __init__(self, receive_func, max_rows):
        self.receive_func = receive_func
        self._cols = []
        self._rows = deque(maxlen=max_rows)
        self.lock_cols = Lock()
        self.lock_rows = Lock()
        self.running = Event()


    def start(self):
        def collect():
            self.running.set()
            while self.running.is_set():
                msg = self.receive_func()

                if msg.format_changed:
                    with self.lock_cols:
                        self._cols.clear()
                    with self.lock_rows:
                        self._rows.clear()

                with self.lock_cols:
                    if not self._cols:
                        cols = make_cols(msg)
                        self._cols.extend(cols)

                row = make_row(msg)
                with self.lock_rows:
                    self._rows.append(row)

        Thread(target=collect, daemon=True).start()


    def stop(self):
        self.running.clear()
        sleep(0.1) # give the collect loop time to end


    @property
    def cols(self):
        with self.lock_cols:
            return list(self._cols)

    @property
    def rows(self):
        with self.lock_rows:
            return list(self._rows)



def make_cols(msg):
    return FIXED + list(msg.data.keys())

def make_row(msg):
    return [getattr(msg, i) for i in FIXED] + [v.value for v in msg.data.values()]



