from .bases import BaseTable
from .data import make_cols, make_row


SEPARATOR = "\t"


class ClassicTable(BaseTable):

    def run(self):
        join = SEPARATOR.join
        while True:
            msg = self.receive_func()

            if msg.format_changed:
                print()
                cols = make_cols(msg)
                print(join(cols))

            row = make_row(msg)
            print(join(map(str, row)))



