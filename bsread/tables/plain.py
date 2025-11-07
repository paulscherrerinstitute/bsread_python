from .bases import BaseTable
from .data import make_cols, make_row


SEPARATOR = " "


class PlainTable(BaseTable):

    def run(self):
        join = SEPARATOR.join
        cols = []
        widths = []

        while True:
            msg = self.receive_func()

            if msg.format_changed or not cols:
                cols = strs(make_cols(msg))
                widths_cols = lens(cols)

            row = strs(make_row(msg))
            widths_row = lens(row)

            widths_new = maxof(widths_cols, widths_row)
            widths_changed = widths_new != widths

            if msg.format_changed or widths_changed:
                widths = widths_new
                print()
                print(join(pad(cols, widths)))

            print(join(pad(row, widths)))



def strs(seq):
    return [str(i) for i in seq]

def lens(seq):
    return [len(i) for i in seq]

def pad(strings, lengths):
    return [s.ljust(l) for s, l in zip(strings, lengths)]

def maxof(seq1, seq2):
    return [max(i, j) for i, j in zip(seq1, seq2)]



