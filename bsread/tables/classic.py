from .bases import BaseTable
from .data import unpack


SEPARATOR = "\t"


class ClassicTable(BaseTable):

    def run(self):
        join = SEPARATOR.join
        while True:
            msg = self.receive_func()
            data = unpack(msg, self.channel_filter)

            if msg.format_changed:
                print()
                cols = data.keys()
                print(join(cols))

            row = data.values()
            print(join(map(str, row)))



