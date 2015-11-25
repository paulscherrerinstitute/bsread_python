#!/usr/bin/env python

import writer as wr

if __name__ == "__main__":
    writer = wr.Writer()

    writer.open_file('test.h5')
    writer.add_dataset('/test/data')

    for number in range(0, 100):
        writer.write([number])

    writer.close_file()