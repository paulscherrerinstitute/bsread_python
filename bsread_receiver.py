#!/usr/bin/env python

import bsread
import zmq


def handle_data_header(header):
    print header


if __name__ == "__main__":
    receiver = bsread.Bsread(mode=zmq.PULL)
    bsread.connect(address="tcp://localhost:9999", conn_type="connect", )

    while True:
        message_data = bsread.receive()
        if "data_header" in message_data:
            print "Data Header: ", message_data['data_header']
        print message_data['data']
