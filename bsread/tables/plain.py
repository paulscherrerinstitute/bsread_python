from .bases import BaseTable
from .data import unpack


SEPARATOR = " "


class PlainTable(BaseTable):

    def run(self):
        join = SEPARATOR.join
        cols = []
        widths = []

        while True:
            msg = self.receive_func()
            data = unpack(msg, self.channel_filter)

            if msg.format_changed or self.clear or not cols:
                cols = data.keys()
                widths_cols = lens(cols)

            row = data.values()
            widths_row = lens(row)

            widths_new = maxof(widths_cols, widths_row)
            widths_changed = widths_new != widths

            if msg.format_changed or self.clear or widths_changed:
                if self.clear:
                    self.clear_screen()
                widths = widths_new
                print()
                print(join(pad(cols, widths)))

            print(join(pad(row, widths)))



def lens(seq):
    return [len(i) for i in seq]

def pad(strings, lengths):
    return [s.ljust(l) for s, l in zip(strings, lengths)]

def maxof(seq1, seq2):
    return [max(i, j) for i, j in zip(seq1, seq2)]



