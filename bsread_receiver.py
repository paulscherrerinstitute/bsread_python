#!/usr/bin/env python

import bsread
import zmq


def handle_data_header(header):
    print header


if __name__ == "__main__":
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address="tcp://localhost:9999", conn_type="connect", )
    receiver.set_data_header_handler(handle_data_header)

    while True:
        print receiver.receive()
