from time import sleep
from collections import deque
from threading import Event, Lock, Thread


META = [
    "pulse_id",
    "global_timestamp",
    "global_timestamp_offset"
]


class TableData:

    def __init__(self, receive_func, max_rows, channel_filter):
        self.receive_func = receive_func
        self.channel_filter = channel_filter
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
                data = unpack(msg, self.channel_filter)

                if msg.format_changed:
                    with self.lock_cols:
                        self._cols.clear()
                    with self.lock_rows:
                        self._rows.clear()

                with self.lock_cols:
                    if not self._cols:
                        cols = data.keys()
                        self._cols.extend(cols)

                row = data.values()
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



def unpack(msg, channel_filter):
    meta = unpack_meta(msg)
    data = unpack_data(msg, channel_filter)
    return merge_dicts(meta, data)

def unpack_meta(msg):
    return {i: str(getattr(msg, i)) for i in META}

def unpack_data(msg, channel_filter):
    return {k: str(v.value) for k, v in msg.data.items() if channel_filter is None or k in channel_filter}

def merge_dicts(*args):
    res = {}
    for d in args:
        res.update(d)
    return res



